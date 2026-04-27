# src/ingestion/pipeline.py
import datetime as _dt
import hashlib
import json
import logging
import random
import time
from pathlib import Path
from src.ingestion.config import UrlConfig, UrlEntry
from src.ingestion.fetcher import fetch_page, PdfSkipError
from src.ingestion.cleaner import extract_article_text

logger = logging.getLogger(__name__)


def _build_frontmatter(
    company: str,
    source,
    source_type: str,
    region,
    date,
) -> str:
    today = date or _dt.date.today().isoformat()
    lines = [
        "---",
        f"company: {company}",
        f"source: {source or 'unknown'}",
        f"source_type: {source_type}",
        f"region: {region or 'unknown'}",
        f"date: '{today}'",
        "---",
        "",
    ]
    return "\n".join(lines)


def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def _url_slug(url: str, company: str) -> str:
    digest = hashlib.md5(url.encode()).hexdigest()
    return f"{company.lower()}_{digest}.md"


def _ingest_stream(
    entries: list[UrlEntry],
    stream_dir: Path,
    stream_name: str,
    stats: dict,
) -> None:
    stream_dir.mkdir(parents=True, exist_ok=True)
    for i, entry in enumerate(entries):
        if i > 0:
            random_delay()
        try:
            html = fetch_page(entry.url)
            md = extract_article_text(html)
            filename = _url_slug(entry.url, entry.company)
            frontmatter = _build_frontmatter(
                company=entry.company,
                source=entry.source,
                source_type=stream_name,
                region=entry.region,
                date=None,
            )
            content_to_write = frontmatter + f"# Source: {entry.url}\n# Company: {entry.company}\n\n{md}"
            (stream_dir / filename).write_text(content_to_write, encoding="utf-8")
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


def run_ingestion(config: UrlConfig, output_dir: str = "data/raw") -> dict:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    stats: dict = {"total": 0, "succeeded": 0, "failed": 0, "skipped_urls": []}
    _ingest_stream(config.perception, base / "perception", "perception", stats)
    _ingest_stream(config.ground_truth, base / "ground_truth", "ground_truth", stats)
    _ingest_stream(config.policy, base / "policy", "policy", stats)
    _ingest_stream(config.operations, base / "operations", "operations", stats)
    manifest_path = base / "ingestion_manifest.json"
    manifest_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    logger.info(
        "Ingestion summary: %d/%d succeeded, %d failed",
        stats["succeeded"], stats["total"], stats["failed"],
    )
    return stats
