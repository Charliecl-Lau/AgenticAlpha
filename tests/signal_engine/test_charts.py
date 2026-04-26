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


def test_build_divergence_matrix_returns_plotly_figure():
    fig = build_divergence_matrix(_counts_df())
    assert isinstance(fig, go.Figure)


def test_build_divergence_matrix_has_both_companies_in_data():
    fig = build_divergence_matrix(_counts_df())
    all_text = str(fig.to_json())
    assert "CATL" in all_text
    assert "LGES" in all_text


def test_build_divergence_matrix_has_data_labels():
    fig = build_divergence_matrix(_counts_df())
    # At least one bar trace must have text labels set
    assert any(trace.text is not None for trace in fig.data)


def test_build_divergence_matrix_adds_sentiment_subtitle_when_trend_provided():
    fig = build_divergence_matrix(_counts_df(), trend_df=_trend_df())
    title_text = fig.layout.title.text
    # Both sentiment scores must appear in the title subtitle
    assert "7.4" in title_text
    assert "4.1" in title_text


def test_build_divergence_matrix_no_subtitle_without_trend():
    fig = build_divergence_matrix(_counts_df())
    title_text = fig.layout.title.text
    assert "Mean sentiment" not in title_text


def test_build_divergence_matrix_raises_on_missing_columns():
    bad_df = pd.DataFrame([{"company": "CATL", "count": 5}])
    with pytest.raises(KeyError):
        build_divergence_matrix(bad_df)


def test_build_trend_inflection_returns_plotly_figure():
    fig = build_trend_inflection(_trend_df())
    assert isinstance(fig, go.Figure)


def test_build_trend_inflection_y_axis_bounded_0_to_10():
    fig = build_trend_inflection(_trend_df())
    assert list(fig.layout.yaxis.range) == [0, 10]
