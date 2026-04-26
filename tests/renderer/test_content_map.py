import pytest
from src.renderer.content_map import build_slide_specs, SlideSpec, SlideType
from src.human_layer.schema import HumanInputs
from src.human_layer.merger import DeckInput


def _deck_input():
    human = HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%, IRA capped.",
        catl_execution_edge="Hungary on schedule.",
        lges_execution_risk="Ultium delayed 9 months.",
    )
    ai_signals = {
        "CATL": [{"topic_cluster": "Organic_Scale_vs_Export", "sentiment_score": 9,
                  "summary": "CATL at 50 GWh.", "stream": "perception"}],
        "LGES": [{"topic_cluster": "Subsidy_Dependence", "sentiment_score": 3,
                  "summary": "LGES IRA-dependent.", "stream": "perception"}],
    }
    return DeckInput(
        human=human,
        ai_signals=ai_signals,
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
    )


def test_build_slide_specs_returns_list_of_slide_specs():
    specs = build_slide_specs(_deck_input())
    assert isinstance(specs, list)
    assert all(isinstance(s, SlideSpec) for s in specs)


def test_build_slide_specs_max_20_slides():
    specs = build_slide_specs(_deck_input())
    assert len(specs) <= 20


def test_build_slide_specs_includes_disclosure_slides():
    specs = build_slide_specs(_deck_input())
    types = [s.slide_type for s in specs]
    assert SlideType.DISCLOSURE in types


def test_build_slide_specs_includes_counterfactual_slides():
    specs = build_slide_specs(_deck_input())
    types = [s.slide_type for s in specs]
    assert SlideType.COUNTERFACTUAL in types


def test_build_slide_specs_has_no_prohibited_language():
    specs = build_slide_specs(_deck_input())
    prohibited = [
        "we believe", "we conclude", "investment advice",
        "outperform", "underperform", "buy", "sell",
        "target price", "price target", "recommend",
        "not fully priced", "suggests upside", "implies downside",
    ]
    for spec in specs:
        table_text = " ".join(c for row in spec.table_rows for c in row)
        full_text = " ".join([spec.title or "", spec.body or "", table_text]).lower()
        for phrase in prohibited:
            assert phrase not in full_text, f"Prohibited phrase '{phrase}' found in slide: {spec.title}"


def test_prohibited_language_check_catches_analyst_passthrough():
    """Verify the compliance scanner catches prohibited phrases interpolated from analyst fields."""
    from pydantic import ValidationError
    from src.human_layer.schema import HumanInputs
    from src.human_layer.merger import DeckInput

    human = HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%, IRA capped.",
        catl_execution_edge="Hungary on schedule.",
        lges_execution_risk="Ultium delayed 9 months.",
    )
    tainted = DeckInput(
        human=human,
        ai_signals={},
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
    )
    # Manually override a field with a tainted value to simulate analyst error
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
