from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.io import read_canonical_csvs


class DatasetIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = read_canonical_csvs(ROOT / "data" / "canonical")

    def test_declared_counts(self):
        self.assertEqual(len(self.tables["v7_evidence_base"]), 62)
        self.assertEqual(len(self.tables["v7_evidence_hypothesis_links"]), 112)

    def test_role_counts(self):
        counts = self.tables["v7_evidence_hypothesis_links"]["Role"].value_counts().to_dict()
        self.assertEqual(counts, {"DIRECTIONAL": 71, "LIMITATION": 26, "CONTEXT": 15})

    def test_e001_e015_source_audit_present(self):
        audited = ROOT / "data" / "validation" / "e001_e015_source_audit.csv"
        self.assertTrue(audited.exists())
        rows = audited.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows) - 1, 15)


if __name__ == "__main__":
    unittest.main()
