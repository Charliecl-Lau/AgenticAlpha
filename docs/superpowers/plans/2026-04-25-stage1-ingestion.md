# Stage 1: Autonomous Hybrid Ingestion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-stream ingestion pipeline that fetches Bloomberg/Moomoo news (Stream A: Perception) and Investor Relations documents (Stream B: Ground Truth) from user-provided URLs, outputting clean Markdown files with a post-run manifest.

**Architecture:** A CLI-driven scraper reads a YAML URL list, fetches each page with `requests` (3-attempt retry + random inter-request delay for rate limiting), strips boilerplate HTML (nav/footer/ads) via BeautifulSoup + markdownify, detects and skips PDF URLs explicitly, deduplicates URLs within each stream, and writes `data/raw/perception/*.md` and `data/raw/ground_truth/*.md` plus an `ingestion_manifest.json` summary. Tests mock HTTP with the `responses` library — no live network calls in CI.

**Known limitation (out of scope for this deadline):** Bloomberg and Moomoo serve JS-rendered paywalled pages that `requests` cannot fully access. Playwright/Selenium would handle these but is too large a dependency for a 5-day timeline. Mitigation: populate `urls.yaml` with accessible cached/archive URLs or use exported article text directly. Document this in Slides 19-20.

**Tech Stack:** Python 3.11+, requests, beautifulsoup4, markdownify, pydantic, pyyaml, pytest, responses

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/ingestion/__init__.py`
- Create: `src/tagger/__init__.py`
- Create: `src/signal_engine/__init__.py`
- Create: `src/human_layer/__init__.py`
- Create: `src/renderer/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/ingestion/__init__.py`
- Create: `tests/tagger/__init__.py`
- Create: `tests/signal_engine/__init__.py`
- Create: `tests/human_layer/__init__.py`
- Create: `tests/renderer/__init__.py`
- Create: `.env.example`

- [ ] **Step 1: Create requirements.txt**

```
requests==2.32.3
beautifulsoup4==4.12.3
markdownify==0.13.1
pydantic==2.7.1
python-dotenv==1.0.1
pyyaml==6.0.1
anthropic==0.28.0
pandas==2.2.2
plotly==5.22.0
kaleido==0.2.1
python-pptx==0.6.23
pytest==8.2.0
pytest-mock==3.14.0
responses==0.25.3
```

- [ ] **Step 2: Create directory structure and empty init files**

```bash
mkdir -p src/ingestion src/tagger src/signal_engine src/human_layer src/renderer
mkdir -p tests/ingestion tests/tagger tests/signal_engine tests/human_layer tests/renderer
mkdir -p data/raw/perception data/raw/ground_truth data/processed/tags
mkdir -p output/charts output/deck config
touch src/__init__.py src/ingestion/__init__.py src/tagger/__init__.py
touch src/signal_engine/__init__.py src/human_layer/__init__.py src/renderer/__init__.py
touch tests/__init__.py tests/ingestion/__init__.py tests/tagger/__init__.py
touch tests/signal_engine/__init__.py tests/human_layer/__init__.py tests/renderer/__init__.py
```

- [ ] **Step 3: Create .env.example**

```
ANTHROPIC_API_KEY=your_key_here
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/ tests/ data/ output/ config/ .env.example
git commit -m "chore: scaffold project directory structure for AI analyst pipeline

Sets up the five-stage pipeline package layout (ingestion, tagger, signal_engine,
human_layer, renderer), creates empty data/output/config directories, and pins
all Python dependencies. .env.example documents the required ANTHROPIC_API_KEY."
```

---

### Task 2: URL Config Loader

**Files:**
- Create: `src/ingestion/config.py`
- Create: `config/urls.yaml`
- Test: `tests/ingestion/test_config.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/ingestion/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.ingestion.config'`

- [ ] **Step 3: Implement config loader**

```python
# src/ingestion/config.py
from pathlib import Path
from pydantic import BaseModel, field_validator
import yaml


class UrlEntry(BaseModel):
    url: str
    company: str

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"url must start with http:// or https://, got: {v!r}")
        return v


class UrlConfig(BaseModel):
    perception: list[UrlEntry]
    ground_truth: list[UrlEntry]

    @field_validator("perception", "ground_truth", mode="before")
    @classmethod
    def deduplicate_urls(cls, entries: list) -> list:
        seen: set[str] = set()
        deduped = []
        for e in entries:
            url = e["url"] if isinstance(e, dict) else e.url
            if url not in seen:
                seen.add(url)
                deduped.append(e)
        return deduped


def load_url_config(path: str) -> UrlConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(p) as f:
        data = yaml.safe_load(f)
    return UrlConfig(**data)
```

- [ ] **Step 4: Create sample config**

```yaml
# config/urls.yaml
# Replace placeholder URLs with real accessible article URLs.
# Bloomberg/Moomoo paywalled pages: use cached/archive.org versions or exported text.
# Ground truth: prefer HTML earnings release pages over PDF links (PDF not supported).
perception:
  - url: "https://www.bloomberg.com/news/articles/catl-example-url"
    company: "CATL"
  - url: "https://www.bloomberg.com/news/articles/lges-example-url"
    company: "LGES"
ground_truth:
  - url: "https://www.catl.com/en/news/661.html"
    company: "CATL"
  - url: "https://www.lgensol.com/en/investor"
    company: "LGES"
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/ingestion/test_config.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/config.py tests/ingestion/test_config.py config/urls.yaml
git commit -m "feat(ingestion): add URL config loader with validation and deduplication

UrlEntry validates that URLs start with http(s)://. UrlConfig deduplicates
within each stream at load time so duplicate YAML entries don't waste API
quota or produce duplicate output files. Raises FileNotFoundError on
missing config and ValidationError on bad URL format or missing company."
```

---

### Task 3: HTTP Fetcher with Retry and PDF Detection

**Files:**
- Create: `src/ingestion/fetcher.py`
- Test: `tests/ingestion/test_fetcher.py`

- [ ] **Step 1: Write failing test**

```python
# tests/ingestion/test_fetcher.py
import responses as rsps_lib
import pytest
from src.ingestion.fetcher import fetch_page, PdfSkipError


@rsps_lib.activate
def test_fetch_page_returns_html_body():
    rsps_lib.add(rsps_lib.GET, "https://example.com/news/1",
                 body="<html><body><p>Battery news</p></body></html>", status=200)
    html = fetch_page("https://example.com/news/1")
    assert "<p>Battery news</p>" in html


@rsps_lib.activate
def test_fetch_page_raises_runtime_error_after_retries():
    # Register 3 consecutive 503s — all retries exhausted
    for _ in range(3):
        rsps_lib.add(rsps_lib.GET, "https://example.com/down", status=503)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        fetch_page("https://example.com/down")


@rsps_lib.activate
def test_fetch_page_succeeds_on_second_attempt():
    rsps_lib.add(rsps_lib.GET, "https://example.com/flaky", status=503)
    rsps_lib.add(rsps_lib.GET, "https://example.com/flaky",
                 body="<html><body><p>Recovered.</p></body></html>", status=200)
    html = fetch_page("https://example.com/flaky")
    assert "Recovered." in html


@rsps_lib.activate
def test_fetch_page_raises_pdf_skip_error_on_pdf_content_type():
    rsps_lib.add(rsps_lib.GET, "https://example.com/report.pdf",
                 body=b"%PDF-1.4 fake content",
                 content_type="application/pdf", status=200)
    with pytest.raises(PdfSkipError):
        fetch_page("https://example.com/report.pdf")


@rsps_lib.activate
def test_fetch_page_raises_pdf_skip_error_on_pdf_url_extension():
    rsps_lib.add(rsps_lib.GET, "https://catl.com/2024-annual-report.pdf",
                 body=b"%PDF content", status=200)
    with pytest.raises(PdfSkipError):
        fetch_page("https://catl.com/2024-annual-report.pdf")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/ingestion/test_fetcher.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement fetcher**

```python
# src/ingestion/fetcher.py
import time
import random
import requests

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AgenticAlpha/1.0; research-only)"
}
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0   # seconds; doubles each retry


class PdfSkipError(RuntimeError):
    """Raised when a URL resolves to a PDF — pipeline should log and skip."""


def fetch_page(url: str, timeout: int = 30) -> str:
    if url.lower().endswith(".pdf"):
        raise PdfSkipError(f"PDF URL skipped (no PDF parser in stack): {url}")

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=timeout)
            content_type = resp.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                raise PdfSkipError(f"PDF content-type at {url} — skipped")
            if resp.status_code == 200:
                return resp.text
            last_exc = RuntimeError(f"HTTP {resp.status_code} fetching {url}")
        except PdfSkipError:
            raise
        except Exception as exc:
            last_exc = exc

        if attempt < _MAX_RETRIES - 1:
            sleep_secs = _BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(sleep_secs)

    raise last_exc  # type: ignore[misc]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/ingestion/test_fetcher.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/ingestion/fetcher.py tests/ingestion/test_fetcher.py
git commit -m "feat(ingestion): add retry logic, rate-limit backoff, and PDF detection to fetcher

Retries up to 3 times with exponential backoff (1s, 2s + jitter) on
non-200 responses. Raises PdfSkipError — not RuntimeError — when a PDF
is detected (by URL extension or Content-Type) so the pipeline can log
a clear skip reason rather than treating it as a generic failure."
```

---

### Task 4: HTML-to-Markdown Cleaner

**Files:**
- Create: `src/ingestion/cleaner.py`
- Test: `tests/ingestion/test_cleaner.py`

- [ ] **Step 1: Write failing test**

```python
# tests/ingestion/test_cleaner.py
from src.ingestion.cleaner import html_to_markdown, extract_article_text


def test_html_to_markdown_strips_nav_and_footer():
    html = (
        "<html><nav>Site nav</nav>"
        "<article><p>CATL reported strong Q3 margins.</p></article>"
        "<footer>Copyright 2024</footer></html>"
    )
    md = html_to_markdown(html)
    assert "CATL reported strong Q3 margins" in md
    assert "Site nav" not in md
    assert "Copyright" not in md


def test_html_to_markdown_collapses_excess_blank_lines():
    html = "<p>First.</p><br><br><br><br><p>Second.</p>"
    md = html_to_markdown(html)
    assert md.count("\n\n\n") == 0


def test_extract_article_text_prefers_article_tag():
    html = (
        "<html><body>"
        "<div class='ad'>Buy stuff now!</div>"
        "<article><h1>LGES IRA Update</h1><p>LGES secured $1.2B credits.</p></article>"
        "</body></html>"
    )
    text = extract_article_text(html)
    assert "LGES secured $1.2B credits" in text
    assert "Buy stuff now" not in text


def test_extract_article_text_falls_back_to_body():
    html = "<html><body><p>Earnings summary here.</p></body></html>"
    text = extract_article_text(html)
    assert "Earnings summary here" in text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/ingestion/test_cleaner.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement cleaner**

```python
# src/ingestion/cleaner.py
import re
from bs4 import BeautifulSoup
import markdownify


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["nav", "footer", "header", "aside", "script", "style"]):
        tag.decompose()
    for sel in [".ad", ".advertisement", "[class*='cookie']", "[class*='banner']"]:
        for el in soup.select(sel):
            el.decompose()
    md = markdownify.markdownify(str(soup), heading_style="ATX")
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md


def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["nav", "footer", "header", "aside", "script", "style"]):
        tag.decompose()
    for sel in [".ad", ".advertisement", "[class*='cookie']"]:
        for el in soup.select(sel):
            el.decompose()
    root = soup.find("article") or soup.find("main") or soup.find("body")
    if root is None:
        return html_to_markdown(html)
    md = markdownify.markdownify(str(root), heading_style="ATX")
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/ingestion/test_cleaner.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/ingestion/cleaner.py tests/ingestion/test_cleaner.py
git commit -m "feat(ingestion): add HTML-to-Markdown cleaner

Strips nav/footer/header/ads before converting HTML to Markdown.
Prefers <article> or <main> tags over full-body extraction to reduce
boilerplate. Collapses 3+ blank lines to 2 to keep output readable."
```

---

### Task 5: Ingestion Pipeline, Manifest & CLI

**Files:**
- Create: `src/ingestion/pipeline.py`
- Create: `src/ingestion/cli.py`
- Test: `tests/ingestion/test_pipeline.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/ingestion/test_pipeline.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement pipeline**

```python
# src/ingestion/pipeline.py
import hashlib
import json
import logging
import random
import time
from pathlib import Path
from src.ingestion.config import UrlConfig, UrlEntry
from src.ingestion.fetcher import fetch_page, PdfSkipError

logger = logging.getLogger(__name__)


def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def _url_slug(url: str, company: str) -> str:
    digest = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{company.lower()}_{digest}.md"


def _ingest_stream(
    entries: list[UrlEntry],
    stream_dir: Path,
    stats: dict,
) -> None:
    stream_dir.mkdir(parents=True, exist_ok=True)
    for i, entry in enumerate(entries):
        if i > 0:
            random_delay()
        try:
            html = fetch_page(entry.url)
            from src.ingestion.cleaner import extract_article_text
            md = extract_article_text(html)
            filename = _url_slug(entry.url, entry.company)
            (stream_dir / filename).write_text(
                f"# Source: {entry.url}\n# Company: {entry.company}\n\n{md}",
                encoding="utf-8",
            )
            stats["succeeded"] += 1
            logger.info("Ingested %s -> %s", entry.url, filename)
        except PdfSkipError as exc:
            stats["failed"] += 1
            stats["skipped_urls"].append({"url": entry.url, "reason": "pdf_not_supported"})
            logger.warning("PDF skipped %s: %s", entry.url, exc)
        except Exception as exc:
            stats["failed"] += 1
            stats["skipped_urls"].append({"url": entry.url, "reason": str(exc)})
            logger.warning("Failed %s: %s", entry.url, exc)
        stats["total"] += 1


def run_ingestion(config: UrlConfig, output_dir: str = "data/raw") -> None:
    base = Path(output_dir)
    stats: dict = {"total": 0, "succeeded": 0, "failed": 0, "skipped_urls": []}
    _ingest_stream(config.perception, base / "perception", stats)
    _ingest_stream(config.ground_truth, base / "ground_truth", stats)
    manifest_path = base / "ingestion_manifest.json"
    manifest_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    logger.info(
        "Ingestion summary: %d/%d succeeded, %d failed",
        stats["succeeded"], stats["total"], stats["failed"],
    )
```

- [ ] **Step 4: Implement CLI**

```python
# src/ingestion/cli.py
import argparse
import json
import logging
from src.ingestion.config import load_url_config
from src.ingestion.pipeline import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest news and IR documents into Markdown")
    parser.add_argument("--config", default="config/urls.yaml")
    parser.add_argument("--output", default="data/raw")
    args = parser.parse_args()
    config = load_url_config(args.config)
    run_ingestion(config, output_dir=args.output)
    import json
    from pathlib import Path
    manifest = json.loads((Path(args.output) / "ingestion_manifest.json").read_text())
    print(
        f"Ingestion complete: {manifest['succeeded']}/{manifest['total']} succeeded, "
        f"{manifest['failed']} failed. See {args.output}/ingestion_manifest.json"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run all ingestion tests**

```bash
pytest tests/ingestion/ -v
```

Expected: PASS (all 15 tests)

- [ ] **Step 6: Smoke-test with real URLs (do this before proceeding to Stage 2)**

Update `config/urls.yaml` with 5-10 real accessible URLs (mix of news and IR pages — no PDF links), then run:

```bash
python -m src.ingestion.cli --config config/urls.yaml --output data/raw
```

Inspect the output:
```bash
cat data/raw/ingestion_manifest.json
head -50 data/raw/perception/catl_*.md
```

Expected: Manifest shows succeeded count > 0. Markdown files contain readable financial text, not JS bundle garbage. If output is noisy, adjust `extract_article_text` selectors before tagging.

- [ ] **Step 7: Commit**

```bash
git add src/ingestion/pipeline.py src/ingestion/cli.py tests/ingestion/test_pipeline.py
git commit -m "feat(ingestion): add pipeline with rate limiting, PDF skip, and manifest output

Adds random 1-3s inter-request delay to avoid IP bans. PdfSkipError is
caught separately from generic failures so the manifest distinguishes
pdf_not_supported from HTTP errors. Post-run manifest JSON logs total/
succeeded/failed counts and the URL+reason for every skip — giving the
human analyst a clear picture of data completeness before tagging runs."
```
