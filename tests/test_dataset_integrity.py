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

    def test_e016_e030_source_audit_present(self):
        audited = ROOT / "data" / "validation" / "e016_e030_source_audit.csv"
        self.assertTrue(audited.exists())
        rows = audited.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows) - 1, 15)

    def test_e031_e045_source_audit_present(self):
        audited = ROOT / "data" / "validation" / "e031_e045_source_audit.csv"
        self.assertTrue(audited.exists())
        rows = audited.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows) - 1, 15)
        self.assertTrue(any("SOURCE-CHECKED-ABSTRACT-ONLY" in row for row in rows))

    def test_e046_e062_source_audit_present(self):
        audited = ROOT / "data" / "validation" / "e046_e062_source_audit.csv"
        self.assertTrue(audited.exists())
        rows = audited.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows) - 1, 17)
        self.assertTrue(any("SOURCE-CHECKED-ABSTRACT-ONLY" in row for row in rows))

    def test_v10_source_material_triage_present(self):
        triage = ROOT / "data" / "validation" / "v10_source_material_triage.csv"
        self.assertTrue(triage.exists())
        rows = triage.read_text(encoding="utf-8-sig").splitlines()
        self.assertGreaterEqual(len(rows) - 1, 10)
        body = "\n".join(rows[1:])
        for source_id in ["S01", "S02", "S03", "S04", "S05", "S06", "S07"]:
            self.assertIn(source_id, body)
        self.assertIn("M-GETTY-GUIDELINES", body)
        self.assertIn("DOWNLOADED-VERIFIED-PDF", body)

if __name__ == "__main__":
    unittest.main()

