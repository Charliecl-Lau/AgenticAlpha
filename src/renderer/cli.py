import argparse
import json
import logging
import pathlib

from src.human_layer.schema import load_human_inputs
from src.human_layer.merger import merge_inputs
from src.signal_engine.loader import load_tags
from src.renderer.content_map import build_slide_specs
from src.renderer.slide_builder import build_pptx
from src.synthesis.schema import SynthesisOutput

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
    parser.add_argument("--differentiation-matrix", default="output/charts/differentiation_matrix.png")
    parser.add_argument("--why-now-timeline", default="output/charts/why_now_timeline.png")
    parser.add_argument("--contradictions", default="output/charts/contradictions.png")
    parser.add_argument("--risk-tree", default="output/charts/risk_tree.png")
    parser.add_argument("--evidence-scale", default="output/charts/evidence_scale.png")
    parser.add_argument("--synthesis", default="output/synthesis.json",
                        help="Path to synthesis JSON (optional — skipped if absent)")
    parser.add_argument("--output", default="output/deck/catl_lges_pair_trade.pptx")
    args = parser.parse_args()

    human = load_human_inputs(args.human_inputs)
    tag_df = load_tags(args.tags)

    synthesis = None
    synthesis_path = pathlib.Path(args.synthesis)
    if synthesis_path.exists():
        synthesis = SynthesisOutput(**json.loads(synthesis_path.read_text()))

    deck_input = merge_inputs(
        human=human,
        tag_df=tag_df,
        divergence_matrix_path=args.divergence_matrix,
        trend_inflection_path=args.trend_inflection,
        differentiation_matrix_path=args.differentiation_matrix,
        why_now_timeline_path=args.why_now_timeline,
        contradictions_path=args.contradictions,
        risk_tree_path=args.risk_tree,
        evidence_scale_path=args.evidence_scale,
        synthesis=synthesis,
    )
    run_renderer(deck_input, output_path=args.output)
    print(f"Deck saved to {args.output}")


if __name__ == "__main__":
    main()
