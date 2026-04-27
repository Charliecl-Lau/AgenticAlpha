# Stage 4: Human-in-the-Loop Financial Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define a YAML config file for human analyst inputs (baseline margins, shock deltas, execution edges), validate that all required fields are populated and within plausible ranges, and merge them with the top AI signals from Stage 2 into a single `DeckInput` object (including Stage 3 chart paths) consumed by Stage 5.

**Architecture:** Human inputs live in `config/human_inputs.yaml`. A Pydantic validator loads and enforces completeness — any empty/placeholder field or out-of-range numeric raises an error before the renderer is invoked. A merger function combines the validated human inputs with a summary of AI signals pulled from the tag DataFrame, weighting ground-truth stream entries 2× over perception to prevent flashy headlines from outranking dry IR earnings data. Chart paths produced by Stage 3 are carried through `DeckInput` so Stage 5 has a single source of truth. The result is a single `DeckInput` dataclass serialisable to JSON for Stage 5.

**Tech Stack:** Python 3.11+, pydantic, pyyaml, pandas, pytest

**Prerequisite:** Stage 2 complete. `data/processed/tags/` contains JSON files. Stage 3 complete. `output/charts/quality_divergence_matrix.png` and `output/charts/trend_inflection.png` exist.

---

### Task 1: Human Input Schema

**Files:**
- Create: `src/human_layer/schema.py`
- Create: `config/human_inputs.yaml`
- Test: `tests/human_layer/test_schema.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/human_layer/test_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.human_layer.schema'`

- [ ] **Step 3: Implement schema**

```python
# src/human_layer/schema.py
from pathlib import Path
from pydantic import BaseModel, field_validator
import yaml

_PLACEHOLDERS = {"tbd", "todo", "fill in", "fill me", "placeholder", "n/a", "?"}


def _reject_placeholder(v: str, field_name: str) -> str:
    if not v.strip():
        raise ValueError(f"{field_name} must not be empty")
    if v.strip().lower() in _PLACEHOLDERS:
        raise ValueError(f"{field_name} contains a placeholder value: '{v}' — human analysis required")
    return v


class HumanInputs(BaseModel):
    catl_overseas_gross_margin_pct: float
    catl_domestic_gross_margin_pct: float
    lges_q1_operating_margin_ex_ira_pct: float
    roic_shock_delta_bps: int
    shock_scenario: str
    catl_execution_edge: str
    lges_execution_risk: str

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


def load_human_inputs(path: str) -> HumanInputs:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Human inputs config not found: {path}")
    with open(p) as f:
        data = yaml.safe_load(f)
    return HumanInputs(**data)
```

- [ ] **Step 4: Create sample human_inputs.yaml**

```yaml
# config/human_inputs.yaml
# HUMAN ANALYST: Fill in all fields with real data. Empty or placeholder values will cause the pipeline to fail.

catl_overseas_gross_margin_pct: 31.4        # CATL reported overseas gross margin (Q3 2024)
catl_domestic_gross_margin_pct: 24.0        # CATL domestic gross margin (Q3 2024)
lges_q1_operating_margin_ex_ira_pct: 2.1   # LGES Q1 operating margin EXCLUDING IRA credits

roic_shock_delta_bps: 180
shock_scenario: "US EV demand contracts 20% YoY; IRA credits capped at current 2024 levels for the duration of the model horizon."

catl_execution_edge: "CATL Hungary gigafactory reached 50 GWh annualised run-rate 6 months ahead of schedule with no announced cost overruns."
lges_execution_risk: "Ultium Cells JV Line 2 delayed 9 months; management disclosed incremental costs of ~$340M in the Q2 2024 earnings call."
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/human_layer/test_schema.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add src/human_layer/schema.py tests/human_layer/test_schema.py config/human_inputs.yaml
git commit -m "feat(human_layer): add human input schema with placeholder and range enforcement

HumanInputs uses Pydantic to validate that no analyst-filled field
is empty or a common placeholder (TBD, TODO, N/A). Numeric fields are
also bounds-checked — gross margins must be 0-100, operating margin
-50-100, and roic_shock_delta_bps within ±2000 bps — catching the
common data-entry error of entering 314 instead of 31.4. The pipeline
aborts early if inputs are shallow or malformed, ensuring the deck
cannot be built on incomplete fundamental data."
```

---

### Task 2: AI Signal Summariser

**Files:**
- Create: `src/human_layer/summariser.py`
- Test: `tests/human_layer/test_summariser.py`

- [ ] **Step 1: Write failing test**

```python
# tests/human_layer/test_summariser.py
import pandas as pd
from src.human_layer.summariser import extract_top_signals


def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 9, "summary": "CATL Hungary at 50 GWh.", "stream": "perception"},
        {"company": "CATL", "topic_cluster": "Capex_Execution",
         "sentiment_score": 8, "summary": "CATL capex efficiency outperforms.", "stream": "perception"},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 3, "summary": "LGES IRA credits dominate revenue.", "stream": "perception"},
        {"company": "LGES", "topic_cluster": "Geopolitical_Noise",
         "sentiment_score": 4, "summary": "LGES faces US tariff uncertainty.", "stream": "perception"},
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 7, "summary": "CATL LFP volume up 40% YoY.", "stream": "ground_truth"},
    ])


def test_extract_top_signals_returns_top_3_per_company():
    df = _make_df()
    signals = extract_top_signals(df, n=3)
    assert "CATL" in signals
    assert "LGES" in signals
    assert len(signals["CATL"]) <= 3
    assert len(signals["LGES"]) <= 3


def test_extract_top_signals_prefers_ground_truth_over_higher_raw_score():
    """A ground_truth entry at sentiment_score 7 (weighted 14) should rank above
    a perception entry at sentiment_score 9 (weighted 9)."""
    df = _make_df()
    signals = extract_top_signals(df, n=3)
    top_catl = signals["CATL"]
    assert top_catl[0]["stream"] == "ground_truth"


def test_extract_top_signals_includes_summary_and_topic():
    df = _make_df()
    signals = extract_top_signals(df, n=1)
    top_catl = signals["CATL"][0]
    assert "summary" in top_catl
    assert "topic_cluster" in top_catl


def test_extract_top_signals_output_does_not_expose_weighted_score():
    """Internal weighting must not leak into the output dicts."""
    df = _make_df()
    signals = extract_top_signals(df, n=3)
    for record in signals["CATL"]:
        assert "_weighted_score" not in record
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/human_layer/test_summariser.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement summariser**

```python
# src/human_layer/summariser.py
import pandas as pd


def extract_top_signals(df: pd.DataFrame, n: int = 3) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for company in df["company"].unique():
        sub = df[df["company"] == company].copy()
        # Ground-truth IR earnings data is weighted 2× over perception/news sentiment.
        # This prevents a bullish press release from outranking a dry but credible earnings release.
        sub["_weighted_score"] = sub.apply(
            lambda r: r["sentiment_score"] * (2 if r["stream"] == "ground_truth" else 1),
            axis=1,
        )
        top = sub.sort_values("_weighted_score", ascending=False).head(n)
        result[company] = top[["topic_cluster", "sentiment_score", "summary", "stream"]].to_dict("records")
    return result
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/human_layer/test_summariser.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/human_layer/summariser.py tests/human_layer/test_summariser.py
git commit -m "feat(human_layer): add AI signal summariser with ground-truth stream weighting

extract_top_signals returns the N highest-weighted tag records per company.
Ground-truth stream entries are scored at 2× their raw sentiment score to
prevent perception-heavy news headlines from ranking above lower-sentiment
but more credible IR earnings data. The weighting is an internal detail
and does not appear in the output dicts."
```

---

### Task 3: Merger & DeckInput

**Files:**
- Create: `src/human_layer/merger.py`
- Test: `tests/human_layer/test_merger.py`

- [ ] **Step 1: Write failing test**

```python
# tests/human_layer/test_merger.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/human_layer/test_merger.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement merger and DeckInput**

```python
# src/human_layer/merger.py
from dataclasses import dataclass
import pandas as pd
from src.human_layer.schema import HumanInputs
from src.human_layer.summariser import extract_top_signals


@dataclass
class DeckInput:
    human: HumanInputs
    ai_signals: dict[str, list[dict]]
    divergence_matrix_path: str
    trend_inflection_path: str

    def to_dict(self) -> dict:
        return {
            "human": self.human.model_dump(),
            "ai_signals": self.ai_signals,
            "divergence_matrix_path": self.divergence_matrix_path,
            "trend_inflection_path": self.trend_inflection_path,
        }


def merge_inputs(
    human: HumanInputs,
    tag_df: pd.DataFrame,
    divergence_matrix_path: str,
    trend_inflection_path: str,
    top_n: int = 3,
) -> DeckInput:
    ai_signals = extract_top_signals(tag_df, n=top_n)
    return DeckInput(
        human=human,
        ai_signals=ai_signals,
        divergence_matrix_path=divergence_matrix_path,
        trend_inflection_path=trend_inflection_path,
    )
```

- [ ] **Step 4: Run all human_layer tests**

```bash
pytest tests/human_layer/ -v
```

Expected: PASS (all 14 tests)

- [ ] **Step 5: Commit**

```bash
git add src/human_layer/merger.py tests/human_layer/test_merger.py
git commit -m "feat(human_layer): add DeckInput merger with chart path passthrough

merge_inputs packages validated human inputs, top-N weighted AI signals,
and Stage 3 chart paths into a single DeckInput dataclass. Carrying
divergence_matrix_path and trend_inflection_path ensures Stage 5 has a
single source of truth and does not need to hardcode or rediscover chart
locations. DeckInput.to_dict() produces a JSON-serialisable payload
for the renderer."
```
