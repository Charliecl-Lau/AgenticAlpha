import argparse
import json
import os

import pandas as pd

from src.signal_engine.aggregator import (
    compute_differentiation_matrix,
    compute_contradictions,
)
from src.signal_engine.loader import load_tags
from src.human_layer.summariser import extract_top_signals
from src.synthesis.prompt_builder import build_synthesis_prompt
from src.synthesis.synthesiser import synthesise


def run_synthesis(
    tags_dir: str,
    charts_dir: str,
    output_path: str,
    model: str = "claude-sonnet-4-6",
) -> None:
    has_tags = os.path.isdir(tags_dir) and any(
        f.endswith(".json") for f in os.listdir(tags_dir)
    )
    tag_df = load_tags(tags_dir) if has_tags else pd.DataFrame()

    diff_df = compute_differentiation_matrix(tag_df)
    contra_df = compute_contradictions(tag_df)
    top_signals = extract_top_signals(tag_df, n=3) if not tag_df.empty else {}

    prompt = build_synthesis_prompt(
        diff_df=diff_df,
        contradictions_df=contra_df,
        top_signals=top_signals,
    )

    output = synthesise(prompt, model=model)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output.model_dump(), f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthesis layer (single Claude call)")
    parser.add_argument("--tags",   default="data/processed/tags",  help="Tag JSON directory")
    parser.add_argument("--charts", default="output/charts",         help="Charts directory")
    parser.add_argument("--output", default="output/synthesis.json", help="Output synthesis JSON")
    parser.add_argument("--model",  default="claude-sonnet-4-6",     help="Claude model ID")
    args = parser.parse_args()
    run_synthesis(args.tags, args.charts, args.output, args.model)


if __name__ == "__main__":
    main()
