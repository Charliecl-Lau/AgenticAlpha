# AgenticAlpha v2 — Phase 5: Human Layer & Renderer Expansion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `HumanInputs` with an analyst action layer (six new fields: takeaway + followup per artifact), expand `DeckInput` with five new chart paths and an optional `synthesis` field, and rebuild the renderer from 13 slides to 15 slides incorporating the new evidence engine charts and synthesis output.

**Architecture:** `HumanInputs` gains six string fields validated as non-empty non-placeholders. `DeckInput` is a dataclass that gains `synthesis: Optional[SynthesisOutput]` and five new `_path` fields. `build_slide_specs()` is fully rewritten to produce exactly 15 slides. The renderer CLI gains five new path arguments and loads `output/synthesis.json` if it exists.

**Tech Stack:** Python 3.11+, Pydantic v2, python-pptx, dataclasses.

**Prerequisites:**
- Phase 1 complete (new `Tag` fields)
- Phase 3 complete (five new chart PNGs exist)
- Phase 4 complete (`src/synthesis/schema.py` exists; `output/synthesis.json` produced)

**Next phase:** Phase 6 (Audit Module) is independent and can run after this phase or in parallel.

---

## File Map

- Modify: `src/human_layer/schema.py` — add 6 analyst action layer fields
- Modify: `src/human_layer/merger.py` — expand `DeckInput` with 5 chart paths + synthesis
- Modify: `src/renderer/content_map.py` — rewrite `build_slide_specs()` to 15 slides
- Modify: `src/renderer/cli.py` — add 5 new chart path args + `--synthesis` arg
- Modify: `config/human_inputs.yaml` — add 6 new analyst action layer fields
- Modify: `tests/human_layer/test_schema.py` — new field tests
- Modify: `tests/human_layer/test_merger.py` — new DeckInput field tests
- Modify: `tests/renderer/test_content_map.py` — 15-slide + new slide content tests

---

## Task 15: Expand HumanInputs and DeckInput

**Files:**
- Modify: `src/human_layer/schema.py`
- Modify: `src/human_layer/merger.py`
- Modify: `config/human_inputs.yaml`
- Modify: `tests/human_layer/test_schema.py`
- Modify: `tests/human_layer/test_merger.py`

- [ ] **Step 1: Read current files**

```bash
cat src/human_layer/schema.py
cat src/human_layer/merger.py
cat config/human_inputs.yaml
```

Note: the existing validators reject placeholder strings ("tbd", "todo", "fill in") and empty strings. The six new fields must pass the same validation.

- [ ] **Step 2: Write failing tests for new HumanInputs fields**

Add to `tests/human_layer/test_schema.py`:

```python
from src.human_layer.schema import load_human_inputs
import pytest
from pydantic import ValidationError

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
    import yaml
    cfg = tmp_path / "human_inputs.yaml"
    cfg.write_text(yaml.dump(base))
    return str(cfg)

def test_human_inputs_loads_new_analyst_fields(tmp_path):
    inputs = load_human_inputs(_full_yaml(tmp_path))
    assert inputs.why_now_takeaway == "Operational divergence accelerated in 2025-26"
    assert inputs.why_now_followup == "Verify Hungary utilization assumptions"
    assert inputs.differentiation_takeaway == "CATL execution consistently 2x LGES on our scoring"
    assert inputs.differentiation_followup == "Check if CATL localization data captures JV structures"
    assert inputs.contradiction_takeaway == "IRA exposure risk more acute than consensus models"
    assert inputs.contradiction_followup == "Model IRA cliff scenario for LGES 2026 guidance"

def test_why_now_takeaway_rejects_empty(tmp_path):
    with pytest.raises(Exception):
        load_human_inputs(_full_yaml(tmp_path, why_now_takeaway=""))

def test_why_now_takeaway_rejects_placeholder(tmp_path):
    with pytest.raises(Exception):
        load_human_inputs(_full_yaml(tmp_path, why_now_takeaway="tbd"))
```

```
pytest tests/human_layer/test_schema.py -v
```

Expected: FAIL (new fields not defined).

- [ ] **Step 3: Add six new fields to `HumanInputs` in `src/human_layer/schema.py`**

After the existing fields (before validators), add:

```python
    # Analyst action layer
    why_now_takeaway: str
    why_now_followup: str
    differentiation_takeaway: str
    differentiation_followup: str
    contradiction_takeaway: str
    contradiction_followup: str
```

Add validators for the six new fields using the same pattern as `catl_execution_edge` (reject empty, reject placeholders like "tbd", "todo", "fill in"). Example — add to the existing placeholder validator's field list:

```python
@field_validator(
    "shock_scenario", "catl_execution_edge", "lges_execution_risk",
    "why_now_takeaway", "why_now_followup", "differentiation_takeaway",
    "differentiation_followup", "contradiction_takeaway", "contradiction_followup",
)
@classmethod
def no_placeholder(cls, v: str) -> str:
    if not v or not v.strip():
        raise ValueError("field must not be empty")
    lower = v.strip().lower()
    for bad in ("tbd", "todo", "fill in", "placeholder", "fixme"):
        if bad in lower:
            raise ValueError(f"field contains placeholder text: {v!r}")
    return v
```

(Check that the existing validator is not a duplicate — merge if needed.)

- [ ] **Step 4: Update `config/human_inputs.yaml`**

Append to the existing file:

```yaml
why_now_takeaway: "Operational divergence accelerated materially in 2025-26"
why_now_followup: "Verify Hungary plant utilization assumptions for 2026"
differentiation_takeaway: "CATL scores approximately 2.5x higher than LGES on execution and localization"
differentiation_followup: "Confirm CATL JV structures are captured in localization scoring"
contradiction_takeaway: "IRA exposure risk is more acute than consensus models price in"
contradiction_followup: "Model IRA cliff scenario for LGES 2026 margin guidance"
```

- [ ] **Step 5: Write failing tests for expanded DeckInput**

Add to `tests/human_layer/test_merger.py`:

```python
import dataclasses
from src.human_layer.merger import DeckInput

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
```

```
pytest tests/human_layer/test_merger.py -v
```

Expected: FAIL.

- [ ] **Step 6: Expand `DeckInput` and `merge_inputs` in `src/human_layer/merger.py`**

```python
from dataclasses import dataclass
from typing import Optional

from src.human_layer.schema import HumanInputs


@dataclass
class DeckInput:
    human: HumanInputs
    ai_signals: dict[str, list[dict]]
    synthesis: Optional[object]          # SynthesisOutput at runtime; avoid circular import
    divergence_matrix_path: str
    trend_inflection_path: str
    differentiation_matrix_path: str
    why_now_timeline_path: str
    contradictions_path: str
    risk_tree_path: str
    evidence_scale_path: str


def merge_inputs(
    human: HumanInputs,
    tag_df,
    divergence_matrix_path: str,
    trend_inflection_path: str,
    differentiation_matrix_path: str,
    why_now_timeline_path: str,
    contradictions_path: str,
    risk_tree_path: str,
    evidence_scale_path: str,
    synthesis=None,
    top_n: int = 3,
) -> DeckInput:
    from src.human_layer.summariser import extract_top_signals
    ai_signals = extract_top_signals(tag_df, top_n=top_n)
    return DeckInput(
        human=human,
        ai_signals=ai_signals,
        synthesis=synthesis,
        divergence_matrix_path=divergence_matrix_path,
        trend_inflection_path=trend_inflection_path,
        differentiation_matrix_path=differentiation_matrix_path,
        why_now_timeline_path=why_now_timeline_path,
        contradictions_path=contradictions_path,
        risk_tree_path=risk_tree_path,
        evidence_scale_path=evidence_scale_path,
    )
```

- [ ] **Step 7: Run all human layer tests**

```
pytest tests/human_layer/ -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/human_layer/schema.py src/human_layer/merger.py config/human_inputs.yaml tests/human_layer/
git commit -m "feat(human_layer): add analyst action layer fields and expand DeckInput

HumanInputs gains 6 new fields (why_now/differentiation/contradiction
takeaway + followup) with the same placeholder-rejection validators.
DeckInput gains synthesis field and 5 new chart path fields to carry
the v2 evidence engine outputs through to the renderer."
```

---

## Task 16: Expand Renderer to 15 Slides

**Files:**
- Modify: `src/renderer/content_map.py`
- Modify: `src/renderer/cli.py`
- Modify: `tests/renderer/test_content_map.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/renderer/test_content_map.py`:

```python
import pathlib
from src.renderer.content_map import build_slide_specs

def _make_full_deck_input(tmp_path):
    from src.human_layer.schema import HumanInputs
    from src.human_layer.merger import DeckInput

    human = HumanInputs(
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

    # Fake SynthesisOutput
    class FakeSynthesis:
        executive_summary = "CATL leads on globalization."
        why_now = "Divergence accelerated in 2025Q4."
        differentiation_takeaway = "Execution gap is 4pts."
        contradiction_summary = "IRA dependency challenged by 3 docs."
        risk_summary = "Policy reversal is primary bear case."
        analyst_questions = ["What is LGES Hungary utilization at IRA cap?"]
        limitations = ["Evidence limited to public disclosures."]

    for name in ["div.png", "trend.png", "diff.png", "why.png", "contra.png", "risk.png", "ev.png"]:
        (tmp_path / name).write_bytes(b"PNG")

    return DeckInput(
        human=human,
        ai_signals={"CATL": [{"claim_summary": "Strong."}], "LGES": [{"claim_summary": "Weak."}]},
        synthesis=FakeSynthesis(),
        divergence_matrix_path=str(tmp_path / "div.png"),
        trend_inflection_path=str(tmp_path / "trend.png"),
        differentiation_matrix_path=str(tmp_path / "diff.png"),
        why_now_timeline_path=str(tmp_path / "why.png"),
        contradictions_path=str(tmp_path / "contra.png"),
        risk_tree_path=str(tmp_path / "risk.png"),
        evidence_scale_path=str(tmp_path / "ev.png"),
    )

def test_slide_count_is_15(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    assert len(specs) == 15

def test_differentiation_matrix_slide_present(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    assert any("Differentiation" in s.title for s in specs)

def test_why_now_slide_present(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    assert any("Why Now" in s.title for s in specs)

def test_contradiction_scanner_slide_present(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    assert any("Contradiction" in s.title for s in specs)

def test_risk_tree_slide_present(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    assert any("Risk" in s.title for s in specs)

def test_analyst_questions_slide_uses_synthesis(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    q_slide = next((s for s in specs if "Analyst" in s.title and "Question" in s.title), None)
    assert q_slide is not None
    assert "Hungary" in q_slide.body

def test_no_prohibited_language(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    forbidden = {"buy", "sell", "hold", "we believe", "we recommend", "outperform", "underperform"}
    for spec in specs:
        text = (spec.title + " " + spec.body).lower()
        for word in forbidden:
            assert word not in text, f"Prohibited '{word}' in slide '{spec.title}'"

def test_disclosure_slide_present(tmp_path):
    specs = build_slide_specs(_make_full_deck_input(tmp_path))
    assert any("Disclosure" in s.title or "Methodology" in s.title for s in specs)
```

```
pytest tests/renderer/test_content_map.py -v
```

Expected: failures on slide count and missing slides.

- [ ] **Step 2: Rewrite `build_slide_specs` in `src/renderer/content_map.py`**

Replace the entire `build_slide_specs()` function body with the 15-slide implementation below. Keep all existing imports and enums (`SlideType`, `SlideSpec`) unchanged.

```python
def build_slide_specs(deck_input) -> list["SlideSpec"]:
    h = deck_input.human
    s = deck_input.synthesis
    signals = deck_input.ai_signals

    catl_body = "\n".join(
        f"• {sig.get('claim_summary', sig.get('summary', ''))}"
        for sig in signals.get("CATL", [])
    ) or "• No CATL signals tagged."

    lges_body = "\n".join(
        f"• {sig.get('claim_summary', sig.get('summary', ''))}"
        for sig in signals.get("LGES", [])
    ) or "• No LGES signals tagged."

    analyst_questions_body = (
        "\n".join(f"• {q}" for q in s.analyst_questions)
        if s else "• [Add analyst questions here]"
    )
    limitations_body = (
        "\n".join(f"• {lim}" for lim in s.limitations)
        if s else "• Evidence limited to public IR disclosures and news media."
    )
    executive_summary = s.executive_summary if s else ""
    why_now_body = (
        f"{s.why_now}\n\nTakeaway: {h.why_now_takeaway}\nFollow-up: {h.why_now_followup}"
        if s else h.why_now_takeaway
    )
    diff_body = (
        f"{s.differentiation_takeaway}\n\nTakeaway: {h.differentiation_takeaway}\nFollow-up: {h.differentiation_followup}"
        if s else h.differentiation_takeaway
    )
    contra_body = (
        f"{s.contradiction_summary}\n\nTakeaway: {h.contradiction_takeaway}\nFollow-up: {h.contradiction_followup}"
        if s else h.contradiction_takeaway
    )

    specs = [
        SlideSpec(                                                              # 1
            slide_type=SlideType.TITLE,
            title="CATL vs LGES: Globalization Quality Divergence",
            body="AI-Assisted Institutional Research | AgenticAlpha v2",
        ),
        SlideSpec(                                                              # 2
            slide_type=SlideType.THESIS,
            title="Pair Thesis: Quality of Globalization",
            body=(
                f"CATL overseas gross margin: {h.catl_overseas_gross_margin_pct:.1f}%\n"
                f"LGES operating margin ex-IRA: {h.lges_q1_operating_margin_ex_ira_pct:.1f}%\n\n"
                f"{executive_summary}"
            ),
        ),
        SlideSpec(                                                              # 3
            slide_type=SlideType.AI_SIGNAL,
            title="AI Workflow: Evidence Engine Architecture",
            body=(
                "Pipeline: Ingestion → Rich Tagger → Evidence Engine → Synthesis\n"
                "Human layer: Analyst inputs + takeaways layered on top\n"
                "All LLM outputs validated against structured schemas.\n"
                "No valuation, no buy/sell signals."
            ),
        ),
        SlideSpec(                                                              # 4
            slide_type=SlideType.CHART,
            title="Differentiation Matrix: Factor Scores (1–10)",
            body=diff_body,
            chart_path=deck_input.differentiation_matrix_path,
        ),
        SlideSpec(                                                              # 5
            slide_type=SlideType.CHART,
            title="Why Now: Topic Frequency Timeline",
            body=why_now_body,
            chart_path=deck_input.why_now_timeline_path,
        ),
        SlideSpec(                                                              # 6
            slide_type=SlideType.CHART,
            title="Contradiction Scanner: Evidence Challenging Thesis",
            body=contra_body,
            chart_path=deck_input.contradictions_path,
        ),
        SlideSpec(                                                              # 7
            slide_type=SlideType.CHART,
            title="Evidence Scale: Document Attribution by Stream",
            body="Corroboration across perception, ground truth, policy, and operations streams.",
            chart_path=deck_input.evidence_scale_path,
        ),
        SlideSpec(                                                              # 8
            slide_type=SlideType.AI_SIGNAL,
            title="Top Perception Signals: CATL",
            body=catl_body,
        ),
        SlideSpec(                                                              # 9
            slide_type=SlideType.AI_SIGNAL,
            title="Top Perception Signals: LGES",
            body=lges_body,
        ),
        SlideSpec(                                                              # 10
            slide_type=SlideType.FUNDAMENTALS,
            title="Margin Bridge: AI Signal vs Fundamental Data",
            table_rows=[
                ["Metric", "CATL", "LGES"],
                ["Overseas Gross Margin", f"{h.catl_overseas_gross_margin_pct:.1f}%", "N/A"],
                ["Domestic Gross Margin", f"{h.catl_domestic_gross_margin_pct:.1f}%", "N/A"],
                ["Operating Margin ex-IRA", "N/A", f"{h.lges_q1_operating_margin_ex_ira_pct:.1f}%"],
            ],
        ),
        SlideSpec(                                                              # 11
            slide_type=SlideType.CHART,
            title="Risk Tree: Likelihood × Impact Matrix",
            body="Policy risk, execution risk, capex mismatch, and ROIC deterioration.",
            chart_path=deck_input.risk_tree_path,
        ),
        SlideSpec(                                                              # 12
            slide_type=SlideType.COUNTERFACTUAL,
            title="Downside Scenario: IRA Credit Cap",
            body=(
                f"Scenario: {h.shock_scenario}\n"
                f"ROIC impact: {h.roic_shock_delta_bps:+d} bps\n"
                f"Execution risk: {h.lges_execution_risk}"
            ),
        ),
        SlideSpec(                                                              # 13
            slide_type=SlideType.AI_SIGNAL,
            title="Analyst Questions for Follow-Up",
            body=analyst_questions_body,
        ),
        SlideSpec(                                                              # 14
            slide_type=SlideType.DISCLOSURE,
            title="Methodology Limitations",
            body=limitations_body,
        ),
        SlideSpec(                                                              # 15
            slide_type=SlideType.DISCLOSURE,
            title="AI Methodology Disclosure",
            body=(
                "Evidence collected via automated ingestion from public sources.\n"
                "Tags generated by LLM (Google Gemini) with schema validation.\n"
                "Synthesis generated by Claude (Anthropic) — one call, no recommendations.\n"
                "No valuation analysis, channel checks, or non-public information."
            ),
        ),
    ]

    assert len(specs) <= 20, f"Slide count {len(specs)} exceeds maximum of 20"
    return specs
```

- [ ] **Step 3: Run content map tests**

```
pytest tests/renderer/test_content_map.py -v
```

Expected: all PASS.

- [ ] **Step 4: Update `src/renderer/cli.py`**

Read the file:

```bash
cat src/renderer/cli.py
```

Add five new `--chart` arguments and `--synthesis` to the argument parser:

```python
parser.add_argument("--differentiation-matrix",
                    default="output/charts/differentiation_matrix.png")
parser.add_argument("--why-now-timeline",
                    default="output/charts/why_now_timeline.png")
parser.add_argument("--contradictions",
                    default="output/charts/contradictions.png")
parser.add_argument("--risk-tree",
                    default="output/charts/risk_tree.png")
parser.add_argument("--evidence-scale",
                    default="output/charts/evidence_scale.png")
parser.add_argument("--synthesis",
                    default="output/synthesis.json",
                    help="Path to synthesis JSON (optional — skipped if absent)")
```

Load synthesis before calling `merge_inputs()`:

```python
import json, pathlib
from src.synthesis.schema import SynthesisOutput

synthesis = None
synthesis_path = pathlib.Path(args.synthesis)
if synthesis_path.exists():
    synthesis = SynthesisOutput(**json.loads(synthesis_path.read_text()))
```

Update the `merge_inputs()` call to pass all new arguments:

```python
deck_input = merge_inputs(
    human=human_inputs,
    tag_df=tag_df,
    divergence_matrix_path=args.divergence_matrix,
    trend_inflection_path=args.trend_inflection,
    differentiation_matrix_path=args.differentiation_matrix,
    why_now_timeline_path=args.why_now_timeline,
    contradictions_path=args.contradictions,
    risk_tree_path=args.risk_tree,
    evidence_scale_path=args.evidence_scale,
    synthesis=synthesis,
)
```

- [ ] **Step 5: Run full renderer and human layer tests**

```
pytest tests/renderer/ tests/human_layer/ -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/renderer/content_map.py src/renderer/cli.py tests/renderer/test_content_map.py
git commit -m "feat(renderer): expand to 15 slides with differentiation matrix, contradiction scanner, risk tree, analyst Q&A

Replaces 13-slide v1 structure. New slides: Differentiation Matrix
(anchor), Why Now Timeline, Contradiction Scanner (elite slide),
Evidence Scale, Risk Tree, Analyst Questions (from synthesis),
Limitations (from synthesis). Synthesis is loaded from JSON if present,
gracefully omitted if not. CLI gains 5 new chart path args and
--synthesis."
```

---

## Self-Review

**Spec coverage:**
- Expanded `DeckInput` with all new artifact paths — Task 15 ✓
- Analyst action layer (takeaway + followup per artifact) — Task 15 ✓
- 15-slide renderer — Task 16 ✓
- Slide 3: AI Workflow (AI vs human separation) — Task 16 ✓
- Slide 4: Differentiation Matrix (anchor) — Task 16 ✓
- Slide 5: Why Now Timeline — Task 16 ✓
- Slide 6: Contradiction Scanner — Task 16 ✓
- Slide 7: Evidence Scale — Task 16 ✓
- Slide 11: Risk Tree — Task 16 ✓
- Slide 13: Analyst Questions (from synthesis) — Task 16 ✓
- Slide 14: Limitations (from synthesis) — Task 16 ✓
- Slide 15: Methodology Disclosure — Task 16 ✓

**No placeholders present.**

**Type consistency:** `DeckInput.synthesis` typed as `Optional[object]` to avoid circular import — at runtime it is a `SynthesisOutput` instance. `build_slide_specs()` accesses `s.analyst_questions` (a `list[str]`) and `s.limitations` (a `list[str]`) — both defined on `SynthesisOutput` in Phase 4. The `FakeSynthesis` in tests mirrors the same attributes. Consistent.
