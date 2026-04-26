import json
import pandas as pd
from src.human_layer.schema import HumanInputs
from src.human_layer.merger import merge_inputs, DeckInput

_DIVERGENCE_PATH = "output/charts/quality_divergence_matrix.png"
_INFLECTION_PATH = "output/charts/trend_inflection.png"


def _human_inputs():
    return HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%, IRA credits capped.",
        catl_execution_edge="Hungary 50 GWh on schedule.",
        lges_execution_risk="Ultium delayed 9 months.",
    )


def _tag_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 9, "summary": "CATL at 50 GWh.", "stream": "perception"},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 3, "summary": "LGES IRA-dependent.", "stream": "perception"},
    ])


def test_merge_inputs_returns_deck_input():
    result = merge_inputs(_human_inputs(), _tag_df(), _DIVERGENCE_PATH, _INFLECTION_PATH)
    assert isinstance(result, DeckInput)


def test_deck_input_contains_human_data():
    result = merge_inputs(_human_inputs(), _tag_df(), _DIVERGENCE_PATH, _INFLECTION_PATH)
    assert result.human.catl_overseas_gross_margin_pct == 31.4
    assert result.human.roic_shock_delta_bps == 180


def test_deck_input_contains_ai_signals():
    result = merge_inputs(_human_inputs(), _tag_df(), _DIVERGENCE_PATH, _INFLECTION_PATH)
    assert "CATL" in result.ai_signals
    assert len(result.ai_signals["CATL"]) >= 1


def test_deck_input_carries_chart_paths():
    result = merge_inputs(_human_inputs(), _tag_df(), _DIVERGENCE_PATH, _INFLECTION_PATH)
    assert result.divergence_matrix_path == _DIVERGENCE_PATH
    assert result.trend_inflection_path == _INFLECTION_PATH


def test_deck_input_is_json_serialisable(tmp_path):
    result = merge_inputs(_human_inputs(), _tag_df(), _DIVERGENCE_PATH, _INFLECTION_PATH)
    json_str = json.dumps(result.to_dict())
    parsed = json.loads(json_str)
    assert "human" in parsed
    assert "ai_signals" in parsed
    assert "divergence_matrix_path" in parsed
    assert "trend_inflection_path" in parsed
