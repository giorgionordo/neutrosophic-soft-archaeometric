from __future__ import annotations

import argparse
import zlib
from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.io import read_canonical_csvs


@dataclass(frozen=True)
class PdfStyle:
    stroke: str = "0.16 0.19 0.22"
    grid: str = "0.82 0.84 0.86"
    muted: str = "0.42 0.46 0.50"
    t_color: str = "0.05 0.43 0.62"
    i_color: str = "0.84 0.55 0.10"
    f_color: str = "0.67 0.18 0.20"
    c_color: str = "0.36 0.36 0.40"
    h21_color: str = "0.05 0.43 0.62"
    h33_color: str = "0.67 0.18 0.20"


class SimplePdf:
    """Small vector-PDF writer for dependency-free manuscript figures."""

    def __init__(self, path: Path, width: int = 520, height: int = 340) -> None:
        self.path = path
        self.width = width
        self.height = height
        self.commands: list[str] = []

    def raw(self, command: str) -> None:
        self.commands.append(command)

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str, width: float = 1.0) -> None:
        self.raw(f"q {color} RG {width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q")

    def rect(self, x: float, y: float, w: float, h: float, color: str) -> None:
        self.raw(f"q {color} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f Q")

    def text(self, x: float, y: float, text: str, size: int = 9, color: str = "0 0 0") -> None:
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.raw(f"q {color} rg BT /F1 {size} Tf {x:.2f} {y:.2f} Td ({escaped}) Tj ET Q")

    def save(self) -> None:
        stream = "\n".join(self.commands).encode("latin-1")
        compressed = zlib.compress(stream)
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width} {self.height}] "
                "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
            ).encode("ascii"),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(compressed) + compressed + b"\nendstream",
        ]
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(out))
            out.extend(f"{index} 0 obj\n".encode("ascii"))
            out.extend(obj)
            out.extend(b"\nendobj\n")
        xref = len(out)
        out.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets[1:]:
            out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        out.extend(
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(out)


def x_scale(value: float, left: float, width: float) -> float:
    return left + max(0.0, min(1.0, float(value))) * width


def draw_axis(pdf: SimplePdf, left: float, bottom: float, width: float, style: PdfStyle) -> None:
    for tick in (0.0, 0.25, 0.50, 0.75, 1.0):
        x = x_scale(tick, left, width)
        pdf.line(x, bottom, x, bottom + 238, style.grid, 0.45)
        pdf.text(x - 8, bottom - 17, f"{tick:.2f}", 7, style.muted)
    pdf.line(left, bottom, left + width, bottom, style.stroke, 0.8)
    pdf.text(left + width - 45, bottom - 32, "membership degree", 8, style.muted)


def make_ivn_profile(tables: dict[str, pd.DataFrame], out_path: Path) -> None:
    style = PdfStyle()
    df = tables["v9_synthesis_results"].set_index("Hypothesis_ID")
    pdf = SimplePdf(out_path)
    left, width = 132, 334
    pdf.text(30, 315, "H21/H33 interval-valued neutrosophic profile", 13, style.stroke)
    draw_axis(pdf, left, 52, width, style)

    metrics = [
        ("T", "truth/support", "T_low", "T_high", style.t_color),
        ("I", "indeterminacy", "I_low", "I_high", style.i_color),
        ("F", "falsity/opposition", "F_low", "F_high", style.f_color),
        ("C", "contradiction", "C_low", "C_high", style.c_color),
    ]
    y = 273
    for hid in ("H21", "H33"):
        row = df.loc[hid]
        pdf.text(30, y + 8, hid, 11, style.stroke)
        for label, desc, low_key, high_key, color in metrics:
            low = float(row[low_key])
            high = float(row[high_key])
            mid = (low + high) / 2.0
            pdf.text(57, y, f"{label}  {desc}", 8, style.stroke)
            x1 = x_scale(low, left, width)
            x2 = x_scale(high, left, width)
            xm = x_scale(mid, left, width)
            pdf.line(x1, y + 3, x2, y + 3, color, 5.5)
            pdf.line(x1, y - 3, x1, y + 9, color, 1.0)
            pdf.line(x2, y - 3, x2, y + 9, color, 1.0)
            pdf.rect(xm - 2.2, y + 0.8, 4.4, 4.4, color)
            pdf.text(474, y, f"[{low:.3f}, {high:.3f}]", 7, style.muted)
            y -= 23
        y -= 14
    pdf.text(30, 22, "Bars show lower-upper intervals; squares mark midpoints. C is reported separately from I.", 8, style.muted)
    pdf.save()


def make_weight_sensitivity(tables: dict[str, pd.DataFrame], out_path: Path) -> None:
    style = PdfStyle()
    df = tables["v9_weight_sensitivity"].copy()
    scenario_order = [
        "EQUAL",
        "PRODUCTION_FOCUSED",
        "INTEGRATION_FOCUSED",
        "CORE_HEAVY",
        "CHRONOLOGY_HEAVY",
        "NO_CHRONOLOGY",
        "NO_CORE_PROV",
        "NO_METAL",
        "NO_ASSEMBLY",
    ]
    labels = ["Equal", "Prod.", "Integr.", "Core", "Chron.", "No chron.", "No core", "No metal", "No ass."]
    pdf = SimplePdf(out_path, 560, 350)
    left, bottom, width, height = 74, 72, 420, 210
    pdf.text(30, 320, "H21/H33 net midpoint under weight-sensitivity scenarios", 13, style.stroke)

    ymin, ymax = 0.0, 0.58
    for tick in (0.0, 0.2, 0.4):
        y = bottom + (tick - ymin) / (ymax - ymin) * height
        pdf.line(left, y, left + width, y, style.grid, 0.45)
        pdf.text(36, y - 3, f"{tick:.1f}", 8, style.muted)
    pdf.line(left, bottom, left, bottom + height, style.stroke, 0.8)
    pdf.line(left, bottom, left + width, bottom, style.stroke, 0.8)
    pdf.text(28, bottom + height + 8, "Net_mid", 8, style.muted)

    def point(index: int, value: float) -> tuple[float, float]:
        step = width / (len(scenario_order) - 1)
        return left + index * step, bottom + (value - ymin) / (ymax - ymin) * height

    for target, color in (("H21", style.h21_color), ("H33", style.h33_color)):
        sub = df[df["Target"] == target].set_index("Scenario_ID")
        pts = [point(i, float(sub.loc[sid, "Net_mid"])) for i, sid in enumerate(scenario_order)]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            pdf.line(x1, y1, x2, y2, color, 1.6)
        for x, y in pts:
            pdf.rect(x - 2.6, y - 2.6, 5.2, 5.2, color)
    for i, label in enumerate(labels):
        x, _ = point(i, 0.0)
        pdf.text(x - 16, 47, label, 7, style.muted)

    pdf.rect(414, 305, 9, 9, style.h21_color)
    pdf.text(428, 305, "H21", 8, style.stroke)
    pdf.rect(464, 305, 9, 9, style.h33_color)
    pdf.text(478, 305, "H33", 8, style.stroke)
    pdf.text(30, 20, "The broad H21 reading remains less opposition-sensitive; H33 is deliberately stricter.", 8, style.muted)
    pdf.save()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate manuscript figures from canonical Riace IVN CSVs.")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "canonical")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "figures")
    args = parser.parse_args()

    tables = read_canonical_csvs(args.data_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    make_ivn_profile(tables, args.output_dir / "ivn_h21_h33_profile.pdf")
    make_weight_sensitivity(tables, args.output_dir / "h21_h33_weight_sensitivity.pdf")
    print(f"Generated figures in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
