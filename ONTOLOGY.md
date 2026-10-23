# Project Delphi Ontology (v2.0)

Authoritative vocabulary for the Project Delphi / Science Oracle probabilistic knowledge graph. This directory is
the single source of truth for the namespaces the paper should cite; the machine-readable T-Box is
[`delphi.ttl`](./delphi.ttl).

## Namespaces

| Prefix | IRI | Holds |
|---|---|---|
| `delphi:` | `https://w3id.org/delphi/ontology/` | **Terms** (classes & predicates) — the T-Box. Slash-based and unversioned (`…/ontology/Claim`); the version lives in `owl:versionIRI` (`…/ontology/2.0`) only. Earlier `probknow` slash terms (`…/probknow/ontology/<Term>`) and version 1.0 hash terms (`…/probknow/ontology/1.0#`) are mapped in the crosswalk. |
| `delphir:` | `https://w3id.org/delphi/resource/` | **Individuals** (papers, claims, hypotheses, assessments…) — the A-Box |

Both are intended to be **dereferenceable** via a [w3id.org](https://w3id.org) redirect to this
repository (and, for `delphi:`, to content-negotiate the Turtle file). Individuals are
`delphir:<kind>/<id>`, where the id is either the application's own key (letters, digits, `_`, `-`) or
the artifact code of the nanopublication that introduces the individual (`delphir:claim/RA…`), which is
what the Project Delphi templates mint in Nanodash and what the pipeline mints when it is given no id. This replaces every earlier,
non-dereferenceable identifier (`https://w3id.org/probknow/resource/*`, `urn:pkg:*`, `urn:levin-kg:*`, `https://example.org/levin-kg/*`)
and the three per-export-wave bases (`w3id.org/{levin-kg,aif,morphopkg}`).

## Design rule

> Reuse a standard term wherever one **means the same thing**; mint a `delphi:` term only where
> none does — chiefly the probabilistic-evaluation layer, which has no settled standard.

"Means the same thing" is the whole test, and it is applied conservatively. A minted term is
replaced when the standard term it would give way to is from a widely adopted vocabulary **and**
the minted term carries nothing the rest of the data does not already say. It is kept when the
standard candidates only roughly overlap it, when the only candidates come from vocabularies with
no real uptake, or when the minted term is the only type or key a node carries — because
nanopublication query endpoints run without inference, so on the network an alignment axiom is
documentation, not a substitute for the term. [Terms kept on purpose](#terms-kept-on-purpose-and-why)
records each of those decisions.

## What 2.0 changes

Version 2.0 is the first release that changes what an existing term means, hence the major bump.
Nothing already published loses its meaning: every deprecated term keeps its definition and its
subsumption axiom, so a reasoning store derives the replacement from old data.

| Change | Before (≤ 1.3) | From 2.0 |
|---|---|---|
| Claims and hypotheses are one hierarchy | `delphi:Claim` and `delphi:Hypothesis` were siblings; a hypothesis was specifically a *named cluster* of claims | `delphi:Claim` ⊑ `delphi:Hypothesis`. A hypothesis is any proposition the graph represents without asserting; a claim is one that a source states. Clustering is `skos:narrower`, not a class |
| The assessor is an agent, the model an element of it | `delphi:Model`, one node that was both the agent an assessment was attributed to and the model it ran | `prov:SoftwareAgent` for the assessor, `delphi:usesModel` → `delphi:LanguageModel` for the model it runs, so two agents sharing a model but differing in prompt are distinguishable |
| Redundant project terms give way to standards | `delphi:assessedBy`, `delphi:derivedFromPaper`, `delphi:Paper` | `prov:wasAttributedTo`, `prov:wasDerivedFrom` — which the builders already emitted in the provenance graph for the same facts — and `fabio:ScholarlyWork` |

Why the collapse rather than a rename: `delphi:hasAssessment` was already used with claims as its
subject, and its `owl:inverseOf` — `delphi:evaluatesHypothesis` — has `delphi:Hypothesis` as its range, so
every assessed claim was a hypothesis by entailment well before 2.0 said so. The 1.x split was not
holding.

## T-Box — classes

| Term | Status | Aligns to | Meaning |
|---|---|---|---|
| `delphi:Paper` | **deprecated (v2.0)** | → `fabio:ScholarlyWork`; ⊑ it | An ingested scholarly work (DOI where available). Said no more than FaBiO's class, and its 1.x superclass `fabio:ResearchPaper` was narrower than what it typed. |
| `delphi:Concept` | minted | `skos:Concept` | A reusable entity/method/term referenced by claims. |
| `delphi:Hypothesis` | minted | `skos:Concept` | A proposition the graph represents without asserting — anything whose credibility is carried by attached `delphi:Assessment` instances. Hierarchical via `skos:broader`/`narrower`. |
| `delphi:Claim` | minted | ⊑ `delphi:Hypothesis`; SEPIO (assertion) | A hypothesis that a source states: extracted from a paper (or a commit, dataset or rubric) and linked to it with `prov:wasDerivedFrom`. **A belief, not an asserted fact.** |
| `delphi:TestableHypothesis` | minted | ⊑ `delphi:Hypothesis` | Hypothesis + proposed test + prior + resolvability. |
| `delphi:EconomicPrediction` | minted | — | Dated market-size / time-to-impact forecast tied to a hypothesis. |
| `delphi:EvidenceItem` | minted | ECO | One piece of supporting/opposing evidence. |
| `delphi:Assessment` | minted | ⊑ `prov:Entity`; SEPIO | An n-ary evaluation yielding a probability/verdict. |
| `delphi:BayesianAssessment` | minted | ⊑ `delphi:Assessment` | Assessment with Bayes factors + calibration. |
| `delphi:LLMClaimAssessment` | minted | ⊑ `delphi:Assessment` | Assessment produced by a software agent running a language model. |
| `delphi:LanguageModel` | minted (v2.0) | ⊑ `prov:Entity` | The trained model a software agent runs: one element of the agent, not the agent itself. Name in `rdfs:label`, API id in `dcterms:identifier`, version in `schema:softwareVersion`. |
| `delphi:Model` | **deprecated (v2.0)** | → `prov:SoftwareAgent`; ⊑ it | Conflated the assessing agent with the model it runs. Kept so published nanopubs stay interpretable. |
| `delphi:Domain` | minted | ⊑ `skos:Concept` | A frontier-science domain (`delphir:domain/<slug>`, labelled with the slug). |

## T-Box — properties

| Term | Kind | Status | Aligns to | Meaning |
|---|---|---|---|---|
| `delphi:hasAssessment` | object | minted | — | Hypothesis (so also claim) → its assessment. |
| `delphi:evaluatesHypothesis` | object | minted | inverse of `delphi:hasAssessment` | Assessment → proposition evaluated; covers claims since 2.0. |
| `delphi:usesModel` | object | minted (v2.0) | — | `prov:SoftwareAgent` → the `delphi:LanguageModel` it runs. Repeatable. |
| `delphi:assessedBy` | object | **deprecated (v2.0)** | → `prov:wasAttributedTo`; ⊑ it | Assessment → agent that produced it. Range widened to `prov:Agent`. |
| `delphi:hasEvidence` | object | minted | — | Claim/assessment → evidence item. |
| `delphi:derivedFromPaper` | object | **deprecated (v2.0)** | → `prov:wasDerivedFrom`; ⊑ it | Claim → source paper. |
| `delphi:hasEconomicPrediction` | object | minted | — | Hypothesis → economic prediction. |
| `delphi:hasProbability` | data | minted | — | P(claim true) ∈ [0,1]. |
| `delphi:hasConfidence` | data | minted | — | Assessor self-confidence ∈ [0,1]. |
| `delphi:hasPriorProbability` | data | minted | — | Prior on a testable hypothesis. |
| `delphi:hasResolvability` | data | minted | — | How decidably a hypothesis can be tested ∈ [0,1]. |
| `delphi:hasVerdict` | data | minted | — | Short categorical label. |
| `delphi:hasScore` | data | minted | — | Score of an assessment on a rubric dimension (or overall), normalized to [0,1]; a graded judgement, not a probability. Added in 1.2. |
| `delphi:evidenceFor` | data | minted | `cito:supports` | Free-text supporting point. |
| `delphi:evidenceAgainst` | data | minted | `cito:disagreesWith` | Free-text opposing point. |
| `delphi:weightOfEvidence` | data | minted | — | Panel-assigned weight of evidence, a score in [0,1]. On the claim/evidence IRI, or on a single-statement nanopub's assertion graph (in its provenance graph). |
| `delphi:weightOfEvidenceDeciban` | data | minted | — | Weight of evidence in decibans (10·log10 of the combined Bayes factor). |
| `delphi:vovkSellkeMaxPRatio` | data | minted | — | Vovk–Sellke maximum p-ratio bound on an evidence item's Bayes factor. |
| `delphi:statisticalTest` | data | minted | — | Free-text description of the test an evidence item's p-value comes from. |
| `delphi:context` | data | minted | — | Free-text experimental context; domain widened from `delphi:Claim` to `delphi:Hypothesis` in 2.0. |
| `delphi:bayesFactor` | data | minted | — | Bayes factor. |
| `delphi:pValue` | data | minted | — | Statistical p-value of an evidence item. |
| `delphi:calibrationMethod` | data | minted | — | Calibration procedure used. |
| `delphi:proposedTest` | data | minted | — | The experiment that would resolve the hypothesis. |
| `delphi:assessmentType` | data | minted | — | Kind of assessment (e.g. 'multi-llm-claim-evaluation'). |
| `delphi:hypothesisType` | data | minted | — | Kind of hypothesis (e.g. 'platonic-space-of-forms'). |
| `delphi:marketSizeUsdBillions` | data | minted | — | Addressable market — **unit fixed: USD billions**. |
| `delphi:yearsToAchievement` | data | minted | — | Years until realization. |
| `delphi:domain` | object | minted | ⊑ `dcterms:subject` | Nanopub/node → its `delphi:Domain` (`delphir:domain/<slug>`). Pre-2026-10 nanopubs carry the slug as a literal. |
| `delphi:leanDeclaration` | data | minted (v1.3) | — | `delphi:Concept` (a mathematical law) → fully qualified Lean 4 identifier of the definition that formalises it. |
| `delphi:leanTheorem` | data | minted (v1.3) | — | `delphi:Concept` → fully qualified Lean 4 identifier of the theorem proved about the law; repeatable. |
| `delphi:leanVerified` | data | minted (v1.3) | — | `xsd:boolean`: the Lean 4 kernel accepted the module (no `sorry`, no extra axioms) at the commit in `rdfs:seeAlso`. A fact about the proof text, **not** a probability. |

### Datatypes

| Term | Status | Meaning |
|---|---|---|
| `delphi:lean4` | minted (v1.3) | Literal datatype for Lean 4 source text. Used on `skos:definition` of a `delphi:Concept` that formalises a law: `skos:definition "def … theorem … := by …"^^delphi:lean4`. |

### Formal-verification convention (v1.3)

A `delphi:Concept` that stands for a governing mathematical law of a claim's model carries the law
three ways, in increasing strictness: `skos:notation` (the formula as humans write it),
`skos:definition` typed `delphi:lean4` (the Lean 4 `def` and `theorem`), and
`delphi:leanDeclaration` / `delphi:leanTheorem` / `delphi:leanVerified` (the identifiers the kernel checked and
whether it accepted them), with `schema:programmingLanguage "Lean 4"` and commit-pinned
`rdfs:seeAlso` loci for both the Lean module and the implementing code. The terms are
prover-specific on purpose: "verified" means something different under each kernel. A kernel
check establishes the theorem as stated in Lean; whether that statement is a faithful rendering of
the published law, and whether a script implements it, remain `delphi:Assessment` questions on the
claim. First used by MorphoEval (`morpholib/morphoeval/math_kg.py`, 22 law concepts, all
`delphi:leanVerified true`); see `examples/probknow-math-law-lean.example.ttl`.

### Reused directly (no `delphi:` term minted)

`fabio:ScholarlyWork` (FaBiO — replaces the minted `delphi:Paper` as of 2.0);
`np:Nanopublication`, `np:hasAssertion`/`hasProvenance`/`hasPublicationInfo`, `npx:introduces`,
`npx:supersedes`, `npx:hasNanopubType`, `npx:Bot`/`SoftwareAgent`,
`npx:declaredBy`/`hasAlgorithm`/`hasPublicKey` (nanopub schema + signing);
`prov:wasDerivedFrom`/`wasAttributedTo`/`wasGeneratedBy`/`actedOnBehalfOf`, `prov:SoftwareAgent`,
`prov:Entity` (PROV-O — `wasDerivedFrom`, `wasAttributedTo` and `SoftwareAgent` replace minted terms as of 2.0);
`skos:Concept`/`broader`/`narrower`/`exactMatch`/`notation`/`definition` (SKOS);
`schema:programmingLanguage`, `schema:softwareVersion`, `schema:value`/`targetValue`/`unitText`/`error`, `schema:QuantitativeValue` (schema.org, for measured evidence items and language-model versions);
`dcterms:title`/`identifier`/`created`/`creator`/`description`/`license`/`date`/`subject`/`isReplacedBy` (Dublin Core);
`foaf:name`/`homepage`, `frbr:owner` (agent introduction).

## Deprecated in 2.0 — migrating

| Deprecated | Use instead | What to do with data that has the old term |
|---|---|---|
| `delphi:Model` (class) | `prov:SoftwareAgent` for the assessor; `delphi:usesModel` → `delphi:LanguageModel` for the model | Published nanopubs keep the type and still entail `prov:SoftwareAgent`. New assessments mint `delphir:agent/<model-id>` for the agent and `delphir:model/<model-id>` for the model it runs. |
| `delphi:assessedBy` | `prov:wasAttributedTo` | Nothing: the builders already wrote `prov:wasAttributedTo` into the provenance graph of every assessment nanopub, so the fact is present twice in existing data. |
| `delphi:derivedFromPaper` | `prov:wasDerivedFrom` | Nothing: likewise already written in provenance. |
| `delphi:Paper` (class) | `fabio:ScholarlyWork` | Published nanopubs keep the type and still entail `fabio:ScholarlyWork`. Prefer naming a source paper by its `https://doi.org/` IRI, which needs no class. |

Deprecation here means `owl:deprecated true` plus `dcterms:isReplacedBy` on the term, and the
**subsumption** axiom (`rdfs:subClassOf` / `rdfs:subPropertyOf`) to its replacement — not
`owl:equivalent*`, which would wrongly make every `prov:SoftwareAgent` a `delphi:Model`. A store that
reasons therefore answers a `prov:wasAttributedTo` query over data published with `delphi:assessedBy`.

Nanopub Query runs on RDF4J **without inference** (see
[`nanopubs/queries-views/README.md`](nanopubs/queries-views/README.md)), so a query that must reach
both generations enumerates both spellings, exactly as the published queries already enumerate the
legacy namespaces. `canonicalIri()` in
[`pipeline/probknow-builders.ts`](pipeline/probknow-builders.ts) rewrites the three deprecated terms
on the way out, so newly built nanopublications carry only the replacements.

### Terms kept on purpose, and why

The reuse pass considered every minted term. These were deliberately **not** replaced:

| Term | Candidate | Why it was kept |
|---|---|---|
| `delphi:Concept` | `skos:Concept` | Its extension includes things that are not units of thought in the SKOS sense (a gene, an instrument), and it is the only type these nodes carry, so without inference it is the only handle by which they can be found on the network. Kept as `⊑ skos:Concept`. |
| `delphi:domain` | `dcterms:subject` | Membership in Delphi's curated domain index is narrower than being a topic of a resource, and it is the key every domain query partitions on, which a term as widely used as `dcterms:subject` could not serve. Now `⊑ dcterms:subject`. |
| `delphi:Assessment` and its subclasses, `delphi:hasProbability`, `delphi:hasConfidence`, `delphi:hasScore`, `delphi:hasVerdict`, `delphi:weightOfEvidence*`, `delphi:bayesFactor`, `delphi:calibrationMethod` | SEPIO, ECO | SEPIO models assertions and evidence items but is, in its own words, in early development with no uptake outside the Monarch Initiative; ECO types kinds of evidence rather than n-ary evaluations. Kept with `rdfs:seeAlso` alignment targets. |
| `delphi:pValue`, `delphi:statisticalTest`, `delphi:vovkSellkeMaxPRatio` | OBI, STATO | Those vocabularies model statistical quantities as *classes* of information entities, not as datatype properties, so adopting them would be a remodelling rather than a term swap. |
| `delphi:evidenceFor`, `delphi:evidenceAgainst` | `cito:supports`, `cito:disagreesWith` | The CiTO terms are object properties between works; these carry free text. The `rdfs:seeAlso` pointers say which CiTO term to use when the evidence *is* a citable work. |
| `delphi:marketSizeUsdBillions`, `delphi:yearsToAchievement` | `schema:MonetaryAmount`, `schema:QuantitativeValue` | A possible future remodelling, not a term swap: the unit is fixed in the predicate on purpose so a value can never be read in the wrong currency or scale. |
| `delphi:lean4`, `delphi:leanDeclaration`, `delphi:leanTheorem`, `delphi:leanVerified` | — | No RDF vocabulary for machine-checked mathematics is in use (OMDoc/MMT are XML formats without an RDF binding). Deliberately prover-specific; see below. |

## Legacy → canonical crosswalk

Earlier export waves used identifiers that are now legacy, pre-rebrand nanopubs used `https://w3id.org/probknow/ontology/<Term>` and `https://w3id.org/probknow/resource/<kind>/<id>`, and ontology version 1.0 used hash-based term IRIs (`https://w3id.org/probknow/ontology/1.0#<Term>`), of which `weightOfEvidence` and `domain` occur in published nanopubs; every `probknow` and 1.0 term is mapped to its `https://w3id.org/delphi/ontology/<Term>` successor of the same name. Published nanopubs are
immutable, so the ontology maps every legacy **term** with `owl:equivalentClass` /
`owl:equivalentProperty` axioms (section *Backward-compatibility crosswalk* in the TTL), and
the builders rewrite every legacy identifier they are handed with `canonicalIri()` in
`pipeline/probknow-builders.ts`, driven by the same table. `example.org` is reserved for
documentation (RFC 2606) and `w3id.org/levin-kg` was never registered, so neither may appear
in new nanopubs; the builders throw on any `example.*` IRI that survives canonicalization.

**Individuals** map by pattern:

| Legacy identifier (pre-1.3) | Canonical (`https://w3id.org/delphi/resource/`) |
|---|---|
| `https://w3id.org/probknow/resource/<kind>/<id>` | `delphir:<kind>/<id>` |
| `https://example.org/levin-kg/claim-<id>` (also `w3id.org/levin-kg/…`) | `delphir:claim/<id>` |
| `https://example.org/levin-kg/evidence-<id>` | `delphir:evidence/<id>` |
| `https://example.org/levin-kg/assessment-<id>` | `delphir:assessment/<id>` |
| `urn:pkg:assessment:<id>` | `delphir:assessment/<id>` |
| `urn:pkg:hypothesis:<id>` | `delphir:hypothesis/<id>` |
| `urn:pkg:model:<m>` | `delphir:model/<m>` |
| `urn:pkg:platonic:<code>` | `delphir:platonic/<code>` |
| `urn:levin-kg:assertion:<id>` | `delphir:claim/<id>` |
| `urn:levin-kg:paper:<id>` | `delphir:paper/<id>` |
| `urn:levin-kg:system:publisher` | the system agent (`SYSTEM_ID`) |

**Terms** map one to one:

| Legacy term | Canonical (1.0) |
|---|---|
| `example.org/levin-kg/Assertion` | `delphi:Claim` |
| `example.org/levin-kg/BayesianAssessment` (also `w3id.org/levin-kg/…`) | `delphi:BayesianAssessment` |
| `example.org/levin-kg/EvidenceItem` | `delphi:EvidenceItem` |
| `example.org/levin-kg/weightOfEvidence`, `npx:hasEvidenceWeight` | `delphi:weightOfEvidence` |
| `example.org/levin-kg/weightOfEvidence_deciban` (also `w3id.org/levin-kg/…`) | `delphi:weightOfEvidenceDeciban` |
| `example.org/levin-kg/bayesFactorCombined` (also `w3id.org/levin-kg/…`) | `delphi:bayesFactor` |
| `example.org/levin-kg/bayesFactorVS_MPR` | `delphi:vovkSellkeMaxPRatio` |
| `example.org/levin-kg/calibrationMethod` | `delphi:calibrationMethod` |
| `example.org/levin-kg/pValue` | `delphi:pValue` |
| `example.org/levin-kg/statisticalTest` | `delphi:statisticalTest` |
| `example.org/levin-kg/context` | `delphi:context` |
| `example.org/levin-kg/hasAssessment` | `delphi:hasAssessment` |
| `urn:pkg:TestableHypothesis`, `urn:pkg:hasPriorProbability`, `urn:pkg:hasResolvability`, `urn:pkg:proposedTest`, `urn:pkg:hypothesisType` | `delphi:*` of the same name |
| `urn:levin-kg:property:domain` | `delphi:domain` |

## Scope boundary (deliberate)

The live **nanopub generation** path (`server/nanopub-signer.ts`, built on `pipeline/`) emits
the canonical `delphi:`/`delphir:` namespaces as of v1.0, rewriting legacy identifiers on the way out.
Two things are intentionally **not** rewritten:

1. **Already-signed, stored nanopubs** keep their original Trusty URIs and TriG. Trusty URIs are
   content hashes, so historical artifacts are immutable by design; only newly signed nanopubs use
   v1.0 terms. (This is a vocabulary version bump, not a data migration.)
2. **Persisted graph-instance URLs** inside stored assertions (e.g. `https://example.org/levin-kg/…`)
   are bound to existing rows and the seed `.trig` fixtures. The builders canonicalize them at
   export time, so new nanopubs are clean regardless; rewriting the rows themselves (with the
   same rules) is a separate A-Box migration in the application database.

Cited source papers continue to use real `https://doi.org/<doi>` IRIs as their subjects, which is
already dereferenceable and preferred over any minted identifier.

### Not done yet for 2.0

The ontology, the builders, the examples and the template *sources* are on 2.0. Three artifacts on
the network are not, because changing a published nanopublication means publishing a new version of
it with the signing key:

1. **Assertion templates 04, 05, 07 and 18** (`nanopubs/src/`) are regenerated against 2.0 and carry
   a `skos:changeNote`, but the signed and published versions in `nanopubs/signed/` still describe the
   1.x shape. Until `python3 nanopubs/generate.py && bash nanopubs/sign.sh` is run and the new
   versions are published, a nanopub built by `pipeline/` links the template version it no longer
   matches; `TEMPLATES` in `pipeline/probknow-builders.ts` carries the same warning and the IRIs to
   replace afterwards.
2. **The published `list-delphi-nanopubs` query** (`nanopubs/queries-views/`) enumerates class IRIs
   and so will need `delphi:LanguageModel` added when a next version is derived. It keeps working for
   everything published so far, including every `delphi:Model` nanopub.
3. **Stored nanopubs and application rows** keep `delphi:Model`, `delphi:assessedBy` and
   `delphi:derivedFromPaper`; the deprecation axioms are what keep them interpretable, and the builders
   rewrite the terms the next time a row is exported.
