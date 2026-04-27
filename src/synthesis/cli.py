import argparse
import json
import os
import pathlib

import pandas as pd

from src.signal_engine.aggregator import (
    compute_differentiation_matrix,
    compute_contradictions,
    compute_topic_counts,
    compute_weighted_sentiment,
)
from src.signal_engine.loader import load_tags
from src.human_layer.schema import load_human_inputs
from src.human_layer.summariser import extract_top_signals
from src.synthesis.prompt_builder import build_synthesis_prompt
from src.synthesis.synthesiser import synthesise
from src.synthesis.schema import SynthesisOutput


def _to_markdown(output: SynthesisOutput) -> str:
    lines = [
        "# AI Analyst Brief – CATL vs LGES Globalization Quality",
        "",
        f"**Research Question:** {output.research_question}",
        "",
        "## Executive Summary",
        output.executive_summary,
        "",
        "## Differentiation Matrix",
        "| Factor | CATL Evidence | LGES Evidence | Implication | Supporting Tags |",
        "|--------|--------------|--------------|-------------|-----------------|",
    ]
    for row in output.differentiation_matrix:
        lines.append(
            f"| {row.factor} | {row.catl_evidence} | {row.lges_evidence} | {row.implication} | {row.supporting_tags} |"
        )
    lines += [
        "",
        "## Why Now?",
        output.why_now,
        "",
        "## Strongest Supporting Evidence",
    ]
    for e in output.strongest_supporting_evidence:
        lines.append(f"- {e}")
    lines += ["", "## Contrary / Risk Evidence"]
    for e in output.contrary_risk_evidence:
        lines.append(f"- {e}")
    lines += ["", "## Open Questions for Human Analysts"]
    for q in output.analyst_questions:
        lines.append(f"- {q}")
    lines += [
        "",
        f"**Overall Confidence:** {output.overall_confidence}",
        "",
        "## Limitations & Bias",
    ]
    for lim in output.limitations:
        lines.append(f"- {lim}")
    return "\n".join(lines)


def run_synthesis(
    tags_dir: str,
    charts_dir: str,
    output_path: str,
    model: str = "gemma-4-31b-it",
    human_inputs_path: str = "config/human_inputs.yaml",
) -> None:
    has_tags = os.path.isdir(tags_dir) and any(
        f.endswith(".json") for f in os.listdir(tags_dir)
    )
    tag_df = load_tags(tags_dir) if has_tags else pd.DataFrame()

    human = None
    try:
        human = load_human_inputs(human_inputs_path)
    except Exception:
        pass

    diff_df = compute_differentiation_matrix(tag_df)
    contra_df = compute_contradictions(tag_df)
    top_signals = extract_top_signals(tag_df, n=7) if not tag_df.empty else {}
    topic_counts = compute_topic_counts(tag_df, stream="perception", normalize=True) if not tag_df.empty else None
    sentiment = compute_weighted_sentiment(tag_df) if not tag_df.empty else None

    chart_paths = {
        "quality_divergence_matrix": os.path.join(charts_dir, "quality_divergence_matrix.png"),
        "trend_inflection": os.path.join(charts_dir, "trend_inflection.png"),
        "differentiation_matrix": os.path.join(charts_dir, "differentiation_matrix.png"),
        "why_now_timeline": os.path.join(charts_dir, "why_now_timeline.png"),
        "contradictions": os.path.join(charts_dir, "contradictions.png"),
        "risk_tree": os.path.join(charts_dir, "risk_tree.png"),
        "evidence_scale": os.path.join(charts_dir, "evidence_scale.png"),
    }

    prompt = build_synthesis_prompt(
        diff_df=diff_df,
        contradictions_df=contra_df,
        top_signals=top_signals,
        human_inputs=human,
        topic_counts_df=topic_counts,
        sentiment_df=sentiment,
        chart_paths=chart_paths,
    )

    output = synthesise(prompt, model=model)

    out_path = pathlib.Path(output_path)
    os.makedirs(out_path.parent, exist_ok=True)
    out_path.write_text(json.dumps(output.model_dump(), indent=2), encoding="utf-8")

    md_path = out_path.with_suffix(".md")
    md_path.write_text(_to_markdown(output), encoding="utf-8")

    briefing_dir = pathlib.Path("output/briefing")
    briefing_dir.mkdir(parents=True, exist_ok=True)
    (briefing_dir / "analyst_brief.json").write_text(
        json.dumps(output.model_dump(), indent=2), encoding="utf-8"
    )
    (briefing_dir / "analyst_brief.md").write_text(_to_markdown(output), encoding="utf-8")

    print(f"Synthesis JSON:  {out_path}")
    print(f"Analyst brief:   {md_path}")
    print(f"Briefing output: {briefing_dir / 'analyst_brief.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthesis layer (single LLM call)")
    parser.add_argument("--tags",          default="data/processed/tags",   help="Tag JSON directory")
    parser.add_argument("--charts",        default="output/charts",          help="Charts directory")
    parser.add_argument("--output",        default="output/synthesis.json",  help="Output synthesis JSON")
    parser.add_argument("--model",         default="gemma-4-31b-it",         help="Gemma model ID")
    parser.add_argument("--human-inputs",  default="config/human_inputs.yaml")
    args = parser.parse_args()
    run_synthesis(args.tags, args.charts, args.output, args.model, args.human_inputs)


if __name__ == "__main__":
    main()
