from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.experimental_refinements import (
    IVNState,
    aggregate_experimental_pipeline,
    apply_novelty_discount,
    delphi_interval,
    delphi_states_from_frame,
    entropy_weights,
    epistemic_novelty,
    ivn_distance,
    monte_carlo_delphi_intervals,
    monte_carlo_experimental_pipeline,
    parse_dependency_dag_cell,
    read_experimental_csv,
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

    def test_parse_dependency_dag_cell_accepts_compact_edges(self):
        edges = parse_dependency_dag_cell("E3", "E1:0.25; E2=0.50; E0->E3:0.10")
        self.assertEqual(edges, [("E1", "E3", 0.25), ("E2", "E3", 0.5), ("E0", "E3", 0.1)])

    def test_experimental_pipeline_runs_from_template(self):
        path = ROOT / "data" / "examples" / "delphi_refinement_template.csv"
        frame = read_experimental_csv(path)
        outputs = aggregate_experimental_pipeline(frame, group_by="bronze")
        self.assertEqual(set(outputs), {"evidence_states", "meta_family_states", "entropy_weights", "topsis_ranking"})
        self.assertEqual(len(outputs["evidence_states"]), 6)
        self.assertEqual(set(outputs["topsis_ranking"]["bronze"]), {"A", "B"})
        self.assertAlmostEqual(outputs["entropy_weights"].groupby("bronze")["entropy_weight"].sum().loc["A"], 1.0)

    def test_genealogic_discount_lowers_reanalysis_quality(self):
        path = ROOT / "data" / "examples" / "delphi_refinement_template.csv"
        states = delphi_states_from_frame(read_experimental_csv(path))
        row = states[states["evidence_id"] == "EX002"].iloc[0]
        self.assertLess(row["Q_discounted_high"], row["Q_high"])
        self.assertAlmostEqual(row["eta"], 0.65)

    def test_monte_carlo_pipeline_returns_rc_and_confidence(self):
        path = ROOT / "data" / "examples" / "delphi_refinement_template.csv"
        frame = read_experimental_csv(path)
        outputs = monte_carlo_experimental_pipeline(frame, iterations=3, seed=42, group_by="bronze")
        self.assertEqual(len(outputs["rc_samples"]), 6)
        self.assertIn("A>B", set(outputs["pairwise_confidence"]["comparison"]))


if __name__ == "__main__":
    unittest.main()
