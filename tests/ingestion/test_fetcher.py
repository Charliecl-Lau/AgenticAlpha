import responses as rsps_lib
import pytest
from unittest.mock import patch
from src.ingestion.fetcher import fetch_page, PdfSkipError


@rsps_lib.activate
def test_fetch_page_returns_html_body():
    rsps_lib.add(rsps_lib.GET, "https://example.com/news/1",
                 body="<html><body><p>Battery news</p></body></html>", status=200)
    html = fetch_page("https://example.com/news/1")
    assert "<p>Battery news</p>" in html


@rsps_lib.activate
@patch("src.ingestion.fetcher.time.sleep")
def test_fetch_page_raises_runtime_error_after_retries(mock_sleep):
    # Register 3 consecutive 503s — all retries exhausted
    for _ in range(3):
        rsps_lib.add(rsps_lib.GET, "https://example.com/down", status=503)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        fetch_page("https://example.com/down")


@rsps_lib.activate
@patch("src.ingestion.fetcher.time.sleep")
def test_fetch_page_succeeds_on_second_attempt(mock_sleep):
    rsps_lib.add(rsps_lib.GET, "https://example.com/flaky", status=503)
    rsps_lib.add(rsps_lib.GET, "https://example.com/flaky",
                 body="<html><body><p>Recovered.</p></body></html>", status=200)
    html = fetch_page("https://example.com/flaky")
    assert "Recovered." in html


@rsps_lib.activate
def test_fetch_page_raises_pdf_skip_error_on_pdf_content_type():
    rsps_lib.add(rsps_lib.GET, "https://example.com/report",
                 body=b"%PDF-1.4 fake content",
                 content_type="application/pdf", status=200)
    with pytest.raises(PdfSkipError):
        fetch_page("https://example.com/report")


@rsps_lib.activate
def test_fetch_page_raises_pdf_skip_error_on_pdf_url_extension():
    rsps_lib.add(rsps_lib.GET, "https://catl.com/2024-annual-report.pdf",
                 body=b"%PDF content", status=200)
    with pytest.raises(PdfSkipError):
        fetch_page("https://catl.com/2024-annual-report.pdf")
