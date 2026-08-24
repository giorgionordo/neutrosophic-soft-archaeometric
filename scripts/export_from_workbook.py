from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.io import export_workbook_tables


def main() -> int:
    parser = argparse.ArgumentParser(description="Export canonical CSV tables from the Riace workbook.")
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "canonical")
    args = parser.parse_args()
    export_workbook_tables(args.workbook, args.output_dir)
    print(f"Exported canonical tables to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
