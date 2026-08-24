from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.experimental_refinements import (  # noqa: E402
    aggregate_experimental_pipeline,
    monte_carlo_experimental_pipeline,
    read_experimental_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the optional Delphi/DAG/entropy/TOPSIS experimental refinement pipeline."
    )
    parser.add_argument("--input", required=True, help="CSV with the V10 experimental panel-score schema.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated CSV outputs.")
    parser.add_argument(
        "--group-by",
        default="bronze",
        help="Column used as the TOPSIS alternative identifier. Defaults to bronze.",
    )
    parser.add_argument(
        "--include-nondirectional",
        action="store_true",
        help="Include CONTEXT and LIMITATION rows in experimental aggregation.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Optional Monte Carlo iterations. Use 0 to skip robustness sampling.",
    )
    parser.add_argument("--sigma", type=float, default=0.5, help="Gaussian perturbation sigma for panel scores.")
    parser.add_argument("--seed", type=int, default=20260824, help="Monte Carlo random seed.")
    return parser.parse_args()


def write_outputs(outputs: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)


def main() -> int:
    args = parse_args()
    frame = read_experimental_csv(args.input)
    output_dir = Path(args.output_dir)

    outputs = aggregate_experimental_pipeline(
        frame,
        group_by=args.group_by,
        directional_only=not args.include_nondirectional,
    )
    write_outputs(outputs, output_dir)

    if args.iterations > 0:
        mc_outputs = monte_carlo_experimental_pipeline(
            frame,
            iterations=args.iterations,
            sigma=args.sigma,
            seed=args.seed,
            group_by=args.group_by,
        )
        write_outputs(mc_outputs, output_dir)

    print(f"Wrote experimental refinement outputs to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
