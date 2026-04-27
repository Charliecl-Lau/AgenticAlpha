# tests/human_layer/test_schema.py
import pytest
import yaml
from pydantic import ValidationError
from src.human_layer.schema import HumanInputs, load_human_inputs

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NEW_FIELDS = dict(
    why_now_takeaway="Operational divergence accelerated in 2025-26",
    why_now_followup="Verify Hungary utilization assumptions",
    differentiation_takeaway="CATL execution consistently 2x LGES on our scoring",
    differentiation_followup="Check if CATL localization data captures JV structures",
    contradiction_takeaway="IRA exposure risk more acute than consensus models",
    contradiction_followup="Model IRA cliff scenario for LGES 2026 guidance",
)

_BASE_FIELDS = dict(
    catl_overseas_gross_margin_pct=31.4,
    catl_domestic_gross_margin_pct=24.0,
    lges_q1_operating_margin_ex_ira_pct=2.1,
    roic_shock_delta_bps=180,
    shock_scenario="US EV demand -20%, IRA credits capped.",
    catl_execution_edge="Hungary 50 GWh on schedule.",
    lges_execution_risk="Ultium delayed 9 months.",
)

_ALL_FIELDS = {**_BASE_FIELDS, **_NEW_FIELDS}


def _full_yaml(tmp_path, **overrides):
    base = {
        "catl_overseas_gross_margin_pct": 31.4,
        "catl_domestic_gross_margin_pct": 28.0,
        "lges_q1_operating_margin_ex_ira_pct": 2.1,
        "roic_shock_delta_bps": -150,
        "shock_scenario": "IRA credit cap reduces LGES ROIC by 150bps",
        "catl_execution_edge": "CATL commissioned 4 overseas plants on schedule in 2025",
        "lges_execution_risk": "LGES Hungary ramp delayed by 6 months vs initial guidance",
        "why_now_takeaway": "Operational divergence accelerated in 2025-26",
        "why_now_followup": "Verify Hungary utilization assumptions",
        "differentiation_takeaway": "CATL execution consistently 2x LGES on our scoring",
        "differentiation_followup": "Check if CATL localization data captures JV structures",
        "contradiction_takeaway": "IRA exposure risk more acute than consensus models",
        "contradiction_followup": "Model IRA cliff scenario for LGES 2026 guidance",
    }
    base.update(overrides)
    cfg = tmp_path / "human_inputs.yaml"
    cfg.write_text(yaml.dump(base))
    return str(cfg)


# ---------------------------------------------------------------------------
# Existing tests (updated to include 6 new required fields)
# ---------------------------------------------------------------------------

def test_load_human_inputs_succeeds_with_valid_yaml(tmp_path):
    yaml_text = """\
catl_overseas_gross_margin_pct: 31.4
catl_domestic_gross_margin_pct: 24.0
lges_q1_operating_margin_ex_ira_pct: 2.1
roic_shock_delta_bps: 180
shock_scenario: "US EV demand -20%, IRA credits capped at current level"
catl_execution_edge: "Hungary plant hit 50 GWh run-rate 6 months ahead of schedule; no Ultium-style ramp delays."
lges_execution_risk: "Ultium JV line 2 delayed 9 months; incremental cost $340M."
why_now_takeaway: "Operational divergence accelerated in 2025-26"
why_now_followup: "Verify Hungary utilization assumptions"
differentiation_takeaway: "CATL execution consistently 2x LGES on our scoring"
differentiation_followup: "Check if CATL localization data captures JV structures"
contradiction_takeaway: "IRA exposure risk more acute than consensus models"
contradiction_followup: "Model IRA cliff scenario for LGES 2026 guidance"
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
            **{**_ALL_FIELDS, "shock_scenario": ""},  # empty — invalid
        )


def test_human_inputs_rejects_placeholder_strings():
    with pytest.raises(ValidationError, match="placeholder"):
        HumanInputs(
            **{**_ALL_FIELDS, "shock_scenario": "TBD"},  # placeholder — invalid
        )


def test_human_inputs_rejects_out_of_range_gross_margin():
    with pytest.raises(ValidationError):
        HumanInputs(
            **{**_ALL_FIELDS, "catl_overseas_gross_margin_pct": 150.0},  # > 100
        )


def test_human_inputs_rejects_unreasonable_roic_shock():
    with pytest.raises(ValidationError):
        HumanInputs(
            **{**_ALL_FIELDS, "roic_shock_delta_bps": 5000},  # > 2000 bps
        )


def test_load_human_inputs_raises_on_empty_file(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    with pytest.raises(ValueError, match="empty or malformed"):
        load_human_inputs(str(f))


def test_human_inputs_rejects_extra_keys():
    with pytest.raises(ValidationError):
        HumanInputs(
            **{**_ALL_FIELDS, "unknown_field": "should be rejected"},
        )


def test_human_inputs_rejects_out_of_range_roic_shock_negative():
    with pytest.raises(ValidationError):
        HumanInputs(
            **{**_ALL_FIELDS, "roic_shock_delta_bps": -5000},
        )


def test_human_inputs_rejects_out_of_range_operating_margin():
    with pytest.raises(ValidationError):
        HumanInputs(
            **{**_ALL_FIELDS, "lges_q1_operating_margin_ex_ira_pct": -60.0},
        )


def test_human_inputs_rejects_placeholder_in_execution_edge():
    with pytest.raises(ValidationError, match="placeholder"):
        HumanInputs(
            **{**_ALL_FIELDS, "catl_execution_edge": "TBD"},
        )


def test_human_inputs_rejects_placeholder_in_execution_risk():
    with pytest.raises(ValidationError, match="placeholder"):
        HumanInputs(
            **{**_ALL_FIELDS, "lges_execution_risk": "n/a"},
        )


# ---------------------------------------------------------------------------
# New tests for the 6 analyst action layer fields
# ---------------------------------------------------------------------------

def test_human_inputs_loads_new_analyst_fields(tmp_path):
    inputs = load_human_inputs(_full_yaml(tmp_path))
    assert inputs.why_now_takeaway == "Operational divergence accelerated in 2025-26"
    assert inputs.why_now_followup == "Verify Hungary utilization assumptions"
    assert inputs.differentiation_takeaway == "CATL execution consistently 2x LGES on our scoring"
    assert inputs.differentiation_followup == "Check if CATL localization data captures JV structures"
    assert inputs.contradiction_takeaway == "IRA exposure risk more acute than consensus models"
    assert inputs.contradiction_followup == "Model IRA cliff scenario for LGES 2026 guidance"


def test_why_now_takeaway_rejects_empty(tmp_path):
    with pytest.raises(ValidationError):
        load_human_inputs(_full_yaml(tmp_path, why_now_takeaway=""))


def test_why_now_takeaway_rejects_placeholder(tmp_path):
    with pytest.raises(ValidationError):
        load_human_inputs(_full_yaml(tmp_path, why_now_takeaway="tbd"))
