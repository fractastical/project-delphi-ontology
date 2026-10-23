import copy
import unittest
from pilot import map_sample, jsonld


def statement(**updates):
    st = {"type": "Phosphorylation", "enz": {"name": "SRC", "db_refs": {"HGNC": "11283"}},
          "sub": {"name": "GJA1", "db_refs": {"HGNC": "4274"}},
          "belief": 0.8, "evidence": [{"source_api": "test", "pmid": "123", "text": "Synthetic fixture",
                                      "source_hash": 9223372036854775806}]}
    st.update(updates)
    return st


class PilotTests(unittest.TestCase):
    def test_duplicate_claim_and_evidence(self):
        s = map_sample({"results": {"1": statement(), "2": statement()}})
        self.assertEqual(s["summary"]["mappedClaims"], 1)
        self.assertEqual(s["summary"]["evidenceRecords"], 1)

    def test_readers_are_not_independent_papers(self):
        st = statement()
        st["evidence"].append({**st["evidence"][0], "source_api": "other"})
        c = map_sample([st])["claims"][0]
        self.assertEqual(len(c["paperIds"]), 1)
        self.assertEqual(c["repeatedSourceEvidence"], 1)

    def test_paper_alias_transitivity(self):
        ev = [{"pmid": "123"}, {"text_refs": {"DOI": "10.1/ABC"}},
              {"pmid": "123", "text_refs": {"DOI": "https://doi.org/10.1/abc", "PMCID": "PMC1"}}]
        self.assertEqual(map_sample([statement(evidence=ev)])["summary"]["paperGroups"], 1)

    def test_context_and_site_are_not_collapsed(self):
        a, b = statement(position="368"), statement(position="279")
        self.assertEqual(map_sample([a, b])["summary"]["mappedClaims"], 2)
        self.assertIn("missing_participant", map_sample([statement(enz=None)])["claims"][0]["flags"])

    def test_exact_hash_and_separate_score(self):
        sample = map_sample([statement()])
        c = sample["claims"][0]
        self.assertEqual(c["evidence"][0]["sourceHash"], "9223372036854775806")
        graph = jsonld(sample)["@graph"]
        self.assertFalse(any("delphi:hasProbability" in n or "delphi:weightOfEvidence" in n for n in graph))
        self.assertTrue(any(n.get("pilot:indraBelief") == 0.8 for n in graph))

    def test_unknown_type_quarantined(self):
        self.assertEqual(map_sample([statement(type="Unknown")])["summary"]["quarantinedStatements"], 1)

    def test_unlinked_evidence_not_invented(self):
        c = map_sample([statement(evidence=[{"text": "No ID"}])])["claims"][0]
        self.assertEqual(c["paperIds"], [])
        self.assertIn("no_linked_paper", c["flags"])

    def test_invalid_scores_fail(self):
        for value in (float("nan"), 1.1, True, "0.8"):
            with self.assertRaises(ValueError):
                map_sample([statement(belief=value)])

    def test_identity_conflict_flagged(self):
        c = map_sample([statement(evidence=[
            {"pmid": "1", "text_refs": {"DOI": "10.1/a"}},
            {"pmid": "2", "text_refs": {"DOI": "10.1/a"}}])])["claims"][0]
        self.assertIn("conflicting_paper_identifiers", c["flags"])

    def test_no_source_passages_in_export(self):
        self.assertNotIn("Synthetic fixture", str(map_sample([statement()])))


if __name__ == "__main__":
    unittest.main()
