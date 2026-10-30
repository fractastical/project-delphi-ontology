import test from "node:test";
import assert from "node:assert/strict";
import { Socket } from "node:net";
import {
  DC, DCAT, DELPHI, DELPHIR, NPX, OWL, PROV, RDF, SCHEMA, SPDX,
  buildDatasetNanopub, buildEntityNanopub, buildAssertionNanopub, type DatasetForNanopub,
} from "../probknow-builders";
import { triplesToTrig } from "../seal";
import { lintBatch } from "../lint";

Socket.prototype.connect = function () { throw new Error("Offline test attempted network access"); } as any;
globalThis.fetch = async () => { throw new Error("Offline test attempted fetch"); };

const date = new Date("2026-10-30T12:00:00Z");
// FishShapes v1, as in ../../examples/probknow-dataset.example.ttl.
const fishshapes: DatasetForNanopub = {
  id: "fishshapes-v1",
  label: "FishShapes v1: functionally relevant measurements of teleost shape and size on three dimensions",
  identifier: "10.5061/dryad.vt4b8gtvf",
  citation: "Price S, Friedman S, Corn K, Larouche O, et al. (2022). FishShapes v1. Dryad, doi:10.5061/dryad.vt4b8gtvf.",
  describedByDoi: "10.1002/ecy.3829",
  creators: ["Price, Samantha", "Friedman, Sarah", "Corn, Katherine", "Larouche, Olivier"],
  license: "https://creativecommons.org/publicdomain/zero/1.0/",
  issued: "2022-06-14",
  version: "v1",
  files: [{
    title: "FishShapes_specimensv1.csv",
    downloadUrl: "https://zenodo.org/records/6642650/files/FishShapes_specimensv1.csv",
    sha256: "7447fdc92c5fd5c9ecf1d9713bbd4207d2de7ab4b2ea0e320871041da8e34264",
    md5: "122b495274d0167c5447db104c7acbfe",
    byteSize: 1662135,
  }],
  counts: [
    { propertyId: "n_specimens", value: 16523, description: "Rows of FishShapes_specimensv1.csv." },
    { propertyId: "n_species", value: 6112, description: "Distinct non-empty Tree_name values, before any filtering." },
  ],
  measurementTechnique: "Linear calliper measurements (mm) of 8 traits plus specimen mass.",
  vendoredBy: { iri: `${DELPHIR}agent/morpholib-thompson-fetch-inputs`, label: "morpholib thompson/portfolio/fetch_inputs.py" },
  retrievedAt: date,
  domain: "morphology",
  createdAt: date,
};
const DS = `${DELPHIR}dataset/fishshapes-v1`;
const trig = (b: ReturnType<typeof buildDatasetNanopub>) => triplesToTrig(b.triples, b.preUri);
const claim = (over: Record<string, unknown> = {}) => buildEntityNanopub({
  id: "thompson-blind-test-fishshapes", type: DELPHI + "Claim",
  label: "Thompson blind test: predicted body-depth ratios against FishShapes v1",
  statements: [{ predicate: PROV + "used", object: DS }], domain: "morphology", createdAt: date, ...over,
});
const rules = (files: { file: string; trig: string }[], opts = {}) => lintBatch(files, opts).map(f => f.rule).sort();

test("a dataset nanopub carries the dataset convention exactly", () => {
  const { triples, preUri } = buildDatasetNanopub(fishshapes);
  const a = triples.filter(t => t.graph === preUri + "/assertion");
  const one = (s: string, p: string) => a.filter(t => t.subject === s && t.predicate === p).map(t => t.object);
  assert.deepEqual(one(DS, RDF + "type"), [DCAT + "Dataset"]);
  assert.deepEqual(one(DS, DC + "identifier"), ['"10.5061/dryad.vt4b8gtvf"']);
  assert.deepEqual(one(DS, OWL + "sameAs"), ["https://doi.org/10.5061/dryad.vt4b8gtvf"]);
  assert.deepEqual(one(DS, DC + "isReferencedBy"), ["https://doi.org/10.1002/ecy.3829"]);
  const [dist] = one(DS, DCAT + "distribution");
  assert.equal(dist, `${DS}/fishshapes-specimensv1-csv`);
  const sums = one(dist, SPDX + "checksum");
  assert.equal(sums.length, 2);
  assert.ok(sums.some(c => one(c, SPDX + "algorithm")[0] === SPDX + "checksumAlgorithm_sha256"
    && one(c, SPDX + "checksumValue")[0].startsWith('"7447fdc9')));
  const counts = one(DS, SCHEMA + "additionalProperty").map(pv => [one(pv, SCHEMA + "propertyID")[0], one(pv, SCHEMA + "value")[0]]);
  assert.deepEqual(counts, [['"n_specimens"', '"16523"^^http://www.w3.org/2001/XMLSchema#integer'],
    ['"n_species"', '"6112"^^http://www.w3.org/2001/XMLSchema#integer']]);
  // No blank nodes: nanopublications do not allow them.
  assert.ok(triples.every(t => !t.subject.startsWith("_:") && !t.object.startsWith("_:")));
  const pub = triples.filter(t => t.graph === preUri + "/pubinfo");
  assert.deepEqual(pub.filter(t => t.predicate === NPX + "introduces").map(t => t.object), [DS]);
  assert.deepEqual(pub.filter(t => t.predicate === NPX + "hasNanopubType").map(t => t.object), [DCAT + "Dataset"]);
});

test("a dataset without what PUBLISHING.md requires is refused before signing", () => {
  const without = (over: Partial<DatasetForNanopub>) => () => buildDatasetNanopub({ ...fishshapes, ...over });
  assert.throws(without({ identifier: null }), /identifier: required/);
  assert.throws(without({ noPersistentIdentifier: true }), /either identifier or noPersistentIdentifier/);
  assert.throws(without({ creators: [] }), /creators/);
  assert.throws(without({ files: [] }), /files/);
  assert.throws(without({ counts: [] }), /counts/);
  assert.throws(without({ files: [{ ...fishshapes.files[0], sha256: "abc" }] }), /sha256/);
  assert.throws(without({ counts: [{ propertyId: "n_species", value: 6112.5, description: "x" }] }), /integer/);
  assert.throws(without({ counts: [{ propertyId: "n_species", value: 1, description: "" }] }), /description: required/);
  assert.throws(without({ license: "https://example.org/license" }), /reserved for documentation/);
  assert.throws(without({ describedByDoi: "ecy.3829" }), /not a DOI/);
  // A dataset with no persistent identifier is identified by its file and says so.
  const { triples } = buildDatasetNanopub({ ...fishshapes, identifier: null, noPersistentIdentifier: true });
  assert.ok(triples.some(t => t.subject === DS && t.predicate === DC + "identifier"
    && t.object === `"${fishshapes.files[0].downloadUrl}"`));
});

test("a clean batch passes: the dataset and a claim that uses it", () => {
  assert.deepEqual(rules([{ file: "ds.trig", trig: trig(buildDatasetNanopub(fishshapes)) },
    { file: "claim.trig", trig: trig(claim()) }]), []);
  // Or the dataset was published earlier.
  assert.deepEqual(rules([{ file: "claim.trig", trig: trig(claim()) }], { publishedDatasets: [DS] }), []);
});

test("a claim with no dataset, or an unpublished one, is rejected", () => {
  const noData = claim({ statements: [] });
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(noData) }]), ["CLAIM-NO-DATASET"]);
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(claim()) }]), ["CLAIM-DATASET-UNPUBLISHED"]);
  // Exempt claims and paper-extraction batches are not required to name one.
  const iri = `${DELPHIR}claim/thompson-blind-test-fishshapes`;
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(noData) }], { exempt: new Map([[iri, "pure theorem"]]) }), []);
  const edge = buildAssertionNanopub({ id: "e1", subject: `${DELPHIR}claim/c1`, predicate: DC + "description",
    object: "Gap junctions mediate the signal", domain: "bioelectricity", createdAt: date });
  assert.deepEqual(rules([{ file: "e.trig", trig: trig(edge) }]), ["CLAIM-NO-DATASET"]);
  assert.deepEqual(rules([{ file: "e.trig", trig: trig(edge) }], { extracted: true }), []);
});

test("the morpholib#320 failure shapes are caught", () => {
  // A count in the label that disagrees with, or is missing from, the structured values.
  const wrong = { ...fishshapes, label: "FishShapes v1 (6,095 species)" };
  assert.deepEqual(rules([{ file: "d.trig", trig: trig(buildDatasetNanopub(wrong)) }]), ["COUNT-MISMATCH"]);
  const approx = { ...fishshapes, label: "Pheidole worker heads (~200 species)", counts: [
    { propertyId: "n_species", value: 290, description: "Species with at least one measured worker." }] };
  assert.deepEqual(rules([{ file: "d.trig", trig: trig(buildDatasetNanopub(approx)) }]), ["COUNT-APPROXIMATE"]);
  const unstructured = claim({ label: "Ant caste allometry across 300 species" });
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(unstructured) }], { publishedDatasets: [DS] }),
    ["COUNT-UNSTRUCTURED"]);
  // The exact structured value in the label passes.
  const right = { ...fishshapes, label: "FishShapes v1 (6,112 species)" };
  assert.deepEqual(rules([{ file: "d.trig", trig: trig(buildDatasetNanopub(right)) }]), []);
});

test("dummy data is caught, and real DOIs ending in four digits are not", () => {
  const scaffold = claim({ label: "TODO: fill in the law", paper: { title: "Seed", doi: "10.1242/dev.1998.0101" } });
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(scaffold) }], { publishedDatasets: [DS] }),
    ["DUMMY-DOI", "DUMMY-TEXT", "DUMMY-TEXT"]);
  const fake = claim({ paper: { title: "Seed", doi: "10.0000/morphoeval.0042" } });
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(fake) }], { publishedDatasets: [DS] }), ["DUMMY-DOI"]);
  // 10.1002/ecy.3829 is the real FishShapes paper.
  assert.deepEqual(rules([{ file: "d.trig", trig: trig(buildDatasetNanopub(fishshapes)) }]), []);
});

test("year-plus-slot DOIs are accepted from registrants that really mint them", () => {
  // Turing (1952) and a Theoretical Population Biology paper (Academic Press); both resolve.
  for (const doi of ["10.1098/rstb.1952.0012", "10.1006/tpbi.1999.1420"]) {
    const real = claim({ paper: { title: "Real", doi } });
    assert.deepEqual(rules([{ file: "c.trig", trig: trig(real) }], { publishedDatasets: [DS] }), [], doi);
  }
  // The same suffix shape under another registrant is still flagged, also beside a real one.
  const mixed = claim({ paper: { title: "Seed", doi: "10.1242/dev.1998.0101" },
    statements: [{ predicate: DC + "description", object: "See 10.1098/rstb.1952.0012" },
      { predicate: PROV + "used", object: DS }] });
  assert.deepEqual(rules([{ file: "c.trig", trig: trig(mixed) }], { publishedDatasets: [DS] }), ["DUMMY-DOI"]);
});

test("a dataset written by hand without checksums or counts is rejected", () => {
  const ttl = `<${DELPHIR}x> { <${DS}> a <${DCAT}Dataset> ; <${DC}identifier> "10.5061/dryad.vt4b8gtvf" . }`;
  assert.deepEqual(rules([{ file: "h.trig", trig: ttl }]),
    ["DATASET-COUNTS", "DATASET-CREATOR", "DATASET-FILES", "DATASET-LICENSE"]);
});
