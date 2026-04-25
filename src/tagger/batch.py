import json
import logging
import re
from collections import Counter
from pathlib import Path
from src.tagger.tagger import tag_document

logger = logging.getLogger(__name__)

_HEADER_RE = re.compile(r"^#\s*Company:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def _parse_header(text: str) -> dict:
    match = _HEADER_RE.search(text)
    return {"company": match.group(1) if match else "Unknown"}


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

    for stream, dir_path in input_dirs.items():
        for md_file in sorted(Path(dir_path).glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            meta = _parse_header(text)
            try:
                tag = tag_document(model, text, company=meta["company"], stream=stream)
                result = tag.model_dump()
                result["source_file"] = md_file.name
                result["stream"] = stream
                result["company"] = meta["company"]
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
