from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.experimental_refinements import (
    IVNState,
    apply_novelty_discount,
    delphi_interval,
    entropy_weights,
    epistemic_novelty,
    ivn_distance,
    monte_carlo_delphi_intervals,
    topsis_rank,
)


class ExperimentalRefinementsTest(unittest.TestCase):
    def test_delphi_interval_expands_with_disagreement(self):
        tight = delphi_interval("3,3,3")
        wide = delphi_interval("1,3,4")
        self.assertLess(tight[1] - tight[0], wide[1] - wide[0])

    def test_epistemic_novelty_discount(self):
        eta = epistemic_novelty("E3", [("E1", "E3", 0.25), ("E2", "E3", 0.5)])
        self.assertAlmostEqual(eta, 0.375)
        self.assertEqual(apply_novelty_discount(0.8, 0.9, eta), (0.30000000000000004, 0.3375))

    def test_entropy_weights_favor_lower_uncertainty(self):
        states = {
            "LOW_I": IVNState(0.7, 0.8, 0.1, 0.2, 0.0, 0.1),
            "HIGH_I": IVNState(0.7, 0.8, 0.7, 0.9, 0.0, 0.1),
        }
        weights = entropy_weights(states)
        self.assertGreater(weights["LOW_I"], weights["HIGH_I"])
        self.assertAlmostEqual(sum(weights.values()), 1.0)

    def test_topsis_orders_positive_state_first(self):
        states = {
            "A": IVNState(0.8, 0.9, 0.1, 0.2, 0.0, 0.1),
            "B": IVNState(0.1, 0.2, 0.8, 0.9, 0.7, 0.9),
        }
        ranked = topsis_rank(states)
        self.assertEqual(ranked.iloc[0]["Hypothesis_ID"], "A")
        self.assertGreater(ivn_distance(states["A"], IVNState(0, 0, 1, 1, 1, 1)), 0.0)

    def test_monte_carlo_delphi_shape(self):
        row = {
            "r_scores": "3,3,4",
            "m_scores": "3,3,3",
            "a_scores": "2,3,3",
            "d_scores": "4,4,3",
            "s_scores": "3,4,4",
            "o_scores": "0,0,1",
        }
        samples = monte_carlo_delphi_intervals(row, iterations=5, seed=123)
        self.assertEqual(len(samples), 5)
        self.assertIn("s_high", samples.columns)


if __name__ == "__main__":
    unittest.main()
