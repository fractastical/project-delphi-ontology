// Publish-time lint for a batch of ProbKnow nanopublications (../PUBLISHING.md).
//
// Run it on the signed TriG of a batch before publishing to the test registry, and again
// before promoting the batch to production. Every finding is an error: a batch with any
// finding is not published.
//
//   npx tsx lint.ts <file.trig | directory> … [--published-datasets <file>] [--exempt <file>] [--extracted]
//
//   --published-datasets  one delphir:dataset/ IRI per line: datasets already published, so
//                         claims in this batch may cite them without the batch containing them
//   --exempt              "<claim IRI><TAB><reason>" per line: claims with no empirical input
//                         (e.g. a pure theorem), recorded in the publication manifest
//   --extracted           the batch holds claims extracted from a paper's text, which cite the
//                         paper rather than a dataset; the dataset requirement is not applied
//
// SPDX-License-Identifier: MIT

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { Parser, type Quad } from "n3";
import { ARTIFACT_CODE, DC, DCAT, DELPHI, DELPHIR, NP_NS, NPX, PROV, RDF, RDFS, SCHEMA, SPDX } from "./probknow-builders.js";

export interface Finding {
  rule: string;
  file: string;
  subject: string;
  message: string;
}

export interface LintOptions {
  publishedDatasets?: Iterable<string>;
  /** Claim IRI → why it has no dataset. */
  exempt?: Map<string, string>;
  extracted?: boolean;
}

export interface NanopubFile {
  file: string;
  trig: string;
}

const DATASET_NS = `${DELPHIR}dataset/`;
const SHA256 = `${SPDX}checksumAlgorithm_sha256`;
const PLACEHOLDER = /\b(TODO|TBD|FIXME|XXX)\b|lorem ipsum|\bplaceholder\b|\bdummy (data|value)/i;
const RESERVED_IRI = /^https?:\/\/([a-z0-9-]+\.)*example\.(org|com|net)\//i;
// Generators that fabricate DOIs either use the reserved 10.0000 prefix or append a slot number
// to a year (10.1242/dev.1998.0101). A bare ".dddd" suffix is common in real DOIs (10.1002/ecy.3829).
// Some registrants really do mint <journal>.<year>.<number> suffixes, so year-plus-slot DOIs under
// them are not flagged: the Royal Society (10.1098/rstb.1952.0012) and Academic Press
// (10.1006/jtbi.2000.2093). Add a registrant only after checking real DOIs of that form resolve.
const RESERVED_DOI = /\b10\.0000\//;
const YEAR_SLOT_DOI = /\b(10\.\d{4,9})\/\S*\.(?:19|20)\d{2}\.\d{4}\b/g;
const YEAR_SLOT_REGISTRANTS = new Set(["10.1098", "10.1006"]);
const fabricatedDoi = (v: string): boolean =>
  RESERVED_DOI.test(v) || [...v.matchAll(YEAR_SLOT_DOI)].some(m => !YEAR_SLOT_REGISTRANTS.has(m[1]));
// A number hyphenated to the word before it names a stage or format ("stage-45 images",
// "96-well samples"), not a count, so it is skipped.
const COUNT_IN_TEXT = /(~|≈|\bc\.\s*|\babout\s+|\bapprox(?:\.|imately)?\s+|\bon the order of\s+)?(?<![\w-])(\d{1,3}(?:,\d{3})+|\d+)\s+(species|specimens|genera|families|taxa|individuals|samples|images|sites|populations)\b/gi;

/** Lint a batch. Returns every finding; an empty list means the batch may be published. */
export function lintBatch(files: NanopubFile[], opts: LintOptions = {}): Finding[] {
  const findings: Finding[] = [];
  const parsed = files.map(f => {
    try {
      return { file: f.file, quads: new Parser({ format: "application/trig" }).parse(f.trig) };
    } catch (e) {
      findings.push({ rule: "PARSE", file: f.file, subject: "", message: `does not parse as TriG: ${(e as Error).message}` });
      return { file: f.file, quads: [] as Quad[] };
    }
  });

  const datasetsInBatch = new Set<string>();
  for (const { quads } of parsed)
    for (const q of quads)
      if (q.predicate.value === RDF + "type" && q.object.value === DCAT + "Dataset") datasetsInBatch.add(q.subject.value);
  const known = new Set([...datasetsInBatch, ...(opts.publishedDatasets ?? [])]);

  for (const { file, quads } of parsed) {
    const seen = new Set<string>();
    const add = (rule: string, subject: string, message: string) => {
      const key = `${rule}\n${subject}\n${message}`;
      if (!seen.has(key)) findings.push({ rule, file, subject, message });
      seen.add(key);
    };
    const out = (s: string, p: string) => quads.filter(q => q.subject.value === s && q.predicate.value === p).map(q => q.object);
    const typed = (cls: string) => [...new Set(quads.filter(q => q.predicate.value === RDF + "type" && q.object.value === cls).map(q => q.subject.value))];
    const assertionGraphs = new Set(quads.filter(q => q.predicate.value === NP_NS + "hasAssertion").map(q => q.object.value));

    // ── Dummy data ──
    for (const q of quads) {
      for (const t of [q.subject, q.predicate, q.object]) {
        if (t.termType === "NamedNode") {
          if (RESERVED_IRI.test(t.value)) add("DUMMY-IRI", t.value, "under a domain reserved for documentation");
          if (t.value.includes(ARTIFACT_CODE)) add("DUMMY-MARKER", t.value, "unreplaced artifact-code marker; sign before linting");
          if (fabricatedDoi(t.value)) add("DUMMY-DOI", t.value, "has the form of a fabricated DOI");
        }
      }
      if (q.object.termType === "Literal") {
        const v = q.object.value;
        const m = PLACEHOLDER.exec(v);
        if (m) add("DUMMY-TEXT", q.subject.value, `placeholder text ${JSON.stringify(m[0])} in ${q.predicate.value}`);
        if (fabricatedDoi(v)) add("DUMMY-DOI", q.subject.value, `${JSON.stringify(v)} has the form of a fabricated DOI`);
      }
    }

    // ── Datasets: the dataset convention in ../ONTOLOGY.md ──
    for (const ds of typed(DCAT + "Dataset")) {
      if (!ds.startsWith(DATASET_NS)) add("DATASET-IRI", ds, `a dataset must be minted as ${DATASET_NS}<id>`);
      if (!out(ds, DC + "identifier").length) add("DATASET-IDENTIFIER", ds, "no dct:identifier");
      if (!out(ds, DC + "license").length) add("DATASET-LICENSE", ds, "no dct:license");
      if (!out(ds, DC + "creator").length) add("DATASET-CREATOR", ds, "no dct:creator");
      const dists = out(ds, DCAT + "distribution").map(t => t.value);
      if (!dists.length) add("DATASET-FILES", ds, "no dcat:distribution for the files actually used");
      for (const dist of dists) {
        const hasSha = out(dist, SPDX + "checksum").some(c =>
          out(c.value, SPDX + "algorithm").some(a => a.value === SHA256) && out(c.value, SPDX + "checksumValue").length);
        if (!hasSha) add("DATASET-SHA256", dist, "distribution has no SHA-256 checksum");
        if (!out(dist, DCAT + "downloadURL").length) add("DATASET-URL", dist, "distribution has no dcat:downloadURL");
      }
      const counts = out(ds, SCHEMA + "additionalProperty").map(t => t.value);
      if (!counts.length) add("DATASET-COUNTS", ds, "no structured counts (schema:additionalProperty)");
      for (const pv of counts)
        if (!out(pv, SCHEMA + "description").length) add("DATASET-COUNTS", ds, `count ${pv} does not say what it counts (schema:description)`);
    }

    // ── Claims name the datasets they used ──
    for (const claim of typed(DELPHI + "Claim")) {
      const refs = [
        ...out(claim, PROV + "used").map(t => t.value),
        ...out(claim, PROV + "wasDerivedFrom").map(t => t.value).filter(v => v.startsWith(DATASET_NS)),
      ];
      for (const ref of refs)
        if (!known.has(ref))
          add("CLAIM-DATASET-UNPUBLISHED", claim, `${ref} is not a dataset in this batch or in --published-datasets`);
      if (refs.length || opts.extracted || opts.exempt?.has(claim)) continue;
      // A single-statement nanopub types its assertion graph as the claim; the claim's statements are its triples.
      add("CLAIM-NO-DATASET", claim, assertionGraphs.has(claim)
        ? "single-statement claim names no dataset; build it as an entity nanopub with prov:used"
        : "claim names no dataset (prov:used delphir:dataset/<id>); exempt it with --exempt only if it has no empirical input");
    }

    // ── Numbers in labels match the structured counts ──
    const structured = (node: string) => {
      const m = new Map<string, number>();
      for (const pv of out(node, SCHEMA + "additionalProperty")) {
        const id = out(pv.value, SCHEMA + "propertyID")[0]?.value;
        const v = out(pv.value, SCHEMA + "value")[0]?.value;
        if (id && v != null) m.set(id, Number(v));
      }
      return m;
    };
    for (const q of quads) {
      if (q.object.termType !== "Literal") continue;
      if (![RDFS + "label", DC + "title", DC + "description", RDFS + "comment"].includes(q.predicate.value)) continue;
      // A nanopub's own label describes the resource it introduces.
      const node = out(q.subject.value, NPX + "introduces")[0]?.value ?? q.subject.value;
      for (const m of q.object.value.matchAll(COUNT_IN_TEXT)) {
        const [text, approx, num, unit] = m;
        const value = Number(num.replace(/,/g, ""));
        const id = `n_${unit.toLowerCase()}`;
        const have = structured(node);
        if (!have.has(id)) {
          add("COUNT-UNSTRUCTURED", node, `"${text.trim()}" in ${q.predicate.value} has no structured ${id}`);
        } else if (approx) {
          add("COUNT-APPROXIMATE", node, `"${text.trim()}" is approximate; state the structured value ${have.get(id)}`);
        } else if (have.get(id) !== value) {
          add("COUNT-MISMATCH", node, `"${text.trim()}" in ${q.predicate.value} disagrees with structured ${id} = ${have.get(id)}`);
        }
      }
    }
  }
  return findings;
}

function trigFiles(path: string): string[] {
  if (statSync(path).isDirectory())
    return readdirSync(path).sort().flatMap(n => trigFiles(join(path, n)));
  return path.endsWith(".trig") ? [path] : [];
}

function main(argv: string[]): number {
  const paths: string[] = [];
  const opts: LintOptions = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--extracted") opts.extracted = true;
    else if (a === "--published-datasets")
      opts.publishedDatasets = readFileSync(argv[++i], "utf8").split("\n").map(l => l.trim()).filter(Boolean);
    else if (a === "--exempt")
      opts.exempt = new Map(readFileSync(argv[++i], "utf8").split("\n").filter(l => l.trim()).map(l => {
        const [iri, ...reason] = l.split("\t");
        if (!reason.join("").trim()) throw new Error(`--exempt: ${iri} has no reason`);
        return [iri.trim(), reason.join("\t").trim()] as [string, string];
      }));
    else paths.push(a);
  }
  const files = paths.flatMap(trigFiles).map(file => ({ file, trig: readFileSync(file, "utf8") }));
  if (!files.length) {
    console.error("usage: npx tsx lint.ts <file.trig | directory> … [--published-datasets <file>] [--exempt <file>] [--extracted]");
    return 2;
  }
  const findings = lintBatch(files, opts);
  for (const f of findings) console.log(`${f.file}: ${f.rule}: ${f.subject ? `<${f.subject}> ` : ""}${f.message}`);
  console.log(`${files.length} file(s), ${findings.length} finding(s)`);
  return findings.length ? 1 : 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) process.exit(main(process.argv.slice(2)));
