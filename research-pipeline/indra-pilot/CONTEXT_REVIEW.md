# Frozen sample context review

This agent-reviewed layer covers the original 40 statements / 200 evidence
records, not the wider collection. It is not independent expert validation.
Original imports, scores, and blank `review.csv` remain unchanged.

## Findings

- 32 passages explicitly name an organism or a substrate/host/lysate origin.
  These are not 32 uniform organism-level experiments.
- 196 records have setting notes. Many are background reports, hypotheses,
  titles, negative findings, or incomplete descriptions—not recovered protocols.
- 18 evidence-specific additions are supported by inspected paper abstracts.
- 29 evidence records are rejected **in the overlay only** as GJA1 support:
  GJs/pol (5), ODD-Luc (5), ODD hydroxylation (5), ODD acetylation (4),
  GJ/gJ (5), and psychiatric ADHD/ODD (5).
- Other identity cautions include TAT peptide and EGFP fusion constructs,
  Cx40.8 versus GJA5, and GJIC as a process rather than a protein.
- The eight incomplete-participant claims remain globally incomplete.
  Individual passages name PKC/PKC epsilon, ERK/p38, PP2A or ARD1, but a
  statement spanning multiple papers must not inherit one record's catalyst.
  Nedd4 association is not proof of direct catalysis; PAK1 is not a phosphatase.
- The ungrounded GJIC participant is interpretable as gap junctional
  intercellular communication. Its replacement ontology accession stays unknown.

## Sources and limits

All 200 imported passages were inspected, including truncated and empty
passages. Europe PMC metadata/abstract retrieval succeeded for all 172 imported
document groups. Selected abstracts were inspected for targeted additions,
especially missing participants and identity errors. Full texts were not
exhaustively reviewed. Retrieval alone is not source validation.

The source links and original passage hashes identify every decision. Paper
additions carry an abstract locator and cache hash. Unknown values use null.
Human identifiers in INDRA do not establish experimental species. A rat
background sentence in a mouse paper remains rat background; cell-free rabbit
lysate and zebrafish constructs are not conflated with host-organism experiments.
Rejected-context rows describe the actual source subject, not a repaired GJA1
claim. A retained row is still pending expert judgment of relation correctness.

Repeated readers and PMID/PMCID/DOI aliases are document-level groupings.
No document group is labeled an independent study. Secondary citations,
overlapping models, and laboratory dependencies remain unassessed.

## Reproduce without changing imports

From the repository root (use the equivalent shared-home directory there):

```sh
python scripts/indra-pilot/fetch_review_sources.py \
  --sample generated-artifacts/indra-pilot/mapped.json \
  --out generated-artifacts/indra-context-sources
python scripts/indra-pilot/review_context.py \
  --input generated-artifacts/indra-pilot \
  --sources generated-artifacts/indra-context-sources \
  --out generated-artifacts/indra-context-reviewed
python -m unittest discover -s scripts/indra-pilot -p 'test_*.py' -v
```

The original raw snapshot must be supplied locally; it is not redistributed.
The script refuses a different snapshot, a mismatching mapped file, incomplete
review coverage, missing paper anchors, and overwriting an existing review.
Use a new output directory for each revision. Keep cached passages local.
No live ingestion, hypothesis assignment, publication, or confidence updates.

The shared pilot currently lives on the open pilot branch of
`fractastical/project-delphi-ontology`, under `research-pipeline/indra-pilot`,
not on its default branch.
