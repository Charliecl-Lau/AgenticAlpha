# AgenticAlpha v2 — Phase 6: Audit Module

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new `src/audit/` module that produces a structured audit trail table — one row per tagged claim, with columns: claim, source doc, confidence, and caveat — making the AI pipeline defensible and appendix-ready.

**Architecture:** `src/audit/trail.py` exposes two pure functions: `build_audit_table(df)` produces a list of dicts from a tag DataFrame, and `format_audit_table_rows(rows)` converts it to a `list[list[str]]` ready for `python-pptx` table insertion. No CLI required — the audit table is called by the renderer when building the appendix slide (optional extension in a later sprint).

**Tech Stack:** Python 3.11+, Pandas.

**Prerequisites:** Phase 1 complete (tag DataFrame must have `claim_summary`, `source_file`, `confidence`, `contradiction_reason` columns). Phase 5 complete (renderer can optionally use `format_audit_table_rows()` for an appendix slide — but this phase is self-contained and testable without the renderer).

---

## File Map

- Create: `src/audit/__init__.py`
- Create: `src/audit/trail.py`
- Create: `tests/audit/__init__.py`
- Create: `tests/audit/test_trail.py`

---

## Task 17: Audit Trail Module

**Files:**
- Create: `src/audit/__init__.py`
- Create: `src/audit/trail.py`
- Create: `tests/audit/__init__.py`
- Create: `tests/audit/test_trail.py`

- [ ] **Step 1: Create empty `__init__` files**

```bash
touch src/audit/__init__.py
touch tests/audit/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/audit/test_trail.py`:

```python
import pandas as pd
import pytest
from src.audit.trail import build_audit_table, format_audit_table_rows

def _make_df():
    return pd.DataFrame([
        {
            "company": "CATL",
            "claim_summary": "CATL shipped 12 GWh overseas in Q4 2025.",
            "source_file": "catl_abc.md",
            "confidence": 0.9,
            "contradiction_reason": None,
            "stream": "ground_truth",
        },
        {
            "company": "LGES",
            "claim_summary": "LGES IRA credit may be capped by 2027 policy revision.",
            "source_file": "lges_xyz.md",
            "confidence": 0.7,
            "contradiction_reason": "Challenges IRA dependency thesis.",
            "stream": "policy",
        },
    ])

def test_build_audit_table_returns_list_of_dicts():
    result = build_audit_table(_make_df())
    assert isinstance(result, list)
    assert len(result) == 2

def test_build_audit_table_has_required_keys():
    result = build_audit_table(_make_df())
    for row in result:
        assert "claim" in row
        assert "docs" in row
        assert "confidence" in row
        assert "caveat" in row

def test_audit_row_caveat_shows_contradiction_reason():
    result = build_audit_table(_make_df())
    lges_row = next(r for r in result if "IRA" in r["claim"])
    assert "Challenges" in lges_row["caveat"]

def test_audit_row_caveat_is_none_identified_when_no_contradiction():
    result = build_audit_table(_make_df())
    catl_row = next(r for r in result if "CATL" in r["claim"])
    assert catl_row["caveat"] == "None identified"

def test_audit_row_confidence_formatted_as_percent():
    result = build_audit_table(_make_df())
    catl_row = next(r for r in result if "CATL" in r["claim"])
    assert "%" in catl_row["confidence"]
    assert "90" in catl_row["confidence"]

def test_audit_row_confidence_unknown_when_missing():
    df = pd.DataFrame([{
        "company": "CATL",
        "claim_summary": "CATL claim.",
        "source_file": "catl.md",
        "contradiction_reason": None,
    }])
    result = build_audit_table(df)
    assert result[0]["confidence"] == "unknown"

def test_build_audit_table_empty_df_returns_empty_list():
    result = build_audit_table(pd.DataFrame())
    assert result == []

def test_format_audit_table_rows_header_is_first_row():
    rows = build_audit_table(_make_df())
    table_rows = format_audit_table_rows(rows)
    assert table_rows[0] == ["Claim", "Source", "Confidence", "Caveat"]

def test_format_audit_table_rows_correct_count():
    rows = build_audit_table(_make_df())
    table_rows = format_audit_table_rows(rows)
    assert len(table_rows) == 3  # header + 2 data rows

def test_format_audit_table_rows_empty_input():
    table_rows = format_audit_table_rows([])
    assert table_rows == [["Claim", "Source", "Confidence", "Caveat"]]

def test_format_audit_table_rows_truncates_long_claims():
    long_row = {
        "claim": "A" * 200,
        "docs": "file.md",
        "confidence": "90%",
        "caveat": "None identified",
    }
    table_rows = format_audit_table_rows([long_row])
    assert len(table_rows[1][0]) <= 80

def test_format_audit_table_rows_truncates_long_caveats():
    long_row = {
        "claim": "Short claim.",
        "docs": "file.md",
        "confidence": "90%",
        "caveat": "C" * 200,
    }
    table_rows = format_audit_table_rows([long_row])
    assert len(table_rows[1][3]) <= 60
```

```
pytest tests/audit/test_trail.py -v
```

Expected: FAIL (module not found).

- [ ] **Step 3: Implement `src/audit/trail.py`**

```python
import pandas as pd


def build_audit_table(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    rows = []
    for _, row in df.iterrows():
        conf = row.get("confidence")
        if conf is not None:
            conf_str = f"{float(conf):.0%}"
        else:
            conf_str = "unknown"

        caveat = row.get("contradiction_reason")
        caveat_str = str(caveat) if caveat else "None identified"

        rows.append({
            "claim": str(row.get("claim_summary", "")),
            "docs":  str(row.get("source_file", "")),
            "confidence": conf_str,
            "caveat": caveat_str,
        })
    return rows


def format_audit_table_rows(audit_rows: list[dict]) -> list[list[str]]:
    header = ["Claim", "Source", "Confidence", "Caveat"]
    data = [
        [
            row["claim"][:80],
            row["docs"],
            row["confidence"],
            row["caveat"][:60],
        ]
        for row in audit_rows
    ]
    return [header] + data
```

- [ ] **Step 4: Run tests**

```
pytest tests/audit/test_trail.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full test suite to confirm no regressions**

```
pytest tests/ -v --tb=short
```

Expected: all PASS across all phases.

- [ ] **Step 6: Commit**

```bash
git add src/audit/__init__.py src/audit/trail.py tests/audit/__init__.py tests/audit/test_trail.py
git commit -m "feat(audit): add audit trail module — claim/docs/confidence/caveat table

build_audit_table() converts a tag DataFrame into a list of dicts with
four keys: claim (from claim_summary), docs (source_file), confidence
(formatted as %), caveat (contradiction_reason or 'None identified').
format_audit_table_rows() wraps it for python-pptx table insertion.
Makes AI pipeline defensible and appendix-ready."
```

---

## Final Smoke Test

Run the complete v2 pipeline after all phases are complete:

```bash
# 1. Ingestion
python -m src.ingestion.cli --config config/urls.yaml --output data/raw

# 2. Tagger (requires GEMINI API key)
python -m src.tagger.cli \
  --perception data/raw/perception \
  --ground-truth data/raw/ground_truth \
  --policy data/raw/policy \
  --operations data/raw/operations \
  --output data/processed/tags

# 3. Evidence Engine
python -m src.signal_engine.cli \
  --tags data/processed/tags \
  --output output/charts \
  --human-inputs config/human_inputs.yaml

# 4. Synthesis (requires ANTHROPIC_API_KEY)
python -m src.synthesis.cli \
  --tags data/processed/tags \
  --charts output/charts \
  --output output/synthesis.json

# 5. Renderer
python -m src.renderer.cli \
  --human-inputs config/human_inputs.yaml \
  --tags data/processed/tags \
  --divergence-matrix output/charts/quality_divergence_matrix.png \
  --trend-inflection output/charts/trend_inflection.png \
  --differentiation-matrix output/charts/differentiation_matrix.png \
  --why-now-timeline output/charts/why_now_timeline.png \
  --contradictions output/charts/contradictions.png \
  --risk-tree output/charts/risk_tree.png \
  --evidence-scale output/charts/evidence_scale.png \
  --synthesis output/synthesis.json \
  --output output/deck/catl_lges_pair_trade_v2.pptx
```

Verify slide count:

```bash
python -c "
from pptx import Presentation
prs = Presentation('output/deck/catl_lges_pair_trade_v2.pptx')
count = len(prs.slides)
print(f'Slide count: {count}')
assert count == 15, f'Expected 15 slides, got {count}'
print('OK')
"
```

---

## Self-Review

**Spec coverage:**
- Audit module producing `claim | docs | confidence | caveat` table — Task 17 ✓
- `src/audit/` directory — Task 17 ✓
- Makes AI defensible — `build_audit_table()` exposes contradiction reasons ✓

**No placeholders present.**

**Type consistency:** `build_audit_table(df)` reads `df["claim_summary"]` — the Phase 1 schema renamed `summary` → `claim_summary`. `format_audit_table_rows()` returns `list[list[str]]` — the same type accepted by `slide_builder.py`'s table rendering via `table_rows` field on `SlideSpec`. Consistent.
