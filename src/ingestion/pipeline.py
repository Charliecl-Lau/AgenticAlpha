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
