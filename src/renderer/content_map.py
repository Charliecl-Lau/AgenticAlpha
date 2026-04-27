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
    if deck_input.analyst_brief:
        limitations_body = _extract_brief_section(deck_input.analyst_brief, "## Limitations & Bias")
    elif s:
        limitations_body = "\n".join(f"• {lim}" for lim in s.limitations)
    else:
        limitations_body = "• Evidence limited to public IR disclosures and news media."
    executive_summary = s.executive_summary if s else ""

    catl_m = h.catl_overseas_gross_margin_pct
    catl_dom = h.catl_domestic_gross_margin_pct
    lges_m = h.lges_q1_operating_margin_ex_ira_pct

    diff_body = (
        f"AI-tagged perception shows CATL emphasis on execution-led organic globalization "
        f"(aligns with human-verified {catl_m:.1f}% overseas gross margin vs. {catl_dom:.1f}% domestic). "
        f"LGES perception skewed toward subsidy dependence "
        f"(aligns with weak {lges_m:.1f}% ex-IRA operating margin).\n\n"
        f"Takeaway: {h.differentiation_takeaway}\n"
        f"Follow-up: {h.differentiation_followup}"
    )

    diff_table_rows: list[list[str]] = []
    if s and s.differentiation_matrix:
        diff_table_rows = [["Factor", "CATL Evidence", "LGES Evidence", "Implication", "Supporting Tags"]]
        for row in s.differentiation_matrix:
            diff_table_rows.append([
                row.factor,
                row.catl_evidence,
                row.lges_evidence,
                row.implication,
                row.supporting_tags,
            ])

    why_now_body = (
        (f"{s.why_now}\n\n" if s else "")
        + f"Takeaway: {h.why_now_takeaway}\n"
        f"Follow-up: {h.why_now_followup}"
    )

    contra_body = (
        (f"{s.contradiction_summary}\n\n" if s else "")
        + f"Takeaway: {h.contradiction_takeaway}\n"
        f"Follow-up: {h.contradiction_followup}"
    )

    evidence_caption = (
        "AI processed perception (news/analyst) and ground_truth (IR/earnings) documents "
        "— evidence volume and corroboration scale beyond manual analysis capacity. "
        "Confidence scores reflect structured schema validation at each stage."
    )

    sentiment_caption = (
        f"CATL sentiment consistently higher on Organic Scale and Capex Execution topics "
        f"— aligning with human-verified {catl_m:.1f}% overseas gross margin. "
        f"LGES lower sentiment on Subsidy Dependence confirms vulnerability ex-IRA ({lges_m:.1f}% operating margin)."
    )

    risk_caption = (
        f"LGES disproportionately exposed to IRA policy risk vs. CATL. "
        f"CATL execution edge ({h.catl_execution_edge[:80]}…) limits ramp delay risk. "
        f"ROIC shock scenario: {h.roic_shock_delta_bps:+d} bps under IRA cap."
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
                f"CATL overseas gross margin: {catl_m:.1f}% vs domestic {catl_dom:.1f}%\n"
                f"LGES operating margin ex-IRA: {lges_m:.1f}%\n\n"
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
        SlideSpec(                                                              # 4  Evidence Attribution (prove scale first)
            slide_type=SlideType.CHART,
            title="Evidence Scale: AI Processed Beyond Manual Capacity",
            body=evidence_caption,
            chart_path=deck_input.evidence_scale_path,
        ),
        SlideSpec(                                                              # 5  Differentiation Matrix (core asymmetry)
            slide_type=SlideType.CHART,
            title="Differentiation Matrix: Factor Scores (1–10, ordered by delta)",
            body=diff_body,
            chart_path=deck_input.differentiation_matrix_path,
            table_rows=diff_table_rows,
        ),
        SlideSpec(                                                              # 6  Sentiment Divergence by Topic
            slide_type=SlideType.CHART,
            title="Signal Quality: Sentiment Divergence by Topic",
            body=sentiment_caption,
            chart_path=deck_input.trend_inflection_path,
        ),
        SlideSpec(                                                              # 7  Risk Counterfactual Heatmap
            slide_type=SlideType.CHART,
            title="Risk Counterfactual Heatmap: Scenario Impact on Pair",
            body=risk_caption,
            chart_path=deck_input.risk_tree_path,
        ),
        SlideSpec(                                                              # 8  Why Now Timeline
            slide_type=SlideType.CHART,
            title="Why Now: Coverage Momentum Divergence 2025–26",
            body=why_now_body,
            chart_path=deck_input.why_now_timeline_path,
        ),
        SlideSpec(                                                              # 9  Contradiction Scanner
            slide_type=SlideType.CHART,
            title="Contradiction Scanner: Evidence Challenging Thesis",
            body=contra_body,
            chart_path=deck_input.contradictions_path,
        ),
        SlideSpec(                                                              # 10  AI Evidence Quality
            slide_type=SlideType.AI_SIGNAL,
            title="AI Evidence Quality: Supporting vs Contrary",
            body=(
                (f"Confidence: {s.overall_confidence}\n\n" if s else "")
                + "Supporting evidence and contrary risks drawn directly from AI-processed corpus."
            ),
            table_rows=(
                [["Supporting Evidence", "Contrary / Risk Evidence"]]
                + [
                    [
                        sup,
                        con if i < len(s.contrary_risk_evidence) else "",
                    ]
                    for i, (sup, con) in enumerate(
                        zip(
                            s.strongest_supporting_evidence,
                            s.contrary_risk_evidence + [""] * len(s.strongest_supporting_evidence),
                        )
                    )
                ]
                if s else []
            ),
        ),
        SlideSpec(                                                              # 11
            slide_type=SlideType.AI_SIGNAL,
            title="Top Perception Signals: CATL",
            body=catl_body,
        ),
        SlideSpec(                                                              # 12
            slide_type=SlideType.AI_SIGNAL,
            title="Top Perception Signals: LGES",
            body=lges_body,
        ),
        SlideSpec(                                                              # 12
            slide_type=SlideType.FUNDAMENTALS,
            title="Margin Bridge: AI Signal vs Fundamental Data",
            table_rows=[
                ["Metric", "CATL", "LGES"],
                ["Overseas Gross Margin", f"{catl_m:.1f}%", "N/A"],
                ["Domestic Gross Margin", f"{catl_dom:.1f}%", "N/A"],
                ["Operating Margin ex-IRA", "N/A", f"{lges_m:.1f}%"],
                ["Execution Edge", h.catl_execution_edge[:60] + "…", "—"],
                ["Execution Risk", "—", h.lges_execution_risk[:60] + "…"],
            ],
        ),
        SlideSpec(                                                              # 13
            slide_type=SlideType.COUNTERFACTUAL,
            title="Downside Scenario: IRA Credit Cap",
            body=(
                f"Scenario: {h.shock_scenario}\n"
                f"ROIC impact: {h.roic_shock_delta_bps:+d} bps\n"
                f"Execution risk: {h.lges_execution_risk}"
            ),
        ),
        SlideSpec(                                                              # 14
            slide_type=SlideType.AI_SIGNAL,
            title="Analyst Questions for Follow-Up",
            body=analyst_questions_body,
        ),
        SlideSpec(                                                              # 15
            slide_type=SlideType.DISCLOSURE,
            title="Methodology Limitations",
            body=limitations_body,
        ),
        SlideSpec(                                                              # 16
            slide_type=SlideType.DISCLOSURE,
            title="AI Methodology Disclosure",
            body=(
                "Evidence collected via automated ingestion from public sources (news, IR filings).\n"
                "Tags generated by Google Gemma 4 LLM with Pydantic schema validation.\n"
                "Synthesis generated by Google Gemma 4 — one structured call, no recommendations.\n"
                "No valuation analysis, channel checks, or non-public information used.\n"
                "All outputs are evidence for human judgment — not investment conclusions."
            ),
        ),
    ]

    assert len(specs) <= 20, f"Slide count {len(specs)} exceeds maximum of 20"
    return specs


def _extract_brief_section(brief: str, heading: str) -> str:
    """Return the text body of a markdown section from analyst_brief, up to the next heading."""
    lines = brief.splitlines()
    in_section = False
    body_lines: list[str] = []
    for line in lines:
        if line.strip() == heading.strip():
            in_section = True
            continue
        if in_section:
            if line.startswith("## ") or line.startswith("# "):
                break
            body_lines.append(line)
    return "\n".join(body_lines).strip() or brief
