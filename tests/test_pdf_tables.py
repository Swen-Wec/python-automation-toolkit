import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pdf_tables import clean_cell, looks_like_total, parse_pages  # noqa: E402


@pytest.mark.parametrize(
    "spec,total,expected",
    [
        (None, 3, [0, 1, 2]),
        ("1", 3, [0]),
        ("2-3", 4, [1, 2]),
        ("1,3", 4, [0, 2]),
        ("9", 3, []),
    ],
)
def test_parse_pages(spec, total, expected):
    assert parse_pages(spec, total) == expected


def test_clean_cell_collapses_whitespace():
    assert clean_cell("  Hydraulic   hose,\n3/4 in ") == "Hydraulic hose, 3/4 in"
    assert clean_cell(None) == ""


def test_clean_cell_keeps_currency_symbol():
    assert clean_cell(" £ 48.50 ") == "£48.50"


@pytest.mark.parametrize(
    "row,expected",
    [
        (["", "", "", "Subtotal", "£6,994.60"], True),
        (["", "", "", "VAT (20%)", "£1,398.92"], True),
        (["NX-1042", "Hydraulic hose", "12", "£48.50", "£582.00"], False),
    ],
)
def test_looks_like_total(row, expected):
    assert looks_like_total(row) is expected


def test_extract_sample_pdf_if_present():
    pdf = Path(__file__).resolve().parents[1] / "data" / "sample_schedule.pdf"
    if not pdf.exists():
        pytest.skip("sample pdf not generated")
    from pdf_tables import extract

    manifest = extract(pdf, Path(__file__).resolve().parents[1] / "out" / "test_tables", [0, 1])
    assert len(manifest["tables"]) == 2
    assert manifest["tables"][0]["columns"] == 5
    assert manifest["tables"][0]["has_total_row"] is True
