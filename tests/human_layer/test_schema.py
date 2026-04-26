# tests/human_layer/test_schema.py
import pytest
from pydantic import ValidationError
from src.human_layer.schema import HumanInputs, load_human_inputs


def test_load_human_inputs_succeeds_with_valid_yaml(tmp_path):
    yaml_text = """\
catl_overseas_gross_margin_pct: 31.4
catl_domestic_gross_margin_pct: 24.0
lges_q1_operating_margin_ex_ira_pct: 2.1
roic_shock_delta_bps: 180
shock_scenario: "US EV demand -20%, IRA credits capped at current level"
catl_execution_edge: "Hungary plant hit 50 GWh run-rate 6 months ahead of schedule; no Ultium-style ramp delays."
lges_execution_risk: "Ultium JV line 2 delayed 9 months; incremental cost $340M."
"""
    f = tmp_path / "human_inputs.yaml"
    f.write_text(yaml_text)
    inputs = load_human_inputs(str(f))
    assert inputs.catl_overseas_gross_margin_pct == 31.4
    assert inputs.roic_shock_delta_bps == 180


def test_load_human_inputs_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_human_inputs("does_not_exist.yaml")


def test_human_inputs_rejects_empty_strings():
    with pytest.raises(ValidationError):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=180,
            shock_scenario="",           # empty — invalid
            catl_execution_edge="Valid edge.",
            lges_execution_risk="Valid risk.",
        )


def test_human_inputs_rejects_placeholder_strings():
    with pytest.raises(ValidationError, match="placeholder"):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=180,
            shock_scenario="TBD",         # placeholder — invalid
            catl_execution_edge="Valid.",
            lges_execution_risk="Valid.",
        )


def test_human_inputs_rejects_out_of_range_gross_margin():
    with pytest.raises(ValidationError):
        HumanInputs(
            catl_overseas_gross_margin_pct=150.0,   # > 100 — likely a data entry error (314 vs 31.4)
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=180,
            shock_scenario="Valid scenario.",
            catl_execution_edge="Valid edge.",
            lges_execution_risk="Valid risk.",
        )


def test_human_inputs_rejects_unreasonable_roic_shock():
    with pytest.raises(ValidationError):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=5000,   # > 2000 bps — implausible
            shock_scenario="Valid scenario.",
            catl_execution_edge="Valid edge.",
            lges_execution_risk="Valid risk.",
        )


def test_load_human_inputs_raises_on_empty_file(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    with pytest.raises(ValueError, match="empty or malformed"):
        load_human_inputs(str(f))


def test_human_inputs_rejects_extra_keys():
    with pytest.raises(ValidationError):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=180,
            shock_scenario="Valid scenario.",
            catl_execution_edge="Valid edge.",
            lges_execution_risk="Valid risk.",
            unknown_field="should be rejected",
        )


def test_human_inputs_rejects_out_of_range_roic_shock_negative():
    with pytest.raises(ValidationError):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=-5000,
            shock_scenario="Valid scenario.",
            catl_execution_edge="Valid edge.",
            lges_execution_risk="Valid risk.",
        )


def test_human_inputs_rejects_out_of_range_operating_margin():
    with pytest.raises(ValidationError):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=-60.0,
            roic_shock_delta_bps=180,
            shock_scenario="Valid scenario.",
            catl_execution_edge="Valid edge.",
            lges_execution_risk="Valid risk.",
        )


def test_human_inputs_rejects_placeholder_in_execution_edge():
    with pytest.raises(ValidationError, match="placeholder"):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=180,
            shock_scenario="Valid scenario.",
            catl_execution_edge="TBD",
            lges_execution_risk="Valid risk.",
        )


def test_human_inputs_rejects_placeholder_in_execution_risk():
    with pytest.raises(ValidationError, match="placeholder"):
        HumanInputs(
            catl_overseas_gross_margin_pct=31.4,
            catl_domestic_gross_margin_pct=24.0,
            lges_q1_operating_margin_ex_ira_pct=2.1,
            roic_shock_delta_bps=180,
            shock_scenario="Valid scenario.",
            catl_execution_edge="Valid edge.",
            lges_execution_risk="n/a",
        )
