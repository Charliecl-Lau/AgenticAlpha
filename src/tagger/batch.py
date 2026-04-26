import json
import logging
import re
from collections import Counter
from pathlib import Path
from src.tagger.tagger import tag_document

logger = logging.getLogger(__name__)

_HEADER_RE = re.compile(r"^#\s*Company:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)

_STREAM_WEIGHTS: dict[str, float] = {
    "perception": 1.0,
    "ground_truth": 2.0,
    "policy": 1.5,
    "operations": 2.0,
}


def source_weight_for_stream(stream: str) -> float:
    return _STREAM_WEIGHTS.get(stream, 1.0)


def parse_frontmatter_date(markdown: str) -> "str | None":
    match = re.match(r"^---\n(.*?)\n---\n", markdown, re.DOTALL)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith("date:"):
            return line.split(":", 1)[1].strip()
    return None


def _parse_header(text: str) -> dict:
    match = _HEADER_RE.search(text)
    return {"company": match.group(1) if match else "Unknown"}


def _iter_dirs(dir_value):
    """Yield Path objects from a string, Path, or list thereof."""
    if isinstance(dir_value, (str, Path)):
        yield Path(dir_value)
    else:
        for d in dir_value:
            yield Path(d)


def run_batch(
    input_dirs: dict,
    output_dir: str,
    model,
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    processed = 0
    skipped = 0
    cluster_counts: Counter = Counter()

    for stream, dir_value in input_dirs.items():
        for dir_path in _iter_dirs(dir_value):
            for md_file in sorted(dir_path.glob("*.md")):
                text = md_file.read_text(encoding="utf-8")
                meta = _parse_header(text)
                try:
                    tag = tag_document(model, text, company=meta["company"], stream=stream)
                    result = tag.model_dump()
                    result["stream"] = stream
                    result["company"] = meta["company"]
                    result["source_file"] = md_file.name
                    result["source_weight"] = source_weight_for_stream(stream)
                    result["date"] = parse_frontmatter_date(text)
                    out_file = out / f"{stream}_{md_file.stem}.json"
                    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
                    cluster_counts[result["topic_cluster"]] += 1
                    processed += 1
                    logger.info("Tagged %s -> %s", md_file.name, out_file.name)
                except Exception as exc:
                    skipped += 1
                    logger.warning("Skipping %s: %s", md_file.name, exc)

    print(f"\n=== Tagging Report ===")
    print(f"Processed: {processed} | Skipped: {skipped}")
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        print(f"  {cluster}: {count}")
    print("======================")
