# tests/renderer/test_cli.py
from unittest.mock import patch
from src.renderer.cli import run_renderer
from src.human_layer.merger import DeckInput
from src.human_layer.schema import HumanInputs


def _deck_input():
    human = HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%.",
        catl_execution_edge="Hungary on schedule.",
        lges_execution_risk="Ultium delayed.",
    )
    return DeckInput(
        human=human,
        ai_signals={
            "CATL": [{"topic_cluster": "Organic_Scale_vs_Export", "sentiment_score": 9,
                      "summary": "CATL at 50 GWh.", "stream": "perception"}],
            "LGES": [{"topic_cluster": "Subsidy_Dependence", "sentiment_score": 3,
                      "summary": "LGES IRA-dependent.", "stream": "perception"}],
        },
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
    )


def test_run_renderer_calls_build_pptx(tmp_path):
    out_path = str(tmp_path / "deck.pptx")
    with patch("src.renderer.cli.build_pptx") as mock_build:
        run_renderer(_deck_input(), output_path=out_path)
    mock_build.assert_called_once()
    specs_arg = mock_build.call_args[0][0]
    assert len(specs_arg) <= 20


def test_run_renderer_passes_correct_output_path(tmp_path):
    out_path = str(tmp_path / "deck.pptx")
    with patch("src.renderer.cli.build_pptx") as mock_build:
        run_renderer(_deck_input(), output_path=out_path)
    assert mock_build.call_args[0][1] == out_path
