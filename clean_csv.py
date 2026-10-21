"""Clean messy CSV exports and report exactly what changed.

Usage:
    python clean_csv.py data/messy_sales.csv --audit
    python clean_csv.py data/messy_sales.csv -o data/clean_sales.csv

Every transformation is recorded so a client can see why a number moved.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d %b %Y", "%b %d %Y", "%Y/%m/%d")

AMOUNT_RE = re.compile(r"^\(?\s*[£$€]?\s*(-?[\d,]+(?:\.\d+)?)\s*\)?\s*(cr|dr)?$", re.I)


def parse_amount(value: str):
    """'£1,234.50' -> 1234.5; '(123)' -> -123.0; '12.5 CR' -> 12.5; '' -> None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "n/a", "na", "-", "--"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    match = AMOUNT_RE.match(text)
    if not match:
        raise ValueError(f"unparseable amount: {value!r}")
    number = float(match.group(1).replace(",", ""))
    if match.group(2) and match.group(2).lower() == "dr":
        negative = True
    return -number if negative else number


def parse_date(value: str):
    """Try a fixed set of formats and return ISO date, or raise with the offending value."""
    text = (value or "").strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unparseable date: {value!r}")


def normalise_header(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")


@dataclass
class Audit:
    rows_read: int = 0
    duplicate_rows: int = 0
    blank_cells: dict = field(default_factory=dict)
    amount_fixes: int = 0
    date_fixes: int = 0
    errors: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"rows read:          {self.rows_read}",
            f"duplicate rows:     {self.duplicate_rows}",
            f"amounts normalised: {self.amount_fixes}",
            f"dates normalised:   {self.date_fixes}",
        ]
        if self.blank_cells:
            blanks = ", ".join(f"{k}={v}" for k, v in sorted(self.blank_cells.items()))
            lines.append(f"blank cells:        {blanks}")
        if self.errors:
            lines.append(f"errors:             {len(self.errors)}")
            for err in self.errors[:10]:
                lines.append(f"  - {err}")
        return "\n".join(lines)


def looks_numeric(column: str) -> bool:
    return bool(re.search(r"amount|price|total|cost|revenue|value", column))


def looks_date(column: str) -> bool:
    return bool(re.search(r"date|day|month|period", column))


def clean(rows, header):
    audit = Audit(rows_read=len(rows))
    cleaned, seen = [], set()

    for index, row in enumerate(rows, start=2):  # row 1 is the header
        record = {}
        for column in header:
            raw = row.get(column, "")
            if str(raw).strip() == "":
                audit.blank_cells[column] = audit.blank_cells.get(column, 0) + 1
            try:
                if looks_numeric(column) and raw not in (None, ""):
                    record[column] = parse_amount(raw)
                    if isinstance(raw, str) and re.search(r"[£$€,()\s]", raw):
                        audit.amount_fixes += 1
                elif looks_date(column) and raw not in (None, ""):
                    record[column] = parse_date(raw)
                    if isinstance(raw, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw.strip()):
                        audit.date_fixes += 1
                else:
                    record[column] = str(raw).strip()
            except ValueError as exc:
                record[column] = None
                audit.errors.append(f"row {index}, {column}: {exc}")

        fingerprint = tuple(sorted((k, str(v)) for k, v in record.items()))
        if fingerprint in seen:
            audit.duplicate_rows += 1
            continue
        seen.add(fingerprint)
        cleaned.append(record)

    return cleaned, audit


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = [normalise_header(h) for h in (reader.fieldnames or [])]
        rows = []
        for raw in reader:
            rows.append({normalise_header(k): v for k, v in raw.items() if k is not None})
    return header, rows


def write_csv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Clean a messy CSV export.")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="write cleaned CSV here")
    parser.add_argument("--audit", action="store_true", help="report problems without writing")
    args = parser.parse_args(argv)

    header, rows = read_csv(args.input)
    cleaned, audit = clean(rows, header)
    print(audit.summary())

    if args.output:
        write_csv(args.output, header, cleaned)
        print(f"\nwrote {len(cleaned)} rows -> {args.output}")
    elif not args.audit:
        print("\n(no output path given; pass -o to write, or --audit to only report)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
