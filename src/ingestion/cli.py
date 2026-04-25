# src/ingestion/cli.py
import argparse
import json
import logging
from pathlib import Path
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
    manifest = json.loads((Path(args.output) / "ingestion_manifest.json").read_text())
    print(
        f"Ingestion complete: {manifest['succeeded']}/{manifest['total']} succeeded, "
        f"{manifest['failed']} failed. See {args.output}/ingestion_manifest.json"
    )


if __name__ == "__main__":
    main()
