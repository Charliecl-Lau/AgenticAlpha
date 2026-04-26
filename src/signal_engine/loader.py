import json
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def load_tags(tags_dir: str) -> pd.DataFrame:
    json_paths = sorted(Path(tags_dir).glob("*.json"))
    if not json_paths:
        raise ValueError(f"No tag files found in {tags_dir}")
    records = []
    for path in json_paths:
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.warning("Skipping %s: %s", path.name, exc)
    if not records:
        raise ValueError(f"All JSON files in {tags_dir} were malformed")
    return pd.DataFrame(records)
