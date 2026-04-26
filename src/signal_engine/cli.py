import argparse
import logging
from pathlib import Path
from src.signal_engine.loader import load_tags
from src.signal_engine.aggregator import compute_topic_counts, compute_sentiment_trend
from src.signal_engine.charts import build_divergence_matrix, build_trend_inflection

logger = logging.getLogger(__name__)


def run_signal_engine(tags_dir: str, output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = load_tags(tags_dir)
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    trend = compute_sentiment_trend(df, stream="perception")

    divergence_fig = build_divergence_matrix(counts, trend_df=trend)
    inflection_fig = build_trend_inflection(trend)

    divergence_path = str(out / "quality_divergence_matrix.png")
    inflection_path = str(out / "trend_inflection.png")
    divergence_fig.write_image(divergence_path, width=1200, height=700)
    inflection_fig.write_image(inflection_path, width=900, height=600)
    logger.info("Saved %s", divergence_path)
    logger.info("Saved %s", inflection_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Generate signal charts from tagged data")
    parser.add_argument("--tags", default="data/processed/tags")
    parser.add_argument("--output", default="output/charts")
    args = parser.parse_args()
    run_signal_engine(tags_dir=args.tags, output_dir=args.output)
    print(f"Charts written to {args.output}/")


if __name__ == "__main__":
    main()
