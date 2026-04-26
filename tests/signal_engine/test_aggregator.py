# tests/signal_engine/test_aggregator.py
import pandas as pd
import pytest
from src.signal_engine.aggregator import compute_topic_counts, compute_sentiment_trend, compute_topic_sentiment, compute_weighted_sentiment


def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "stream": "perception", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 8, "direction": "positive"},
        {"company": "CATL", "stream": "perception", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 7, "direction": "positive"},
        {"company": "LGES", "stream": "perception", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 4, "direction": "negative"},
        {"company": "LGES", "stream": "perception", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 3, "direction": "negative"},
        {"company": "LGES", "stream": "perception", "topic_cluster": "Geopolitical_Noise",
         "sentiment_score": 5, "direction": "neutral"},
    ])


def test_compute_topic_counts_returns_counts_per_company_and_topic():
    df = _make_df()
    counts = compute_topic_counts(df, stream="perception")
    catl_row = counts[(counts["company"] == "CATL") & (counts["topic_cluster"] == "Organic_Scale_vs_Export")]
    assert catl_row["count"].iloc[0] == 2
    lges_subsidy = counts[(counts["company"] == "LGES") & (counts["topic_cluster"] == "Subsidy_Dependence")]
    assert lges_subsidy["count"].iloc[0] == 2


def test_compute_topic_counts_filters_by_stream():
    df = _make_df()
    counts = compute_topic_counts(df, stream="ground_truth")
    assert len(counts) == 0


def test_compute_topic_counts_normalizes_by_company_total():
    df = _make_df()
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    # CATL: 2 Organic_Scale_vs_Export out of 2 total → 100.0%
    catl_row = counts[(counts["company"] == "CATL") & (counts["topic_cluster"] == "Organic_Scale_vs_Export")]
    assert abs(catl_row["count"].iloc[0] - 100.0) < 0.1
    # LGES: 2 Subsidy_Dependence out of 3 total → 66.7%
    lges_row = counts[(counts["company"] == "LGES") & (counts["topic_cluster"] == "Subsidy_Dependence")]
    assert abs(lges_row["count"].iloc[0] - 66.7) < 0.2


def test_compute_topic_counts_normalize_sums_to_100_per_company():
    df = _make_df()
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    lges_total = counts[counts["company"] == "LGES"]["count"].sum()
    assert abs(lges_total - 100.0) < 0.2


def test_compute_sentiment_trend_returns_mean_per_company():
    df = _make_df()
    trend = compute_sentiment_trend(df, stream="perception")
    catl_mean = trend[trend["company"] == "CATL"]["mean_sentiment"].iloc[0]
    assert abs(catl_mean - 7.5) < 0.01
    lges_mean = trend[trend["company"] == "LGES"]["mean_sentiment"].iloc[0]
    assert abs(lges_mean - 4.0) < 0.01


def test_compute_sentiment_trend_empty_stream_returns_empty():
    df = _make_df()
    trend = compute_sentiment_trend(df, stream="ground_truth")
    assert len(trend) == 0


def test_compute_topic_sentiment_returns_mean_per_company_and_topic():
    df = _make_df()
    result = compute_topic_sentiment(df)
    catl_row = result[(result["company"] == "CATL") & (result["topic_cluster"] == "Organic_Scale_vs_Export")]
    assert abs(catl_row["mean_sentiment"].iloc[0] - 7.5) < 0.01
    lges_row = result[(result["company"] == "LGES") & (result["topic_cluster"] == "Subsidy_Dependence")]
    assert abs(lges_row["mean_sentiment"].iloc[0] - 3.5) < 0.01


def test_compute_topic_sentiment_includes_all_streams():
    df = _make_df().copy()
    df.loc[0, "stream"] = "ground_truth"
    result = compute_topic_sentiment(df)
    # ground_truth row should still be included (no stream filter)
    catl_row = result[(result["company"] == "CATL") & (result["topic_cluster"] == "Organic_Scale_vs_Export")]
    assert len(catl_row) == 1


def test_compute_topic_sentiment_empty_returns_empty():
    result = compute_topic_sentiment(pd.DataFrame())
    assert len(result) == 0


def test_compute_weighted_sentiment_boosts_ground_truth():
    df = pd.DataFrame([
        {"company": "CATL", "stream": "perception", "topic_cluster": "Organic_Scale_vs_Export", "sentiment_score": 6},
        {"company": "CATL", "stream": "ground_truth", "topic_cluster": "Organic_Scale_vs_Export", "sentiment_score": 9},
    ])
    result = compute_weighted_sentiment(df)
    row = result[(result["company"] == "CATL") & (result["topic_cluster"] == "Organic_Scale_vs_Export")]
    # weighted: (6*1 + 9*2) / (1+2) = 24/3 = 8.0
    assert abs(row["weighted_mean_sentiment"].iloc[0] - 8.0) < 0.01


def test_compute_weighted_sentiment_equals_mean_when_all_same_stream():
    df = _make_df()  # all perception
    result = compute_weighted_sentiment(df)
    catl_row = result[(result["company"] == "CATL") & (result["topic_cluster"] == "Organic_Scale_vs_Export")]
    # (8+7)/2 = 7.5
    assert abs(catl_row["weighted_mean_sentiment"].iloc[0] - 7.5) < 0.01


def test_compute_weighted_sentiment_empty_returns_empty():
    result = compute_weighted_sentiment(pd.DataFrame())
    assert len(result) == 0
