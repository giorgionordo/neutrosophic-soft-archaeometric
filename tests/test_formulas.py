from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.aggregate import aggregate_v7_results, aggregate_v9_synthesis
from riace_ivn.io import read_canonical_csvs
from riace_ivn.model import compute_link_state


class FormulaReproductionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = read_canonical_csvs(ROOT / "data" / "canonical")

    def test_link_level_formulas(self):
        links = self.tables["v7_evidence_hypothesis_links"]
        for _, row in links.iterrows():
            computed = compute_link_state(row)
            for key, value in computed.items():
                self.assertAlmostEqual(value, float(row[key]), places=9, msg=f"{row['Link_ID']} {key}")

    def test_v7_aggregation_midpoints(self):
        expected = self.tables["v7_results"].dropna(subset=["T_mid"])
        computed = aggregate_v7_results(
            self.tables["v7_evidence_hypothesis_links"],
            self.tables["hypotheses"],
        )
        merged = expected.merge(computed, on="Hypothesis_ID", suffixes=("_expected", "_computed"))
        self.assertEqual(len(merged), 31)
        for _, row in merged.iterrows():
            for key in ("T_mid", "I_final_mid", "F_mid", "Net_mid"):
                self.assertAlmostEqual(row[f"{key}_computed"], row[f"{key}_expected"], places=9)

    def test_v9_synthesis_midpoints(self):
        expected = self.tables["v9_synthesis_results"]
        computed = aggregate_v9_synthesis(
            self.tables["v9_meta_components"],
            self.tables["v9_meta_families"],
        )
        merged = expected.merge(computed, on="Hypothesis_ID", suffixes=("_expected", "_computed"))
        self.assertEqual(set(merged["Hypothesis_ID"]), {"H21", "H33"})
        for _, row in merged.iterrows():
            for key in ("T_mid", "I_mid", "F_mid", "Net_mid"):
                self.assertAlmostEqual(row[f"{key}_computed"], row[f"{key}_expected"], places=9)


if __name__ == "__main__":
    unittest.main()
