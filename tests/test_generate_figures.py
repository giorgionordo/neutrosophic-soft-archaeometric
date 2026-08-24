from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.generate_figures import make_ivn_profile, make_weight_sensitivity
from riace_ivn.io import read_canonical_csvs


class FigureGenerationTests(unittest.TestCase):
    def test_manuscript_figures_are_generated_as_pdfs(self) -> None:
        root = Path(__file__).resolve().parents[1]
        tables = read_canonical_csvs(root / "data" / "canonical")
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            profile = out_dir / "ivn_h21_h33_profile.pdf"
            sensitivity = out_dir / "h21_h33_weight_sensitivity.pdf"
            make_ivn_profile(tables, profile)
            make_weight_sensitivity(tables, sensitivity)
            for path in (profile, sensitivity):
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 1000)
                self.assertEqual(path.read_bytes()[:5], b"%PDF-")


if __name__ == "__main__":
    unittest.main()
