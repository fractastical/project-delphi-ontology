# INDRA → Project Delphi: isolated GJA1 pilot

A bounded, read-only mapping of real INDRA connexin-43/GJA1 statements into the
current Project Delphi ontology. This is not a biological validation, an
independent-replication assessment, or a production ingestion.

## Run

Python 3.10+; standard library only, no package installation or credentials.

```sh
python3 pilot.py --out generated-artifacts/indra-pilot
python3 pilot.py --input generated-artifacts/indra-pilot/raw.json --out generated-artifacts/indra-replay
python3 -m unittest discover -s . -p 'test_*.py' -v
```

Run from this directory, or prefix the script path. If the public endpoint later
requires authentication, this program fails explicitly; it does not fabricate a
sample. Use a legitimately obtained INDRA JSON snapshot with `--input` instead.
Do not commit generated outputs or the raw snapshot.

## Files produced

- `raw.json`: exact local response, including upstream source passages; preserve
  locally for audit. Source-specific licensing applies; not for blanket redistribution.
- `manifest.json`: snapshot SHA-256, mapper SHA-256, retrieval/replay mode and query.
- `mapped.json`: typed mechanisms, source IDs, context, flags, separate INDRA beliefs.
- `mapped.jsonld`: unsigned, unpublished RDF export using the current slash-form
  `delphi:` namespace. Custom `pilot:` fields are explicitly local extensions.
- `summary.json`: structural checks, not scientific accuracy metrics.
- `review.csv`: blank expert evaluation fields for a same-paper comparison.
- `report.html`: self-contained, browsable review report with source links and
  expandable mechanism/context details. No source passages are republished.

## Mapping contract

| INDRA information | Destination |
| --- | --- |
| Supported statement, including qualifiers and agent states | `delphi:Claim` + lossless mechanism JSON |
| Paper identifiers | `fabio:ScholarlyWork`, `prov:wasDerivedFrom` |
| Evidence metadata and experimental context | `delphi:EvidenceItem`, `delphi:hasEvidence`, `delphi:context` |
| Original belief | `delphi:Assessment` + **pilot:indraBelief**, never `delphi:hasProbability` or `delphi:weightOfEvidence` |
| Statement/source hashes | Strings, preserving exact integer identity |
| Unsupported statement types | Explicit quarantine; never silently coerced |

The endpoint does not identify its belief scorer/version. We retain that as
unknown and do not label the score Bayesian or assign a Delphi confidence.
Up to five evidence records are requested per statement; imported belief scores
can reflect a larger evidence pool. This sample is not exhaustive or random.

Paper aliases (PMID, PMCID, normalized DOI) are joined transitively. Repeated
readers/passages do not create new paper groups. Conflicting aliases are flagged.
These are **document groups**, not independent experiments or validated identities.
Cross-paper study dependencies and preprint/version relationships still need review.
Names/identifiers are retained as supplied, not independently re-grounded.
No organism, enzyme, missing context, or broader hypothesis link is inferred.

Supported types: Activation, Inhibition, IncreaseAmount, DecreaseAmount,
Phosphorylation, Dephosphorylation, Ubiquitination, Hydroxylation, Acetylation,
and Complex. A generic type label is not a claim that a mechanism occurs in all
organisms or experimental conditions.

## Review gate

Review entity identity, relation correctness, paper support, context retention,
and performance against the current extraction on the same papers. No production
writes, nanopublication submissions, hypothesis assignment, or confidence
aggregation are implemented. Any promotion is a separate decision.

Ontology: https://github.com/fractastical/project-delphi-ontology
INDRA: https://www.indra.bio/
Source query: https://db.indra.bio/statements/from_agents?agent0=GJA1&limit=40&ev_limit=5
