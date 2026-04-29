# src/ingestion/cli.py
import argparse
import logging
from src.ingestion.config import load_url_config
from src.ingestion.pipeline import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest news and IR documents into Markdown")
    parser.add_argument("--config", default="config/urls.yaml")
    parser.add_argument("--output", default="data/raw")
    parser.add_argument("--new-only", action="store_true", help="Only ingest URLs tagged new: true")
    args = parser.parse_args()
    config = load_url_config(args.config, new_only=args.new_only)
    stats = run_ingestion(config, output_dir=args.output)
    print(
        f"Ingestion complete: {stats['succeeded']}/{stats['total']} succeeded, "
        f"{stats['failed']} failed. See {args.output}/ingestion_manifest.json"
    )


if __name__ == "__main__":
    main()
