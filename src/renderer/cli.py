# src/renderer/cli.py
import argparse
import logging
from src.human_layer.schema import load_human_inputs
from src.human_layer.merger import merge_inputs
from src.signal_engine.loader import load_tags
from src.renderer.content_map import build_slide_specs
from src.renderer.slide_builder import build_pptx

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_renderer(deck_input, output_path: str) -> None:
    specs = build_slide_specs(deck_input)
    logger.info("Building %d slides", len(specs))
    build_pptx(specs, output_path)
    logger.info("Deck written to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PPTX deck from AI signals and human inputs")
    parser.add_argument("--human-inputs", default="config/human_inputs.yaml")
    parser.add_argument("--tags", default="data/processed/tags")
    parser.add_argument("--divergence-matrix", default="output/charts/quality_divergence_matrix.png")
    parser.add_argument("--trend-inflection", default="output/charts/trend_inflection.png")
    parser.add_argument("--output", default="output/deck/catl_lges_pair_trade.pptx")
    args = parser.parse_args()
    human = load_human_inputs(args.human_inputs)
    tag_df = load_tags(args.tags)
    deck_input = merge_inputs(human, tag_df, args.divergence_matrix, args.trend_inflection)
    run_renderer(deck_input, output_path=args.output)
    print(f"Deck saved to {args.output}")


if __name__ == "__main__":
    main()
