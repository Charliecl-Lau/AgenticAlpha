# tests/signal_engine/test_cli.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import plotly.graph_objects as go
import pytest
from src.signal_engine.cli import run_signal_engine


def _write_tag(path: Path, company: str, topic: str, stream: str = "perception") -> None:
    path.write_text(json.dumps({
        "sentiment_score": 7, "direction": "positive",
        "topic_cluster": topic, "geo_exposure": ["EU"],
        "summary": "Summary sentence.", "stream": stream,
        "company": company, "source_file": path.name,
    }))


def test_run_signal_engine_produces_two_png_files(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    _write_tag(tags_dir / "catl_1.json", "CATL", "Organic_Scale_vs_Export")
    _write_tag(tags_dir / "lges_1.json", "LGES", "Subsidy_Dependence")
    out_dir = tmp_path / "charts"

    dummy_fig = MagicMock(spec=go.Figure)
    with patch("src.signal_engine.cli.build_divergence_matrix", return_value=dummy_fig), \
         patch("src.signal_engine.cli.build_trend_inflection", return_value=dummy_fig):
        run_signal_engine(tags_dir=str(tags_dir), output_dir=str(out_dir))

    assert dummy_fig.write_image.call_count == 2


def test_run_signal_engine_passes_trend_to_divergence_matrix(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    _write_tag(tags_dir / "catl_1.json", "CATL", "Organic_Scale_vs_Export")
    _write_tag(tags_dir / "lges_1.json", "LGES", "Subsidy_Dependence")
    out_dir = tmp_path / "charts"

    dummy_fig = MagicMock(spec=go.Figure)
    captured_kwargs: dict = {}

    def capture_divergence(counts_df, trend_df=None, sentiment_df=None, human_metrics=None):
        captured_kwargs["trend_df"] = trend_df
        captured_kwargs["sentiment_df"] = sentiment_df
        captured_kwargs["human_metrics"] = human_metrics
        return dummy_fig

    with patch("src.signal_engine.cli.build_divergence_matrix", side_effect=capture_divergence), \
         patch("src.signal_engine.cli.build_trend_inflection", return_value=dummy_fig):
        run_signal_engine(tags_dir=str(tags_dir), output_dir=str(out_dir))

    assert captured_kwargs["trend_df"] is not None
    assert len(captured_kwargs["trend_df"]) > 0
    assert captured_kwargs["sentiment_df"] is not None
    assert len(captured_kwargs["sentiment_df"]) > 0
    assert captured_kwargs["human_metrics"] is not None
    assert "catl_margin" in captured_kwargs["human_metrics"]


import json
from src.signal_engine.cli import run_signal_engine

def test_run_signal_engine_produces_five_new_charts(tmp_path):
    tag = {
        "company": "CATL", "stream": "perception", "source_weight": 1.0,
        "date": "2025-06-01", "sentiment_score": 7.5, "direction": "positive",
        "confidence": 0.8, "topic_cluster": "Capex_Execution", "geo_exposure": ["US"],
        "globalization_model": "export-led", "localization_score": 8,
        "subsidy_dependency": 3, "execution_quality": 9, "margin_signal": 7,
        "capex_signal": 8, "ROIC_signal": 7, "contradiction_flag": False,
        "contradiction_reason": None, "claim_summary": "CATL on track.", "key_quote": None,
    }
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    (tags_dir / "catl_test.json").write_text(json.dumps(tag))

    out_dir = tmp_path / "charts"
    out_dir.mkdir()

    run_signal_engine(str(tags_dir), str(out_dir), human_inputs_path=None)

    for fname in [
        "differentiation_matrix.png",
        "why_now_timeline.png",
        "contradictions.png",
        "risk_tree.png",
        "evidence_scale.png",
    ]:
        assert (out_dir / fname).exists(), f"Missing: {fname}"
