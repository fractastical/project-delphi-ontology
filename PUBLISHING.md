# Publishing best practice

How every Delphi / ProbKnow / MorphoEval nanopublication gets from a generator to the
network. It applies to every generator that emits ProbKnow nanopubs, in this repository
and in downstream ones such as [morpholib](https://github.com/fractastical/morpholib).

Production nanopubs are immutable. A mistake that reaches production costs a full
supersede or retract round, and the mistaken version stays on the network forever.
Most of the rules below exist because something like that has already happened (see
[Why these rules](#why-these-rules)).

## The short version

1. **Build through the 12-step loop** wherever the work allows it.
2. **Inspect for dummy data** before anything is signed.
3. **Publish every batch to the test registry immediately.**
4. **Revisit test batches periodically and promote the ones that pass to production.**
5. **Source every assertion** with a dataset identifier, and give structured values that
   match the labels.
6. **Give every dataset its own nanopub** stating its provenance and our confidence in it.
   Claims point at that nanopub's dataset IRI.
7. **Never overwrite: supersede or retract**, signed with the same key.
8. **Record every publication** in a manifest.

## 1. Use the 12-step loop where possible

The [MorphoEval 12-step closed loop](https://github.com/fractastical/morpholib#the-12-step-closed-loop)
is the default route to a published claim:

| Tier | Steps | What it guarantees before publication |
|---|---|---|
| A: build | 1 Scout · 2 Paper · 3 Formal source · 4 Pin the rules (Lean 4) · 5 Script · 6 Output & compare | Inputs are vendored and SHA-256 locked, the paper's invariants are machine-checked, and outputs sit beside real specimens. |
| B: audit | 7 Dual-agent audit · 8 Measure · 9 Write as claims · 10 Sign & publish · 11 Public record · 12 Remediate | Two assessors from **different providers** score the work (`assessor != builder`, never self-certified), outputs are hashed and measured independently, and every defect loops back to step 5. |

When the loop does not fit, for example a pre-registration, an ontology or template
change, or an inventory or entity nanopub, say so in the nanopub's provenance or the
publication manifest, and still apply sections 2–8.

The loop's audit is AI-only. A nanopub may not describe a finding as validated by an
expert unless a human validation record exists (morpholib `morphoeval/human_validation.py`).
Otherwise it is "AI-audited".

## 2. Always inspect for dummy data

No placeholder, template, or synthetic stand-in may be published as if it were real
data. Check every batch for:

- **Synthetic series presented as measurements**: random-number or formula-generated
  values (e.g. a generic `alpha * x^1.25` series) in place of the paper's or dataset's
  actual numbers.
- **Fabricated or slot-encoded identifiers**: DOIs, accessions, or URLs that do not
  resolve, or that encode a run or slot number rather than a real record.
- **Template provenance**: a shared helper's default sources reused for an unrelated
  claim (see [Why these rules](#why-these-rules)).
- **Stub proofs**: Lean files that compile with 0 `sorry` but prove generic arithmetic
  rather than the stated law.
- **Placeholder IRIs and text**: `example.org`, `TODO`, `lorem`, `TBD`, `XXX`,
  `~~~ARTIFACTCODE~~~` left unreplaced, or empty labels.
- **Numbers that disagree**: a count or year in a label that differs from the structured
  value, the results file, or the report and dashboard that show the same quantity.

Tools that already catch part of this:

| Check | Tool |
|---|---|
| Science actually present (Tier A) vs. paper named only (B) vs. scaffold (C) | morpholib `morphoeval/audit_science_provenance.py` |
| Lean stub census | morpholib `morphoeval/census_lean_stubs.py --check` |
| `example.org` and legacy IRIs refused at construction | [`pipeline/probknow-builders.ts`](pipeline/probknow-builders.ts) (`canonicalIri()`) |
| Non-finite or out-of-range scores refused | `pipeline/` `npm test` |

Only Tier A work is published as a result. Tier B and C artifacts are not published.
If any already reached production, retract them (morpholib
`morphoeval/retract_scaffold_nanopubs.py`).

Also open a sample of the signed TriG by hand: a few nanopubs per batch, chosen at
random rather than the first few.

## 3. Publish to the test registry immediately

As soon as a batch is signed and passes section 2, publish all of it to the test
registry (`https://test.registry.knowledgepixels.com/`), not just a handful:

```bash
python3 nanopubs/publish_all_nanopubs.py --publish test     # morpholib
```

Then check it on test:

- The nanopub-java `check -v` passes on the signed files.
- A sample renders correctly in Nanodash, and its links and cited identifiers resolve.
- A SPARQL or Nanopub Query count matches the number of files published.

Test is a staging area, not a record. Do not cite test URIs in papers, dashboards,
or other nanopubs' `prov:wasDerivedFrom`. They change when the batch is promoted.

## 4. Periodically revisit and publish to production

Hold a promotion review on a fixed cadence (default: weekly, plus before any external
announcement). For each batch sitting on test, promote it only if all of these hold:

- [ ] The **same** batch passed on test: same generator commit, same inputs, same files.
- [ ] Section 2 and the sourcing checks in sections 5 and 6 pass with zero errors.
- [ ] A human has reviewed a sample. High-stakes or public-facing claims need a second
      reviewer.
- [ ] The result is final: the analysis is frozen and the report is written. Anything
      still in remediation (step 12) stays on test.
- [ ] Nothing it depends on (sources, superseded nanopubs, templates) is itself still
      on test.

```bash
python3 nanopubs/publish_all_nanopubs.py --publish prod     # morpholib
```

Batches that fail are fixed, rebuilt, and go back through section 3. They are never
patched in place on production.

**Exception: pre-registrations.** A blind prediction's value is its timestamp, so it
goes to production as soon as it passes sections 2 and 3, before the outcome is known.
Its outcome nanopub follows the normal cadence.

## 5. Source every assertion

- **A dataset identifier per assertion is required**, not per generator. Every claim
  names each dataset it actually used with `prov:used` pointing at that dataset's IRI
  (`delphir:dataset/<id>`, see section 6). A claim with no dataset identifier is not
  published. The only exception is a claim with no empirical input, such as a pure
  theorem, and it must say so explicitly.
- **Pin versions**: input file SHA-256 or dataset version, and the generator's commit.
- **Sample sizes as structured triples** (`n_specimens`, `n_species`, measurement
  protocol), not only in labels.
- **Cite secondary sources separately**: phylogenies, calibration data, and literature
  drawings are cited apart from the primary trait data.
- **State results in the nanopub**: for each hypothesis, the statement, the
  pre-registered pass criterion, the measured value, and the verdict. A link to a
  report is supplementary.
- **No hard-coded provenance defaults** in shared helpers. A builder must be given its
  sources and must fail if it is not.
- **`prov:wasDerivedFrom` points at what was actually used**, not at a planning document.
- **Attribute the agent** (human, model, or script) with `prov:wasAttributedTo` and
  `prov:actedOnBehalfOf`, and include label, license, and creator in pubinfo (see
  [`pipeline/README.md`](pipeline/README.md)).

## 6. Every dataset gets its own nanopub

By default, each dataset is published once as its own entity nanopub, and every claim
that uses it refers to it by IRI. Provenance is then stated once and checked once
instead of being re-typed into each claim, where a shared helper can get it wrong.
"Which claims used dataset X?" becomes a one-line query, so if a dataset turns out to
be wrong, every affected claim can be found.

**The dataset nanopub** introduces `delphir:dataset/<id>`, typed `dcat:Dataset`. It
reuses standard terms rather than minting new ones:

| What | Term |
|---|---|
| Persistent identifier (DOI, Zenodo, Dryad, PANGAEA, accession) | `dcterms:identifier`, plus the IRI itself in `owl:sameAs` when it is a DOI |
| Human-readable citation | `rdfs:label`, `dcterms:bibliographicCitation` |
| Paper that produced or describes it | `prov:wasDerivedFrom` / `cito:citesAsDataSource` → its DOI |
| Creator and publisher | `dcterms:creator`, `dcterms:publisher` |
| Version and the exact files used | `dcat:version`; one `dcat:distribution` per file with `dcat:downloadURL` and its SHA-256 (`spdx:checksum`) |
| Size and scope | structured counts (`n_specimens`, `n_species`, …), taxa, measurement protocol |
| License | `dcterms:license` |
| How we obtained it | `prov:wasAttributedTo` the agent that vendored it, and the retrieval date |

With no DOI, the distribution's URL and SHA-256 are the identifier and the nanopub says
so explicitly.

**Confidence in the dataset** is a separate assessment nanopub, made with the rubric
assessment template. The ontology assesses hypotheses, so the assessment evaluates one
claim about the dataset: "dataset X is an authentic, complete record of what it
describes". It scores that claim on a fixed rubric:

- **Source authority**: peer-reviewed, a curated repository, or an unreviewed upload.
- **Integrity**: the identifier resolves, and the hash matches the file we used.
- **Completeness**: missing values, and sample size against what the paper reports.
- **Independence**: not derived from our own model outputs.
- **Authenticity**: passes section 2 (real Tier A data, not a synthetic or template series).

Each dimension gets a `delphi:hasScore`, and the overall result gets
`delphi:hasProbability` and `delphi:hasConfidence`. The `assessor != builder` rule from
section 1 applies: the agent that vendored the dataset does not score it.

Confidence in a dataset is not the same as its fitness for a particular claim. Using an
excellent fish dataset for an ant claim was the error in morpholib#320, and it is not a
property of the dataset. Fitness is judged in the claim's own assessment.

**Publishing order**: the dataset nanopub and its assessment go through test and
production before any claim that cites them is promoted (the dependency gate in
section 4). A new version of a dataset supersedes its nanopub, and the claims that used
the old version keep pointing at it.

## 7. Corrections: supersede or retract, never overwrite

- **Supersede** (`npx:supersedes`) when the claim still stands but its content, sources,
  or values change. The superseding nanopub states what changed and why.
- **Retract** (`npx:retracts`) when the claim should not exist, for example scaffold
  data or a wrong dataset with no valid replacement.
- Both must be signed with the **same key** as the original, or the network ignores them.
- Corrections go through the same test-then-production path.
- Update downstream links (dashboards, synthesis nanopubs, `wasDerivedFrom` chains) to
  the new URIs, and keep the old → new mapping.

## 8. Record every publication

Every published file is recorded in a manifest with its file path, trusty URI,
registry (test or production), timestamp, and generator commit. Examples are morpholib
`nanopubs/published_manifest_{test,prod}.txt`, `morphoeval/kg/<audit>/published.json`,
and [`nanopubs/published.json`](nanopubs/published.json) here. A batch that is not in
the test manifest cannot be promoted.

Never commit signing keys, nanopub profiles, or API tokens. Keys stay in
`~/.nanopub/` or the CI secret store.

## Why these rules

- **Wrong sources on production**
  ([morpholib#320](https://github.com/fractastical/morpholib/issues/320)): 16 Thompson
  clade nanopubs (ants, bees, frogs, …) went to production citing the *fish* phylogeny
  and landmark paper, because a shared helper hard-coded them. Sample sizes appeared
  only in titles, and counts disagreed across nanopub, report, and graph.
- **Self-certified audit**: a builder model scored its own audit at 93.8. The
  independent cross-provider re-score was 26.4. This is why step 7 requires
  `assessor != builder`.
- **Scaffold loops**: template-generated datasets, slot-encoded DOIs, and stub Lean
  proofs were produced at scale, and some reached production before
  `audit_science_provenance.py` and `census_lean_stubs.py` existed to catch them.

## Still to do

Tracked in [#23](https://github.com/fractastical/project-delphi-ontology/issues/23):

- A dataset template in `nanopubs/src/` and a `buildDatasetNanopub` builder in
  `pipeline/probknow-builders.ts`, plus the dataset-reliability rubric as a rubric
  nanopub.
- A publish-time lint (in `pipeline/` or `tests/`) that rejects a claim whose
  `prov:used` is missing or does not resolve to a published dataset nanopub, missing
  structured sample sizes or results, label numbers that disagree with structured
  values, and the dummy-data patterns in section 2.
- Publishing scripts that refuse `prod` unless the batch has a recorded test pass and a
  clean lint.
- CI that runs the lint on generated TriG.
- The vocabulary for structured sample sizes (`schema:PropertyValue` or `delphi:`
  terms), and adding the `dcat:` and `spdx:` prefixes to the builders' prefix table.
