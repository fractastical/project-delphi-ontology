"""Offline syntax and actual SPARQL-result tests; never query the public registry."""
import re
import socket
import unittest
from pathlib import Path
from rdflib import Dataset, Graph, URIRef, Literal, Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
DELPHI = Namespace("https://w3id.org/delphi/ontology/")
PROBKNOW_TERMS = Namespace("https://w3id.org/probknow/ontology/")
OLD = Namespace("https://w3id.org/probknow/ontology/1.0#")
DELPHIR = Namespace("https://w3id.org/delphi/resource/")
NP = Namespace("http://www.nanopub.org/nschema#")
PROV = Namespace("http://www.w3.org/ns/prov#")
FABIO = Namespace("http://purl.org/spar/fabio/")


def no_network(*args, **kwargs):
    raise AssertionError("Offline tests attempted network access")


socket.socket.connect = no_network
socket.create_connection = no_network


class OntologyTests(unittest.TestCase):
    def test_all_turtle_and_trig_parse(self):
        paths = sorted(ROOT.glob("*.ttl"))
        for directory in ("examples", "nanopubs"):
            paths += sorted((ROOT / directory).rglob("*.ttl"))
            paths += sorted((ROOT / directory).rglob("*.trig"))
        paths = [p for p in paths if "tmp" not in p.relative_to(ROOT).parts]
        self.assertGreater(len(paths), 2, "RDF discovery unexpectedly found no examples")
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                graph = Dataset() if path.suffix == ".trig" else Graph()
                text = path.read_text()
                # Source templates deliberately leave the publication date for
                # sign.sh. Expand only that marker in unsigned source templates;
                # signed and historical examples are always parsed unchanged.
                if path.is_relative_to(ROOT / "nanopubs" / "src"):
                    text = text.replace("__NOW__", "2026-01-02T03:04:05Z")
                graph.parse(data=text, publicID=path.as_uri(),
                            format="trig" if path.suffix == ".trig" else "turtle")
                self.assertGreater(len(graph), 0)

    def ontology(self):
        graph = Graph()
        graph.parse(ROOT / "delphi.ttl", format="turtle")
        return graph

    def test_claim_is_a_kind_of_hypothesis(self):
        # Collapsed in 2.0: both are propositions carrying delphi:Assessment, and
        # delphi:evaluatesHypothesis — the inverse of delphi:hasAssessment, which claims
        # already used — ranges over delphi:Hypothesis.
        graph = self.ontology()
        for subclass in (DELPHI.Claim, DELPHI.TestableHypothesis):
            self.assertIn((subclass, RDFS.subClassOf, DELPHI.Hypothesis), graph)
        self.assertEqual(set(graph.objects(DELPHI.hasAssessment, RDFS.domain)), {DELPHI.Hypothesis})

    def test_deprecated_terms_name_and_still_entail_their_replacement(self):
        # A deprecated term keeps its subsumption axiom, so a store that reasons
        # derives the replacement from nanopublications already on the network.
        graph = self.ontology()
        deprecated = set(graph.subjects(OWL.deprecated, Literal(True)))
        self.assertEqual(deprecated, {DELPHI.Model, DELPHI.Paper, DELPHI.assessedBy,
                                      DELPHI.derivedFromPaper})
        axiom = {DELPHI.Model: RDFS.subClassOf, DELPHI.Paper: RDFS.subClassOf,
                 DELPHI.assessedBy: RDFS.subPropertyOf,
                 DELPHI.derivedFromPaper: RDFS.subPropertyOf}
        for term in deprecated:
            replacements = set(graph.objects(term, DCTERMS.isReplacedBy))
            self.assertEqual(len(replacements), 1, term)
            replacement = replacements.pop()
            # Every replacement comes from a vocabulary the ontology already reuses.
            self.assertTrue(str(replacement).startswith((str(PROV), str(FABIO))), replacement)
            self.assertIn((term, axiom[term], replacement), graph)
            # Equivalence would be wrong: the replacements are more general.
            self.assertEqual(set(graph.objects(term, OWL.equivalentClass)), set())
            self.assertEqual(set(graph.objects(term, OWL.equivalentProperty)), set())

    def test_examples_and_template_sources_avoid_deprecated_terms(self):
        # Signed nanopubs under nanopubs/signed/ are published and immutable, so
        # they keep whatever term they were signed with; everything the repository
        # still generates or hands to readers uses the replacement.
        graph = self.ontology()
        deprecated = set(graph.subjects(OWL.deprecated, Literal(True)))
        paths = sorted((ROOT / "examples").rglob("*.ttl")) + \
            sorted((ROOT / "examples").rglob("*.trig")) + \
            sorted((ROOT / "nanopubs" / "src").rglob("*.trig"))
        self.assertGreater(len(paths), 10)
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text().replace("__NOW__", "2026-01-02T03:04:05Z")
                parsed = Dataset() if path.suffix == ".trig" else Graph()
                parsed.parse(data=text, publicID=path.as_uri(),
                             format="trig" if path.suffix == ".trig" else "turtle")
                used = {term for quad in parsed for term in quad[:3]
                        if isinstance(term, URIRef) and term in deprecated}
                self.assertEqual(used, set())

    def test_delphi_prefix_labels_bind_to_the_delphi_namespaces(self):
        # The delphi:/delphir: labels replaced pk:/pkr: in 2.0. Five template sources
        # under nanopubs/src/ are the published form of templates that predate the
        # namespace migration and still bind pk: to w3id.org/probknow; they keep that
        # label, because relabelling it delphi: would point the label at probknow.
        pattern = re.compile(r"^@prefix\s+(delphir?|pkr?):\s*<([^>]+)>", re.M)
        expected = {"delphi": str(DELPHI), "delphir": str(DELPHIR),
                    "pk": str(PROBKNOW_TERMS), "pkr": "https://w3id.org/probknow/resource/"}
        paths = sorted(ROOT.glob("*.ttl")) + sorted((ROOT / "examples").rglob("*.ttl")) + \
            sorted((ROOT / "nanopubs" / "src").rglob("*.trig"))
        self.assertGreater(len(paths), 10)
        seen = set()
        for path in paths:
            for label, iri in pattern.findall(path.read_text()):
                with self.subTest(path=str(path.relative_to(ROOT)), prefix=label):
                    self.assertEqual(iri, expected[label])
                    seen.add(label)
        self.assertIn("delphi", seen)

    def dataset(self):
        dataset = Dataset()
        # Register the empty default graph before GRAPH queries enumerate contexts.
        # RDFLib's memory store otherwise adds it during iteration.
        dataset.store.add_graph(dataset.default_context)
        # New/old vocabulary, exactly-on-threshold, low, missing and unrelated
        # examples exercise selection, aggregation, and backwards compatibility.
        for ident, vocabulary, weight, domain, entity in [
            ("new", DELPHI, .9, "bio", True),
            ("boundary", OLD, .8, "bio", False),
            ("low", DELPHI, .79, "chemistry", True),
            ("missing", DELPHI, None, "chemistry", True),
            ("unrelated", Namespace("https://unrelated.test/vocab/"), .99, None, True),
        ]:
            np = URIRef("https://fixtures.test/np/" + ident)
            assertion = URIRef(str(np) + "/assertion")
            claim = DELPHIR["claim/" + ident] if domain else URIRef("https://unrelated.test/claim")
            head = dataset.graph(URIRef(str(np) + "/head"))
            head.add((np, RDF.type, NP.Nanopublication))
            head.add((np, NP.hasAssertion, assertion))
            head.add((np, NP.hasPublicationInfo, URIRef(str(np) + "/pubinfo")))
            dataset.graph(assertion).add((claim, RDF.type, vocabulary.Claim))
            # Older single-edge weights can be in provenance, not assertion.
            score_graph = dataset.graph(assertion if entity else URIRef(str(np) + "/provenance"))
            score_subject = claim if entity else assertion
            score_graph.add((score_subject, RDFS.label, Literal(ident)))
            if weight is not None:
                score_graph.add((score_subject, vocabulary.weightOfEvidence, Literal(weight, datatype=XSD.double)))
            if domain:
                pub = dataset.graph(URIRef(str(np) + "/pubinfo"))
                value = DELPHIR["domain/" + domain] if vocabulary == DELPHI else Literal(domain)
                pub.add((np, vocabulary.domain, value))
                if vocabulary == DELPHI:
                    pub.add((value, RDFS.label, Literal(domain)))
        return dataset

    def query(self, name):
        return list(self.dataset().query((ROOT / "queries" / name).read_text()))

    def test_all_probknow_query_excludes_unrelated_vocab(self):
        rows = self.query("all-probknow-nanopubs.rq")
        self.assertEqual({str(row[0]).rsplit("/", 1)[-1] for row in rows},
                         {"new", "boundary", "low", "missing"})

    def test_domain_counts_fold_legacy_literal_and_current_resource(self):
        rows = self.query("claims-by-domain.rq")
        self.assertEqual({str(row[0]): int(row[1]) for row in rows},
                         {"bio": 2, "chemistry": 2})

    def test_high_confidence_boundary_and_absence(self):
        rows = self.query("high-confidence-claims.rq")
        self.assertEqual([(str(row[1]), float(row[2])) for row in rows],
                         [("new", .9), ("boundary", .8)])

    def test_all_queries_parse_and_execute_on_empty_dataset(self):
        paths = sorted((ROOT / "queries").glob("*.rq"))
        self.assertGreaterEqual(len(paths), 3)
        for path in paths:
            with self.subTest(query=path.name):
                dataset = Dataset()
                dataset.store.add_graph(dataset.default_context)
                self.assertEqual(list(dataset.query(path.read_text())), [])


if __name__ == "__main__":
    unittest.main()
