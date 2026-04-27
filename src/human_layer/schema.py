from pathlib import Path
from pydantic import BaseModel, ConfigDict, field_validator
import yaml

_PLACEHOLDERS = {"tbd", "todo", "fill in", "fill me", "placeholder", "n/a", "?"}


def _reject_placeholder(v: str, field_name: str) -> str:
    if not v.strip():
        raise ValueError(f"{field_name} must not be empty")
    if v.strip().lower() in _PLACEHOLDERS:
        raise ValueError(f"{field_name} contains a placeholder value: '{v}' — human analysis required")
    return v


class HumanInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catl_overseas_gross_margin_pct: float
    catl_domestic_gross_margin_pct: float
    lges_q1_operating_margin_ex_ira_pct: float
    roic_shock_delta_bps: int
    shock_scenario: str
    catl_execution_edge: str
    lges_execution_risk: str

    # Analyst action layer
    why_now_takeaway: str
    why_now_followup: str
    differentiation_takeaway: str
    differentiation_followup: str
    contradiction_takeaway: str
    contradiction_followup: str

    @field_validator("catl_overseas_gross_margin_pct", "catl_domestic_gross_margin_pct")
    @classmethod
    def gross_margin_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError(f"Gross margin must be between 0 and 100, got {v}")
        return v

    @field_validator("lges_q1_operating_margin_ex_ira_pct")
    @classmethod
    def operating_margin_in_range(cls, v: float) -> float:
        if not (-50.0 <= v <= 100.0):
            raise ValueError(f"Operating margin must be between -50 and 100, got {v}")
        return v

    @field_validator("roic_shock_delta_bps")
    @classmethod
    def roic_shock_reasonable(cls, v: int) -> int:
        if not (-2000 <= v <= 2000):
            raise ValueError(f"roic_shock_delta_bps must be between -2000 and 2000, got {v}")
        return v

    @field_validator("shock_scenario")
    @classmethod
    def shock_scenario_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "shock_scenario")

    @field_validator("catl_execution_edge")
    @classmethod
    def catl_edge_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "catl_execution_edge")

    @field_validator("lges_execution_risk")
    @classmethod
    def lges_risk_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "lges_execution_risk")

    @field_validator("why_now_takeaway")
    @classmethod
    def why_now_takeaway_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "why_now_takeaway")

    @field_validator("why_now_followup")
    @classmethod
    def why_now_followup_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "why_now_followup")

    @field_validator("differentiation_takeaway")
    @classmethod
    def differentiation_takeaway_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "differentiation_takeaway")

    @field_validator("differentiation_followup")
    @classmethod
    def differentiation_followup_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "differentiation_followup")

    @field_validator("contradiction_takeaway")
    @classmethod
    def contradiction_takeaway_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "contradiction_takeaway")

    @field_validator("contradiction_followup")
    @classmethod
    def contradiction_followup_not_placeholder(cls, v: str) -> str:
        return _reject_placeholder(v, "contradiction_followup")


def load_human_inputs(path: str) -> HumanInputs:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Human inputs config not found: {path}")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Human inputs config is empty or malformed: {path}")
    return HumanInputs(**data)
