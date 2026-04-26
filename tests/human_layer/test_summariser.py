import pandas as pd
from src.human_layer.summariser import extract_top_signals


def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 9, "summary": "CATL Hungary at 50 GWh.", "stream": "perception"},
        {"company": "CATL", "topic_cluster": "Capex_Execution",
         "sentiment_score": 8, "summary": "CATL capex efficiency outperforms.", "stream": "perception"},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 3, "summary": "LGES IRA credits dominate revenue.", "stream": "perception"},
        {"company": "LGES", "topic_cluster": "Geopolitical_Noise",
         "sentiment_score": 4, "summary": "LGES faces US tariff uncertainty.", "stream": "perception"},
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 7, "summary": "CATL LFP volume up 40% YoY.", "stream": "ground_truth"},
    ])


def test_extract_top_signals_returns_top_3_per_company():
    df = _make_df()
    signals = extract_top_signals(df, n=3)
    assert "CATL" in signals
    assert "LGES" in signals
    assert len(signals["CATL"]) <= 3
    assert len(signals["LGES"]) <= 3


def test_extract_top_signals_prefers_ground_truth_over_higher_raw_score():
    """A ground_truth entry at sentiment_score 7 (weighted 14) should rank above
    a perception entry at sentiment_score 9 (weighted 9)."""
    df = _make_df()
    signals = extract_top_signals(df, n=3)
    top_catl = signals["CATL"]
    assert top_catl[0]["stream"] == "ground_truth"


def test_extract_top_signals_includes_summary_and_topic():
    df = _make_df()
    signals = extract_top_signals(df, n=1)
    top_catl = signals["CATL"][0]
    assert "summary" in top_catl
    assert "topic_cluster" in top_catl


def test_extract_top_signals_output_does_not_expose_weighted_score():
    """Internal weighting must not leak into the output dicts."""
    df = _make_df()
    signals = extract_top_signals(df, n=3)
    for record in signals["CATL"]:
        assert "_weighted_score" not in record
