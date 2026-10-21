"""Scrape an HTML table into CSV, with bounded retries and a real user agent.

Usage:
    python scrape_table.py https://example.com/prices --table-id prices --out data/prices.csv
    python scrape_table.py https://example.com/prices --table-index 0 --out data/t.csv

Why not a one-liner: sites move, throttle, and return partial HTML. This retries with
jittered exponential backoff, fails loudly, and keeps the raw HTML so a broken parse can
be re-run offline instead of hammering the site again.
"""
from __future__ import annotations

import argparse
import random
import time
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)


def fetch(url: str, attempts: int = 4, timeout: int = 20) -> str:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            if response.status_code == 429:
                raise requests.HTTPError("429 rate limited", response=response)
            response.raise_for_status()
            if "<table" not in response.text.lower():
                raise ValueError("no <table> in response (page may be JS-rendered)")
            return response.text
        except Exception as exc:  # noqa: BLE001 - surfaced after the final attempt
            last_error = exc
            if attempt == attempts:
                break
            delay = min(2 ** attempt, 20) * (0.5 + random.random())
            print(f"attempt {attempt} failed ({exc}); retrying in {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError(f"failed after {attempts} attempts: {last_error}")


def extract(html: str, table_id: str | None, table_index: int) -> pd.DataFrame:
    tables = pd.read_html(StringIO(html))
    if not tables:
        raise ValueError("no tables parsed")
    if table_id:
        # pandas does not expose id=, so match on the attribute in the raw HTML order
        match = [t for t in tables if table_id in html]
        if not match:
            raise ValueError(f"table id {table_id!r} not found")
        selected = match[0]
    else:
        selected = tables[table_index]
    selected.columns = [str(c).strip().lower().replace(" ", "_") for c in selected.columns]
    return selected


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape an HTML table to CSV.")
    parser.add_argument("url")
    parser.add_argument("--table-id")
    parser.add_argument("--table-index", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--keep-html", type=Path, help="save raw HTML for offline re-parsing")
    args = parser.parse_args(argv)

    html = fetch(args.url)
    if args.keep_html:
        args.keep_html.parent.mkdir(parents=True, exist_ok=True)
        args.keep_html.write_text(html, encoding="utf-8")

    frame = extract(html, args.table_id, args.table_index)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(f"{len(frame)} rows x {len(frame.columns)} cols -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
