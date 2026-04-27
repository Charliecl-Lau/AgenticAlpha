from __future__ import annotations

import pandas as pd


def build_synthesis_prompt(
    diff_df: pd.DataFrame,
    contradictions_df: pd.DataFrame,
    top_signals: dict[str, list[dict]],
    human_inputs=None,
    topic_counts_df: pd.DataFrame | None = None,
    sentiment_df: pd.DataFrame | None = None,
    chart_paths: dict | None = None,
) -> str:
    human_block = _format_human_inputs(human_inputs)
    counts_block = _format_topic_counts(topic_counts_df)
    sentiment_block = _format_sentiment(sentiment_df)
    charts_block = _format_chart_names(chart_paths)
    return f"""You are a quantitative research analyst writing an AI Analyst Brief for an institutional equity pair trade.
Your audience is UBS investment analysts who will lift sections directly into their deck.

RESEARCH QUESTION:
How does the quality of globalization (localization capabilities vs. export/subsidy models, margin impact, capex execution,
and return cycles) differ between CATL and LGES, and what does this imply for sustainability of returns?

RULES:
- Do NOT make investment recommendations (no buy/sell/hold).
- Every claim must trace to the data inputs below — no invented facts.
- Use specific numbers where available (scores, margins, deltas, sentiment scores, coverage shares).
- Write substantive paragraphs (3–5 sentences for summaries, not 1-liners).
- Analyst questions must be concrete, forward-looking, and verifiable.
- Limitations must be genuine methodological constraints.
- When referencing visual evidence, name the exact chart (e.g. "differentiation_matrix", "quality_divergence_matrix").

HUMAN-VERIFIED FINANCIALS:
{human_block}

DIFFERENTIATION MATRIX (AI-scored factors, mean 1–10):
{_format_diff_df(diff_df)}

TOPIC COVERAGE DISTRIBUTION (% share of perception corpus):
{counts_block}

SENTIMENT BY TOPIC (weighted mean, ground_truth 2×):
{sentiment_block}

CONTRADICTIONS IDENTIFIED IN THE CORPUS:
{_format_contradictions(contradictions_df)}

TOP SIGNALS BY COMPANY (weighted: ground_truth 2×, up to 7 per company):
{_format_signals(top_signals)}

AVAILABLE CHARTS (reference these by name in your output):
{charts_block}

Return a JSON object matching this schema EXACTLY. No markdown fences, no explanation outside the JSON:
{{
  "research_question": "<one sentence restating the research question in your own words>",
  "executive_summary": "<3–4 sentences grounding the asymmetry in specific scores, margins, and evidence from the corpus above>",
  "differentiation_matrix": [
    {{
      "factor": "<factor name>",
      "catl_evidence": "<score or sentiment direction + 1 sentence of evidence>",
      "lges_evidence": "<score or sentiment direction + 1 sentence of evidence>",
      "implication": "<1 sentence on what the delta means for return sustainability>",
      "supporting_tags": "<topic cluster names>"
    }}
  ],
  "why_now": "<2–3 sentences on what specifically changed in 2025–26 to sharpen the divergence, grounded in the data>",
  "differentiation_takeaway": "<1 sentence on the single most significant factor delta with the number>",
  "contradiction_summary": "<2 sentences summarizing the strongest contradictions to the bull thesis with supporting evidence>",
  "risk_summary": "<2 sentences on the primary bear scenarios with specific triggers>",
  "strongest_supporting_evidence": [
    "<traceable evidence point 1 referencing corpus data or human inputs>",
    "<traceable evidence point 2>"
  ],
  "contrary_risk_evidence": [
    "<contrary or risk evidence point 1>",
    "<contrary or risk evidence point 2>"
  ],
  "analyst_questions": [
    "<specific verifiable forward-looking question 1>",
    "<question 2>",
    "<question 3>"
  ],
  "overall_confidence": "<X/10 — one sentence on what drives confidence and what limits it>",
  "limitations": [
    "<genuine methodological constraint 1>",
    "<genuine methodological constraint 2>",
    "<genuine methodological constraint 3>"
  ]
}}
"""


def _format_human_inputs(h) -> str:
    if h is None:
        return "  (no human inputs provided)"
    lines = [
        f"  CATL overseas gross margin: {h.catl_overseas_gross_margin_pct:.1f}%",
        f"  CATL domestic gross margin: {h.catl_domestic_gross_margin_pct:.1f}%",
        f"  LGES operating margin ex-IRA: {h.lges_q1_operating_margin_ex_ira_pct:.1f}%",
        f"  ROIC shock delta: {h.roic_shock_delta_bps} bps",
        f"  Shock scenario: {h.shock_scenario}",
        f"  CATL execution edge: {h.catl_execution_edge}",
        f"  LGES execution risk: {h.lges_execution_risk}",
    ]
    return "\n".join(lines)


def _format_diff_df(df: pd.DataFrame) -> str:
    if df.empty:
        return "  (no differentiation data available)"
    lines = ["  factor | CATL | LGES | delta"]
    for _, row in df.iterrows():
        lines.append(f"  {row['factor']} | {row['CATL']} | {row['LGES']} | {row['delta']}")
    return "\n".join(lines)


def _format_contradictions(df: pd.DataFrame) -> str:
    if df.empty:
        return "  (no contradictions flagged)"
    lines = []
    for _, row in df.iterrows():
        reason = row.get("contradiction_reason", "")
        lines.append(f"  [{row['company']}] {row['claim_summary']} — {reason}")
    return "\n".join(lines)


def _format_signals(signals: dict[str, list[dict]]) -> str:
    lines = []
    for company, sigs in signals.items():
        lines.append(f"  {company}:")
        for sig in sigs[:7]:
            summary = sig.get("claim_summary") or sig.get("summary", "")
            topic = sig.get("topic_cluster", "")
            stream = sig.get("stream", "")
            score = sig.get("sentiment_score")
            score_str = f" (score: {score:.1f})" if score is not None else ""
            tag_str = f" [{stream}/{topic}]" if stream or topic else ""
            lines.append(f"    -{tag_str}{score_str} {summary}")
    return "\n".join(lines) if lines else "  (no signals)"


def _format_topic_counts(df: pd.DataFrame | None) -> str:
    if df is None or df.empty:
        return "  (no topic count data available)"
    lines = ["  company | topic | share_%"]
    for _, row in df.iterrows():
        lines.append(f"  {row['company']} | {row['topic_cluster']} | {row['count']:.1f}%")
    return "\n".join(lines)


def _format_sentiment(df: pd.DataFrame | None) -> str:
    if df is None or df.empty:
        return "  (no sentiment data available)"
    col = "weighted_mean_sentiment" if "weighted_mean_sentiment" in df.columns else "mean_sentiment"
    lines = ["  company | topic | sentiment"]
    for _, row in df.iterrows():
        lines.append(f"  {row['company']} | {row['topic_cluster']} | {row[col]:.2f}")
    return "\n".join(lines)


def _format_chart_names(chart_paths: dict | None) -> str:
    if not chart_paths:
        return "  (no chart paths provided)"
    lines = []
    for name, path in chart_paths.items():
        import os
        lines.append(f"  {name}: {os.path.basename(path)}")
    return "\n".join(lines)
