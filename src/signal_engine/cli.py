import argparse
import logging
from pathlib import Path
from src.signal_engine.loader import load_tags
from src.signal_engine.aggregator import compute_topic_counts, compute_sentiment_trend, compute_weighted_sentiment
from src.signal_engine.aggregator import (
    compute_differentiation_matrix,
    compute_timeline,
    compute_contradictions,
    compute_risk_tree,
    compute_evidence_attribution,
)
from src.signal_engine.charts import build_divergence_matrix, build_trend_inflection
from src.signal_engine.charts import (
    build_differentiation_matrix_chart,
    build_why_now_timeline_chart,
    build_contradiction_chart,
    build_risk_tree_chart,
    build_evidence_scale_chart,
)
from src.human_layer.schema import load_human_inputs

logger = logging.getLogger(__name__)


def run_signal_engine(tags_dir: str, output_dir: str, human_inputs_path: str = "config/human_inputs.yaml") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = load_tags(tags_dir)
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    trend = compute_sentiment_trend(df, stream="perception")
    sentiment = compute_weighted_sentiment(df)

    try:
        human_data = load_human_inputs(human_inputs_path)
        human_metrics = {
            "catl_margin": human_data.catl_overseas_gross_margin_pct,
            "lges_margin": human_data.lges_q1_operating_margin_ex_ira_pct
        }
    except Exception as e:
        logger.warning("Could not load human inputs, using defaults. Error: %s", e)
        human_metrics = {"catl_margin": 31.4, "lges_margin": 2.1}

    divergence_fig = build_divergence_matrix(counts, trend_df=trend, sentiment_df=sentiment, human_metrics=human_metrics)
    inflection_fig = build_trend_inflection(sentiment)

    divergence_path = str(out / "quality_divergence_matrix.png")
    inflection_path = str(out / "trend_inflection.png")
    divergence_fig.write_image(divergence_path, width=1200, height=700)
    inflection_fig.write_image(inflection_path, width=900, height=600)
    logger.info("Saved %s", divergence_path)
    logger.info("Saved %s", inflection_path)

    import os as _os

    diff_df = compute_differentiation_matrix(df)
    build_differentiation_matrix_chart(diff_df, _os.path.join(output_dir, "differentiation_matrix.png"))

    timeline_df = compute_timeline(df)
    build_why_now_timeline_chart(timeline_df, _os.path.join(output_dir, "why_now_timeline.png"))

    contra_df = compute_contradictions(df)
    build_contradiction_chart(contra_df, _os.path.join(output_dir, "contradictions.png"))

    risk_df = compute_risk_tree(df)
    build_risk_tree_chart(risk_df, _os.path.join(output_dir, "risk_tree.png"))

    attrib_df = compute_evidence_attribution(df)
    build_evidence_scale_chart(attrib_df, _os.path.join(output_dir, "evidence_scale.png"))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Generate signal charts from tagged data")
    parser.add_argument("--tags", default="data/processed/tags")
    parser.add_argument("--output", default="output/charts")
    parser.add_argument("--human-inputs", default="config/human_inputs.yaml")
    args = parser.parse_args()
    run_signal_engine(tags_dir=args.tags, output_dir=args.output, human_inputs_path=args.human_inputs)
    print(f"Charts written to {args.output}/")


if __name__ == "__main__":
    main()
