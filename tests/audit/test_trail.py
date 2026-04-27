import pandas as pd
import pytest
from src.audit.trail import build_audit_table, format_audit_table_rows

def _make_df():
    return pd.DataFrame([
        {
            "company": "CATL",
            "claim_summary": "CATL shipped 12 GWh overseas in Q4 2025.",
            "source_file": "catl_abc.md",
            "confidence": 0.9,
            "contradiction_reason": None,
            "stream": "ground_truth",
        },
        {
            "company": "LGES",
            "claim_summary": "LGES IRA credit may be capped by 2027 policy revision.",
            "source_file": "lges_xyz.md",
            "confidence": 0.7,
            "contradiction_reason": "Challenges IRA dependency thesis.",
            "stream": "policy",
        },
    ])

def test_build_audit_table_returns_list_of_dicts():
    result = build_audit_table(_make_df())
    assert isinstance(result, list)
    assert len(result) == 2

def test_build_audit_table_has_required_keys():
    result = build_audit_table(_make_df())
    for row in result:
        assert "claim" in row
        assert "docs" in row
        assert "confidence" in row
        assert "caveat" in row

def test_audit_row_caveat_shows_contradiction_reason():
    result = build_audit_table(_make_df())
    lges_row = next(r for r in result if "IRA" in r["claim"])
    assert "Challenges" in lges_row["caveat"]

def test_audit_row_caveat_is_none_identified_when_no_contradiction():
    result = build_audit_table(_make_df())
    catl_row = next(r for r in result if "CATL" in r["claim"])
    assert catl_row["caveat"] == "None identified"

def test_audit_row_confidence_formatted_as_percent():
    result = build_audit_table(_make_df())
    catl_row = next(r for r in result if "CATL" in r["claim"])
    assert "%" in catl_row["confidence"]
    assert "90" in catl_row["confidence"]

def test_audit_row_confidence_unknown_when_missing():
    df = pd.DataFrame([{
        "company": "CATL",
        "claim_summary": "CATL claim.",
        "source_file": "catl.md",
        "contradiction_reason": None,
    }])
    result = build_audit_table(df)
    assert result[0]["confidence"] == "unknown"

def test_build_audit_table_empty_df_returns_empty_list():
    result = build_audit_table(pd.DataFrame())
    assert result == []

def test_format_audit_table_rows_header_is_first_row():
    rows = build_audit_table(_make_df())
    table_rows = format_audit_table_rows(rows)
    assert table_rows[0] == ["Claim", "Source", "Confidence", "Caveat"]

def test_format_audit_table_rows_correct_count():
    rows = build_audit_table(_make_df())
    table_rows = format_audit_table_rows(rows)
    assert len(table_rows) == 3  # header + 2 data rows

def test_format_audit_table_rows_empty_input():
    table_rows = format_audit_table_rows([])
    assert table_rows == [["Claim", "Source", "Confidence", "Caveat"]]

def test_format_audit_table_rows_truncates_long_claims():
    long_row = {
        "claim": "A" * 200,
        "docs": "file.md",
        "confidence": "90%",
        "caveat": "None identified",
    }
    table_rows = format_audit_table_rows([long_row])
    assert len(table_rows[1][0]) <= 80

def test_format_audit_table_rows_truncates_long_caveats():
    long_row = {
        "claim": "Short claim.",
        "docs": "file.md",
        "confidence": "90%",
        "caveat": "C" * 200,
    }
    table_rows = format_audit_table_rows([long_row])
    assert len(table_rows[1][3]) <= 60
