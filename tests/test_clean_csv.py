import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clean_csv import clean, normalise_header, parse_amount, parse_date  # noqa: E402


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("£1,234.50", 1234.50),
        ("$99", 99.0),
        ("(123)", -123.0),
        ("12.5 CR", 12.5),
        ("12.5 DR", -12.5),
        ("", None),
        ("n/a", None),
        ("  42  ", 42.0),
    ],
)
def test_parse_amount_handles_real_exports(raw, expected):
    assert parse_amount(raw) == expected


def test_parse_amount_rejects_garbage():
    with pytest.raises(ValueError, match="unparseable amount"):
        parse_amount("about fifty")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2026-01-31", "2026-01-31"),
        ("31/01/2026", "2026-01-31"),
        ("31 Jan 2026", "2026-01-31"),
        ("", None),
    ],
)
def test_parse_date_formats(raw, expected):
    assert parse_date(raw) == expected


def test_parse_date_rejects_impossible_dates():
    with pytest.raises(ValueError, match="unparseable date"):
        parse_date("2026-13-01")


def test_normalise_header():
    assert normalise_header("Order  Value (£)") == "order_value"
    assert normalise_header("  DATE ") == "date"


def test_clean_drops_duplicates_and_reports_errors():
    header = ["date", "customer", "amount"]
    rows = [
        {"date": "31/01/2026", "customer": "Acme", "amount": "£1,000"},
        {"date": "31/01/2026", "customer": "Acme", "amount": "£1,000"},  # duplicate
        {"date": "2026-13-01", "customer": "Beta", "amount": "call us"},  # two bad cells
    ]
    cleaned, audit = clean(rows, header)

    assert len(cleaned) == 2
    assert audit.duplicate_rows == 1
    assert cleaned[0]["date"] == "2026-01-31"
    assert cleaned[0]["amount"] == 1000.0
    assert len(audit.errors) == 2
    assert cleaned[1]["date"] is None and cleaned[1]["amount"] is None
