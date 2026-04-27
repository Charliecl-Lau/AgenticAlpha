import pandas as pd


def build_synthesis_prompt(
    diff_df: pd.DataFrame,
    contradictions_df: pd.DataFrame,
    top_signals: dict[str, list[dict]],
) -> str:
    return f"""You are a quantitative research analyst synthesizing structured AI-generated evidence about CATL and LGES for an institutional equity research report.

RULES:
- Do NOT make investment recommendations (no buy/sell/hold).
- Do NOT infer facts not supported by the evidence below.
- Summarize asymmetry only. Be specific and precise.
- Analyst questions must be concrete, verifiable, and forward-looking.
- Limitations must be genuine methodological constraints, not generic disclaimers.

DIFFERENTIATION MATRIX (mean scores 1–10):
{_format_diff_df(diff_df)}

CONTRADICTIONS IDENTIFIED:
{_format_contradictions(contradictions_df)}

TOP SIGNALS BY COMPANY:
{_format_signals(top_signals)}

Return a JSON object matching this schema exactly. No markdown fences, no explanation:
{{
  "executive_summary": "<2-3 sentences on the key asymmetry>",
  "why_now": "<1-2 sentences on what changed in 2025-26 to make this pair trade relevant>",
  "differentiation_takeaway": "<1 sentence on the most significant factor delta>",
  "contradiction_summary": "<1-2 sentences summarizing challenges to the bull thesis>",
  "risk_summary": "<1-2 sentences on the primary bear scenarios>",
  "analyst_questions": ["<specific verifiable question 1>", "<question 2>", "<question 3>"],
  "limitations": ["<genuine constraint 1>", "<genuine constraint 2>"]
}}
"""


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
        for sig in sigs[:3]:
            summary = sig.get("claim_summary") or sig.get("summary", "")
            lines.append(f"    - {summary}")
    return "\n".join(lines) if lines else "  (no signals)"
