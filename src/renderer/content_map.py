from dataclasses import dataclass, field
from enum import Enum
from src.human_layer.merger import DeckInput


class SlideType(str, Enum):
    TITLE = "title"
    THESIS = "thesis"
    AI_SIGNAL = "ai_signal"
    FUNDAMENTALS = "fundamentals"
    CHART = "chart"
    COUNTERFACTUAL = "counterfactual"
    DISCLOSURE = "disclosure"


@dataclass
class SlideSpec:
    slide_type: SlideType
    title: str = ""
    body: str = ""
    chart_path: str = ""
    table_rows: list[list[str]] = field(default_factory=list)


def build_slide_specs(deck_input: DeckInput) -> list[SlideSpec]:
    h = deck_input.human
    s = deck_input.synthesis
    signals = deck_input.ai_signals

    catl_body = "\n".join(
        f"• {sig.get('claim_summary', sig.get('summary', ''))}"
        for sig in signals.get("CATL", [])
    ) or "• No CATL signals tagged."

    lges_body = "\n".join(
        f"• {sig.get('claim_summary', sig.get('summary', ''))}"
        for sig in signals.get("LGES", [])
    ) or "• No LGES signals tagged."

    analyst_questions_body = (
        "\n".join(f"• {q}" for q in s.analyst_questions)
        if s else "• [Add analyst questions here]"
    )
    limitations_body = (
        "\n".join(f"• {lim}" for lim in s.limitations)
        if s else "• Evidence limited to public IR disclosures and news media."
    )
    executive_summary = s.executive_summary if s else ""
    why_now_body = (
        f"{s.why_now}\n\nTakeaway: {h.why_now_takeaway}\nFollow-up: {h.why_now_followup}"
        if s else h.why_now_takeaway
    )
    diff_body = (
        f"{s.differentiation_takeaway}\n\nTakeaway: {h.differentiation_takeaway}\nFollow-up: {h.differentiation_followup}"
        if s else h.differentiation_takeaway
    )
    contra_body = (
        f"{s.contradiction_summary}\n\nTakeaway: {h.contradiction_takeaway}\nFollow-up: {h.contradiction_followup}"
        if s else h.contradiction_takeaway
    )

    specs = [
        SlideSpec(                                                              # 1
            slide_type=SlideType.TITLE,
            title="CATL vs LGES: Globalization Quality Divergence",
            body="AI-Assisted Institutional Research | AgenticAlpha v2",
        ),
        SlideSpec(                                                              # 2
            slide_type=SlideType.THESIS,
            title="Pair Thesis: Quality of Globalization",
            body=(
                f"CATL overseas gross margin: {h.catl_overseas_gross_margin_pct:.1f}%\n"
                f"LGES operating margin ex-IRA: {h.lges_q1_operating_margin_ex_ira_pct:.1f}%\n\n"
                f"{executive_summary}"
            ),
        ),
        SlideSpec(                                                              # 3
            slide_type=SlideType.AI_SIGNAL,
            title="AI Workflow: Evidence Engine Architecture",
            body=(
                "Pipeline: Ingestion → Rich Tagger → Evidence Engine → Synthesis\n"
                "Human layer: Analyst inputs + takeaways layered on top\n"
                "All LLM outputs validated against structured schemas.\n"
                "No valuation analysis. No trade recommendations."
            ),
        ),
        SlideSpec(                                                              # 4
            slide_type=SlideType.CHART,
            title="Differentiation Matrix: Factor Scores (1–10)",
            body=diff_body,
            chart_path=deck_input.differentiation_matrix_path,
        ),
        SlideSpec(                                                              # 5
            slide_type=SlideType.CHART,
            title="Why Now: Topic Frequency Timeline",
            body=why_now_body,
            chart_path=deck_input.why_now_timeline_path,
        ),
        SlideSpec(                                                              # 6
            slide_type=SlideType.CHART,
            title="Contradiction Scanner: Evidence Challenging Thesis",
            body=contra_body,
            chart_path=deck_input.contradictions_path,
        ),
        SlideSpec(                                                              # 7
            slide_type=SlideType.CHART,
            title="Evidence Scale: Document Attribution by Stream",
            body="Corroboration across perception, ground truth, policy, and operations streams.",
            chart_path=deck_input.evidence_scale_path,
        ),
        SlideSpec(                                                              # 8
            slide_type=SlideType.AI_SIGNAL,
            title="Top Perception Signals: CATL",
            body=catl_body,
        ),
        SlideSpec(                                                              # 9
            slide_type=SlideType.AI_SIGNAL,
            title="Top Perception Signals: LGES",
            body=lges_body,
        ),
        SlideSpec(                                                              # 10
            slide_type=SlideType.FUNDAMENTALS,
            title="Margin Bridge: AI Signal vs Fundamental Data",
            table_rows=[
                ["Metric", "CATL", "LGES"],
                ["Overseas Gross Margin", f"{h.catl_overseas_gross_margin_pct:.1f}%", "N/A"],
                ["Domestic Gross Margin", f"{h.catl_domestic_gross_margin_pct:.1f}%", "N/A"],
                ["Operating Margin ex-IRA", "N/A", f"{h.lges_q1_operating_margin_ex_ira_pct:.1f}%"],
            ],
        ),
        SlideSpec(                                                              # 11
            slide_type=SlideType.CHART,
            title="Risk Tree: Likelihood × Impact Matrix",
            body="Policy risk, execution risk, capex mismatch, and ROIC deterioration.",
            chart_path=deck_input.risk_tree_path,
        ),
        SlideSpec(                                                              # 12
            slide_type=SlideType.COUNTERFACTUAL,
            title="Downside Scenario: IRA Credit Cap",
            body=(
                f"Scenario: {h.shock_scenario}\n"
                f"ROIC impact: {h.roic_shock_delta_bps:+d} bps\n"
                f"Execution risk: {h.lges_execution_risk}"
            ),
        ),
        SlideSpec(                                                              # 13
            slide_type=SlideType.AI_SIGNAL,
            title="Analyst Questions for Follow-Up",
            body=analyst_questions_body,
        ),
        SlideSpec(                                                              # 14
            slide_type=SlideType.DISCLOSURE,
            title="Methodology Limitations",
            body=limitations_body,
        ),
        SlideSpec(                                                              # 15
            slide_type=SlideType.DISCLOSURE,
            title="AI Methodology Disclosure",
            body=(
                "Evidence collected via automated ingestion from public sources.\n"
                "Tags generated by LLM (Google Gemini) with schema validation.\n"
                "Synthesis generated by Claude (Anthropic) — one call, no recommendations.\n"
                "No valuation analysis, channel checks, or non-public information."
            ),
        ),
    ]

    assert len(specs) <= 20, f"Slide count {len(specs)} exceeds maximum of 20"
    return specs
