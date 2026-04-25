# tests/ingestion/test_pipeline.py
import json
import random
from pathlib import Path
from unittest.mock import patch
from src.ingestion.pipeline import run_ingestion
from src.ingestion.config import UrlConfig, UrlEntry
from src.ingestion.fetcher import PdfSkipError

_FAKE_HTML = "<article><p>Battery capacity grew 40%.</p></article>"


def test_run_ingestion_writes_both_streams(tmp_path):
    config = UrlConfig(
        perception=[UrlEntry(url="https://example.com/news/1", company="CATL")],
        ground_truth=[UrlEntry(url="https://example.com/ir/1", company="CATL")],
    )
    with patch("src.ingestion.pipeline.fetch_page", return_value=_FAKE_HTML), \
         patch("src.ingestion.pipeline.random_delay"):
        run_ingestion(config, output_dir=str(tmp_path))
    assert len(list((tmp_path / "perception").glob("*.md"))) == 1
    assert len(list((tmp_path / "ground_truth").glob("*.md"))) == 1


def test_run_ingestion_skips_failed_urls_and_continues(tmp_path):
    config = UrlConfig(
        perception=[
            UrlEntry(url="https://example.com/ok", company="CATL"),
            UrlEntry(url="https://example.com/fail", company="LGES"),
        ],
        ground_truth=[],
    )

    def fake_fetch(url, **kwargs):
        if "fail" in url:
            raise RuntimeError("HTTP 403")
        return _FAKE_HTML

    with patch("src.ingestion.pipeline.fetch_page", side_effect=fake_fetch), \
         patch("src.ingestion.pipeline.random_delay"):
        run_ingestion(config, output_dir=str(tmp_path))
    assert len(list((tmp_path / "perception").glob("*.md"))) == 1


def test_run_ingestion_skips_pdf_urls(tmp_path):
    config = UrlConfig(
        perception=[UrlEntry(url="https://example.com/report.pdf", company="CATL")],
        ground_truth=[],
    )
    with patch("src.ingestion.pipeline.fetch_page", side_effect=PdfSkipError("PDF skipped")), \
         patch("src.ingestion.pipeline.random_delay"):
        run_ingestion(config, output_dir=str(tmp_path))
    assert len(list((tmp_path / "perception").glob("*.md"))) == 0


def test_run_ingestion_writes_manifest(tmp_path):
    config = UrlConfig(
        perception=[
            UrlEntry(url="https://example.com/ok", company="CATL"),
            UrlEntry(url="https://example.com/fail", company="LGES"),
        ],
        ground_truth=[],
    )

    def fake_fetch(url, **kwargs):
        if "fail" in url:
            raise RuntimeError("HTTP 403")
        return _FAKE_HTML

    with patch("src.ingestion.pipeline.fetch_page", side_effect=fake_fetch), \
         patch("src.ingestion.pipeline.random_delay"):
        run_ingestion(config, output_dir=str(tmp_path))
    manifest = json.loads((tmp_path / "ingestion_manifest.json").read_text())
    assert manifest["total"] == 2
    assert manifest["succeeded"] == 1
    assert manifest["failed"] == 1
    assert len(manifest["skipped_urls"]) == 1


def test_run_ingestion_includes_source_url_in_output(tmp_path):
    config = UrlConfig(
        perception=[UrlEntry(url="https://bloomberg.com/catl-123", company="CATL")],
        ground_truth=[],
    )
    with patch("src.ingestion.pipeline.fetch_page", return_value=_FAKE_HTML), \
         patch("src.ingestion.pipeline.random_delay"):
        run_ingestion(config, output_dir=str(tmp_path))
    content = list((tmp_path / "perception").glob("*.md"))[0].read_text()
    assert "https://bloomberg.com/catl-123" in content
