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
    ai = deck_input.ai_signals
    specs: list[SlideSpec] = []

    # Slide 1: Title
    specs.append(SlideSpec(
        slide_type=SlideType.TITLE,
        title="CATL vs LGES: Globalization Quality Divergence",
        body="UBS Finance Challenge 2026 — Pair Trade Analysis",
    ))

    # Slide 2: Thesis — factual framing only
    specs.append(SlideSpec(
        slide_type=SlideType.THESIS,
        title="Observed Divergence: Globalization Quality",
        body=(
            "CATL's overseas expansion is organic and margin-accretive (greenfield, LFP volume). "
            "LGES's US presence is structurally dependent on IRA policy arbitrage. "
            f"Perception and fundamental data show divergent quality: CATL overseas margin {h.catl_overseas_gross_margin_pct:.1f}% "
            f"vs LGES ex-IRA operating margin {h.lges_q1_operating_margin_ex_ira_pct:.1f}%. "
            "Human analyst interprets implications for return sustainability."
        ),
    ))

    # Slide 3: Quality Divergence Matrix chart
    specs.append(SlideSpec(
        slide_type=SlideType.CHART,
        title="Quality Divergence Matrix: Narrative Evidence",
        body=(
            "Normalized topic coverage share per company (perception stream). "
            f"Human-verified: CATL overseas gross margin {h.catl_overseas_gross_margin_pct:.1f}% "
            f"vs domestic {h.catl_domestic_gross_margin_pct:.1f}% — consistent with Organic_Scale perception weight."
        ),
        chart_path=deck_input.divergence_matrix_path,
    ))

    # Slide 4: Trend Inflection chart
    specs.append(SlideSpec(
        slide_type=SlideType.CHART,
        title="Sentiment Divergence by Topic",
        body=(
            "Mean sentiment score (1–10) per topic cluster, grouped by company. "
            f"Human-verified: LGES ex-IRA operating margin {h.lges_q1_operating_margin_ex_ira_pct:.1f}% "
            "— consistent with Subsidy_Dependence low-sentiment signal."
        ),
        chart_path=deck_input.trend_inflection_path,
    ))

    # Slides 5-6: Top AI Signals per company
    for company in ["CATL", "LGES"]:
        signals = ai.get(company, [])
        bullets = "\n".join(
            f"• [{s['topic_cluster']}] {s['summary']}" for s in signals[:3]
        )
        specs.append(SlideSpec(
            slide_type=SlideType.AI_SIGNAL,
            title=f"Top Perception Signals: {company}",
            body=bullets,
        ))

    # Slide 7: Margin Comparison Table
    specs.append(SlideSpec(
        slide_type=SlideType.FUNDAMENTALS,
        title="Margin Reality: AI Signal vs Fundamental Data",
        body="Human-verified financial data cross-checked against perception narratives.",
        table_rows=[
            ["Metric", "CATL", "LGES"],
            ["Overseas Gross Margin", f"{h.catl_overseas_gross_margin_pct:.1f}%", "N/A"],
            ["Domestic Gross Margin", f"{h.catl_domestic_gross_margin_pct:.1f}%", "N/A"],
            ["Operating Margin ex-IRA", "N/A", f"{h.lges_q1_operating_margin_ex_ira_pct:.1f}%"],
        ],
    ))

    # Slide 8: Execution Edge
    specs.append(SlideSpec(
        slide_type=SlideType.FUNDAMENTALS,
        title="Execution Edge vs Execution Risk",
        body=(
            f"CATL: {h.catl_execution_edge}\n\n"
            f"LGES: {h.lges_execution_risk}"
        ),
    ))

    # Slides 9-14: Fundamentals (placeholder for analyst expansion)
    for i in range(6):
        specs.append(SlideSpec(
            slide_type=SlideType.FUNDAMENTALS,
            title=f"Fundamental Analysis {i + 1}",
            body="[Analyst-populated slide — insert DCF assumptions, capex schedules, or channel check data here.]",
        ))

    # Slides 15-18: Counterfactuals
    specs.append(SlideSpec(
        slide_type=SlideType.COUNTERFACTUAL,
        title="Downside Scenario: IRA Credit Cap",
        body=(
            f"Shock: {h.shock_scenario}\n"
            f"Estimated ROIC impact: -{h.roic_shock_delta_bps} bps for LGES.\n"
            "CATL exposure: limited — organic margin not IRA-derived."
        ),
    ))
    for i in range(3):
        specs.append(SlideSpec(
            slide_type=SlideType.COUNTERFACTUAL,
            title=f"Counterfactual Scenario {i + 2}",
            body="[Analyst-populated — insert specific basis-point impact tied to named risk scenario.]",
        ))

    # Slides 19-20: Disclosures
    specs.append(SlideSpec(
        slide_type=SlideType.DISCLOSURE,
        title="AI Methodology Disclosure",
        body=(
            "The AI Analyst module was used strictly to scale the processing of unstructured perception data "
            "beyond manual capacity. It did NOT build valuation models, conduct channel checks, or generate "
            "fundamental forecasts. The AI surfaces narrative divergence; human analysts verified the "
            "sustainability of returns.\n\n"
            "LLM: Claude 3.5 Sonnet (Anthropic). Tagged fields: sentiment_score, direction, topic_cluster, "
            "geo_exposure, summary. All summaries are direct factual extractions — no AI opinions or conclusions."
        ),
    ))
    specs.append(SlideSpec(
        slide_type=SlideType.DISCLOSURE,
        title="Limitations & Data Sources",
        body=(
            "• Perception stream: Bloomberg and Moomoo news URLs (12-24 month window).\n"
            "• Ground Truth stream: Investor Relations documents (earnings transcripts, capex filings).\n"
            "• Sentiment scores are relative within this dataset — not absolute market signals.\n"
            "• No channel checks, primary research, or equity research model access was used by the AI module."
        ),
    ))

    assert len(specs) <= 20, f"Deck exceeds 20 slides: {len(specs)}"
    return specs
