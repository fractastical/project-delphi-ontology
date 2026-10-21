#!/usr/bin/env python3
"""Generate the unsigned TriG sources of the ProbKnow Space and its governed templates.

Writes nanopubs/src/*.trig with placeholder base URIs (http://purl.org/nanopub/temp/…)
and a __NOW__ timestamp marker; nanopubs/sign.sh fills the timestamp, signs them in
order and derives the maintained-resource declarations from the signed template kinds.

published.json (written after publishing) records what is live on the network; a template
that has a published version is generated as a NEW VERSION: it supersedes the live nanopub
and keeps its kind IRI.
"""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "src")
os.makedirs(OUT, exist_ok=True)
PUBLISHED = json.load(open(os.path.join(HERE, "published.json"))) if os.path.exists(os.path.join(HERE, "published.json")) else {}

SPACE = "https://w3id.org/spaces/delphi"
PK = "https://w3id.org/delphi/ontology/"
PKR = "https://w3id.org/delphi/resource/"
TOBIAS = ("https://orcid.org/0000-0002-1267-0234", "Tobias Kuhn")
JOEL = ("https://orcid.org/0009-0007-4948-9192", "Joel Dietz")
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
FIND_THINGS = "https://w3id.org/np/l/nanopub-query-1.1/api/RAyMrQ89RECTi9gZK5q7gjL1wKTiP8StkLy0NIkkCiyew/find-things?type="

# Published templates these nanopubs are created from (see ../nanopub-skill/SKILL.md)
META_TEMPLATE = "https://w3id.org/np/RAWwJ-TzFhUJN5l6cTUIeCIUqqzS8ek-_zumlDczSUipk/template"
# Provenance and pubinfo templates are still defined through legacy-identity meta-templates
# (the template node is the assertion graph itself); their kind/governance triples are the
# "half-way mix" the nanopub skill documents: legacy node + dct:isVersionOf + gen:governedBy
# + npx:embeds pointing at the assertion graph.
META_PROV_TEMPLATE = "https://w3id.org/np/RAlxVeww5o6RsAzkcaMKjgAjPPaB1IMqqFg06_AzXNFZc"
META_PUBINFO_TEMPLATE = "https://w3id.org/np/RA3KyKGBWWXKZa-Tgq1XW8djl-9veFZDC2lcXIOeNz1WE"
SPACE_TEMPLATE = "https://w3id.org/np/RAgrIys3ge48pXrL_qNE0Rt1DHnIP8Rl2_29BnacMqYYY"
PROV_ATTRIBUTED = "https://w3id.org/np/RA7lSq6MuK_TIC6JMSHvLtee3lpLoZDOqLJCLXevnrPoU"
PUBINFO_LICENSE = "https://w3id.org/np/RACJ58Gvyn91LqCKIO9zu1eijDQIeEff28iyDrJgjSJF8"
PUBINFO_CREATOR = "https://w3id.org/np/RAukAcWHRDlkqxk7H2XNSegc1WnHI569INvNr-xdptDGI"
PUBINFO_SUPERSEDES = "https://w3id.org/np/RAoTD7udB2KtUuOuAe74tJi1t3VzK0DyWS7rYVAq1GRvw"
PUBINFO_CHANGENOTE = "https://w3id.org/np/RAKc76yHLDbloE6ObluzYQsfX37v6qrZXbYeIKpe8-YUo"

PREFIXES = """@prefix this: <http://purl.org/nanopub/temp/np001/> .
@prefix sub: <http://purl.org/nanopub/temp/np001/> .
@prefix np: <http://www.nanopub.org/nschema#> .
@prefix npx: <http://purl.org/nanopub/x/> .
@prefix nt: <https://w3id.org/np/o/ntemplate/> .
@prefix gen: <https://w3id.org/kpxl/gen/terms/> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix orcid: <https://orcid.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix pk: <https://w3id.org/delphi/ontology/> .
@prefix pkr: <https://w3id.org/delphi/resource/> .
@prefix schema: <https://schema.org/> .
"""

HEAD = """
sub:Head {
  this: a np:Nanopublication ;
    np:hasAssertion sub:assertion ;
    np:hasProvenance sub:provenance ;
    np:hasPublicationInfo sub:pubinfo .
}
"""

def lit(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

def pubinfo(label, extra, templates, creator=TOBIAS, extra_statements=(), pubinfo_templates=()):
    lines = [f"  orcid:{creator[0].rsplit('/',1)[1]} foaf:name {lit(creator[1])} ."]
    lines += ["  " + st for st in extra_statements]
    lines.append("")
    lines.append("  this: dct:created \"__NOW__\"^^xsd:dateTime ;")
    lines.append(f"    dct:creator orcid:{creator[0].rsplit('/',1)[1]} ;")
    lines.append(f"    dct:license <{LICENSE}> ;")
    lines.append(f"    rdfs:label {lit(label)} ;")
    for l in extra:
        lines.append("    " + l + " ;")
    lines.append(f"    nt:wasCreatedFromProvenanceTemplate <{PROV_ATTRIBUTED}> ;")
    lines.append("    nt:wasCreatedFromPubinfoTemplate " + ", ".join(f"<{t}>" for t in [PUBINFO_CREATOR, PUBINFO_LICENSE, *pubinfo_templates]) + " ;")
    lines.append(f"    nt:wasCreatedFromTemplate <{templates}> .")
    return "\nsub:pubinfo {\n" + "\n".join(lines) + "\n}\n"

def provenance(agent=TOBIAS):
    return f"\nsub:provenance {{\n  sub:assertion prov:wasAttributedTo <{agent[0]}> .\n}}\n"

def write(name, assertion, prov, pub):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(PREFIXES + HEAD + "\nsub:assertion {\n" + assertion + "}\n" + prov + pub)
    print("wrote", name)

# ─── 1. The ProbKnow Space ───────────────────────────────────────────────────
if "space-probknow" in PUBLISHED:
    print("kept 01-space-probknow.trig (published)")
else:
  write("01-space-probknow.trig",
  f"""  <{SPACE}> a gen:Space, gen:Group ;
      rdfs:label "ProbKnow" ;
      dct:description "ProbKnow (probknow.com) is a probabilistic knowledge graph that aggregates scientific claims, evidence and hypotheses across frontier-science domains such as bioelectricity, active inference and synthetic biology, and publishes them as nanopublications. This space governs the ProbKnow ontology (https://w3id.org/probknow/ontology/) and the templates for ProbKnow claims, evidence items, assessments and hypotheses." ;
      gen:hasAdmin <{TOBIAS[0]}>, <{JOEL[0]}> ;
      gen:hasRootDefinition this: .
  """,
  provenance(),
  pubinfo("ProbKnow", [f"npx:introduces <{SPACE}>", "npx:hasNanopubType gen:Space"], SPACE_TEMPLATE,
          extra_statements=[f"orcid:{JOEL[0].rsplit('/',1)[1]} foaf:name {lit(JOEL[1])} ."]))

# ─── Template machinery ──────────────────────────────────────────────────────
TERM_LABELS = {
    "rdf:type": "is a", "rdfs:label": "has the label", "rdfs:comment": "has the comment",
    "dct:description": "has the description", "dct:identifier": "has the identifier",
    "dct:title": "has the title", "dct:date": "has the date",
    "prov:wasSupportedBy": "is supported by", "prov:wasAttributedTo": "is attributed to",
    "prov:wasDerivedFrom": "is derived from",
    "pk:Claim": "claim", "pk:EvidenceItem": "evidence item", "pk:BayesianAssessment": "Bayesian assessment",
    "pk:LLMClaimAssessment": "LLM claim assessment", "pk:TestableHypothesis": "testable hypothesis",
    "pk:Model": "language model",
    "pk:context": "has the experimental context", "pk:weightOfEvidence": "has the weight of evidence (0–1)",
    "pk:weightOfEvidenceDeciban": "has the weight of evidence in decibans",
    "pk:derivedFromPaper": "is derived from the paper", "pk:hasAssessment": "has the assessment",
    "pk:hasEvidence": "has the evidence item", "pk:pValue": "has the p-value",
    "pk:statisticalTest": "comes from the statistical test", "pk:vovkSellkeMaxPRatio": "has the Vovk–Sellke maximum p-ratio",
    "pk:bayesFactor": "has the combined Bayes factor", "pk:calibrationMethod": "uses the calibration method",
    "pk:evaluatesHypothesis": "evaluates the hypothesis", "pk:assessedBy": "is assessed by",
    "pk:hasProbability": "has the probability", "pk:hasConfidence": "has the confidence",
    "pk:hasVerdict": "has the verdict", "pk:evidenceFor": "has evidence for",
    "pk:evidenceAgainst": "has evidence against", "pk:proposedTest": "has the proposed test",
    "pk:hasPriorProbability": "has the prior probability", "pk:hasResolvability": "has the resolvability",
    "pk:domain": "belongs to the domain",
    "pk:hasScore": "has the score (0–1)", "pk:assessmentType": "has the assessment type", "pk:Concept": "concept",
    "dct:subject": "is about", "dct:source": "has the source", "rdfs:seeAlso": "see also",
    "prov:actedOnBehalfOf": "acts on behalf of", "foaf:homepage": "has the homepage",
    "skos:Concept": "SKOS concept", "skos:narrower": "has the narrower concept", "skos:broader": "has the broader concept",
    "schema:PropertyValue": "property value", "schema:name": "has the name", "schema:value": "has the value",
    "schema:unitText": "has the unit", "schema:measurementTechnique": "was measured by",
    "schema:valueReference": "has the reference value", "schema:SoftwareSourceCode": "software source code",
    "schema:codeRepository": "is in the code repository", "schema:version": "has the version",
    "schema:programmingLanguage": "is written in", "schema:author": "has the author",
}

def placeholder(name, types, label, **kw):
    out = f"  sub:{name} a {', '.join('nt:' + t for t in types)} ;\n    rdfs:label {lit(label)}"
    if "prefix" in kw:
        out += f' ;\n    nt:hasPrefix {lit(kw["prefix"])} ;\n    nt:hasPrefixLabel {lit(kw["prefixLabel"])}'
    if "datatype" in kw:
        out += f' ;\n    nt:hasDatatype {kw["datatype"]}'
    if "default" in kw:
        out += f' ;\n    nt:hasDefaultValue {kw["default"]}'
    if "regex" in kw:
        out += f' ;\n    nt:hasRegex {lit(kw["regex"])}'
    return out + " .\n\n"

def guided(name, label, cls):
    """A reference to an existing ProbKnow resource of class `cls`, searched on the network
    (nt:ExternalUriPlaceholder keeps Nanodash from minting a local name for a typed string)."""
    return (f"  sub:{name} a nt:ExternalUriPlaceholder, nt:GuidedChoicePlaceholder ;\n    rdfs:label {lit(label)} ;\n"
            f"    nt:possibleValuesFromApi {lit(FIND_THINGS + PK + cls)} .\n\n")

def minted(kind):
    """The resource this template creates: pkr:<kind>/<artifact code>. Nanodash expands the
    ~~ARTIFACTCODE~~ marker to the nanopub's artifact code at publish time and matches any
    pkr:<kind>/<id> against it when filling the form from an existing nanopub, so pipeline
    nanopubs with their own ids conform too."""
    return f"<{PKR}{kind}/~~ARTIFACTCODE~~>"

def introduced(kind, label):
    return f"  {minted(kind)} a nt:IntroducedResource ;\n    rdfs:label {lit(label)} .\n\n"

def statement(sid, s, p, o, types=(), order=None):
    out = f"  sub:{sid}"
    if types:
        out += " a " + ", ".join("nt:" + t for t in types) + " ;\n   "
    out += f" rdf:subject {s} ;\n    rdf:predicate {p} ;\n    rdf:object {o}"
    if order is not None:
        out += f" ;\n    nt:statementOrder \"{order}\""
    return out + " .\n\n"

def template(name, kind, ttype, label, description, placeholders, statements, groups=(), target_type=None, label_pattern=None, tag="ProbKnow", change_note=None):
    """ttype: AssertionTemplate | ProvenanceTemplate | PubinfoTemplate.
    placeholders: list of placeholder()/guided()/introduced() strings.
    statements: list of (sid, s, p, o, types, order). groups: list of (gid, [member sids], types)."""
    used = set()
    for sid, s, p, o, *_ in statements:
        for t in (s, p, o):
            if t in TERM_LABELS: used.add(t)
    a = ""
    for t in sorted(used):
        a += f"  {t} rdfs:label {lit(TERM_LABELS[t])} .\n"
    a += "\n" + "".join(placeholders)
    all_sids = [st[0] for st in statements] + [g[0] for g in groups]
    for st in statements:
        a += statement(*st)
    for gid, members, types in groups:
        a += f"  sub:{gid} a {', '.join('nt:' + t for t in ['GroupedStatement'] + list(types))} ;\n    nt:hasStatement {', '.join('sub:' + m for m in members)} .\n\n"
    node = "sub:template" if ttype == "AssertionTemplate" else "sub:assertion"
    meta = {"AssertionTemplate": META_TEMPLATE, "ProvenanceTemplate": META_PROV_TEMPLATE, "PubinfoTemplate": META_PUBINFO_TEMPLATE}[ttype]
    key = name[3:-5].replace("template-", "", 1)
    # A template is generated as a new version only when it carries a change note; a
    # published template without one is left as it is (its source is the published form).
    if key in PUBLISHED and not change_note:
        print("kept", name, "(published; give it a change_note to generate a new version)"); return
    prev = PUBLISHED.get(key) if change_note else None
    kind_ref = f"<{prev['kind']}>" if prev and prev.get("kind") else f"sub:{kind}"
    a += f"  {node} a nt:{ttype} ;\n"
    a += f"    rdfs:label {lit(label)} ;\n"
    a += f"    dct:description {lit(description)} ;\n"
    a += f"    dct:isVersionOf {kind_ref} ;\n"
    a += f"    gen:governedBy <{SPACE}> ;\n"
    if ttype == "AssertionTemplate":
        a += f"    nt:hasTag {lit(tag)} ;\n"
    if target_type:
        a += f"    nt:hasTargetNanopubType {target_type} ;\n"
    if label_pattern:
        a += f"    nt:hasNanopubLabelPattern {lit(label_pattern)} ;\n"
    a += f"    nt:hasStatement {', '.join('sub:' + s for s in sorted(all_sids))} .\n"
    extra = [f"npx:embeds {node}", f"npx:introduces {kind_ref}"]
    pubinfo_templates = []
    if prev:
        extra.append(f"npx:supersedes <{prev['nanopub']}>")
        pubinfo_templates.append(PUBINFO_SUPERSEDES)
        if change_note:
            extra.append(f"skos:changeNote {lit(change_note)}")
            pubinfo_templates.append(PUBINFO_CHANGENOTE)
    write(name, a, provenance(), pubinfo(label, extra, meta, pubinfo_templates=pubinfo_templates))

D = "xsd:double"
OPT, REP, OPTREP = ("OptionalStatement",), ("RepeatableStatement",), ("OptionalStatement", "RepeatableStatement")
WEIGHT_REGEX = "^(0(\\.[0-9]+)?|1(\\.0+)?)$"
NOTE = ("Introduced resources are now minted from the nanopublication's artifact code (pkr:<kind>/RA…), "
        "so they are unique by construction; the pipeline may still use its own ids under the same namespace. "
        "References to other ProbKnow resources are guided choices searched on the network.")
CLAIM, EVIDENCE, ASSESSMENT, HYPOTHESIS = minted("claim"), minted("evidence"), minted("assessment"), minted("platonic")

# ─── 2. Provenance template: extracted from a paper by ProbKnow ─────────────
template("02-template-provenance-probknow-extraction.trig", "provenanceKind", "ProvenanceTemplate",
    "Extracted from a paper by ProbKnow",
    "The assertion was produced within ProbKnow — by its extraction and assessment pipeline, by a model acting as evaluator, or by a person — and is attributed to that agent. It was derived from one or more sources: a scholarly paper identified by its DOI (whose title and year may be recorded), a code commit, a dataset, a rubric. Related pages such as an issue or a report can be linked as well.",
    [placeholder("agent", ["AgentPlaceholder"], "the agent the assertion is attributed to (the ProbKnow system agent, a model, or yourself)", default="nt:CREATOR"),
     placeholder("source", ["ExternalUriPlaceholder"], "a source the assertion was derived from (a paper as https://doi.org/… IRI, a code commit, a dataset, a rubric)"),
     placeholder("title", ["LiteralPlaceholder"], "the title of the source"),
     placeholder("year", ["LiteralPlaceholder"], "the publication year of the source", datatype="xsd:gYear"),
     placeholder("seeAlso", ["ExternalUriPlaceholder"], "a related page (an issue, a report)")],
    [("st1", "nt:ASSERTION", "prov:wasAttributedTo", "sub:agent", REP, 1),
     ("st2a", "nt:ASSERTION", "prov:wasDerivedFrom", "sub:source", (), 2),
     ("st2b", "sub:source", "dct:title", "sub:title", OPT, 3),
     ("st2c", "sub:source", "dct:date", "sub:year", OPT, 4),
     ("st3", "nt:ASSERTION", "rdfs:seeAlso", "sub:seeAlso", OPTREP, 5)],
    groups=[("st2", ["st2a", "st2b", "st2c"], OPTREP)],
    change_note="Sources are now generic and repeatable (papers, code commits, datasets, rubrics) instead of a single DOI, and a related page (issue, report) can be linked with rdfs:seeAlso, so that assessments derived from code and rubrics can use this template.")

# ─── 3. Pubinfo template: ProbKnow domain ────────────────────────────────────
template("03-template-pubinfo-probknow-domain.trig", "domainKind", "PubinfoTemplate",
    "ProbKnow domain",
    "Records the frontier-science domain (e.g. levin-lab, active-inference) a ProbKnow nanopublication belongs to, as a pkr:domain/<slug> IRI.",
    [placeholder("domain", ["ExternalUriPlaceholder"], "the domain", prefix=PKR + "domain/", prefixLabel="pkr:domain/"),
     placeholder("domainLabel", ["LiteralPlaceholder"], "the domain's name (its slug)")],
    [("st1", "nt:NANOPUB", "pk:domain", "sub:domain", (), 1),
     ("st2", "sub:domain", "rdfs:label", "sub:domainLabel", OPT, 2)])

# ─── 4. Assertion template: ProbKnow claim ───────────────────────────────────
template("04-template-probknow-claim.trig", "claimKind", "AssertionTemplate",
    "ProbKnow claim",
    "A discrete scientific claim extracted from a paper by the ProbKnow pipeline, or stated about an artifact such as a simulation script, with its experimental context, the evidence items supporting it, the assessments made of it, and the panel-assigned weight of evidence (a score from 0 to 1). The claim is a belief, not an asserted fact; its credibility is carried by the weight and the assessments. The claim's identifier is minted from this nanopublication's artifact code.",
    [introduced("claim", "this claim"),
     placeholder("label", ["LiteralPlaceholder"], "the claim in one sentence"),
     placeholder("description", ["LongLiteralPlaceholder"], "a longer statement of the claim"),
     placeholder("context", ["LongLiteralPlaceholder"], "experimental context (organism, intervention, measured quantity, time points)"),
     guided("evidence", "an evidence item supporting the claim", "EvidenceItem"),
     guided("assessment", "an assessment of the claim", "Assessment"),
     placeholder("paper", ["ExternalUriPlaceholder"], "the paper the claim was extracted from (DOI as https://doi.org/… IRI)", prefix="https://doi.org/", prefixLabel="DOI"),
     placeholder("weight", ["LiteralPlaceholder"], "panel-assigned weight of evidence, from 0 to 1", datatype=D, regex=WEIGHT_REGEX),
     placeholder("artifact", ["ExternalUriPlaceholder"], "the artifact the claim is about, if any (a script, model or dataset, by URL)"),
     placeholder("artifactLabel", ["LiteralPlaceholder"], "the artifact's name (e.g. the file name)"),
     placeholder("repository", ["ExternalUriPlaceholder"], "the code repository the artifact belongs to"),
     placeholder("version", ["LiteralPlaceholder"], "the artifact's version (e.g. the commit)"),
     placeholder("language", ["LiteralPlaceholder"], "the programming language of the artifact"),
     placeholder("author", ["AgentPlaceholder"], "the artifact's author")],
    [("st01", CLAIM, "rdf:type", "pk:Claim", (), 1),
     ("st02", CLAIM, "rdfs:label", "sub:label", (), 2),
     ("st03", CLAIM, "dct:description", "sub:description", OPT, 3),
     ("st04", CLAIM, "pk:context", "sub:context", OPT, 4),
     ("st05", CLAIM, "pk:derivedFromPaper", "sub:paper", OPTREP, 5),
     ("st06", CLAIM, "prov:wasSupportedBy", "sub:evidence", OPTREP, 6),
     ("st07", CLAIM, "pk:hasAssessment", "sub:assessment", OPTREP, 7),
     ("st08", CLAIM, "pk:weightOfEvidence", "sub:weight", OPT, 8),
     ("st09a", CLAIM, "dct:subject", "sub:artifact", (), 9),
     ("st09b", "sub:artifact", "rdf:type", "schema:SoftwareSourceCode", OPT, 10),
     ("st09c", "sub:artifact", "rdfs:label", "sub:artifactLabel", OPT, 11),
     ("st09d", "sub:artifact", "schema:codeRepository", "sub:repository", OPT, 12),
     ("st09e", "sub:artifact", "schema:version", "sub:version", OPT, 13),
     ("st09f", "sub:artifact", "schema:programmingLanguage", "sub:language", OPT, 14),
     ("st09g", "sub:artifact", "schema:author", "sub:author", OPT, 15)],
    groups=[("st09", ["st09a", "st09b", "st09c", "st09d", "st09e", "st09f", "st09g"], OPTREP)],
    target_type="pk:Claim", label_pattern="${label}",
    change_note="Adds an optional group describing the artifact a claim is about (a script, model or dataset: its URL, name, repository, version, language and author), for claims about software such as simulation-faithfulness claims.")

# ─── 5. Assertion template: ProbKnow evidence item ───────────────────────────
template("05-template-probknow-evidence-item.trig", "evidenceKind", "AssertionTemplate",
    "ProbKnow evidence item",
    "A single piece of evidence for or against a ProbKnow claim, as reported in a paper: the statistical test and p-value it rests on, the Vovk–Sellke maximum p-ratio bound derived from that p-value, and its weight of evidence. The evidence item's identifier is minted from this nanopublication's artifact code.",
    [introduced("evidence", "this evidence item"),
     placeholder("label", ["LiteralPlaceholder"], "the evidence in one sentence"),
     placeholder("description", ["LongLiteralPlaceholder"], "a longer description of the evidence"),
     placeholder("paper", ["ExternalUriPlaceholder"], "the paper reporting the evidence (DOI as https://doi.org/… IRI)", prefix="https://doi.org/", prefixLabel="DOI"),
     placeholder("test", ["LiteralPlaceholder"], "the statistical test the p-value comes from"),
     placeholder("pvalue", ["LiteralPlaceholder"], "the p-value", datatype=D),
     placeholder("vsmpr", ["LiteralPlaceholder"], "Vovk–Sellke maximum p-ratio (bound on the Bayes factor implied by the p-value)", datatype=D),
     placeholder("weight", ["LiteralPlaceholder"], "weight of evidence, from 0 to 1", datatype=D, regex=WEIGHT_REGEX)],
    [("st01", EVIDENCE, "rdf:type", "pk:EvidenceItem", (), 1),
     ("st02", EVIDENCE, "rdfs:label", "sub:label", (), 2),
     ("st03", EVIDENCE, "dct:description", "sub:description", OPT, 3),
     ("st04", EVIDENCE, "pk:derivedFromPaper", "sub:paper", OPT, 4),
     ("st05", EVIDENCE, "pk:statisticalTest", "sub:test", OPT, 5),
     ("st06", EVIDENCE, "pk:pValue", "sub:pvalue", OPT, 6),
     ("st07", EVIDENCE, "pk:vovkSellkeMaxPRatio", "sub:vsmpr", OPT, 7),
     ("st08", EVIDENCE, "pk:weightOfEvidence", "sub:weight", OPT, 8)],
    target_type="pk:EvidenceItem", label_pattern="${label}", change_note=None)

# ─── 6. Assertion template: ProbKnow Bayesian assessment ─────────────────────
template("06-template-probknow-bayesian-assessment.trig", "bayesianAssessmentKind", "AssertionTemplate",
    "ProbKnow Bayesian assessment",
    "A Bayesian assessment of a ProbKnow claim: the combined Bayes factor over the claim's evidence items, the resulting weight of evidence in decibans, and the calibration method used to turn p-values into Bayes factors. The assessment's identifier is minted from this nanopublication's artifact code.",
    [introduced("assessment", "this assessment"),
     guided("claim", "the claim being assessed", "Claim"),
     placeholder("label", ["LiteralPlaceholder"], "short label of the assessment"),
     placeholder("description", ["LongLiteralPlaceholder"], "notes on how the evidence was combined"),
     guided("evidence", "an evidence item that entered the assessment", "EvidenceItem"),
     placeholder("bayesFactor", ["LiteralPlaceholder"], "combined Bayes factor", datatype=D),
     placeholder("deciban", ["LiteralPlaceholder"], "weight of evidence in decibans (10·log10 of the Bayes factor)", datatype=D),
     placeholder("calibration", ["LiteralPlaceholder"], "calibration method (e.g. Vovk–Sellke p-value calibration)")],
    [("st01", ASSESSMENT, "rdf:type", "pk:BayesianAssessment", (), 1),
     ("st02", ASSESSMENT, "rdfs:label", "sub:label", (), 2),
     ("st03", "sub:claim", "pk:hasAssessment", ASSESSMENT, (), 3),
     ("st04", ASSESSMENT, "dct:description", "sub:description", OPT, 4),
     ("st05", ASSESSMENT, "pk:hasEvidence", "sub:evidence", OPTREP, 5),
     ("st06", ASSESSMENT, "pk:bayesFactor", "sub:bayesFactor", OPT, 6),
     ("st07", ASSESSMENT, "pk:weightOfEvidenceDeciban", "sub:deciban", OPT, 7),
     ("st08", ASSESSMENT, "pk:calibrationMethod", "sub:calibration", OPT, 8)],
    target_type="pk:BayesianAssessment", label_pattern="${label}", change_note=None)

# ─── 7. Assertion template: ProbKnow LLM assessment ──────────────────────────
template("07-template-probknow-llm-assessment.trig", "llmAssessmentKind", "AssertionTemplate",
    "ProbKnow LLM assessment of a hypothesis",
    "An assessment of a ProbKnow hypothesis made by a language model acting as evaluator: the model's probability that the hypothesis is true, its self-reported confidence, a verdict, its reasoning, and the points of evidence for and against. The assessment's identifier is minted from this nanopublication's artifact code.",
    [introduced("assessment", "this assessment"),
     placeholder("label", ["LiteralPlaceholder"], "short label of the assessment"),
     placeholder("hypothesis", ["ExternalUriPlaceholder"], "the hypothesis being evaluated", prefix=PKR + "hypothesis/", prefixLabel="pkr:hypothesis/"),
     placeholder("hypothesisLabel", ["LiteralPlaceholder"], "the hypothesis in one sentence"),
     placeholder("hypothesisCode", ["LiteralPlaceholder"], "the hypothesis code (e.g. H1)"),
     placeholder("model", ["ExternalUriPlaceholder"], "the language model that made the assessment", prefix=PKR + "model/", prefixLabel="pkr:model/"),
     placeholder("modelLabel", ["LiteralPlaceholder"], "the model's name and version"),
     placeholder("probability", ["LiteralPlaceholder"], "probability that the hypothesis is true, from 0 to 1", datatype=D),
     placeholder("confidence", ["LiteralPlaceholder"], "the model's confidence in its probability, from 0 to 1", datatype=D),
     placeholder("verdict", ["LiteralPlaceholder"], "short categorical verdict (e.g. Plausible)"),
     placeholder("reasoning", ["LongLiteralPlaceholder"], "the model's reasoning"),
     placeholder("evidenceFor", ["LongLiteralPlaceholder"], "a point of evidence supporting the hypothesis"),
     placeholder("evidenceAgainst", ["LongLiteralPlaceholder"], "a point of evidence against the hypothesis")],
    [("st01", ASSESSMENT, "rdf:type", "pk:LLMClaimAssessment", (), 1),
     ("st02", ASSESSMENT, "rdfs:label", "sub:label", (), 2),
     ("st03", ASSESSMENT, "pk:evaluatesHypothesis", "sub:hypothesis", (), 3),
     ("st04", "sub:hypothesis", "rdfs:label", "sub:hypothesisLabel", (), 4),
     ("st05", "sub:hypothesis", "dct:identifier", "sub:hypothesisCode", OPT, 5),
     ("st06", ASSESSMENT, "pk:assessedBy", "sub:model", (), 6),
     ("st07", "sub:model", "rdf:type", "pk:Model", (), 7),
     ("st08", "sub:model", "rdfs:label", "sub:modelLabel", (), 8),
     ("st09", ASSESSMENT, "pk:hasProbability", "sub:probability", OPT, 9),
     ("st10", ASSESSMENT, "pk:hasConfidence", "sub:confidence", OPT, 10),
     ("st11", ASSESSMENT, "pk:hasVerdict", "sub:verdict", OPT, 11),
     ("st12", ASSESSMENT, "rdfs:comment", "sub:reasoning", OPT, 12),
     ("st13", ASSESSMENT, "pk:evidenceFor", "sub:evidenceFor", OPTREP, 13),
     ("st14", ASSESSMENT, "pk:evidenceAgainst", "sub:evidenceAgainst", OPTREP, 14)],
    target_type="pk:LLMClaimAssessment", label_pattern="${label}", change_note=None)

# ─── 8. Assertion template: ProbKnow testable hypothesis ─────────────────────
template("08-template-probknow-testable-hypothesis.trig", "testableHypothesisKind", "AssertionTemplate",
    "ProbKnow testable hypothesis",
    "A hypothesis stated together with the experiment that would resolve it, a prior probability and a resolvability score (how decidably it can be tested), both from 0 to 1. The hypothesis's identifier is minted from this nanopublication's artifact code.",
    [introduced("platonic", "this hypothesis"),
     placeholder("label", ["LiteralPlaceholder"], "the hypothesis in one sentence"),
     placeholder("code", ["LiteralPlaceholder"], "the hypothesis code (e.g. P1)"),
     placeholder("claim", ["LongLiteralPlaceholder"], "the full statement of the hypothesis"),
     placeholder("test", ["LongLiteralPlaceholder"], "the experiment that would resolve the hypothesis"),
     placeholder("prior", ["LiteralPlaceholder"], "prior probability, from 0 to 1", datatype=D),
     placeholder("resolvability", ["LiteralPlaceholder"], "resolvability, from 0 to 1", datatype=D)],
    [("st01", HYPOTHESIS, "rdf:type", "pk:TestableHypothesis", (), 1),
     ("st02", HYPOTHESIS, "rdfs:label", "sub:label", (), 2),
     ("st03", HYPOTHESIS, "dct:identifier", "sub:code", OPT, 3),
     ("st04", HYPOTHESIS, "rdfs:comment", "sub:claim", (), 4),
     ("st05", HYPOTHESIS, "pk:proposedTest", "sub:test", (), 5),
     ("st06", HYPOTHESIS, "pk:hasPriorProbability", "sub:prior", OPT, 6),
     ("st07", HYPOTHESIS, "pk:hasResolvability", "sub:resolvability", OPT, 7)],
    target_type="pk:TestableHypothesis", label_pattern="${label}", change_note=None)

# ─── 18. Assertion template: ProbKnow rubric assessment of a claim ───────────
RUBRIC_ASSESSMENT_DESC = ("An assessment of a ProbKnow claim against one dimension of a rubric (or against the whole rubric, for the overall score), "
    "made by a language model acting as evaluator: the score from 0 to 1, a verdict, and the evidence items the score rests on — code locations, "
    "passages, or measurements with their reference values. The assessment's identifier is minted from this nanopublication's artifact code; "
    "pipelines may use their own ids under pkr:assessment/.")
EVIDENCE_REF = "sub:evidence"
template("18-template-probknow-rubric-assessment.trig", "rubricAssessmentKind", "AssertionTemplate",
    "ProbKnow rubric assessment of a claim", RUBRIC_ASSESSMENT_DESC,
    [introduced("assessment", "this assessment"),
     placeholder("label", ["LiteralPlaceholder"], "short label of the assessment (claim, dimension and score)"),
     placeholder("date", ["LiteralPlaceholder"], "the date of the assessment", datatype="xsd:date"),
     placeholder("description", ["LongLiteralPlaceholder"], "the assessor's reasoning"),
     guided("claim", "the claim being assessed", "Claim"),
     guided("dimension", "the rubric dimension scored (the rubric itself for the overall score)", "Concept"),
     placeholder("model", ["ExternalUriPlaceholder"], "the language model that made the assessment", prefix=PKR + "model/", prefixLabel="pkr:model/"),
     placeholder("modelLabel", ["LiteralPlaceholder"], "the model's name and version"),
     placeholder("modelId", ["LiteralPlaceholder"], "the model's identifier (e.g. its API model id)"),
     placeholder("modelHomepage", ["ExternalUriPlaceholder"], "the model's homepage"),
     placeholder("operator", ["AgentPlaceholder"], "the person the model acted on behalf of", default="nt:CREATOR"),
     placeholder("assessmentType", ["LiteralPlaceholder"], "the assessment type: rubric, version and dimension (e.g. morphoeval/0.1.0/code-traceability)"),
     placeholder("verdict", ["LiteralPlaceholder"], "short categorical verdict (e.g. mostly faithful)"),
     placeholder("score", ["LiteralPlaceholder"], "the score, from 0 to 1", datatype=D, regex=WEIGHT_REGEX),
     placeholder("evidenceAgainst", ["LongLiteralPlaceholder"], "a point counting against the claim"),
     placeholder("evidence", ["UriPlaceholder"], "an evidence item the score rests on (a code location, a passage, a measurement)", prefix=PKR + "evidence/", prefixLabel="pkr:evidence/"),
     placeholder("evidenceLabel", ["LiteralPlaceholder"], "the evidence in one line"),
     placeholder("evidenceDescription", ["LongLiteralPlaceholder"], "what the evidence shows"),
     placeholder("source", ["ExternalUriPlaceholder"], "where the evidence comes from (a file and line range, a commit, a DOI)"),
     placeholder("quantity", ["LiteralPlaceholder"], "the measured quantity, for a measurement"),
     placeholder("value", ["LiteralPlaceholder"], "the measured value"),
     placeholder("unit", ["LiteralPlaceholder"], "the unit of the measured value"),
     placeholder("technique", ["LongLiteralPlaceholder"], "how the value was measured"),
     placeholder("reference", ["UriPlaceholder"], "the reference value the measurement is compared with", prefix=PKR + "evidence/", prefixLabel="pkr:evidence/"),
     placeholder("referenceValue", ["LiteralPlaceholder"], "the reference value"),
     placeholder("referenceSource", ["LiteralPlaceholder"], "where the reference value comes from")],
    [("st01", ASSESSMENT, "rdf:type", "pk:LLMClaimAssessment", (), 1),
     ("st02", ASSESSMENT, "rdfs:label", "sub:label", (), 2),
     ("st03", ASSESSMENT, "dct:date", "sub:date", OPT, 3),
     ("st04", ASSESSMENT, "dct:description", "sub:description", OPT, 4),
     ("st05", "sub:claim", "pk:hasAssessment", ASSESSMENT, (), 5),
     ("st06", ASSESSMENT, "dct:subject", "sub:dimension", (), 6),
     ("st07", ASSESSMENT, "pk:assessedBy", "sub:model", (), 7),
     ("st08", "sub:model", "rdf:type", "pk:Model", (), 8),
     ("st09", "sub:model", "rdfs:label", "sub:modelLabel", (), 9),
     ("st10", "sub:model", "dct:identifier", "sub:modelId", OPT, 10),
     ("st11", "sub:model", "foaf:homepage", "sub:modelHomepage", OPT, 11),
     ("st12", "sub:model", "prov:actedOnBehalfOf", "sub:operator", OPT, 12),
     ("st13", ASSESSMENT, "pk:assessmentType", "sub:assessmentType", (), 13),
     ("st14", ASSESSMENT, "pk:hasVerdict", "sub:verdict", OPT, 14),
     ("st15", ASSESSMENT, "pk:hasScore", "sub:score", (), 15),
     ("st16", ASSESSMENT, "pk:evidenceAgainst", "sub:evidenceAgainst", OPTREP, 16),
     ("st17a", ASSESSMENT, "pk:hasEvidence", EVIDENCE_REF, (), 17),
     ("st17b", EVIDENCE_REF, "rdf:type", "pk:EvidenceItem", (), 18),
     ("st17c", EVIDENCE_REF, "rdfs:label", "sub:evidenceLabel", (), 19),
     ("st17d", EVIDENCE_REF, "dct:description", "sub:evidenceDescription", OPT, 20),
     ("st17e", EVIDENCE_REF, "prov:wasDerivedFrom", "sub:source", OPT, 21),
     ("st17f", EVIDENCE_REF, "rdf:type", "schema:PropertyValue", OPT, 22),
     ("st17g", EVIDENCE_REF, "schema:name", "sub:quantity", OPT, 23),
     ("st17h", EVIDENCE_REF, "schema:value", "sub:value", OPT, 24),
     ("st17i", EVIDENCE_REF, "schema:unitText", "sub:unit", OPT, 25),
     ("st17j", EVIDENCE_REF, "schema:measurementTechnique", "sub:technique", OPT, 26),
     ("st17k", EVIDENCE_REF, "schema:valueReference", "sub:reference", OPT, 27),
     ("st17l", "sub:reference", "rdf:type", "schema:PropertyValue", OPT, 28),
     ("st17m", "sub:reference", "schema:value", "sub:referenceValue", OPT, 29),
     ("st17n", "sub:reference", "dct:source", "sub:referenceSource", OPT, 30)],
    groups=[("st17", ["st17a", "st17b", "st17c", "st17d", "st17e", "st17f", "st17g", "st17h", "st17i", "st17j", "st17k", "st17l", "st17m", "st17n"], OPTREP)],
    target_type="pk:LLMClaimAssessment", label_pattern="${label}")

# ─── 19. Assertion template: ProbKnow rubric ─────────────────────────────────
RUBRIC = minted("concept")
template("19-template-probknow-rubric.trig", "rubricKind", "AssertionTemplate",
    "ProbKnow rubric",
    "A rubric for assessing ProbKnow claims: a concept with one narrower concept per scored dimension, each with its weight and question in the description. Rubric assessments refer to these concepts as their subject. The rubric's identifier is minted from this nanopublication's artifact code; pipelines may use their own ids under pkr:concept/.",
    [introduced("concept", "this rubric"),
     placeholder("label", ["LiteralPlaceholder"], "the rubric's name and version"),
     placeholder("description", ["LongLiteralPlaceholder"], "what the rubric measures and how the overall score is computed"),
     placeholder("seeAlso", ["ExternalUriPlaceholder"], "the rubric's definition (e.g. a file in a repository)"),
     placeholder("dimension", ["UriPlaceholder"], "a dimension of the rubric", prefix=PKR + "concept/", prefixLabel="pkr:concept/"),
     placeholder("dimensionLabel", ["LiteralPlaceholder"], "the dimension's name"),
     placeholder("dimensionDescription", ["LongLiteralPlaceholder"], "the dimension's weight and the question it answers")],
    [("st01", RUBRIC, "rdf:type", "pk:Concept", (), 1),
     ("st02", RUBRIC, "rdf:type", "skos:Concept", (), 2),
     ("st03", RUBRIC, "rdfs:label", "sub:label", (), 3),
     ("st04", RUBRIC, "dct:description", "sub:description", OPT, 4),
     ("st05", RUBRIC, "rdfs:seeAlso", "sub:seeAlso", OPTREP, 5),
     ("st06a", RUBRIC, "skos:narrower", "sub:dimension", (), 6),
     ("st06b", "sub:dimension", "skos:broader", RUBRIC, (), 7),
     ("st06c", "sub:dimension", "rdf:type", "pk:Concept", (), 8),
     ("st06d", "sub:dimension", "rdf:type", "skos:Concept", (), 9),
     ("st06e", "sub:dimension", "rdfs:label", "sub:dimensionLabel", (), 10),
     ("st06f", "sub:dimension", "dct:description", "sub:dimensionDescription", OPT, 11)],
    groups=[("st06", ["st06a", "st06b", "st06c", "st06d", "st06e", "st06f"], OPTREP)],
    target_type="pk:Concept", label_pattern="${label}")
