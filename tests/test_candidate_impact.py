from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_candidate_impact import build_candidate_impact, load_candidate_links


class CandidateImpactTest(unittest.TestCase):
    def test_candidate_link_scoring_is_noncanonical_and_computable(self):
        links = load_candidate_links(
            ROOT / "data" / "validation" / "v10_candidate_link_scoring.csv"
        )
        self.assertEqual(len(links), 5)
        self.assertIn("L065C_LIM", set(links["Link_ID"]))
        self.assertTrue((links["Status"] == "V10-CANDIDATE-NONCANONICAL").all())
        self.assertGreater(float(links.loc[links["Link_ID"] == "L064C", "T_mid"].iloc[0]), 0.0)

    def test_s06_candidates_raise_h20_structured_indeterminacy(self):
        comparison, _ = build_candidate_impact(
            ROOT / "data" / "canonical",
            ROOT / "data" / "validation" / "v10_candidate_link_scoring.csv",
        )
        rows = comparison.set_index("Scenario")
        self.assertIn("delta", rows.index)
        self.assertAlmostEqual(float(rows.loc["delta", "T_mid"]), 0.0, places=12)
        self.assertGreater(float(rows.loc["delta", "I_final_mid"]), 0.0)
        self.assertLess(float(rows.loc["delta", "Net_mid"]), 0.0)

    def test_candidate_impact_writes_expected_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            comparison, candidate_links = build_candidate_impact(
                ROOT / "data" / "canonical",
                ROOT / "data" / "validation" / "v10_candidate_link_scoring.csv",
            )
            comparison.to_csv(out_dir / "h20_candidate_impact.csv", index=False)
            candidate_links.to_csv(out_dir / "candidate_links_computed.csv", index=False)
            self.assertTrue((out_dir / "h20_candidate_impact.csv").exists())
            self.assertTrue((out_dir / "candidate_links_computed.csv").exists())


if __name__ == "__main__":
    unittest.main()
