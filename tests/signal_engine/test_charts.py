# tests/signal_engine/test_charts.py
import pandas as pd
import pytest
import plotly.graph_objects as go
from src.signal_engine.charts import build_divergence_matrix, build_trend_inflection


def _counts_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export", "count": 66.7},
        {"company": "CATL", "topic_cluster": "Subsidy_Dependence", "count": 13.3},
        {"company": "LGES", "topic_cluster": "Organic_Scale_vs_Export", "count": 16.7},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence", "count": 60.0},
    ])


def _trend_df():
    return pd.DataFrame([
        {"company": "CATL", "mean_sentiment": 7.4},
        {"company": "LGES", "mean_sentiment": 4.1},
    ])


def _sentiment_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export", "mean_sentiment": 9.0},
        {"company": "CATL", "topic_cluster": "Subsidy_Dependence", "mean_sentiment": 7.0},
        {"company": "LGES", "topic_cluster": "Organic_Scale_vs_Export", "mean_sentiment": 5.0},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence", "mean_sentiment": 3.0},
    ])


def test_build_divergence_matrix_returns_plotly_figure():
    fig = build_divergence_matrix(_counts_df())
    assert isinstance(fig, go.Figure)


def test_build_divergence_matrix_has_both_companies_in_data():
    fig = build_divergence_matrix(_counts_df())
    all_text = fig.to_json()
    assert "CATL" in all_text
    assert "LGES" in all_text


def test_build_divergence_matrix_has_data_labels():
    fig = build_divergence_matrix(_counts_df())
    # At least one bar trace must have text labels set
    assert any(trace.text is not None for trace in fig.data)


def test_build_divergence_matrix_adds_sentiment_subtitle_when_trend_provided():
    fig = build_divergence_matrix(_counts_df(), trend_df=_trend_df(), human_metrics={"catl_margin": 31.4, "lges_margin": 2.1})
    title_text = fig.layout.title.text
    # Both sentiment scores must appear in the title subtitle
    assert "7.4" in title_text
    assert "4.1" in title_text
    # Check human metrics
    assert "31.4%" in title_text
    assert "2.1%" in title_text


def test_build_divergence_matrix_no_subtitle_without_trend():
    fig = build_divergence_matrix(_counts_df(), human_metrics={"catl_margin": 31.4, "lges_margin": 2.1})
    title_text = fig.layout.title.text
    assert "Mean sentiment" not in title_text


def test_build_divergence_matrix_raises_on_missing_columns():
    bad_df = pd.DataFrame([{"company": "CATL", "count": 5}])
    with pytest.raises(KeyError):
        build_divergence_matrix(bad_df)


def test_build_divergence_matrix_annotates_bars_with_sentiment_when_provided():
    fig = build_divergence_matrix(_counts_df(), sentiment_df=_sentiment_df())
    all_text = " ".join(
        str(t) for trace in fig.data for t in (trace.text or [])
    )
    assert "★" in all_text


def test_build_divergence_matrix_sentiment_lookup_miss_shows_count_only():
    # sentiment_df only covers CATL — LGES topics have no matching rows
    partial_sentiment = pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export", "mean_sentiment": 9.0},
    ])
    fig = build_divergence_matrix(_counts_df(), sentiment_df=partial_sentiment)
    # Should not raise; LGES bars fall back to count-only label
    lges_trace = next(t for t in fig.data if t.name == "LGES")
    assert all("★" not in str(label) for label in lges_trace.text)


def test_build_trend_inflection_returns_plotly_figure():
    fig = build_trend_inflection(_sentiment_df())
    assert isinstance(fig, go.Figure)


def test_build_trend_inflection_y_axis_bounded_0_to_10():
    fig = build_trend_inflection(_sentiment_df())
    assert list(fig.layout.yaxis.range) == [0, 10]


def test_build_trend_inflection_has_both_companies():
    fig = build_trend_inflection(_sentiment_df())
    assert "CATL" in fig.to_json()
    assert "LGES" in fig.to_json()


def test_build_trend_inflection_uses_grouped_bars():
    fig = build_trend_inflection(_sentiment_df())
    assert fig.layout.barmode == "group"


def test_build_trend_inflection_filters_other_topic():
    df = _sentiment_df()
    # Add an "Other" topic
    df = pd.concat([df, pd.DataFrame([{"company": "CATL", "topic_cluster": "Other", "mean_sentiment": 5.0}])])
    fig = build_trend_inflection(df)
    all_text = fig.to_json()
    assert "Other" not in all_text


def test_build_trend_inflection_has_human_narrative_subtitle():
    fig = build_trend_inflection(_sentiment_df())
    title_text = fig.layout.title.text
    assert "Sentiment divergence on execution topics supports human-verified margin premium" in title_text
