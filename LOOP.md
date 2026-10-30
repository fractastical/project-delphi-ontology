# The 12-step loop

The 12-step closed loop is how a reproduction of a scientific model becomes a set of
Project Delphi nanopublications. It was developed in
[morpholib](https://github.com/fractastical/morpholib) for the MorphoEval audits of
morphogenesis simulations, and it is the default route to a published claim in
[PUBLISHING.md](PUBLISHING.md#1-use-the-12-step-loop-where-possible).

This page describes each step and the ontology terms and templates it produces. For the
tooling, commands, and worked runs, see the
[morpholib README](https://github.com/fractastical/morpholib#the-12-step-closed-loop) and
its sample run walkthroughs in `morphoeval/runs/`.

~~~mermaid
flowchart LR
    subgraph A["Tier A: build"]
        S1["1 Scout"] --> S2["2 Paper"] --> S3["3 Formal source"] --> S4["4 Pin the rules"] --> S5["5 Script"] --> S6["6 Output & compare"]
    end
    subgraph B["Tier B: audit"]
        S7["7 Dual-agent audit"] --> S8["8 Measure"] --> S9["9 Write as claims"] --> S10["10 Sign & publish"] --> S11["11 Public record"] --> S12["12 Remediate"]
    end
    S6 --> S7
    S12 -.->|"Pass 2, 3, …"| S5
~~~

Steps 1–11 are Pass 1. Step 12 turns every defect the assessors found into a checklist
item and sends the work back to step 5. Each later pass runs steps 5–11 again and
publishes nanopubs that supersede the previous pass.

## Tier A: build the reproduction (steps 1–6)

Nothing is published in Tier A. Its job is to make sure that what Tier B audits is real
science: the paper's own equations and data, not a stand-in.

| Step | What happens | What it feeds into the graph |
|---|---|---|
| **1 Scout** | Pick a classic paper, an open empirical dataset, or a quantitative biological claim worth testing. | The subject of the eventual `delphi:Claim`. |
| **2 Paper** | Extract the governing equations, algorithmic rules, and empirical reference tables from the primary literature. | The source of `prov:wasDerivedFrom` on the claim and in its provenance. |
| **3 Formal source** | Vendor or cache the empirical tables and specimen images, and lock every file by SHA-256 so an altered input is refused. | Dataset identifiers and checksums (`prov:used`, `dcat:Dataset` per [PUBLISHING.md §6](PUBLISHING.md#6-every-dataset-gets-its-own-nanopub)). |
| **4 Pin the rules** | Formalise the paper's core invariants as Lean 4 theorems with `0 sorry`, and test them on every record. | A `delphi:Concept` per law, with `skos:definition` typed `delphi:lean4` and `delphi:leanDeclaration`, `delphi:leanTheorem`, `delphi:leanVerified` (see the [formal-verification convention](ONTOLOGY.md#formal-verification-convention-v13)). |
| **5 Script** | Write one self-contained program that reproduces the model, with deterministic self-test assertions. | The `schema:SoftwareSourceCode` the claim is about, pinned to a commit. |
| **6 Output & compare** | Render figures, animations, and a morphometrics table, placing simulated outputs beside real specimens. | The artifacts that step 8 hashes and measures. |

## Tier B: audit and publish (steps 7–12)

| Step | What happens | Ontology terms and templates |
|---|---|---|
| **7 Dual-agent audit** | Two LLM assessors from **different providers** score the script on a weighted rubric (0–100 per dimension), citing commit-pinned code lines. The builder model never scores its own work. | Each assessor is a `prov:SoftwareAgent` that `delphi:usesModel` a `delphi:LanguageModel` and `prov:actedOnBehalfOf` a person. |
| **8 Measure** | Hash the rendered outputs and independently compute residuals against the empirical data. | `delphi:EvidenceItem`s carrying a `schema:PropertyValue` with the measured value, unit, and reference value. |
| **9 Write as claims** | Compile the audit and measurements into nanopubs. | One `delphi:Claim` per simulation (claim template) with `delphi:hasAssessment` pointing to one `delphi:LLMClaimAssessment` per rubric dimension plus an overall one (rubric-assessment template). The rubric itself is a `delphi:Concept` with a `skos:narrower` concept per dimension (rubric template). |
| **10 Sign & publish** | Sign every TriG file with RSA keys, mint trusty URIs (`https://w3id.org/np/RA…`), verify the signatures, and publish to the test registry. | Signed nanopubs with `nt:wasCreatedFromTemplate` links to the Space templates. Promotion to production follows [PUBLISHING.md §3–4](PUBLISHING.md#3-publish-to-the-test-registry-immediately). |
| **11 Public record** | Commit the signed nanopubs, the publication manifest, and a SPARQL summary report. | Manifest entries per [PUBLISHING.md §8](PUBLISHING.md#8-record-every-publication). |
| **12 Remediate** | Every defect the second assessor found becomes a checklist item. The builder reworks steps 5 (and 4), regenerates outputs, re-audits, and signs a new set of nanopubs. | The new claim and assessments carry `npx:supersedes` pointing to the previous pass. Nothing published is overwritten. |

### How rubric scores are represented

- A rubric score is written as `delphi:hasScore` = score / 100. It is an uncalibrated,
  criterion-referenced rating, **not** a probability, so it never goes in
  `delphi:hasProbability`.
- The claim's `delphi:weightOfEvidence` is the overall score / 100, an optional
  unit-interval rescaling for template conformance. Generators may omit it.
- Each assessment records its dimension (`dcterms:subject` the dimension concept, and
  `delphi:assessmentType`), a verdict band (`delphi:hasVerdict`), the rationale, and its
  evidence. Findings against the work, including open remediation items, are
  `delphi:evidenceAgainst`.
- Two assessors on the same dimension are separate assessments. Their agreement is not
  independent experimental replication.

### Ontology versions

Under ontology 1.x, generators attributed assessments with `delphi:assessedBy` a
`delphi:Model` and linked papers with `delphi:derivedFromPaper`. Under 2.0 those are
deprecated in favour of `prov:wasAttributedTo` a `prov:SoftwareAgent`,
`delphi:usesModel` → `delphi:LanguageModel`, and `prov:wasDerivedFrom`. See
[what 2.0 changes](ONTOLOGY.md#what-20-changes). The morpholib builder emits either shape
(`--ontology-version 2.0`) and refuses a 2.0 build until the 2.0 templates are published.

## What the loop does and does not establish

- **It establishes** that the inputs were the paper's real data (step 3), that the stated
  invariants were machine-checked (step 4), and that two assessors from different
  providers scored the work against a fixed rubric with cited evidence (step 7).
- **It does not establish** expert validation. The audit is AI-only. A nanopub may
  describe a finding as expert-validated only if a human validation record exists;
  otherwise it is "AI-audited".
- **A Lean proof checks the mathematics, not the biology.** `delphi:leanVerified true` says
  the kernel accepted the proof text, not that the law holds in organisms. Stub proofs
  that compile but prove generic arithmetic are caught by the dummy-data checks in
  [PUBLISHING.md §2](PUBLISHING.md#2-always-inspect-for-dummy-data).

## When the loop does not fit

Pre-registrations, ontology or template changes, and inventory or entity nanopubs do
not go through all 12 steps. Say so in the nanopub's provenance or the publication
manifest, and still apply sections 2–8 of [PUBLISHING.md](PUBLISHING.md).
