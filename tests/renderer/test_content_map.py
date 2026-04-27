import pytest
from src.renderer.content_map import build_slide_specs, SlideSpec, SlideType
from src.human_layer.schema import HumanInputs
from src.human_layer.merger import DeckInput


def _make_human():
    return HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=28.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=-150,
        shock_scenario="IRA credit cap reduces LGES ROIC by 150bps",
        catl_execution_edge="CATL commissioned 4 plants on schedule",
        lges_execution_risk="LGES Hungary delayed 6 months",
        why_now_takeaway="Divergence accelerated 2025-26",
        why_now_followup="Verify Hungary utilization",
        differentiation_takeaway="CATL 2.5x LGES on execution",
        differentiation_followup="Check JV structures",
        contradiction_takeaway="IRA risk underpriced",
        contradiction_followup="Model IRA cliff scenario",
    )


class FakeSynthesis:
    executive_summary = "CATL leads on globalization."
    why_now = "Divergence accelerated in 2025Q4."
    differentiation_takeaway = "Execution gap is 4pts."
    contradiction_summary = "IRA dependency challenged by 3 docs."
    risk_summary = "Policy reversal is primary bear case."
    analyst_questions = ["What is LGES Hungary utilization at IRA cap?"]
    limitations = ["Evidence limited to public disclosures."]


def _deck_input(synthesis=None):
    return DeckInput(
        human=_make_human(),
        ai_signals={
            "CATL": [{"claim_summary": "Strong."}],
            "LGES": [{"claim_summary": "Weak."}],
        },
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
        differentiation_matrix_path="output/charts/differentiation_matrix.png",
        why_now_timeline_path="output/charts/why_now_timeline.png",
        contradictions_path="output/charts/contradictions.png",
        risk_tree_path="output/charts/risk_tree.png",
        evidence_scale_path="output/charts/evidence_scale.png",
        synthesis=synthesis,
    )


def test_build_slide_specs_returns_list_of_slide_specs():
    specs = build_slide_specs(_deck_input())
    assert isinstance(specs, list)
    assert all(isinstance(s, SlideSpec) for s in specs)


def test_slide_count_is_15():
    specs = build_slide_specs(_deck_input())
    assert len(specs) == 15


def test_differentiation_matrix_slide_present():
    specs = build_slide_specs(_deck_input())
    assert any("Differentiation" in s.title for s in specs)


def test_why_now_slide_present():
    specs = build_slide_specs(_deck_input())
    assert any("Why Now" in s.title for s in specs)


def test_contradiction_scanner_slide_present():
    specs = build_slide_specs(_deck_input())
    assert any("Contradiction" in s.title for s in specs)


def test_risk_tree_slide_present():
    specs = build_slide_specs(_deck_input())
    assert any("Risk" in s.title for s in specs)


def test_analyst_questions_slide_uses_synthesis():
    specs = build_slide_specs(_deck_input(synthesis=FakeSynthesis()))
    q_slide = next((s for s in specs if "Analyst" in s.title and "Question" in s.title), None)
    assert q_slide is not None
    assert "Hungary" in q_slide.body


def test_no_prohibited_language():
    specs = build_slide_specs(_deck_input())
    forbidden = {"buy", "sell", "hold", "we believe", "we recommend", "outperform", "underperform"}
    for spec in specs:
        text = (spec.title + " " + spec.body).lower()
        for word in forbidden:
            assert word not in text, f"Prohibited '{word}' in slide '{spec.title}'"


def test_disclosure_slide_present():
    specs = build_slide_specs(_deck_input())
    assert any("Disclosure" in s.title or "Methodology" in s.title for s in specs)


def test_build_slide_specs_includes_disclosure_slides():
    specs = build_slide_specs(_deck_input())
    types = [s.slide_type for s in specs]
    assert SlideType.DISCLOSURE in types


def test_build_slide_specs_includes_counterfactual_slides():
    specs = build_slide_specs(_deck_input())
    types = [s.slide_type for s in specs]
    assert SlideType.COUNTERFACTUAL in types


def test_prohibited_language_check_catches_analyst_passthrough():
    human = _make_human()
    tainted = DeckInput(
        human=human,
        ai_signals={},
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
        differentiation_matrix_path="output/charts/differentiation_matrix.png",
        why_now_timeline_path="output/charts/why_now_timeline.png",
        contradictions_path="output/charts/contradictions.png",
        risk_tree_path="output/charts/risk_tree.png",
        evidence_scale_path="output/charts/evidence_scale.png",
    )
    object.__setattr__(tainted.human, "shock_scenario", "We believe this implies downside risk.")
    specs = build_slide_specs(tainted)
    prohibited = ["we believe", "implies downside"]
    found = []
    for spec in specs:
        table_text = " ".join(c for row in spec.table_rows for c in row)
        full_text = " ".join([spec.title or "", spec.body or "", table_text]).lower()
        for phrase in prohibited:
            if phrase in full_text:
                found.append(phrase)
    assert len(found) > 0, "Expected prohibited phrases to be detectable in slide content"
