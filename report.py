"""One-page data-quality summary for a cleaned CSV.

Usage:
    python report.py data/clean_sales.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_report(frame: pd.DataFrame) -> str:
    lines = [f"rows: {len(frame):,}   columns: {len(frame.columns)}", ""]
    lines.append(f"{'column':<28}{'type':<10}{'missing':>8}{'unique':>8}{'example':>22}")

    for column in frame.columns:
        series = frame[column]
        missing = series.isna().sum()
        unique = series.nunique(dropna=True)
        sample = next((str(v) for v in series.dropna().head(3)), "")
        lines.append(f"{column[:27]:<28}{str(series.dtype):<10}{missing:>8}{unique:>8}{sample[:21]:>22}")

    numeric = frame.select_dtypes("number")
    if not numeric.empty:
        lines.append("")
        lines.append("numeric summary")
        for column in numeric.columns:
            stats = numeric[column].describe()
            lines.append(
                f"  {column}: min={stats['min']:.2f} median={stats['50%']:.2f} "
                f"mean={stats['mean']:.2f} max={stats['max']:.2f}"
            )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print a data-quality summary.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    frame = pd.read_csv(args.path)
    print(build_report(frame))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
