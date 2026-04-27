# AgenticAlpha v2 — Phase 4: Synthesis Layer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new `src/synthesis/` module that makes a single Claude API call to produce a structured `SynthesisOutput` — executive summary, why_now, differentiation takeaway, contradiction summary, risk summary, analyst questions, and limitations — from aggregated evidence.

**Architecture:** Three files: `schema.py` (Pydantic model), `prompt_builder.py` (assembles the prompt from DataFrames + top signals), `synthesiser.py` (one `anthropic.Anthropic().messages.create()` call + JSON parse). A CLI entry point at `src/synthesis/cli.py` ties it together. No streaming, no tool use — plain JSON in the response.

**Tech Stack:** Python 3.11+, Pydantic v2, `anthropic` SDK (install: `pip install anthropic`), Pandas.

**Prerequisites:** Phase 3 must be complete. `compute_differentiation_matrix()` and `compute_contradictions()` from `src/signal_engine/aggregator` are called by the synthesis CLI. Phase 1's `claim_summary` field must exist in tag JSON for the prompt builder to work.

**Next phase:** Phase 5 (Human Layer & Renderer) loads `output/synthesis.json` produced by this phase's CLI to populate the analyst questions and limitations slides.

---

## File Map

- Create: `src/synthesis/__init__.py`
- Create: `src/synthesis/schema.py`
- Create: `src/synthesis/prompt_builder.py`
- Create: `src/synthesis/synthesiser.py`
- Create: `src/synthesis/cli.py`
- Create: `tests/synthesis/__init__.py`
- Create: `tests/synthesis/test_schema.py`
- Create: `tests/synthesis/test_prompt_builder.py`
- Create: `tests/synthesis/test_synthesiser.py`
- Create: `tests/synthesis/test_cli.py`

---

## Task 12: Synthesis Schema

**Files:**
- Create: `src/synthesis/__init__.py`
- Create: `src/synthesis/schema.py`
- Create: `tests/synthesis/__init__.py`
- Create: `tests/synthesis/test_schema.py`

- [ ] **Step 1: Create empty `__init__` files**

```bash
touch src/synthesis/__init__.py
touch tests/synthesis/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/synthesis/test_schema.py`:

```python
import pytest
from pydantic import ValidationError
from src.synthesis.schema import SynthesisOutput

def test_synthesis_output_valid():
    out = SynthesisOutput(
        executive_summary="CATL demonstrates superior globalization execution vs LGES.",
        why_now="Operational divergence accelerated materially in 2025–26.",
        differentiation_takeaway="CATL scores 2.5x higher on localization and execution vs LGES.",
        contradiction_summary="3 documents challenge the LGES IRA-benefit thesis.",
        risk_summary="Policy risk and capex overruns are the primary bear scenarios for LGES.",
        analyst_questions=[
            "What is Hungary plant utilization assuming IRA credit cap?",
            "How does CATL margin hold if ASP declines 15%?",
        ],
        limitations=[
            "Ground truth limited to public IR disclosures.",
            "Geo data relies on article self-reporting.",
        ],
    )
    assert out.executive_summary.startswith("CATL")
    assert len(out.analyst_questions) == 2
    assert len(out.limitations) == 2

def test_synthesis_output_rejects_empty_executive_summary():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            executive_summary="",
            why_now="test",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=["Q1"],
            limitations=["L1"],
        )

def test_synthesis_output_rejects_whitespace_why_now():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            executive_summary="Summary.",
            why_now="   ",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=["Q1"],
            limitations=["L1"],
        )

def test_synthesis_output_rejects_empty_analyst_questions():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            executive_summary="Summary.",
            why_now="test",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=[],  # must have at least 1
            limitations=["L1"],
        )

def test_synthesis_output_rejects_empty_limitations():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            executive_summary="Summary.",
            why_now="test",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=["Q1"],
            limitations=[],  # must have at least 1
        )

def test_synthesis_output_serializes_to_dict():
    out = SynthesisOutput(
        executive_summary="Summary.",
        why_now="Now.",
        differentiation_takeaway="Diff.",
        contradiction_summary="Contra.",
        risk_summary="Risk.",
        analyst_questions=["Q1"],
        limitations=["L1"],
    )
    d = out.model_dump()
    assert d["executive_summary"] == "Summary."
    assert isinstance(d["analyst_questions"], list)
```

```
pytest tests/synthesis/test_schema.py -v
```

Expected: FAIL (module not found).

- [ ] **Step 3: Implement `src/synthesis/schema.py`**

```python
from pydantic import BaseModel, field_validator


class SynthesisOutput(BaseModel):
    executive_summary: str
    why_now: str
    differentiation_takeaway: str
    contradiction_summary: str
    risk_summary: str
    analyst_questions: list[str]
    limitations: list[str]

    @field_validator(
        "executive_summary", "why_now", "differentiation_takeaway",
        "contradiction_summary", "risk_summary",
    )
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty or whitespace")
        return v

    @field_validator("analyst_questions", "limitations")
    @classmethod
    def must_have_at_least_one(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("list must contain at least one item")
        return v
```

- [ ] **Step 4: Run tests**

```
pytest tests/synthesis/test_schema.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/synthesis/__init__.py src/synthesis/schema.py tests/synthesis/__init__.py tests/synthesis/test_schema.py
git commit -m "feat(synthesis): add SynthesisOutput schema with validation

Seven required fields: executive_summary, why_now,
differentiation_takeaway, contradiction_summary, risk_summary,
analyst_questions, limitations. String fields reject empty/whitespace.
List fields require at least one item."
```

---

## Task 13: Synthesis Prompt Builder

**Files:**
- Create: `src/synthesis/prompt_builder.py`
- Create: `tests/synthesis/test_prompt_builder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/synthesis/test_prompt_builder.py`:

```python
import pandas as pd
from src.synthesis.prompt_builder import build_synthesis_prompt

def _make_diff_df():
    return pd.DataFrame([
        {"factor": "localization", "CATL": 7.5, "LGES": 4.5, "delta": 3.0},
        {"factor": "execution",    "CATL": 8.5, "LGES": 4.5, "delta": 4.0},
    ])

def _make_contra_df():
    return pd.DataFrame([
        {"company": "LGES", "claim_summary": "IRA credit at risk.",
         "contradiction_reason": "Policy change.", "sentiment_score": 2.0},
    ])

def test_prompt_contains_differentiation_data():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={"CATL": [{"claim_summary": "Strong execution."}], "LGES": []},
    )
    assert "localization" in prompt
    assert "3.0" in prompt

def test_prompt_contains_contradiction_data():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={"CATL": [], "LGES": []},
    )
    assert "IRA credit at risk" in prompt

def test_prompt_includes_no_recommendation_rule():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={},
    )
    lower = prompt.lower()
    assert "do not make recommendations" in lower or "do not make investment recommendations" in lower

def test_prompt_includes_json_schema_fields():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={},
    )
    assert "executive_summary" in prompt
    assert "analyst_questions" in prompt
    assert "limitations" in prompt

def test_prompt_handles_empty_dfs():
    prompt = build_synthesis_prompt(
        diff_df=pd.DataFrame(),
        contradictions_df=pd.DataFrame(),
        top_signals={},
    )
    assert "executive_summary" in prompt  # schema still present
```

```
pytest tests/synthesis/test_prompt_builder.py -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `src/synthesis/prompt_builder.py`**

```python
import pandas as pd


def build_synthesis_prompt(
    diff_df: pd.DataFrame,
    contradictions_df: pd.DataFrame,
    top_signals: dict[str, list[dict]],
) -> str:
    return f"""You are a quantitative research analyst synthesizing structured AI-generated evidence about CATL and LGES for an institutional equity research report.

RULES:
- Do NOT make investment recommendations (no buy/sell/hold).
- Do NOT infer facts not supported by the evidence below.
- Summarize asymmetry only. Be specific and precise.
- Analyst questions must be concrete, verifiable, and forward-looking.
- Limitations must be genuine methodological constraints, not generic disclaimers.

DIFFERENTIATION MATRIX (mean scores 1–10):
{_format_diff_df(diff_df)}

CONTRADICTIONS IDENTIFIED:
{_format_contradictions(contradictions_df)}

TOP SIGNALS BY COMPANY:
{_format_signals(top_signals)}

Return a JSON object matching this schema exactly. No markdown fences, no explanation:
{{
  "executive_summary": "<2-3 sentences on the key asymmetry>",
  "why_now": "<1-2 sentences on what changed in 2025-26 to make this pair trade relevant>",
  "differentiation_takeaway": "<1 sentence on the most significant factor delta>",
  "contradiction_summary": "<1-2 sentences summarizing challenges to the bull thesis>",
  "risk_summary": "<1-2 sentences on the primary bear scenarios>",
  "analyst_questions": ["<specific verifiable question 1>", "<question 2>", "<question 3>"],
  "limitations": ["<genuine constraint 1>", "<genuine constraint 2>"]
}}
"""


def _format_diff_df(df: pd.DataFrame) -> str:
    if df.empty:
        return "  (no differentiation data available)"
    lines = ["  factor | CATL | LGES | delta"]
    for _, row in df.iterrows():
        lines.append(f"  {row['factor']} | {row['CATL']} | {row['LGES']} | {row['delta']}")
    return "\n".join(lines)


def _format_contradictions(df: pd.DataFrame) -> str:
    if df.empty:
        return "  (no contradictions flagged)"
    lines = []
    for _, row in df.iterrows():
        reason = row.get("contradiction_reason", "")
        lines.append(f"  [{row['company']}] {row['claim_summary']} — {reason}")
    return "\n".join(lines)


def _format_signals(signals: dict[str, list[dict]]) -> str:
    lines = []
    for company, sigs in signals.items():
        lines.append(f"  {company}:")
        for sig in sigs[:3]:
            summary = sig.get("claim_summary") or sig.get("summary", "")
            lines.append(f"    - {summary}")
    return "\n".join(lines) if lines else "  (no signals)"
```

- [ ] **Step 3: Run tests**

```
pytest tests/synthesis/test_prompt_builder.py -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/synthesis/prompt_builder.py tests/synthesis/test_prompt_builder.py
git commit -m "feat(synthesis): add prompt builder for Claude synthesis call

Assembles differentiation matrix, contradictions, and top signals into
a structured prompt. Enforces the 'do not make recommendations' rule
explicitly. Returns prompt string ready for the Anthropic SDK."
```

---

## Task 14: Synthesiser + CLI

**Files:**
- Create: `src/synthesis/synthesiser.py`
- Create: `src/synthesis/cli.py`
- Create: `tests/synthesis/test_synthesiser.py`
- Create: `tests/synthesis/test_cli.py`

- [ ] **Step 1: Write failing synthesiser tests**

Create `tests/synthesis/test_synthesiser.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from src.synthesis.synthesiser import synthesise
from src.synthesis.schema import SynthesisOutput

_FAKE_JSON = """{
  "executive_summary": "CATL leads on globalization; LGES faces subsidy cliff.",
  "why_now": "IRA policy uncertainty accelerated in 2025Q4.",
  "differentiation_takeaway": "CATL scores 3pt higher on execution.",
  "contradiction_summary": "Two documents challenge IRA dependency assumptions.",
  "risk_summary": "Policy reversal and capex overrun are primary bear cases.",
  "analyst_questions": ["What is LGES Hungary utilization at IRA cap?"],
  "limitations": ["Evidence limited to public disclosures."]
}"""

def test_synthesise_returns_synthesis_output():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_FAKE_JSON)]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        result = synthesise("test prompt")

    assert isinstance(result, SynthesisOutput)
    assert "CATL" in result.executive_summary

def test_synthesise_passes_correct_model():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_FAKE_JSON)]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        mock_create = MockClient.return_value.messages.create
        mock_create.return_value = mock_message
        synthesise("test prompt", model="claude-haiku-4-5-20251001")
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"

def test_synthesise_raises_on_invalid_json():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not valid json at all")]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        with pytest.raises(ValueError, match="Failed to parse synthesis output"):
            synthesise("test prompt")
```

```
pytest tests/synthesis/test_synthesiser.py -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `src/synthesis/synthesiser.py`**

```python
import json
import anthropic

from src.synthesis.schema import SynthesisOutput


def synthesise(prompt: str, model: str = "claude-sonnet-4-6") -> SynthesisOutput:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
        return SynthesisOutput(**data)
    except Exception as exc:
        raise ValueError(
            f"Failed to parse synthesis output: {exc}\n\nRaw response:\n{raw}"
        ) from exc
```

- [ ] **Step 3: Run synthesiser tests**

```
pytest tests/synthesis/test_synthesiser.py -v
```

Expected: all PASS.

- [ ] **Step 4: Write failing CLI tests**

Create `tests/synthesis/test_cli.py`:

```python
import json, pathlib
from unittest.mock import patch
from src.synthesis.schema import SynthesisOutput

_FAKE_OUTPUT = SynthesisOutput(
    executive_summary="CATL leads.",
    why_now="2025 divergence.",
    differentiation_takeaway="Execution gap.",
    contradiction_summary="Two contradictions.",
    risk_summary="Policy risk.",
    analyst_questions=["Q1?"],
    limitations=["L1."],
)

def test_synthesis_cli_writes_json(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir()
    out_path = tmp_path / "synthesis.json"

    with patch("src.synthesis.cli.synthesise", return_value=_FAKE_OUTPUT):
        from src.synthesis.cli import run_synthesis
        run_synthesis(
            tags_dir=str(tags_dir),
            charts_dir=str(charts_dir),
            output_path=str(out_path),
        )

    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["executive_summary"] == "CATL leads."
    assert isinstance(data["analyst_questions"], list)

def test_synthesis_cli_creates_parent_dirs(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    out_path = tmp_path / "nested" / "output" / "synthesis.json"

    with patch("src.synthesis.cli.synthesise", return_value=_FAKE_OUTPUT):
        from src.synthesis.cli import run_synthesis
        run_synthesis(
            tags_dir=str(tags_dir),
            charts_dir=str(tmp_path),
            output_path=str(out_path),
        )

    assert out_path.exists()
```

```
pytest tests/synthesis/test_cli.py -v
```

Expected: FAIL.

- [ ] **Step 5: Implement `src/synthesis/cli.py`**

```python
import argparse
import json
import os

import pandas as pd

from src.signal_engine.aggregator import (
    compute_differentiation_matrix,
    compute_contradictions,
)
from src.signal_engine.loader import load_tags
from src.human_layer.summariser import extract_top_signals
from src.synthesis.prompt_builder import build_synthesis_prompt
from src.synthesis.synthesiser import synthesise


def run_synthesis(
    tags_dir: str,
    charts_dir: str,
    output_path: str,
    model: str = "claude-sonnet-4-6",
) -> None:
    has_tags = os.path.isdir(tags_dir) and any(
        f.endswith(".json") for f in os.listdir(tags_dir)
    )
    tag_df = load_tags(tags_dir) if has_tags else pd.DataFrame()

    diff_df = compute_differentiation_matrix(tag_df)
    contra_df = compute_contradictions(tag_df)
    top_signals = extract_top_signals(tag_df, top_n=3) if not tag_df.empty else {}

    prompt = build_synthesis_prompt(
        diff_df=diff_df,
        contradictions_df=contra_df,
        top_signals=top_signals,
    )

    output = synthesise(prompt, model=model)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output.model_dump(), f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthesis layer (single Claude call)")
    parser.add_argument("--tags",   default="data/processed/tags",  help="Tag JSON directory")
    parser.add_argument("--charts", default="output/charts",         help="Charts directory")
    parser.add_argument("--output", default="output/synthesis.json", help="Output synthesis JSON")
    parser.add_argument("--model",  default="claude-sonnet-4-6",     help="Claude model ID")
    args = parser.parse_args()
    run_synthesis(args.tags, args.charts, args.output, args.model)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run full synthesis test suite**

```
pytest tests/synthesis/ -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/synthesis/synthesiser.py src/synthesis/cli.py tests/synthesis/test_synthesiser.py tests/synthesis/test_cli.py
git commit -m "feat(synthesis): add synthesiser (one Claude API call) and CLI entry point

synthesise() calls anthropic.Anthropic().messages.create() with the
assembled prompt, parses the JSON response into SynthesisOutput, and
raises ValueError with raw response on parse failure. run_synthesis()
CLI writes output/synthesis.json. Invoked as:
  python -m src.synthesis.cli --tags ... --output ..."
```

---

## Self-Review

**Spec coverage:**
- `src/synthesis/` with schema, prompt_builder, synthesiser, CLI — Tasks 12–14 ✓
- `SynthesisOutput` with all 7 fields — Task 12 ✓
- "Do NOT make recommendations" rule in prompt — Task 13 ✓
- Single Claude call — Task 14 ✓
- `python -m src.synthesis.cli` entry point — Task 14 ✓

**No placeholders present.**

**Type consistency:** `build_synthesis_prompt(diff_df=...)` accepts `pd.DataFrame` with columns `factor, CATL, LGES, delta` — exactly what `compute_differentiation_matrix()` (Phase 3) returns. `SynthesisOutput.analyst_questions` is `list[str]` — read in Phase 5 as `s.analyst_questions` iterated with `for q in s.analyst_questions`. Consistent.
