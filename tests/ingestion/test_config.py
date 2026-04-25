# tests/ingestion/test_config.py
import pytest
from pydantic import ValidationError
from src.ingestion.config import load_url_config, UrlConfig, UrlEntry


def test_load_url_config_returns_two_streams(tmp_path):
    config_file = tmp_path / "urls.yaml"
    config_file.write_text(
        "perception:\n"
        "  - url: 'https://bloomberg.com/catl-1'\n"
        "    company: CATL\n"
        "ground_truth:\n"
        "  - url: 'https://catl.com/ir/q1'\n"
        "    company: CATL\n"
    )
    config = load_url_config(str(config_file))
    assert len(config.perception) == 1
    assert len(config.ground_truth) == 1
    assert config.perception[0].company == "CATL"
    assert config.perception[0].url == "https://bloomberg.com/catl-1"


def test_load_url_config_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_url_config("nonexistent.yaml")


def test_load_url_config_validates_required_fields(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("perception:\n  - url: 'https://example.com'\n")  # missing company
    with pytest.raises(Exception):
        load_url_config(str(bad))


def test_url_entry_rejects_non_http_url():
    with pytest.raises(ValidationError, match="must start with http"):
        UrlEntry(url="ftp://example.com/doc.pdf", company="CATL")


def test_url_entry_rejects_bare_domain():
    with pytest.raises(ValidationError, match="must start with http"):
        UrlEntry(url="example.com/page", company="LGES")


def test_load_url_config_deduplicates_within_stream(tmp_path):
    config_file = tmp_path / "urls.yaml"
    config_file.write_text(
        "perception:\n"
        "  - url: 'https://bloomberg.com/catl-1'\n"
        "    company: CATL\n"
        "  - url: 'https://bloomberg.com/catl-1'\n"
        "    company: CATL\n"
        "ground_truth: []\n"
    )
    config = load_url_config(str(config_file))
    assert len(config.perception) == 1
