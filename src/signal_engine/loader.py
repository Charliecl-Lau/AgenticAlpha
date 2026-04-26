import json
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def load_tags(tags_dir: str) -> pd.DataFrame:
    records = []
    for path in sorted(Path(tags_dir).glob("*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.warning("Skipping %s: %s", path.name, exc)
    if not records:
        raise ValueError(f"No tag files found in {tags_dir}")
    return pd.DataFrame(records)
