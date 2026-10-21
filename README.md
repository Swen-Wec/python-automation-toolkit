# Python Automation Toolkit

Small, dependable tools for the unglamorous work that eats hours: cleaning messy spreadsheets,
scraping tables that change shape, and turning both into something you can actually use.

Built and tested on Python 3.11+. No paid services required.

## What's inside

| Tool | Problem it solves |
|---|---|
| `clean_csv.py` | Messy exports: duplicate rows, mixed date formats, currency strings, blank cells, inconsistent headers |
| `scrape_table.py` | Pulling a table from a page that may be slow, rate-limited, or structurally inconsistent |
| `report.py` | Turns a cleaned file into a short data-quality summary you can send to a client |
| `pdf_tables.py` | Pulls tables out of a PDF into one CSV per table, plus a manifest of what was found |

## Quick start

```bash
pip install -r requirements.txt

# 1. See what is wrong with a file before touching it
python clean_csv.py data/messy_sales.csv --audit

# 2. Clean it, keeping a log of every change
python clean_csv.py data/messy_sales.csv -o data/clean_sales.csv

# 3. Scrape a table (respects robots.txt, retries with backoff)
python scrape_table.py https://example.com/prices --table-id prices --out data/prices.csv
```

## Design choices

**Every transformation is logged.** `clean_csv.py --audit` prints a report of what it found and
what it would change *before* writing anything. Clients break trust when numbers move silently.

**Retries are bounded and jittered.** `scrape_table.py` uses exponential backoff with jitter and
caps attempts, so a flaky site does not turn into a runaway loop or an IP ban.

**Failures are explicit.** Missing columns, unparseable dates and ambiguous currency symbols raise
with the row number and the offending value, instead of being coerced to `NaN` and forgotten.

**Tests cover the ugly cases**, not the happy path: `1,234.50`, `£1,234`, `(123)` for negatives,
`2026-13-01`, duplicated headers, ragged rows.

## Tests

```bash
pytest -q
```

## License

MIT
