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


def test_url_config_has_policy_stream(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception: []
ground_truth: []
policy:
  - url: https://www.irs.gov/credits-deductions/inflation-reduction-act
    company: CATL
    source: IRS
    region: US
operations: []
""")
    config = load_url_config(str(cfg))
    assert len(config.policy) == 1
    assert config.policy[0].company == "CATL"


def test_url_config_has_operations_stream(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception: []
ground_truth: []
policy: []
operations:
  - url: https://example.com/lges-commissioning
    company: LGES
    source: LGES IR
    region: EU
""")
    config = load_url_config(str(cfg))
    assert len(config.operations) == 1
    assert config.operations[0].region == "EU"


def test_url_entry_has_optional_source_and_region(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception:
  - url: https://example.com/article
    company: CATL
ground_truth: []
policy: []
operations: []
""")
    config = load_url_config(str(cfg))
    entry = config.perception[0]
    assert entry.source is None
    assert entry.region is None


def test_url_entry_source_and_region_populated_when_given(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception:
  - url: https://example.com/article
    company: CATL
    source: Reuters
    region: US
ground_truth: []
policy: []
operations: []
""")
    config = load_url_config(str(cfg))
    entry = config.perception[0]
    assert entry.source == "Reuters"
    assert entry.region == "US"


def test_missing_policy_key_defaults_to_empty(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("perception: []\nground_truth: []\n")
    config = load_url_config(str(cfg))
    assert config.policy == []
    assert config.operations == []
