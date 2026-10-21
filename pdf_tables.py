"""Extract tables from a PDF into CSV, one file per table, with a manifest.

Usage:
    python pdf_tables.py invoice.pdf --out out/tables
    python pdf_tables.py invoice.pdf --out out/tables --pages 1-3

Design notes:
- pdfplumber handles ruled tables well; unruled ("stream") tables are detected with
  text-based strategy and flagged in the manifest so a human can check them.
- Every table is written as its own CSV plus a row in manifest.json, because silently
  merging pages is how invoice imports go wrong.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(total))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.extend(range(int(start) - 1, int(end)))
        else:
            pages.append(int(part) - 1)
    return [p for p in pages if 0 <= p < total]


def clean_cell(value) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return re.sub(r"\s?[£$€]\s?", lambda m: m.group(0).strip(), text)


def looks_like_total(row: list[str]) -> bool:
    joined = " ".join(row).lower()
    return any(word in joined for word in ("total", "subtotal", "vat", "tax"))


def extract(pdf_path: Path, out_dir: Path, pages: list[int]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"source": pdf_path.name, "tables": [], "warnings": []}

    with pdfplumber.open(pdf_path) as pdf:
        for page_no in pages:
            page = pdf.pages[page_no]
            found = page.extract_tables()
            if not found:
                manifest["warnings"].append(f"page {page_no + 1}: no table detected")
                continue

            for t_index, table in enumerate(found):
                rows = [[clean_cell(c) for c in row] for row in table]
                rows = [r for r in rows if any(cell for cell in r)]
                if len(rows) < 2:
                    continue

                header, body = rows[0], rows[1:]
                width = len(header)
                body = [r + [""] * (width - len(r)) for r in body]

                name = f"page{page_no + 1}_table{t_index + 1}.csv"
                path = out_dir / name
                with path.open("w", encoding="utf-8", newline="") as handle:
                    handle.write(",".join(f'"{h}"' for h in header) + "\n")
                    for row in body:
                        handle.write(",".join(f'"{c}"' for c in row[:width]) + "\n")

                manifest["tables"].append(
                    {
                        "file": name,
                        "page": page_no + 1,
                        "rows": len(body),
                        "columns": width,
                        "header": header,
                        "has_total_row": any(looks_like_total(r) for r in body),
                    }
                )

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Extract PDF tables to CSV.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pages", help="e.g. 1-3 or 1,4,7")
    args = parser.parse_args(argv)

    with pdfplumber.open(args.pdf) as pdf:
        total = len(pdf.pages)

    pages = parse_pages(args.pages, total)
    manifest = extract(args.pdf, args.out, pages)

    print(f"pages scanned: {len(pages)}  tables found: {len(manifest['tables'])}")
    for t in manifest["tables"]:
        flag = "  [has total row]" if t["has_total_row"] else ""
        print(f"  {t['file']:<24} {t['rows']:>4} rows x {t['columns']} cols{flag}")
    for w in manifest["warnings"]:
        print(f"  warning: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
