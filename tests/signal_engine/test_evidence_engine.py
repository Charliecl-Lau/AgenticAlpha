import pathlib
import pandas as pd
import pytest
from src.signal_engine.aggregator import compute_differentiation_matrix

def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "localization_score": 8, "subsidy_dependency": 3,
         "execution_quality": 9, "margin_signal": 7, "capex_signal": 8, "ROIC_signal": 7},
        {"company": "CATL", "localization_score": 7, "subsidy_dependency": 4,
         "execution_quality": 8, "margin_signal": 6, "capex_signal": 7, "ROIC_signal": 6},
        {"company": "LGES", "localization_score": 4, "subsidy_dependency": 8,
         "execution_quality": 4, "margin_signal": 3, "capex_signal": 4, "ROIC_signal": 3},
        {"company": "LGES", "localization_score": 5, "subsidy_dependency": 7,
         "execution_quality": 5, "margin_signal": 4, "capex_signal": 5, "ROIC_signal": 4},
    ])

def test_differentiation_matrix_columns():
    df = compute_differentiation_matrix(_make_df())
    assert set(df.columns) == {"factor", "CATL", "LGES", "delta"}

def test_differentiation_matrix_row_count():
    df = compute_differentiation_matrix(_make_df())
    assert len(df) == 6  # one row per factor

def test_differentiation_matrix_delta_correct():
    df = compute_differentiation_matrix(_make_df())
    row = df[df["factor"] == "localization"].iloc[0]
    assert abs(row["delta"] - (row["CATL"] - row["LGES"])) < 0.01

def test_differentiation_matrix_empty_df_returns_empty():
    df = compute_differentiation_matrix(pd.DataFrame(columns=["company", "localization_score"]))
    assert len(df) == 0

from src.signal_engine.charts import build_differentiation_matrix_chart

def test_build_differentiation_matrix_chart_creates_file(tmp_path):
    df = compute_differentiation_matrix(_make_df())
    out = str(tmp_path / "diff_matrix.png")
    build_differentiation_matrix_chart(df, out)
    assert pathlib.Path(out).exists()
    assert pathlib.Path(out).stat().st_size > 0

from src.signal_engine.aggregator import compute_timeline

def _make_timeline_df():
    return pd.DataFrame([
        {"company": "CATL", "date": "2025-01-10", "topic_cluster": "Capex_Execution",
         "contradiction_flag": False},
        {"company": "CATL", "date": "2025-03-15", "topic_cluster": "Capex_Execution",
         "contradiction_flag": True},
        {"company": "LGES", "date": "2025-01-20", "topic_cluster": "Subsidy_Dependence",
         "contradiction_flag": False},
        {"company": "LGES", "date": "2025-04-05", "topic_cluster": "Subsidy_Dependence",
         "contradiction_flag": False},
    ])

def test_compute_timeline_returns_dataframe():
    assert isinstance(compute_timeline(_make_timeline_df()), pd.DataFrame)

def test_compute_timeline_has_required_columns():
    df = compute_timeline(_make_timeline_df())
    for col in ["quarter", "company", "topic", "mention_count"]:
        assert col in df.columns

def test_compute_timeline_no_date_column_returns_empty():
    df = compute_timeline(pd.DataFrame(columns=["company", "topic_cluster"]))
    assert len(df) == 0

def test_compute_timeline_assigns_quarters():
    df = compute_timeline(_make_timeline_df())
    assert any("2025" in str(q) for q in df["quarter"].unique())

from src.signal_engine.charts import build_why_now_timeline_chart

def test_build_why_now_timeline_chart_creates_file(tmp_path):
    tl = compute_timeline(_make_timeline_df())
    out = str(tmp_path / "why_now.png")
    build_why_now_timeline_chart(tl, out)
    assert pathlib.Path(out).exists()

from src.signal_engine.aggregator import compute_contradictions

def _make_contradiction_df():
    return pd.DataFrame([
        {"company": "CATL", "contradiction_flag": True, "sentiment_score": 3.0,
         "claim_summary": "CATL margins fell sharply.",
         "contradiction_reason": "Challenges bull thesis on margins."},
        {"company": "CATL", "contradiction_flag": False, "sentiment_score": 8.0,
         "claim_summary": "CATL capacity on track.", "contradiction_reason": None},
        {"company": "LGES", "contradiction_flag": True, "sentiment_score": 2.0,
         "claim_summary": "LGES IRA credit at risk.",
         "contradiction_reason": "Policy risk not priced in."},
    ])

def test_compute_contradictions_returns_only_flagged():
    df = compute_contradictions(_make_contradiction_df())
    assert len(df) == 2
    assert all(df["contradiction_flag"])

def test_compute_contradictions_has_required_columns():
    df = compute_contradictions(_make_contradiction_df())
    for col in ["company", "claim_summary", "contradiction_reason", "sentiment_score"]:
        assert col in df.columns

def test_compute_contradictions_empty_when_no_flags():
    df = compute_contradictions(pd.DataFrame([
        {"company": "CATL", "contradiction_flag": False, "sentiment_score": 7.0,
         "claim_summary": "Good.", "contradiction_reason": None},
    ]))
    assert len(df) == 0

def test_compute_contradictions_no_column_returns_empty():
    df = compute_contradictions(pd.DataFrame(columns=["company", "sentiment_score"]))
    assert len(df) == 0

from src.signal_engine.charts import build_contradiction_chart

def test_build_contradiction_chart_creates_file(tmp_path):
    df = compute_contradictions(_make_contradiction_df())
    out = str(tmp_path / "contradictions.png")
    build_contradiction_chart(df, out)
    assert pathlib.Path(out).exists()
