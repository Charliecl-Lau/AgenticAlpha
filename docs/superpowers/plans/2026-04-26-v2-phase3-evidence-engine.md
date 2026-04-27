# AgenticAlpha v2 — Phase 3: Evidence Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `src/signal_engine/` from 3 aggregations to 8 by adding five new functions — differentiation matrix, Why Now timeline, contradiction scanner, risk tree, and evidence attribution — each backed by a Plotly chart, all wired into the CLI to produce 5 additional PNG outputs.

**Architecture:** New aggregator functions appended to `src/signal_engine/aggregator.py`. New chart functions appended to `src/signal_engine/charts.py`. CLI updated to call all new functions after existing ones. All new charts saved alongside existing PNGs in `output/charts/`.

**Tech Stack:** Python 3.11+, Pandas, Plotly + Kaleido (for PNG export).

**Prerequisites:** Phase 1 must be complete. The new aggregators consume tag fields that only exist after the Phase 1 schema expansion: `localization_score`, `subsidy_dependency`, `execution_quality`, `margin_signal`, `capex_signal`, `ROIC_signal`, `contradiction_flag`, `contradiction_reason`, `claim_summary`, `confidence`, `date`. Run Phase 1 first and re-tag documents before running the full pipeline.

**Next phase:** Phase 4 (Synthesis) calls `compute_differentiation_matrix()` and `compute_contradictions()` from this phase.

---

## File Map

- Modify: `src/signal_engine/aggregator.py` — add 5 new functions
- Modify: `src/signal_engine/charts.py` — add 4 new chart functions
- Modify: `src/signal_engine/cli.py` — produce 5 additional PNGs
- Create: `tests/signal_engine/test_evidence_engine.py`
- Modify: `tests/signal_engine/test_cli.py`

---

## Task 6: Differentiation Matrix Aggregator + Chart

**Files:**
- Modify: `src/signal_engine/aggregator.py`
- Modify: `src/signal_engine/charts.py`
- Create: `tests/signal_engine/test_evidence_engine.py`

- [ ] **Step 1: Write failing tests**

Create `tests/signal_engine/test_evidence_engine.py`:

```python
import pathlib
import pandas as pd
import pytest
from src.signal_engine.aggregator import compute_differentiation_matrix

def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "localization_score": 8, "subsidy_dependency": 3,
         "execution_quality": 9, "margin_signal": 7, "capex_signal": 8, "ROIC_signal": 7},
        {"company": "CATL", "localization_score": 7, "subsidy_dependency": 4,
         "execution_quality": 8, "margin_signal": 6, "capex_signal": 7, "ROIC_signal": 6},
        {"company": "LGES", "localization_score": 4, "subsidy_dependency": 8,
         "execution_quality": 4, "margin_signal": 3, "capex_signal": 4, "ROIC_signal": 3},
        {"company": "LGES", "localization_score": 5, "subsidy_dependency": 7,
         "execution_quality": 5, "margin_signal": 4, "capex_signal": 5, "ROIC_signal": 4},
    ])

def test_differentiation_matrix_columns():
    df = compute_differentiation_matrix(_make_df())
    assert set(df.columns) == {"factor", "CATL", "LGES", "delta"}

def test_differentiation_matrix_row_count():
    df = compute_differentiation_matrix(_make_df())
    assert len(df) == 6  # one row per factor

def test_differentiation_matrix_delta_correct():
    df = compute_differentiation_matrix(_make_df())
    row = df[df["factor"] == "localization"].iloc[0]
    assert abs(row["delta"] - (row["CATL"] - row["LGES"])) < 0.01

def test_differentiation_matrix_empty_df_returns_empty():
    df = compute_differentiation_matrix(pd.DataFrame(columns=["company", "localization_score"]))
    assert len(df) == 0
```

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: FAIL (`compute_differentiation_matrix` not importable).

- [ ] **Step 2: Implement `compute_differentiation_matrix` in `src/signal_engine/aggregator.py`**

Append:

```python
_DIFF_FACTORS: dict[str, str] = {
    "localization":     "localization_score",
    "subsidy_reliance": "subsidy_dependency",
    "execution":        "execution_quality",
    "capex_efficiency": "capex_signal",
    "margin_quality":   "margin_signal",
    "ROIC":             "ROIC_signal",
}


def compute_differentiation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for factor_name, col in _DIFF_FACTORS.items():
        if col not in df.columns:
            continue
        catl_vals = df[df["company"] == "CATL"][col]
        lges_vals = df[df["company"] == "LGES"][col]
        if catl_vals.empty and lges_vals.empty:
            continue
        catl_mean = round(float(catl_vals.mean()), 2) if not catl_vals.empty else None
        lges_mean = round(float(lges_vals.mean()), 2) if not lges_vals.empty else None
        delta = round(catl_mean - lges_mean, 2) if (catl_mean is not None and lges_mean is not None) else None
        rows.append({"factor": factor_name, "CATL": catl_mean, "LGES": lges_mean, "delta": delta})
    return pd.DataFrame(rows)
```

- [ ] **Step 3: Write failing chart test**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.charts import build_differentiation_matrix_chart

def test_build_differentiation_matrix_chart_creates_file(tmp_path):
    df = compute_differentiation_matrix(_make_df())
    out = str(tmp_path / "diff_matrix.png")
    build_differentiation_matrix_chart(df, out)
    assert pathlib.Path(out).exists()
    assert pathlib.Path(out).stat().st_size > 0
```

```
pytest tests/signal_engine/test_evidence_engine.py::test_build_differentiation_matrix_chart_creates_file -v
```

Expected: FAIL.

- [ ] **Step 4: Implement `build_differentiation_matrix_chart` in `src/signal_engine/charts.py`**

Append:

```python
def build_differentiation_matrix_chart(diff_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="CATL", x=diff_df["factor"], y=diff_df["CATL"],
        marker_color="#2563EB",
    ))
    fig.add_trace(go.Bar(
        name="LGES", x=diff_df["factor"], y=diff_df["LGES"],
        marker_color="#DC2626",
    ))
    fig.update_layout(
        title="Differentiation Matrix: CATL vs LGES (1–10 scale)",
        barmode="group",
        yaxis=dict(range=[0, 10], title="Signal Score"),
        xaxis_title="Factor",
        template="plotly_white",
        width=900, height=500,
    )
    fig.write_image(output_path)
```

- [ ] **Step 5: Run all evidence engine tests so far**

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/signal_engine/aggregator.py src/signal_engine/charts.py tests/signal_engine/test_evidence_engine.py
git commit -m "feat(signal_engine): add differentiation matrix aggregator and grouped-bar chart"
```

---

## Task 7: Why Now Timeline Aggregator + Chart

**Files:**
- Modify: `src/signal_engine/aggregator.py`
- Modify: `src/signal_engine/charts.py`
- Modify: `tests/signal_engine/test_evidence_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.aggregator import compute_timeline

def _make_timeline_df():
    return pd.DataFrame([
        {"company": "CATL", "date": "2025-01-10", "topic_cluster": "Capex_Execution",
         "contradiction_flag": False},
        {"company": "CATL", "date": "2025-03-15", "topic_cluster": "Capex_Execution",
         "contradiction_flag": True},
        {"company": "LGES", "date": "2025-01-20", "topic_cluster": "Subsidy_Dependence",
         "contradiction_flag": False},
        {"company": "LGES", "date": "2025-04-05", "topic_cluster": "Subsidy_Dependence",
         "contradiction_flag": False},
    ])

def test_compute_timeline_returns_dataframe():
    assert isinstance(compute_timeline(_make_timeline_df()), pd.DataFrame)

def test_compute_timeline_has_required_columns():
    df = compute_timeline(_make_timeline_df())
    for col in ["quarter", "company", "topic", "mention_count"]:
        assert col in df.columns

def test_compute_timeline_no_date_column_returns_empty():
    df = compute_timeline(pd.DataFrame(columns=["company", "topic_cluster"]))
    assert len(df) == 0

def test_compute_timeline_assigns_quarters():
    df = compute_timeline(_make_timeline_df())
    assert any("2025" in str(q) for q in df["quarter"].unique())
```

```
pytest tests/signal_engine/test_evidence_engine.py -k "timeline" -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `compute_timeline` in `src/signal_engine/aggregator.py`**

Append:

```python
def compute_timeline(df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in df.columns:
        return pd.DataFrame(columns=["quarter", "company", "topic", "mention_count"])

    df2 = df.copy()
    df2["_dt"] = pd.to_datetime(df2["date"], errors="coerce")
    df2 = df2.dropna(subset=["_dt"])
    if df2.empty:
        return pd.DataFrame(columns=["quarter", "company", "topic", "mention_count"])

    df2["quarter"] = df2["_dt"].dt.to_period("Q").astype(str)

    rows = []
    for (quarter, company, topic), group in df2.groupby(["quarter", "company", "topic_cluster"]):
        rows.append({"quarter": quarter, "company": company, "topic": topic, "mention_count": len(group)})

    if "contradiction_flag" in df2.columns:
        for (quarter, company), group in df2.groupby(["quarter", "company"]):
            contra = int(group["contradiction_flag"].sum())
            if contra > 0:
                rows.append({"quarter": quarter, "company": company, "topic": "contradiction", "mention_count": contra})

    return pd.DataFrame(rows)
```

- [ ] **Step 3: Write failing chart test**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.charts import build_why_now_timeline_chart

def test_build_why_now_timeline_chart_creates_file(tmp_path):
    tl = compute_timeline(_make_timeline_df())
    out = str(tmp_path / "why_now.png")
    build_why_now_timeline_chart(tl, out)
    assert pathlib.Path(out).exists()
```

- [ ] **Step 4: Implement `build_why_now_timeline_chart` in `src/signal_engine/charts.py`**

Append:

```python
def build_why_now_timeline_chart(timeline_df: pd.DataFrame, output_path: str) -> None:
    import plotly.express as px
    import plotly.graph_objects as go

    if timeline_df.empty:
        go.Figure().update_layout(
            title="Why Now Timeline (no data)", width=900, height=400,
        ).write_image(output_path)
        return

    fig = px.line(
        timeline_df,
        x="quarter",
        y="mention_count",
        color="topic",
        line_dash="company",
        markers=True,
        title="Why Now: Topic Mention Frequency by Quarter",
        labels={"mention_count": "Mentions", "quarter": "Quarter"},
        template="plotly_white",
        width=900,
        height=500,
    )
    fig.write_image(output_path)
```

- [ ] **Step 5: Run tests**

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/signal_engine/aggregator.py src/signal_engine/charts.py tests/signal_engine/test_evidence_engine.py
git commit -m "feat(signal_engine): add Why Now timeline aggregator and line chart"
```

---

## Task 8: Contradiction Scanner Aggregator + Chart

**Files:**
- Modify: `src/signal_engine/aggregator.py`
- Modify: `src/signal_engine/charts.py`
- Modify: `tests/signal_engine/test_evidence_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.aggregator import compute_contradictions

def _make_contradiction_df():
    return pd.DataFrame([
        {"company": "CATL", "contradiction_flag": True, "sentiment_score": 3.0,
         "claim_summary": "CATL margins fell sharply.",
         "contradiction_reason": "Challenges bull thesis on margins."},
        {"company": "CATL", "contradiction_flag": False, "sentiment_score": 8.0,
         "claim_summary": "CATL capacity on track.", "contradiction_reason": None},
        {"company": "LGES", "contradiction_flag": True, "sentiment_score": 2.0,
         "claim_summary": "LGES IRA credit at risk.",
         "contradiction_reason": "Policy risk not priced in."},
    ])

def test_compute_contradictions_returns_only_flagged():
    df = compute_contradictions(_make_contradiction_df())
    assert len(df) == 2
    assert all(df["contradiction_flag"])

def test_compute_contradictions_has_required_columns():
    df = compute_contradictions(_make_contradiction_df())
    for col in ["company", "claim_summary", "contradiction_reason", "sentiment_score"]:
        assert col in df.columns

def test_compute_contradictions_empty_when_no_flags():
    df = compute_contradictions(pd.DataFrame([
        {"company": "CATL", "contradiction_flag": False, "sentiment_score": 7.0,
         "claim_summary": "Good.", "contradiction_reason": None},
    ]))
    assert len(df) == 0

def test_compute_contradictions_no_column_returns_empty():
    df = compute_contradictions(pd.DataFrame(columns=["company", "sentiment_score"]))
    assert len(df) == 0
```

```
pytest tests/signal_engine/test_evidence_engine.py -k "contradiction" -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `compute_contradictions` in `src/signal_engine/aggregator.py`**

Append:

```python
def compute_contradictions(df: pd.DataFrame) -> pd.DataFrame:
    if "contradiction_flag" not in df.columns:
        return pd.DataFrame(columns=["company", "claim_summary", "contradiction_reason", "sentiment_score"])
    flagged = df[df["contradiction_flag"] == True].copy()
    keep = [c for c in ["company", "claim_summary", "contradiction_reason", "sentiment_score", "contradiction_flag"] if c in flagged.columns]
    return flagged[keep].reset_index(drop=True)
```

- [ ] **Step 3: Write failing chart test**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.charts import build_contradiction_chart

def test_build_contradiction_chart_creates_file(tmp_path):
    df = compute_contradictions(_make_contradiction_df())
    out = str(tmp_path / "contradictions.png")
    build_contradiction_chart(df, out)
    assert pathlib.Path(out).exists()
```

- [ ] **Step 4: Implement `build_contradiction_chart` in `src/signal_engine/charts.py`**

Append:

```python
def build_contradiction_chart(contradictions_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if contradictions_df.empty:
        go.Figure().update_layout(
            title="Contradiction Scanner (no contradictions identified)", width=900, height=300,
        ).write_image(output_path)
        return

    fig = go.Figure()
    colors = {"CATL": "#2563EB", "LGES": "#DC2626"}
    for company, sub in contradictions_df.groupby("company"):
        fig.add_trace(go.Scatter(
            x=sub["sentiment_score"],
            y=sub["claim_summary"].str[:60],
            mode="markers+text",
            name=company,
            marker=dict(size=14, color=colors.get(company, "grey")),
            text=sub["contradiction_reason"].str[:40],
            textposition="top center",
        ))

    fig.update_layout(
        title="Contradiction Scanner: Evidence Challenging Bull Thesis",
        xaxis=dict(title="Sentiment Score (lower = more bearish)", range=[0, 10]),
        template="plotly_white",
        width=1000,
        height=max(400, len(contradictions_df) * 60),
    )
    fig.write_image(output_path)
```

- [ ] **Step 5: Run tests**

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/signal_engine/aggregator.py src/signal_engine/charts.py tests/signal_engine/test_evidence_engine.py
git commit -m "feat(signal_engine): add Contradiction Scanner aggregator and severity scatter chart"
```

---

## Task 9: Risk Tree Aggregator + Chart

**Files:**
- Modify: `src/signal_engine/aggregator.py`
- Modify: `src/signal_engine/charts.py`
- Modify: `tests/signal_engine/test_evidence_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.aggregator import compute_risk_tree

def _make_risk_df():
    return pd.DataFrame([
        {"company": "CATL", "subsidy_dependency": 3, "execution_quality": 9,
         "capex_signal": 8, "margin_signal": 7, "ROIC_signal": 7},
        {"company": "LGES", "subsidy_dependency": 8, "execution_quality": 4,
         "capex_signal": 4, "margin_signal": 3, "ROIC_signal": 3},
    ])

def test_compute_risk_tree_has_required_columns():
    df = compute_risk_tree(_make_risk_df())
    for col in ["company", "risk_category", "likelihood", "impact"]:
        assert col in df.columns

def test_compute_risk_tree_likelihood_0_to_1():
    df = compute_risk_tree(_make_risk_df())
    assert (df["likelihood"] >= 0.0).all()
    assert (df["likelihood"] <= 1.0).all()

def test_compute_risk_tree_lges_higher_policy_risk():
    df = compute_risk_tree(_make_risk_df())
    catl = df[(df["company"] == "CATL") & (df["risk_category"] == "policy_risk")]["likelihood"].values[0]
    lges = df[(df["company"] == "LGES") & (df["risk_category"] == "policy_risk")]["likelihood"].values[0]
    assert lges > catl

def test_compute_risk_tree_empty_returns_empty():
    df = compute_risk_tree(pd.DataFrame(columns=["company"]))
    assert len(df) == 0
```

```
pytest tests/signal_engine/test_evidence_engine.py -k "risk" -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `compute_risk_tree` in `src/signal_engine/aggregator.py`**

Append:

```python
_RISK_MAP: dict[str, tuple[str, bool]] = {
    # (column_name, True if high score = high risk)
    "policy_risk":    ("subsidy_dependency", True),
    "execution_risk": ("execution_quality",  False),
    "capex_risk":     ("capex_signal",       False),
    "margin_risk":    ("margin_signal",      False),
    "ROIC_risk":      ("ROIC_signal",        False),
}


def compute_risk_tree(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for company, group in df.groupby("company"):
        for risk_cat, (col, risk_when_high) in _RISK_MAP.items():
            if col not in df.columns:
                continue
            avg = group[col].mean()
            likelihood = round(avg / 10.0 if risk_when_high else (10.0 - avg) / 10.0, 2)
            rows.append({
                "company": company,
                "risk_category": risk_cat,
                "likelihood": likelihood,
                "impact": 0.7,
            })
    return pd.DataFrame(rows)
```

- [ ] **Step 3: Write failing chart test**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.charts import build_risk_tree_chart

def test_build_risk_tree_chart_creates_file(tmp_path):
    df = compute_risk_tree(_make_risk_df())
    out = str(tmp_path / "risk_tree.png")
    build_risk_tree_chart(df, out)
    assert pathlib.Path(out).exists()
```

- [ ] **Step 4: Implement `build_risk_tree_chart` in `src/signal_engine/charts.py`**

Append:

```python
def build_risk_tree_chart(risk_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if risk_df.empty:
        go.Figure().write_image(output_path)
        return

    colors = {"CATL": "#2563EB", "LGES": "#DC2626"}
    fig = go.Figure()
    for company, group in risk_df.groupby("company"):
        fig.add_trace(go.Scatter(
            x=group["likelihood"],
            y=group["impact"],
            mode="markers+text",
            name=company,
            text=group["risk_category"],
            textposition="top center",
            marker=dict(
                size=group["likelihood"] * 40 + 10,
                color=colors.get(company, "grey"),
                opacity=0.7,
            ),
        ))

    fig.update_layout(
        title="Risk Tree: Likelihood × Impact",
        xaxis=dict(title="Likelihood (0–1)", range=[0, 1.1]),
        yaxis=dict(title="Impact (0–1)", range=[0, 1.1]),
        template="plotly_white",
        width=800,
        height=600,
    )
    fig.write_image(output_path)
```

- [ ] **Step 5: Run tests**

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/signal_engine/aggregator.py src/signal_engine/charts.py tests/signal_engine/test_evidence_engine.py
git commit -m "feat(signal_engine): add Risk Tree aggregator (likelihood x impact) and bubble chart"
```

---

## Task 10: Evidence Attribution Aggregator + Chart

**Files:**
- Modify: `src/signal_engine/aggregator.py`
- Modify: `src/signal_engine/charts.py`
- Modify: `tests/signal_engine/test_evidence_engine.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.aggregator import compute_evidence_attribution

def _make_attribution_df():
    return pd.DataFrame([
        {"company": "CATL", "stream": "perception",   "confidence": 0.8},
        {"company": "CATL", "stream": "ground_truth", "confidence": 0.9},
        {"company": "CATL", "stream": "ground_truth", "confidence": 0.95},
        {"company": "LGES", "stream": "perception",   "confidence": 0.7},
        {"company": "LGES", "stream": "policy",       "confidence": 0.85},
    ])

def test_compute_evidence_attribution_columns():
    df = compute_evidence_attribution(_make_attribution_df())
    for col in ["company", "stream", "doc_count", "avg_confidence"]:
        assert col in df.columns

def test_compute_evidence_attribution_counts():
    df = compute_evidence_attribution(_make_attribution_df())
    catl_gt = df[(df["company"] == "CATL") & (df["stream"] == "ground_truth")]["doc_count"].values[0]
    assert catl_gt == 2

def test_compute_evidence_attribution_avg_confidence():
    df = compute_evidence_attribution(_make_attribution_df())
    catl_gt = df[(df["company"] == "CATL") & (df["stream"] == "ground_truth")]["avg_confidence"].values[0]
    assert abs(catl_gt - 0.925) < 0.01
```

```
pytest tests/signal_engine/test_evidence_engine.py -k "attribution" -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `compute_evidence_attribution` in `src/signal_engine/aggregator.py`**

Append:

```python
def compute_evidence_attribution(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (company, stream), group in df.groupby(["company", "stream"]):
        avg_conf = round(float(group["confidence"].mean()), 3) if "confidence" in df.columns else None
        rows.append({
            "company": company,
            "stream": stream,
            "doc_count": len(group),
            "avg_confidence": avg_conf,
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 3: Write failing chart test**

Add to `tests/signal_engine/test_evidence_engine.py`:

```python
from src.signal_engine.charts import build_evidence_scale_chart

def test_build_evidence_scale_chart_creates_file(tmp_path):
    df = compute_evidence_attribution(_make_attribution_df())
    out = str(tmp_path / "evidence_scale.png")
    build_evidence_scale_chart(df, out)
    assert pathlib.Path(out).exists()
```

- [ ] **Step 4: Implement `build_evidence_scale_chart` in `src/signal_engine/charts.py`**

Append:

```python
def build_evidence_scale_chart(attribution_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if attribution_df.empty:
        go.Figure().write_image(output_path)
        return

    colors = {
        "perception": "#60A5FA",
        "ground_truth": "#1D4ED8",
        "policy": "#A78BFA",
        "operations": "#34D399",
    }

    fig = go.Figure()
    for stream, group in attribution_df.groupby("stream"):
        fig.add_trace(go.Bar(
            name=stream,
            x=group["company"],
            y=group["doc_count"],
            marker_color=colors.get(stream, "grey"),
            text=group["avg_confidence"].apply(lambda c: f"conf: {c:.0%}" if c else ""),
            textposition="outside",
        ))

    fig.update_layout(
        title="Evidence Attribution: Documents by Company and Stream",
        barmode="stack",
        yaxis_title="Document Count",
        template="plotly_white",
        width=800,
        height=500,
    )
    fig.write_image(output_path)
```

- [ ] **Step 5: Run tests**

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/signal_engine/aggregator.py src/signal_engine/charts.py tests/signal_engine/test_evidence_engine.py
git commit -m "feat(signal_engine): add Evidence Attribution aggregator and stacked-bar chart"
```

---

## Task 11: Wire Evidence Engine into signal_engine CLI

**Files:**
- Modify: `src/signal_engine/cli.py`
- Modify: `tests/signal_engine/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add to `tests/signal_engine/test_cli.py`:

```python
import json
from src.signal_engine.cli import run_signal_engine

def test_run_signal_engine_produces_five_new_charts(tmp_path):
    tag = {
        "company": "CATL", "stream": "perception", "source_weight": 1.0,
        "date": "2025-06-01", "sentiment_score": 7.5, "direction": "positive",
        "confidence": 0.8, "topic_cluster": "Capex_Execution", "geo_exposure": ["US"],
        "globalization_model": "export-led", "localization_score": 8,
        "subsidy_dependency": 3, "execution_quality": 9, "margin_signal": 7,
        "capex_signal": 8, "ROIC_signal": 7, "contradiction_flag": False,
        "contradiction_reason": None, "claim_summary": "CATL on track.", "key_quote": None,
    }
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    (tags_dir / "catl_test.json").write_text(json.dumps(tag))

    out_dir = tmp_path / "charts"
    out_dir.mkdir()

    run_signal_engine(str(tags_dir), str(out_dir), human_inputs_path=None)

    for fname in [
        "differentiation_matrix.png",
        "why_now_timeline.png",
        "contradictions.png",
        "risk_tree.png",
        "evidence_scale.png",
    ]:
        assert (out_dir / fname).exists(), f"Missing: {fname}"
```

```
pytest tests/signal_engine/test_cli.py::test_run_signal_engine_produces_five_new_charts -v
```

Expected: FAIL.

- [ ] **Step 2: Update `src/signal_engine/cli.py`**

Read the file first:

```bash
cat src/signal_engine/cli.py
```

Add these imports at the top of the file (not inside the function):

```python
from src.signal_engine.aggregator import (
    compute_differentiation_matrix,
    compute_timeline,
    compute_contradictions,
    compute_risk_tree,
    compute_evidence_attribution,
)
from src.signal_engine.charts import (
    build_differentiation_matrix_chart,
    build_why_now_timeline_chart,
    build_contradiction_chart,
    build_risk_tree_chart,
    build_evidence_scale_chart,
)
```

In `run_signal_engine()`, after the existing chart generation calls, append:

```python
import os as _os

diff_df = compute_differentiation_matrix(tag_df)
build_differentiation_matrix_chart(diff_df, _os.path.join(output_dir, "differentiation_matrix.png"))

timeline_df = compute_timeline(tag_df)
build_why_now_timeline_chart(timeline_df, _os.path.join(output_dir, "why_now_timeline.png"))

contra_df = compute_contradictions(tag_df)
build_contradiction_chart(contra_df, _os.path.join(output_dir, "contradictions.png"))

risk_df = compute_risk_tree(tag_df)
build_risk_tree_chart(risk_df, _os.path.join(output_dir, "risk_tree.png"))

attrib_df = compute_evidence_attribution(tag_df)
build_evidence_scale_chart(attrib_df, _os.path.join(output_dir, "evidence_scale.png"))
```

- [ ] **Step 3: Run full signal engine test suite**

```
pytest tests/signal_engine/ -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/signal_engine/cli.py tests/signal_engine/test_cli.py
git commit -m "feat(signal_engine): wire all 5 evidence engine charts into CLI

CLI now produces 7 total chart PNGs: the existing quality_divergence_matrix
and trend_inflection plus the new differentiation_matrix, why_now_timeline,
contradictions, risk_tree, and evidence_scale."
```

---

## Self-Review

**Spec coverage:**
- `compute_differentiation_matrix()` + grouped bar chart → Task 6 ✓
- `compute_timeline()` + line chart → Task 7 ✓
- `compute_contradictions()` + scatter chart → Task 8 ✓
- Risk Tree (likelihood × impact) + bubble chart → Task 9 ✓
- Evidence Attribution + stacked bar → Task 10 ✓
- All 5 charts wired into CLI → Task 11 ✓

**No placeholders present.**

**Type consistency:** `compute_differentiation_matrix()` returns DataFrame with columns `factor, CATL, LGES, delta` — used by Phase 4's `build_synthesis_prompt(diff_df=...)` which calls `df["factor"]`, `df["CATL"]`, etc. — consistent. `compute_contradictions()` returns `claim_summary` column — used by Phase 4's prompt builder `_format_contradictions()` which reads `row['claim_summary']` — consistent.

