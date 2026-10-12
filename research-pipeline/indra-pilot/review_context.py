"""Reproducible, source-bound agent review; never modifies the original import."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from pilot import BASE, digest, statements, map_sample, paper_url

SNAPSHOT = "7a88634c0b8be249c2e1788ae6797ad3de7099a6f7afacdd5949e1add74eb6e3"
# Evidence-specific interpretations, not replacement mechanisms.
IDENTITY = {
    5: "TAT-Cx43 is a cell-penetrating peptide construct, not a complex with human tyrosine aminotransferase. Exact replacement grounding unknown.",
    7: "GJs denotes gap junctions, not the imported pol protein. No replacement protein participant.",
    8: "Cx43-EGFP is a tagged construct; passages do not establish a native two-protein complex. Construct identity retained; exact accession unknown.",
    14: "ODD denotes an oxygen-dependent degradation domain in a luciferase reporter, not GJA1. Do not transfer this context to connexin-43.",
    18: "Evidence mentioning Cx40.8 cannot be silently equated with human GJA5/Cx40; keep accession unresolved for those records.",
    20: "ODD denotes HIF oxygen-dependent degradation domain, not GJA1. Human HIF-1alpha and Drosophila Similar must remain distinct substrates.",
    28: "Mixed claim: only evidence 1 explicitly concerns Cx43. Other passages concern ODD/HIF acetylation and must not support GJA1.",
    35: "GJ denotes gap junction, not the imported gJ protein. No replacement protein participant.",
    36: "GJIC denotes gap junctional intercellular communication, a process, not an ungrounded protein. No ontology accession asserted.",
    37: "ODD and ADHD denote psychiatric disorders, not GJA1 and bacterial adhD. Reject as a molecular complex.",
}
PARTICIPANTS = {
    (0, 1): "ERK and p38 MAPK families are named; no unique enzyme or isoform can be assigned.",
    (1, 4): "PKC family-mediated phosphorylation; measuring PKC alpha does not establish it as the unique catalyst.",
    (2, 3): "PP2A implicated by paper abstract; PAK1 is an upstream activator, not the dephosphorylating enzyme.",
    (4, 1): "Nedd4 E3 ligase association; does not by itself prove direct catalytic ubiquitination.",
    (15, 0): "PKC family (isoform unknown), in cited background.",
    (15, 4): "PKC epsilon explicitly named as interacting with and phosphorylating Cx43 S262.",
    (20, 0): "Drosophila PHD acting on human HIF-1alpha and Drosophila Similar ODD; not a GJA1 correction.",
    (24, 0): "MAP kinase, PKC and PKA; direct or indirect alternatives, no unique enzyme.",
    (24, 3): "PKC epsilon-mediated phosphorylation in cited background; not independently established direct catalysis.",
    (28, 0): "ARD1 named; substrate is ODD, not GJA1.",
    (28, 2): "ARD1 named; substrate is ODD, not GJA1.",
    (28, 4): "ARD1 acetylates HIF-1alpha ODD Lys532, not GJA1.",
}
# Only own-study settings that are explicit in inspected paper abstracts.
# Never apply paper-level species to cited background passages.
PAPER_ADDITIONS = {
    (0, 0): (None, "AZ-521 cells", "AZ-521"),
    (0, 2): (None, "AZ-521 cells", "AZ-521"),
    (0, 3): (None, "AZ-521 cells", "AZ-521"),
    (0, 4): (None, "AZ-521 cells", "AZ-521"),
    (1, 3): (None, "H9c2 cells; simvastatin 10 micromolar for 4 h then doxorubicin 1 micromolar; assessment after 20 h", "H9c2"),
    (1, 4): ("rat", "Neonatal ventricular myocytes; MDMA 10/100/1000 micromolar for 1 h", "neonatal rats"),
    (2, 3): (None, "Rabbit LV myocytes, human failing LV, and HEK293-Cx43 systems; do not collapse into one organism", "PP2A"),
    (4, 1): ("rat", "Cultured astrocytes; LPS for 6 h in association assay", "rat astrocytes"),
    (4, 2): ("rat", "Cultured astrocytes", "rat astrocytes"),
    (4, 4): ("rat", "Cultured astrocytes; future-work statement, not an additional experiment", "rat astrocytes"),
    (5, 0): ("human cells in mouse host", "Human glioma stem cells injected into immunodeficient mice", "immunodeficient mice"),
    (7, 0): ("mouse", "Male C57BL/6 mice and primary mouse astrocytes", "C57BL/6"),
    (15, 1): ("mouse", "STZ type I diabetic mouse heart; cryoinjury/insulin study, not proof of the Ser262 title fragment", "STZ"),
    (15, 2): ("mouse", "Embryonic stem-cell colonies treated with EGF", "mouse embryonic stem"),
    (24, 4): ("mouse", "Embryonic stem-cell colonies treated with EGF", "mouse embryonic stem"),
    (30, 4): ("rat", "Cultured astrocytes; LPS", "rat astrocytes"),
    (36, 0): ("rat", "Primary vascular smooth-muscle cells; cAMP/cGMP, BAY or DADS experiments", "rat primary VSMCs"),
    (38, 2): ("rat", "Cultured astrocytes; LPS association assay", "rat astrocytes"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(raw_path, mapped_path, decisions_path, sources):
    if sha(raw_path) != SNAPSHOT:
        raise ValueError("Decisions are bound to the frozen sample; refuse a different snapshot")
    raw = json.loads(raw_path.read_text())
    mapped = json.loads(mapped_path.read_text())
    if mapped != map_sample(raw):
        raise ValueError("Mapped import does not match raw snapshot")
    entries = statements(raw)
    decisions = list(csv.DictReader(decisions_path.open(), delimiter="\t"))
    expected = {(i, j) for i, (_, s) in enumerate(entries) for j, _ in enumerate(s["evidence"])}
    keys = [(int(d["claim"]), int(d["evidence"])) for d in decisions]
    if set(keys) != expected or len(keys) != len(expected):
        raise ValueError("Review must cover every evidence exactly once")
    rows = []
    for d, (i, j) in zip(decisions, keys):
        sid, st = entries[i]
        claim = next(c for c in mapped["claims"] if sid in c["sourceIds"])
        ev = st["evidence"][j]
        eid = BASE + "evidence:" + digest(ev)
        imported = next(e for e in claim["evidence"] if e["id"] == eid)
        source_file = sources / (imported["paperId"].split(":")[-1] + ".json")
        cached = json.loads(source_file.read_text())
        organism = None if d["organism"] == "?" else d["organism"]
        conditions = None if d["conditions"] == "?" else d["conditions"]
        paper_addition = None
        if (i, j) in PAPER_ADDITIONS:
            species, detail, anchor = PAPER_ADDITIONS[i, j]
            matches = [r for r in cached.get("results", []) if anchor in r.get("abstractText", "")]
            if len(matches) != 1:
                raise ValueError(f"Paper anchor missing or ambiguous at {i}.{j}")
            paper_addition = {"organism": species, "conditions": detail,
                              "basis": "cited paper abstract", "locator": anchor,
                              "sourceUrl": cached["url"], "cacheSha256": sha(source_file)}
        rejected = i in (7, 14, 20, 35, 37) or (i == 28 and j != 1)
        rows.append({
            "claimId": claim["id"], "sourceStatementId": sid, "evidenceId": eid,
            "claimIndex": i, "evidenceIndex": j,
            "paperId": imported["paperId"], "sourceLinks": [paper_url(r) for r in imported["references"]],
            "originalPassageSha256": imported["textSha256"],
            "reviewer": "Replit Agent; source review, not independent biological expert validation",
            "reviewStatus": "reviewed_with_unknowns",
            "originalContext": imported["context"],
            "passageContext": {"organism": organism, "conditions": conditions},
            "paperContextAddition": paper_addition,
            "participantInterpretation": PARTICIPANTS.get((i, j)),
            "participantIdentityIssue": IDENTITY.get(i),
            "contextAppliesToImportedGJA1Claim": not rejected,
            "disposition": "reject_as_GJA1_evidence" if rejected else "retain_for_expert_review",
            "missingParticipantResolvedGlobally": False,
            "unknownReason": "Unspecified fields remain unknown; no organism inferred from HGNC/UniProt, cell-line familiarity, or another evidence record.",
            "paperAccessStatus": cached["status"],
            "passageTruncated": "MISSING/INVALID CREDENTIALS" in ev.get("text", ""),
            "studyIndependence": None,
        })
    return {
        "schemaVersion": 1, "reviewDate": "2026-10-12",
        "originalFiles": {"raw.json": sha(raw_path), "mapped.json": sha(mapped_path)},
        "decisionsSha256": sha(decisions_path),
        "scope": "Frozen 40-claim GJA1 sample only; reviewed overlay, not replacement imports",
        "method": "All 200 original passages reviewed. Public metadata/abstract retrieval attempted for all 172 document groups; selected abstracts inspected for additions. Full texts not exhaustively reviewed.",
        "confidenceUpdates": 0, "productionWrites": 0, "expertValidated": False,
        "documentPolicy": "Imported PMID/PMCID/DOI groups are aliases, not independent studies; no independence count is asserted. Secondary citations and repeated readers remain dependent/unknown.",
        "summary": {"claimsReviewed": len(entries), "evidenceReviewed": len(rows),
                    "passageOrganismKnown": sum(r["passageContext"]["organism"] is not None for r in rows),
                    "passageSettingNotes": sum(r["passageContext"]["conditions"] is not None for r in rows),
                    "paperContextAdditions": sum(r["paperContextAddition"] is not None for r in rows),
                    "rejectedEvidence": sum(not r["contextAppliesToImportedGJA1Claim"] for r in rows)},
        "reviews": rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.resolve() == a.input.resolve():
        p.error("Output must be separate from the original import")
    a.out.mkdir(parents=True, exist_ok=True)
    target = a.out / "reviewed-context.json"
    if target.exists():
        p.error("Review layer already exists; select a new directory to preserve history")
    layer = build(a.input / "raw.json", a.input / "mapped.json",
                  Path(__file__).with_name("context_decisions.tsv"), a.sources)
    target.write_text(json.dumps(layer, indent=2, ensure_ascii=False) + "\n")
    with (a.out / "reviewed-context.csv").open("w") as f:
        fields = ["sourceStatementId", "evidenceId", "disposition", "passageContext",
                  "paperContextAddition", "participantInterpretation", "participantIdentityIssue",
                  "sourceLinks", "studyIndependence"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in layer["reviews"]:
            writer.writerow({k: json.dumps(r[k], ensure_ascii=False) for k in fields})
    print(json.dumps(layer["summary"], indent=2))


if __name__ == "__main__":
    main()
