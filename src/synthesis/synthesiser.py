from __future__ import annotations

import json
import os
import pathlib

from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.synthesis.schema import SynthesisOutput

load_dotenv()


def synthesise(prompt: str, model: str = "gemma-4-31b-it") -> SynthesisOutput:
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.0,
        ),
    )
    raw = response.text.strip()
    # Strip markdown fences if model wraps output
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        data = json.loads(raw)
        return SynthesisOutput(**data)
    except Exception as exc:
        raise ValueError(
            f"Failed to parse synthesis output: {exc}\n\nRaw response:\n{raw}"
        ) from exc


def generate_analyst_brief(
    deck_input,
    charts_dict: dict | None = None,
    output_dir: str = "output/briefing",
    model: str = "gemma-4-31b-it",
) -> tuple[str, SynthesisOutput]:
    """Run synthesis from a fully assembled DeckInput and save to output/briefing/.

    Returns (markdown_text, SynthesisOutput).
    """
    import pandas as pd
    from src.synthesis.prompt_builder import build_synthesis_prompt
    from src.signal_engine.aggregator import (
        compute_differentiation_matrix,
        compute_contradictions,
    )

    h = deck_input.human
    signals = deck_input.ai_signals

    tag_df = getattr(deck_input, "_tag_df", pd.DataFrame())

    diff_df = compute_differentiation_matrix(tag_df) if not tag_df.empty else pd.DataFrame()
    contra_df = compute_contradictions(tag_df) if not tag_df.empty else pd.DataFrame()

    prompt = build_synthesis_prompt(
        diff_df=diff_df,
        contradictions_df=contra_df,
        top_signals=signals,
        human_inputs=h,
        chart_paths=charts_dict,
    )

    output = synthesise(prompt, model=model)

    md = _to_brief_markdown(output)

    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "analyst_brief.json").write_text(
        json.dumps(output.model_dump(), indent=2), encoding="utf-8"
    )
    (out / "analyst_brief.md").write_text(md, encoding="utf-8")

    return md, output


def _to_brief_markdown(output: SynthesisOutput) -> str:
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
        "## Differentiation Takeaway",
        output.differentiation_takeaway,
        "",
        "## Strongest Supporting Evidence",
    ]
    for e in output.strongest_supporting_evidence:
        lines.append(f"- {e}")
    lines += ["", "## Contrary / Risk Evidence"]
    for e in output.contrary_risk_evidence:
        lines.append(f"- {e}")
    lines += ["", "## Contradiction Summary", output.contradiction_summary, "", "## Risk Summary", output.risk_summary]
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
