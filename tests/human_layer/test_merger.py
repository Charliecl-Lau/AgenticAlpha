import dataclasses
import pandas as pd
from src.human_layer.schema import HumanInputs
from src.human_layer.merger import merge_inputs, DeckInput

_DIVERGENCE_PATH = "output/charts/quality_divergence_matrix.png"
_INFLECTION_PATH = "output/charts/trend_inflection.png"
_DIFF_MATRIX_PATH = "output/charts/differentiation_matrix.png"
_WHY_NOW_PATH = "output/charts/why_now_timeline.png"
_CONTRADICTIONS_PATH = "output/charts/contradictions.png"
_RISK_TREE_PATH = "output/charts/risk_tree.png"
_EVIDENCE_SCALE_PATH = "output/charts/evidence_scale.png"


def _human_inputs():
    return HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%, IRA credits capped.",
        catl_execution_edge="Hungary 50 GWh on schedule.",
        lges_execution_risk="Ultium delayed 9 months.",
        why_now_takeaway="Operational divergence accelerated in 2025-26",
        why_now_followup="Verify Hungary utilization assumptions",
        differentiation_takeaway="CATL execution consistently 2x LGES on our scoring",
        differentiation_followup="Check if CATL localization data captures JV structures",
        contradiction_takeaway="IRA exposure risk more acute than consensus models",
        contradiction_followup="Model IRA cliff scenario for LGES 2026 guidance",
    )


def _tag_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 9, "summary": "CATL at 50 GWh.", "stream": "perception"},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 3, "summary": "LGES IRA-dependent.", "stream": "perception"},
    ])


def _merge(**kwargs):
    defaults = dict(
        human=_human_inputs(),
        tag_df=_tag_df(),
        divergence_matrix_path=_DIVERGENCE_PATH,
        trend_inflection_path=_INFLECTION_PATH,
        differentiation_matrix_path=_DIFF_MATRIX_PATH,
        why_now_timeline_path=_WHY_NOW_PATH,
        contradictions_path=_CONTRADICTIONS_PATH,
        risk_tree_path=_RISK_TREE_PATH,
        evidence_scale_path=_EVIDENCE_SCALE_PATH,
    )
    defaults.update(kwargs)
    return merge_inputs(**defaults)


# ---------------------------------------------------------------------------
# Existing tests (updated for new signature)
# ---------------------------------------------------------------------------

def test_merge_inputs_returns_deck_input():
    result = _merge()
    assert isinstance(result, DeckInput)


def test_deck_input_contains_human_data():
    result = _merge()
    assert result.human.catl_overseas_gross_margin_pct == 31.4
    assert result.human.roic_shock_delta_bps == 180


def test_deck_input_contains_ai_signals():
    result = _merge()
    assert "CATL" in result.ai_signals
    assert len(result.ai_signals["CATL"]) >= 1


def test_deck_input_carries_chart_paths():
    result = _merge()
    assert result.divergence_matrix_path == _DIVERGENCE_PATH
    assert result.trend_inflection_path == _INFLECTION_PATH
    assert result.differentiation_matrix_path == _DIFF_MATRIX_PATH
    assert result.why_now_timeline_path == _WHY_NOW_PATH
    assert result.contradictions_path == _CONTRADICTIONS_PATH
    assert result.risk_tree_path == _RISK_TREE_PATH
    assert result.evidence_scale_path == _EVIDENCE_SCALE_PATH


# ---------------------------------------------------------------------------
# New tests for expanded DeckInput
# ---------------------------------------------------------------------------

def test_deck_input_has_five_new_chart_path_fields():
    fields = {f.name for f in dataclasses.fields(DeckInput)}
    assert "differentiation_matrix_path" in fields
    assert "why_now_timeline_path" in fields
    assert "contradictions_path" in fields
    assert "risk_tree_path" in fields
    assert "evidence_scale_path" in fields


def test_deck_input_has_synthesis_field():
    fields = {f.name for f in dataclasses.fields(DeckInput)}
    assert "synthesis" in fields


def test_deck_input_synthesis_defaults_to_none():
    result = _merge()
    assert result.synthesis is None


def test_deck_input_synthesis_can_be_set():
    result = _merge(synthesis={"key": "value"})
    assert result.synthesis == {"key": "value"}
