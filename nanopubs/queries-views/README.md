# Published queries and views

The nanopublications in this directory are the published, signed grlc query
templates, resource views and view displays derived from the ad-hoc SPARQL in
[`../../queries/`](../../queries/). They are **immutable**: the `.trig` files
here are copies of what was published, kept so the repository records what is
live. Changing one means publishing a new version with `npx:supersedes` and
republishing any view that references it by its versioned IRI.

Published 2026-10-22, signed with the ORCID key of
[Tobias Kuhn](https://orcid.org/0000-0002-1267-0234), displayed on the
[ProbKnow space](https://nanodash.knowledgepixels.com/space?id=https://w3id.org/spaces/probknow).

| # | nanopub | artifact code | role |
|---|---------|---------------|------|
| 01 | `list-research-domains` | `RAo75bxxEGpKvhBcfXWjFAv3Q6q6P16Ofp-X1zyoDMh3w` | query |
| 02 | `list-strongest-claims` | `RAzm8_q5_DxIn4g3luEFfAaDtOxP2qpJjYRR5MjpLPXzA` | query |
| 03 | `list-delphi-nanopubs` | `RAvSQDhnAJ2MVy7Yzoo2CEHaCj62UaJOKL5smPpvWv8v0` | query |
| 04 | 🗂 Research domains | `RASqGL0HxlmdLWibHNGzDrP4hJHduePpwhLSWqJTKlY-k` | view, position `3.4.domains` |
| 05 | 🏅 Strongest claims | `RA3ER-lkVXq1UWkN4pwAUPBfnIO2_YvkclMWVOSVGOjvY` | view, position `4.6.strongestClaims` |
| 06 | 📋 All nanopubs | `RAktbxYosidKjU7KjbZZIWEADHaQjRdm7hJ_XCrTwehrs` | view, position `6.5.allNanopubs` |
| 07 | display → 🗂 Research domains | `RACw5Hzey5fpPqvpD3Sd3sqwKQUuL6lQlGz3KPXwCnceY` | space display |
| 08 | display → 🏅 Strongest claims | `RARjF0kRsXwMP5aM5w6eqq_1SKL_qOT8D9TGwm2Y3U_tw` | space display |
| 09 | display → 📋 All nanopubs | `RAvTVjII9KEJl38yuN9Shgqe6YFdNnOrW9-aLv8zSyyZc` | space display |

The `sparql-*.rq` files are the SPARQL bodies as published, kept readable
(outside the escaped `grlc:sparql` literal) for review and for re-use when a
next version is derived.

## Calling the queries

    https://query.knowledgepixels.com/api/<artifact-code>/<query-name>

`list-strongest-claims` takes one optional parameter, `min_weight`, a weight of
evidence on the claim's own 0–1 scale; left out it defaults to `0.7`.

## Namespace-agnostic by construction

All three queries enumerate every known spelling of each term rather than
relying on the ontology's `owl:equivalentClass` / `owl:equivalentProperty`
crosswalk: Nanopub Query runs on RDF4J with **no inference**, so those axioms
are documentation and have no effect at query time. Five generations are
matched:

| generation | example |
|---|---|
| Project Delphi (canonical) | `https://w3id.org/delphi/ontology/domain` |
| ProbKnow, slash form | `https://w3id.org/probknow/ontology/domain` |
| ProbKnow 1.0, hash form | `https://w3id.org/probknow/ontology/1.0#domain` |
| levin-kg, example.org base | `https://example.org/levin-kg/weightOfEvidence_deciban` |
| levin-kg, w3id base | `https://w3id.org/levin-kg/bayesFactorCombined` |

plus the `urn:pkg:` / `urn:levin-kg:` forms and `npx:hasEvidenceWeight`. The
authoritative crosswalk is `canonicalIri()` in
[`../../pipeline/probknow-builders.ts`](../../pipeline/probknow-builders.ts);
the enumerations here must be kept in step with `LEGACY_TERMS` there. Measured
cost of the folding: none — the four-form domain query runs in the same time as
the three-form ad-hoc one, because a `values` block over IRIs is an index hit.

Because the canonical `delphi:` forms are already enumerated, these queries keep
working unchanged when the publishing templates in `../signed/` are re-signed to
mint `delphi:` terms. They do **not** need to be superseded for that migration.

Two consequences of the data as it stands:

- `list-delphi-nanopubs` reaches the early levin-kg records through a second
  union branch keyed on the **class of the asserted resource**, because those
  34 nanopublications carry no `npx:hasNanopubType` at all and so are invisible
  to the admin-graph type entry point every other ProbKnow query starts from.
  The `generation` column keeps them visibly distinct.
- Domain IRIs are emitted in the `https://w3id.org/probknow/resource/domain/`
  namespace, not the canonical `delphi:` one, because that is where the domain
  part-pages and the 🔬 Claims-in-this-domain view
  (`gen:appliesToNamespace`) currently live. Match on all forms, link to the
  form the part page actually exists at. When the domain resources are reminted
  under `delphi:`, that view's namespace has to be widened in the same pass.

## Not done yet

- None of these views carries `gen:governedBy <https://w3id.org/spaces/probknow>`,
  matching the nine ProbKnow views published earlier. Until they do, only the
  key that signed them can publish a new version.
- The nine earlier queries/views are still untracked in this repository; only
  these nine are recorded here.
