# tests/signal_engine/test_loader.py
import json
import pytest
import pandas as pd
from src.signal_engine.loader import load_tags

_TAG_A = {
    "sentiment_score": 8, "direction": "positive",
    "topic_cluster": "Organic_Scale_vs_Export", "geo_exposure": ["EU"],
    "summary": "CATL Hungary plant reached 50 GWh.", "stream": "perception",
    "company": "CATL", "source_file": "catl_abc123.md",
}
_TAG_B = {
    "sentiment_score": 4, "direction": "negative",
    "topic_cluster": "Subsidy_Dependence", "geo_exposure": ["US"],
    "summary": "LGES IRA credits represented 62% of revenue.", "stream": "perception",
    "company": "LGES", "source_file": "lges_def456.md",
}


def test_load_tags_returns_dataframe(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_TAG_A))
    (tmp_path / "b.json").write_text(json.dumps(_TAG_B))
    df = load_tags(str(tmp_path))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_load_tags_has_expected_columns(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_TAG_A))
    df = load_tags(str(tmp_path))
    for col in ["sentiment_score", "direction", "topic_cluster", "geo_exposure", "company", "stream"]:
        assert col in df.columns


def test_load_tags_skips_malformed_json(tmp_path):
    (tmp_path / "good.json").write_text(json.dumps(_TAG_A))
    (tmp_path / "bad.json").write_text("{not valid json")
    df = load_tags(str(tmp_path))
    assert len(df) == 1


def test_load_tags_raises_on_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="No tag files"):
        load_tags(str(tmp_path))


def test_load_tags_raises_on_all_malformed(tmp_path):
    (tmp_path / "bad1.json").write_text("{not valid")
    (tmp_path / "bad2.json").write_text("{also bad")
    with pytest.raises(ValueError, match="malformed"):
        load_tags(str(tmp_path))
