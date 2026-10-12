"""Read-only INDRA -> Project Delphi evaluation. Python standard library only."""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen

URL = "https://db.indra.bio/statements/from_agents?agent0=GJA1&limit=40&ev_limit=5"
PK = "https://w3id.org/probknow/ontology/"
BASE = "urn:delphi:pilot:indra:"
SUPPORTED = {
    "Activation": ("subj", "obj"), "Inhibition": ("subj", "obj"),
    "IncreaseAmount": ("subj", "obj"), "DecreaseAmount": ("subj", "obj"),
    "Phosphorylation": ("enz", "sub"), "Dephosphorylation": ("enz", "sub"),
    "Ubiquitination": ("enz", "sub"), "Hydroxylation": ("enz", "sub"),
    "Acetylation": ("enz", "sub"), "Complex": ("members",),
}
CONTEXT = {
    "pk": PK, "pilot": BASE, "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "prov": "http://www.w3.org/ns/prov#", "dct": "http://purl.org/dc/terms/",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def refs(ev):
    values = dict(ev.get("text_refs") or {})
    if ev.get("pmid"):
        values.setdefault("PMID", ev["pmid"])
    out = []
    for kind in ("PMID", "PMCID", "DOI"):
        value = str(values.get(kind) or "").strip()
        if not value:
            continue
        if kind == "DOI":
            value = value.lower().removeprefix("https://doi.org/").removeprefix("doi:")
        if kind == "PMCID":
            value = value.upper()
        out.append(f"{kind}:{value}")
    return sorted(set(out))


def paper_url(ref):
    kind, value = ref.split(":", 1)
    from urllib.parse import quote
    return {"PMID": "https://pubmed.ncbi.nlm.nih.gov/",
            "PMCID": "https://pmc.ncbi.nlm.nih.gov/articles/",
            "DOI": "https://doi.org/"}[kind] + quote(value, safe="/")


def statements(payload):
    data = payload.get("results", payload.get("statements")) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        return [(str(k), v) for k, v in data.items()]
    if isinstance(data, list):
        return [(str(v.get("matches_hash") or v.get("id") or digest(v)), v) for v in data]
    raise ValueError("Expected INDRA statement list or results/statements object")


def map_sample(payload):
    entries = statements(payload)
    if not entries:
        raise ValueError("INDRA returned no statements")
    # Union paper aliases before mapping, including aliases arriving in later statements.
    # These are source-document groups, never a claim of independent experiments.
    parent = {}

    def root(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = root(parent[x])
        return parent[x]

    for _, st in entries:
        for ev in st.get("evidence", []):
            ids = refs(ev)
            for ident in ids:
                parent[root(ident)] = root(ids[0])
    groups = {}
    for ident in list(parent):
        groups.setdefault(root(ident), []).append(ident)
    papers, lookup = {}, {}
    for aliases in groups.values():
        aliases.sort()
        pid = BASE + "paper:" + digest(aliases)
        conflict = any(sum(a.startswith(k + ":") for a in aliases) > 1 for k in ("PMID", "PMCID", "DOI"))
        papers[pid] = {"id": pid, "references": aliases, "identityConflict": conflict}
        for alias in aliases:
            lookup[alias] = pid

    claims, quarantined, seen, duplicate_rows = [], [], {}, 0
    for source_id, st in entries:
        kind = st.get("type")
        if kind not in SUPPORTED:
            quarantined.append({"sourceId": source_id, "reason": "Unsupported type", "type": kind})
            continue
        # Keep all statement qualifiers; drop only transport/provenance/score fields.
        mechanism = {k: v for k, v in st.items() if k not in
                     ("evidence", "belief", "id", "matches_hash", "supports", "supported_by")}
        cid = BASE + "claim:" + digest(mechanism)
        if cid in seen:
            claim = seen[cid]
            duplicate_rows += 1
        else:
            agents = [a for role in SUPPORTED[kind] for a in
                      (st.get(role) if role == "members" else [st.get(role)]) or [] if a]
            names = [a.get("name", "?") for a in agents]
            flags = []
            if any(not st.get(role) for role in SUPPORTED[kind]):
                flags.append("missing_participant")
            if any(not any(k != "TEXT" for k in a.get("db_refs", {})) for a in agents):
                flags.append("ungrounded_participant")
            claim = {"id": cid, "type": kind, "label": kind + ": " + " / ".join(names),
                     "mechanism": mechanism, "agents": agents, "sourceIds": [],
                     "assessments": [], "evidence": [], "flags": flags}
            claims.append(claim)
            seen[cid] = claim
        if source_id not in claim["sourceIds"]:
            claim["sourceIds"].append(source_id)
        belief = st.get("belief")
        if belief is not None:
            if isinstance(belief, bool) or not isinstance(belief, (int, float)) or not 0 <= belief <= 1:
                raise ValueError("Invalid INDRA belief score")
            assessment = {"sourceId": source_id, "indraBelief": belief,
                          "scorer": "not supplied by endpoint", "delphiConfidence": None}
            if assessment not in claim["assessments"]:
                claim["assessments"].append(assessment)
        for ev in st.get("evidence", []):
            ids = refs(ev)
            pid = lookup[ids[0]] if ids else None
            # Hash original evidence for reproducibility, but do not republish licensed passages.
            eid = BASE + "evidence:" + digest(ev)
            item = {"id": eid, "paperId": pid, "references": ids,
                    "sourceApi": ev.get("source_api"), "sourceHash": str(ev.get("source_hash", "")),
                    "context": ev.get("context"), "epistemics": ev.get("epistemics", {}),
                    "sourceId": ev.get("source_id"),
                    "textSha256": hashlib.sha256((ev.get("text") or "").encode()).hexdigest(),
                    "passageAvailableInRaw": bool(ev.get("text"))}
            if not any(e["id"] == eid for e in claim["evidence"]):
                claim["evidence"].append(item)
    for c in claims:
        c["paperIds"] = sorted({e["paperId"] for e in c["evidence"] if e["paperId"]})
        c["unlinkedEvidence"] = sum(not e["paperId"] for e in c["evidence"])
        c["repeatedSourceEvidence"] = sum(bool(e["paperId"]) for e in c["evidence"]) - len(c["paperIds"])
        if not c["paperIds"]:
            c["flags"].append("no_linked_paper")
        if any(papers[p]["identityConflict"] for p in c["paperIds"]):
            c["flags"].append("conflicting_paper_identifiers")
        if any(not e["context"] for e in c["evidence"]):
            c["flags"].append("structured_context_missing")
        c["reviewStatus"] = "pending_expert_review"
        # No confidence aggregation or replication determination is performed.
    return {"claims": claims, "papers": list(papers.values()), "quarantined": quarantined,
            "summary": {"inputStatements": len(entries), "mappedClaims": len(claims),
                        "duplicateStatementRows": duplicate_rows, "paperGroups": len(papers),
                        "evidenceRecords": sum(len(c["evidence"]) for c in claims),
                        "repeatedSourceEvidenceWithinClaims": sum(c["repeatedSourceEvidence"] for c in claims),
                        "claimsWithoutLinkedPaper": sum(not c["paperIds"] for c in claims),
                        "paperIdentityConflicts": sum(p["identityConflict"] for p in papers.values()),
                        "quarantinedStatements": len(quarantined),
                        "expertReviewed": 0, "productionWrites": 0}}


def jsonld(sample):
    graph = []
    for p in sample["papers"]:
        graph.append({"@id": p["id"], "@type": "pk:Paper", "dct:identifier": p["references"],
                      "pilot:identityConflict": p["identityConflict"]})
    for c in sample["claims"]:
        node = {"@id": c["id"], "@type": "pk:Claim", "rdfs:label": c["label"],
                "dct:identifier": c["sourceIds"], "pilot:mechanismJson": canonical(c["mechanism"]),
                "pilot:reviewStatus": c["reviewStatus"], "pilot:flags": c["flags"],
                "pk:derivedFromPaper": [{"@id": p} for p in c["paperIds"]],
                "pk:hasEvidence": [{"@id": e["id"]} for e in c["evidence"]],
                "pk:hasAssessment": []}
        contexts = [e["context"] for e in c["evidence"] if e["context"]]
        if contexts:
            node["pk:context"] = canonical(contexts)
        for a in c["assessments"]:
            aid = BASE + "assessment:" + digest([c["id"], a])
            node["pk:hasAssessment"].append({"@id": aid})
            graph.append({"@id": aid, "@type": "pk:Assessment",
                          "pk:assessmentType": "Imported INDRA belief; not Delphi confidence",
                          "pilot:indraBelief": a["indraBelief"], "pilot:scorer": a["scorer"],
                          "prov:wasAttributedTo": {"@id": "https://www.indra.bio/"}})
        graph.append(node)
        for e in c["evidence"]:
            en = {"@id": e["id"], "@type": "pk:EvidenceItem",
                  "pilot:sourceApi": e["sourceApi"] or "unknown",
                  "pilot:sourceHash": e["sourceHash"],
                  "pilot:contextJson": canonical(e["context"]),
                  "pilot:epistemicsJson": canonical(e["epistemics"]),
                  "pilot:textSha256": e["textSha256"]}
            if e["paperId"]:
                en["prov:wasDerivedFrom"] = {"@id": e["paperId"]}
            graph.append(en)
    return {"@context": CONTEXT, "@graph": list({n["@id"]: n for n in graph}.values())}


def write_report(sample, out):
    esc = html.escape
    rows = []
    for c in sample["claims"]:
        links = sorted({r for e in c["evidence"] for r in e["references"]})
        references = " · ".join(f'<a href="{esc(paper_url(r))}">{esc(r)}</a>' for r in links)
        rows.append(f'<tr><td><strong>{esc(c["label"])}</strong><br><small>{esc(", ".join(c["sourceIds"]))}</small>'
                    f'<details><summary>Original mechanism &amp; context</summary><pre>{esc(json.dumps({"mechanism":c["mechanism"],"evidence":c["evidence"]}, indent=2))}</pre></details></td>'
                    f'<td>{esc(", ".join(str(a["indraBelief"]) for a in c["assessments"]))}<br><small>Scorer not supplied</small></td>'
                    f'<td>{len(c["paperIds"])} source documents<br>{c["repeatedSourceEvidence"]} repeated-source evidence records<br>{references}</td>'
                    f'<td>{esc(", ".join(c["flags"]) or "No automatic flags")}<br><strong>Expert review pending</strong></td></tr>')
    report = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>INDRA × Project Delphi: GJA1 pilot</title><style>
body{{font:15px/1.5 Arial,sans-serif;color:#203945;max-width:1300px;margin:35px auto;padding:0 22px}}
h1{{font-size:34px;color:#153e4b}}header{{border-top:5px solid #397b7e;padding-top:15px}}
.note{{background:#edf4f3;padding:18px;border-left:4px solid #397b7e}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid #d9e2e4}}
th{{background:#153e4b;color:white}}a{{color:#176b80}}small{{color:#657780}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;max-width:500px}}
.scroll{{overflow-x:auto}}td{{min-width:140px}}summary{{cursor:pointer;color:#176b80}}footer{{margin-top:25px}}
</style><header>PROJECT DELPHI · ISOLATED EVALUATION<h1>Connexin-43: an INDRA mapping sample</h1></header>
<p class="note"><strong>Real imported statements, not validated conclusions.</strong> Scope: GJA1/connexin-43 molecular interactions, not proof of organism-level bioelectricity claims. No live database writes, hypothesis assignments, score updates, or nanopublication submissions.</p>
<p><strong>{sample["summary"]["mappedClaims"]} mapped claims · {sample["summary"]["paperGroups"]} source-document groups · {sample["summary"]["evidenceRecords"]} evidence records</strong></p>
<p>One bounded query, capped at 40 statements and 5 evidence records per statement. Evidence is incomplete; INDRA belief may reflect more evidence than this sample contains. Paper groups are not independent experiments. Missing context stays unknown. Source passages are retained only in the local raw snapshot, not republished here.</p>
<p>Scores below are imported INDRA beliefs with an unspecified scorer; <strong>Delphi confidence is unassigned</strong>. Source identifiers have not been independently checked against full papers. No accuracy improvement has yet been established.</p>
<div class="scroll"><table><thead><tr><th>Claim / original mechanism</th><th>INDRA belief</th><th>Source traceability</th><th>Review flags</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Evaluation summary</h2><pre>{esc(json.dumps(sample["summary"], indent=2))}</pre>
<h2>Decision gate</h2><p>Use review.csv to assess entity identity, relation correctness, source support, context retention, and performance against our current extraction on the same papers. Do not ingest until reviewed; no production-readiness verdict is inferred from structural checks.</p>
<footer><a href="https://www.indra.bio/">INDRA</a> · <a href="https://github.com/fractastical/project-delphi-ontology">Ontology</a> · <a href="https://scienceoracle.com">scienceoracle.com</a></footer></html>"""
    (out / "report.html").write_text(report)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Replay an existing INDRA JSON snapshot (offline)")
    parser.add_argument("--out", type=Path, default=Path("generated-artifacts/indra-pilot"))
    args = parser.parse_args()
    if args.input:
        raw = args.input.read_bytes()
    else:
        with urlopen(Request(URL, headers={"User-Agent": "Delphi-INDRA-evaluation/1.0"}), timeout=60) as r:
            raw = r.read()
    payload = json.loads(raw)  # Python retains exact 64-bit source hashes.
    sample = map_sample(payload)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "raw.json").write_bytes(raw)
    manifest = {"retrievedOrReplayedAt": datetime.now(timezone.utc).isoformat(),
                "sourceUrl": URL if not args.input else None, "inputPath": str(args.input) if args.input else None,
                "snapshotSha256": hashlib.sha256(raw).hexdigest(), "mode": "offline" if args.input else "live",
                "scope": "GJA1 connexin-43 molecular interactions",
                "licenseNote": "Source-specific rights apply; evidence passages excluded from exported review artifacts.",
                "mapperSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for name, value in [("manifest.json", manifest), ("mapped.json", sample),
                        ("mapped.jsonld", jsonld(sample)), ("summary.json", sample["summary"])]:
        (args.out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False))
    with (args.out / "review.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["claim_id", "label", "indra_source_ids", "flags", "source_document_count",
                         "entity_correct", "relation_correct", "source_supports_claim", "context_preserved",
                         "baseline_result", "reviewer_notes"])
        for c in sample["claims"]:
            writer.writerow([c["id"], c["label"], ";".join(c["sourceIds"]), ";".join(c["flags"]),
                             len(c["paperIds"]), "", "", "", "", "", ""])
    write_report(sample, args.out)
    print(json.dumps(sample["summary"], indent=2))


if __name__ == "__main__":
    run()
