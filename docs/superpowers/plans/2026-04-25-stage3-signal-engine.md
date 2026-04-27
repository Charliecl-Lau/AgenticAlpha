# Stage 3: Signal Engine (Data Aggregation & Charts) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load all JSON tag files from Stage 2, aggregate them with Pandas into two chart deliverables — the Quality Divergence Matrix (normalized by company coverage) and the Trend Inflection bar — and export them as PNG files to `output/charts/`.

**Architecture:** A loader reads `data/processed/tags/*.json` into a single DataFrame. Two aggregator functions (raw+normalized counts, mean sentiment) feed two chart builders. The divergence matrix embeds a mean sentiment subtitle so one chart carries both dimensions. A CLI entrypoint runs the full pipeline. Tests use fixture DataFrames — no file I/O or Plotly rendering in unit tests.

**Tech Stack:** Python 3.11+, pandas, plotly, kaleido, pytest

**Prerequisite:** Stage 2 complete. `data/processed/tags/` contains `.json` files with the Tag schema plus `stream`, `company`, `source_file` fields.

**Why normalization matters:** If CATL generates 30 articles and LGES 10, raw counts will make CATL's bars dominate by volume alone. Normalizing to percentage-of-coverage-per-company shows topic emphasis (quality signal), not just media attention (quantity artifact).

---

### Task 1: Tag JSON Loader

**Files:**
- Create: `src/signal_engine/loader.py`
- Test: `tests/signal_engine/test_loader.py`

- [ ] **Step 1: Write failing test**

```python
# tests/signal_engine/test_loader.py
import json
import pytest
import pandas as pd
from src.signal_engine.loader import load_tags

_TAG_A = {
    "sentiment_score": 8, "direction": "positive",
    "topic_cluster": "Organic_Scale_vs_Export", "geo_exposure": ["EU"],
    "summary": "CATL Hungary plant reached 50 GWh.", "stream": "perception",
    "company": "CATL", "source_file": "catl_abc123.md",
}
_TAG_B = {
    "sentiment_score": 4, "direction": "negative",
    "topic_cluster": "Subsidy_Dependence", "geo_exposure": ["US"],
    "summary": "LGES IRA credits represented 62% of revenue.", "stream": "perception",
    "company": "LGES", "source_file": "lges_def456.md",
}


def test_load_tags_returns_dataframe(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_TAG_A))
    (tmp_path / "b.json").write_text(json.dumps(_TAG_B))
    df = load_tags(str(tmp_path))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_load_tags_has_expected_columns(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_TAG_A))
    df = load_tags(str(tmp_path))
    for col in ["sentiment_score", "direction", "topic_cluster", "geo_exposure", "company", "stream"]:
        assert col in df.columns


def test_load_tags_skips_malformed_json(tmp_path):
    (tmp_path / "good.json").write_text(json.dumps(_TAG_A))
    (tmp_path / "bad.json").write_text("{not valid json")
    df = load_tags(str(tmp_path))
    assert len(df) == 1


def test_load_tags_raises_on_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="No tag files"):
        load_tags(str(tmp_path))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/signal_engine/test_loader.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.signal_engine.loader'`

- [ ] **Step 3: Add pandas, plotly, kaleido to requirements.txt**

Add these lines (if not already present):

```
pandas==2.2.2
plotly==5.22.0
kaleido==0.2.1
```

Then install:

```bash
pip install pandas==2.2.2 plotly==5.22.0 kaleido==0.2.1
```

- [ ] **Step 4: Implement loader**

```python
# src/signal_engine/loader.py
import json
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def load_tags(tags_dir: str) -> pd.DataFrame:
    records = []
    for path in sorted(Path(tags_dir).glob("*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.warning("Skipping %s: %s", path.name, exc)
    if not records:
        raise ValueError(f"No tag files found in {tags_dir}")
    return pd.DataFrame(records)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/signal_engine/test_loader.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/signal_engine/loader.py tests/signal_engine/test_loader.py requirements.txt
git commit -m "feat(signal_engine): add tag JSON loader

Reads all *.json files from the tags directory into a Pandas DataFrame.
Malformed files are skipped with a warning. Raises ValueError when the
directory is empty so callers fail fast rather than silently producing
empty charts."
```

---

### Task 2: Topic Frequency Aggregator

**Files:**
- Create: `src/signal_engine/aggregator.py`
- Test: `tests/signal_engine/test_aggregator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/signal_engine/test_aggregator.py
import pandas as pd
import pytest
from src.signal_engine.aggregator import compute_topic_counts, compute_sentiment_trend


def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "stream": "perception", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 8, "direction": "positive"},
        {"company": "CATL", "stream": "perception", "topic_cluster": "Organic_Scale_vs_Export",
         "sentiment_score": 7, "direction": "positive"},
        {"company": "LGES", "stream": "perception", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 4, "direction": "negative"},
        {"company": "LGES", "stream": "perception", "topic_cluster": "Subsidy_Dependence",
         "sentiment_score": 3, "direction": "negative"},
        {"company": "LGES", "stream": "perception", "topic_cluster": "Geopolitical_Noise",
         "sentiment_score": 5, "direction": "neutral"},
    ])


def test_compute_topic_counts_returns_counts_per_company_and_topic():
    df = _make_df()
    counts = compute_topic_counts(df, stream="perception")
    catl_row = counts[(counts["company"] == "CATL") & (counts["topic_cluster"] == "Organic_Scale_vs_Export")]
    assert catl_row["count"].iloc[0] == 2
    lges_subsidy = counts[(counts["company"] == "LGES") & (counts["topic_cluster"] == "Subsidy_Dependence")]
    assert lges_subsidy["count"].iloc[0] == 2


def test_compute_topic_counts_filters_by_stream():
    df = _make_df()
    counts = compute_topic_counts(df, stream="ground_truth")
    assert len(counts) == 0


def test_compute_topic_counts_normalizes_by_company_total():
    df = _make_df()
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    # CATL: 2 Organic_Scale_vs_Export out of 2 total → 100.0%
    catl_row = counts[(counts["company"] == "CATL") & (counts["topic_cluster"] == "Organic_Scale_vs_Export")]
    assert abs(catl_row["count"].iloc[0] - 100.0) < 0.1
    # LGES: 2 Subsidy_Dependence out of 3 total → 66.7%
    lges_row = counts[(counts["company"] == "LGES") & (counts["topic_cluster"] == "Subsidy_Dependence")]
    assert abs(lges_row["count"].iloc[0] - 66.7) < 0.2


def test_compute_topic_counts_normalize_sums_to_100_per_company():
    df = _make_df()
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    lges_total = counts[counts["company"] == "LGES"]["count"].sum()
    assert abs(lges_total - 100.0) < 0.2


def test_compute_sentiment_trend_returns_mean_per_company():
    df = _make_df()
    trend = compute_sentiment_trend(df, stream="perception")
    catl_mean = trend[trend["company"] == "CATL"]["mean_sentiment"].iloc[0]
    assert abs(catl_mean - 7.5) < 0.01
    lges_mean = trend[trend["company"] == "LGES"]["mean_sentiment"].iloc[0]
    assert abs(lges_mean - 4.0) < 0.01


def test_compute_sentiment_trend_empty_stream_returns_empty():
    df = _make_df()
    trend = compute_sentiment_trend(df, stream="ground_truth")
    assert len(trend) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/signal_engine/test_aggregator.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement aggregator**

```python
# src/signal_engine/aggregator.py
import pandas as pd


def compute_topic_counts(df: pd.DataFrame, stream: str, normalize: bool = False) -> pd.DataFrame:
    filtered = df[df["stream"] == stream]
    if filtered.empty:
        return pd.DataFrame(columns=["company", "topic_cluster", "count"])
    counts = (
        filtered.groupby(["company", "topic_cluster"])
        .size()
        .reset_index(name="count")
    )
    if normalize:
        totals = filtered.groupby("company").size().rename("total")
        counts = counts.join(totals, on="company")
        counts["count"] = (counts["count"] / counts["total"] * 100).round(1)
        counts = counts.drop(columns="total")
    return counts


def compute_sentiment_trend(df: pd.DataFrame, stream: str) -> pd.DataFrame:
    filtered = df[df["stream"] == stream]
    if filtered.empty:
        return pd.DataFrame(columns=["company", "mean_sentiment"])
    trend = (
        filtered.groupby("company")["sentiment_score"]
        .mean()
        .reset_index()
        .rename(columns={"sentiment_score": "mean_sentiment"})
    )
    return trend
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/signal_engine/test_aggregator.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/signal_engine/aggregator.py tests/signal_engine/test_aggregator.py
git commit -m "feat(signal_engine): add topic frequency and sentiment aggregators

compute_topic_counts groups by company+topic_cluster. normalize=True
converts raw counts to percentage-of-coverage-per-company, preventing
CATL's larger article pool from inflating bar heights relative to LGES.
compute_sentiment_trend gives per-company mean for trend overlays."
```

---

### Task 3: Quality Divergence Matrix Chart

**Files:**
- Create: `src/signal_engine/charts.py`
- Test: `tests/signal_engine/test_charts.py`

- [ ] **Step 1: Write failing test**

```python
# tests/signal_engine/test_charts.py
import pandas as pd
import pytest
import plotly.graph_objects as go
from src.signal_engine.charts import build_divergence_matrix, build_trend_inflection


def _counts_df():
    return pd.DataFrame([
        {"company": "CATL", "topic_cluster": "Organic_Scale_vs_Export", "count": 66.7},
        {"company": "CATL", "topic_cluster": "Subsidy_Dependence", "count": 13.3},
        {"company": "LGES", "topic_cluster": "Organic_Scale_vs_Export", "count": 16.7},
        {"company": "LGES", "topic_cluster": "Subsidy_Dependence", "count": 60.0},
    ])


def _trend_df():
    return pd.DataFrame([
        {"company": "CATL", "mean_sentiment": 7.4},
        {"company": "LGES", "mean_sentiment": 4.1},
    ])


def test_build_divergence_matrix_returns_plotly_figure():
    fig = build_divergence_matrix(_counts_df())
    assert isinstance(fig, go.Figure)


def test_build_divergence_matrix_has_both_companies_in_data():
    fig = build_divergence_matrix(_counts_df())
    all_text = str(fig.to_json())
    assert "CATL" in all_text
    assert "LGES" in all_text


def test_build_divergence_matrix_has_data_labels():
    fig = build_divergence_matrix(_counts_df())
    # At least one bar trace must have text labels set
    assert any(trace.text is not None for trace in fig.data)


def test_build_divergence_matrix_adds_sentiment_subtitle_when_trend_provided():
    fig = build_divergence_matrix(_counts_df(), trend_df=_trend_df())
    title_text = fig.layout.title.text
    # Both sentiment scores must appear in the title subtitle
    assert "7.4" in title_text
    assert "4.1" in title_text


def test_build_divergence_matrix_no_subtitle_without_trend():
    fig = build_divergence_matrix(_counts_df())
    title_text = fig.layout.title.text
    assert "Mean sentiment" not in title_text


def test_build_divergence_matrix_raises_on_missing_columns():
    bad_df = pd.DataFrame([{"company": "CATL", "count": 5}])
    with pytest.raises(KeyError):
        build_divergence_matrix(bad_df)


def test_build_trend_inflection_returns_plotly_figure():
    fig = build_trend_inflection(_trend_df())
    assert isinstance(fig, go.Figure)


def test_build_trend_inflection_y_axis_bounded_0_to_10():
    fig = build_trend_inflection(_trend_df())
    assert fig.layout.yaxis.range == [0, 10]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/signal_engine/test_charts.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement charts**

```python
# src/signal_engine/charts.py
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_CATL_COLOR = "#1f77b4"
_LGES_COLOR = "#d62728"

_TOPIC_LABELS: dict[str, str] = {
    "Organic_Scale_vs_Export": "Organic Scale",
    "Subsidy_Dependence": "Subsidy Dep.",
    "Geopolitical_Noise": "Geo. Noise",
    "Capex_Execution": "Capex Exec.",
    "Other": "Other",
}


def build_divergence_matrix(
    counts_df: pd.DataFrame,
    trend_df: pd.DataFrame | None = None,
) -> go.Figure:
    # Raises KeyError if required columns are missing — intentional validation
    _ = counts_df[["company", "topic_cluster", "count"]]

    fig = go.Figure()
    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = counts_df[counts_df["company"] == company]
        x_labels = [_TOPIC_LABELS.get(t, t) for t in sub["topic_cluster"]]
        fig.add_trace(go.Bar(
            name=company,
            x=x_labels,
            y=sub["count"],
            text=[f"{v:.1f}" for v in sub["count"]],
            textposition="outside",
            marker_color=color,
        ))

    title = "Quality Divergence Matrix: Topic Coverage Share by Company (%)"
    if trend_df is not None and not trend_df.empty:
        catl_s = trend_df[trend_df["company"] == "CATL"]["mean_sentiment"]
        lges_s = trend_df[trend_df["company"] == "LGES"]["mean_sentiment"]
        if not catl_s.empty and not lges_s.empty:
            title += (
                f"<br><sub>Mean sentiment — CATL: {catl_s.iloc[0]:.1f}/10"
                f" | LGES: {lges_s.iloc[0]:.1f}/10</sub>"
            )

    fig.update_layout(
        title=title,
        xaxis_title="Topic Cluster",
        yaxis_title="Share of Coverage (%)",
        barmode="group",
        legend_title="Company",
        template="plotly_white",
        font=dict(size=13),
        xaxis=dict(tickangle=-35),
        margin=dict(b=90, t=90),
    )
    return fig


def build_trend_inflection(trend_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    colors = {"CATL": _CATL_COLOR, "LGES": _LGES_COLOR}
    for _, row in trend_df.iterrows():
        company = row["company"]
        score = row["mean_sentiment"]
        fig.add_trace(go.Bar(
            name=company,
            x=[company],
            y=[score],
            text=[f"{score:.1f}"],
            textposition="outside",
            marker_color=colors.get(company, "grey"),
        ))

    fig.update_layout(
        title="Mean Perception Sentiment by Company (1–10 scale)",
        yaxis_title="Mean Sentiment Score",
        yaxis_range=[0, 10],
        template="plotly_white",
        font=dict(size=13),
        showlegend=False,
    )
    return fig
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/signal_engine/test_charts.py -v
```

Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/signal_engine/charts.py tests/signal_engine/test_charts.py
git commit -m "feat(signal_engine): add Quality Divergence Matrix and Trend Inflection charts

build_divergence_matrix renders a grouped bar chart with normalized
coverage percentages, shortened x-axis labels (rotated 45°) to prevent
overlap, data labels on each bar, and an optional mean-sentiment subtitle
when trend_df is supplied — so one chart carries both the topic-emphasis
and sentiment-quality dimensions. build_trend_inflection shows per-company
mean sentiment bounded 0-10 for the deck's Why-Now slide."
```

---

### Task 4: Signal Engine CLI

**Files:**
- Create: `src/signal_engine/cli.py`
- Test: `tests/signal_engine/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/signal_engine/test_cli.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import plotly.graph_objects as go
import pytest
from src.signal_engine.cli import run_signal_engine


def _write_tag(path: Path, company: str, topic: str, stream: str = "perception") -> None:
    path.write_text(json.dumps({
        "sentiment_score": 7, "direction": "positive",
        "topic_cluster": topic, "geo_exposure": ["EU"],
        "summary": "Summary sentence.", "stream": stream,
        "company": company, "source_file": path.name,
    }))


def test_run_signal_engine_produces_two_png_files(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    _write_tag(tags_dir / "catl_1.json", "CATL", "Organic_Scale_vs_Export")
    _write_tag(tags_dir / "lges_1.json", "LGES", "Subsidy_Dependence")
    out_dir = tmp_path / "charts"

    dummy_fig = MagicMock(spec=go.Figure)
    with patch("src.signal_engine.cli.build_divergence_matrix", return_value=dummy_fig), \
         patch("src.signal_engine.cli.build_trend_inflection", return_value=dummy_fig):
        run_signal_engine(tags_dir=str(tags_dir), output_dir=str(out_dir))

    assert dummy_fig.write_image.call_count == 2


def test_run_signal_engine_passes_trend_to_divergence_matrix(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    _write_tag(tags_dir / "catl_1.json", "CATL", "Organic_Scale_vs_Export")
    _write_tag(tags_dir / "lges_1.json", "LGES", "Subsidy_Dependence")
    out_dir = tmp_path / "charts"

    dummy_fig = MagicMock(spec=go.Figure)
    captured_kwargs: dict = {}

    def capture_divergence(counts_df, trend_df=None):
        captured_kwargs["trend_df"] = trend_df
        return dummy_fig

    with patch("src.signal_engine.cli.build_divergence_matrix", side_effect=capture_divergence), \
         patch("src.signal_engine.cli.build_trend_inflection", return_value=dummy_fig):
        run_signal_engine(tags_dir=str(tags_dir), output_dir=str(out_dir))

    assert captured_kwargs["trend_df"] is not None
    assert len(captured_kwargs["trend_df"]) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/signal_engine/test_cli.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement CLI**

```python
# src/signal_engine/cli.py
import argparse
import logging
from pathlib import Path
from src.signal_engine.loader import load_tags
from src.signal_engine.aggregator import compute_topic_counts, compute_sentiment_trend
from src.signal_engine.charts import build_divergence_matrix, build_trend_inflection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def run_signal_engine(tags_dir: str, output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = load_tags(tags_dir)
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    trend = compute_sentiment_trend(df, stream="perception")

    divergence_fig = build_divergence_matrix(counts, trend_df=trend)
    inflection_fig = build_trend_inflection(trend)

    divergence_path = str(out / "quality_divergence_matrix.png")
    inflection_path = str(out / "trend_inflection.png")
    divergence_fig.write_image(divergence_path, width=1200, height=700)
    inflection_fig.write_image(inflection_path, width=900, height=600)
    logger.info("Saved %s", divergence_path)
    logger.info("Saved %s", inflection_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate signal charts from tagged data")
    parser.add_argument("--tags", default="data/processed/tags")
    parser.add_argument("--output", default="output/charts")
    args = parser.parse_args()
    run_signal_engine(tags_dir=args.tags, output_dir=args.output)
    print(f"Charts written to {args.output}/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all signal_engine tests**

```bash
pytest tests/signal_engine/ -v
```

Expected: PASS (all 14 tests)

- [ ] **Step 5: Commit**

```bash
git add src/signal_engine/cli.py tests/signal_engine/test_cli.py
git commit -m "feat(signal_engine): add CLI that exports two charts as PNG

Loads tags, computes normalized topic coverage percentages and per-company
mean sentiment for the perception stream, then builds Plotly figures.
The divergence matrix receives the trend DataFrame so it can embed a
mean-sentiment subtitle. Charts write to fixed paths so the renderer
can reference them without configuration."
```

---

### Task 5: Smoke-Test with Real Data

This task is not automated — it validates that the charts visually reinforce the CATL vs. LGES quality gap after a full ingestion + tagging run.

**Files:**
- No new files. Run against actual Stage 1 + 2 output.

- [ ] **Step 1: Run full pipeline**

```bash
python -m src.signal_engine.cli --tags data/processed/tags --output output/charts
```

- [ ] **Step 2: Open PNGs and check for asymmetry**

Open `output/charts/quality_divergence_matrix.png`. Verify:
- CATL bar for `Organic Scale` (i.e., Organic_Scale_vs_Export) is taller than LGES's
- LGES bar for `Subsidy Dep.` is taller than CATL's
- Sentiment subtitle shows CATL mean ≥ LGES mean

Open `output/charts/trend_inflection.png`. Verify:
- CATL bar is visibly higher than LGES bar

If either check fails, the most likely cause is upstream tag drift (Stage 2 prompt issue), not a Stage 3 bug. Check `data/processed/tags/*.json` for asymmetry violations before editing charts.

- [ ] **Step 3: Quick tag audit command**

```bash
python -c "
import json, pathlib, collections
tags = list(pathlib.Path('data/processed/tags').glob('*.json'))
counts = collections.Counter()
for t in tags:
    d = json.loads(t.read_text())
    counts[(d['company'], d['topic_cluster'])] += 1
for (company, cluster), n in sorted(counts.items()):
    print(f'{company:6} {cluster:30} {n}')
"
```

Expected pattern:
```
CATL   Capex_Execution                5
CATL   Organic_Scale_vs_Export       12
LGES   Geopolitical_Noise             3
LGES   Subsidy_Dependence            10
```

If `CATL` has `Subsidy_Dependence` entries or `LGES` has `Organic_Scale_vs_Export` entries — stop and fix Stage 2 prompt before proceeding.

- [ ] **Step 4: If charts look correct — commit with note**

```bash
git add output/charts/
git commit -m "chore: add generated chart PNGs from live data smoke test

quality_divergence_matrix.png and trend_inflection.png produced from
[N] perception tags after full ingestion and Gemma 4 tagging run.
CATL Organic_Scale dominates vs LGES Subsidy_Dependence as expected."
```

---

## Self-Review Against Spec

**Spec coverage:**
- Load tags from Stage 2 JSON output ✓ (Task 1)
- Quality Divergence Matrix chart ✓ (Task 3)
- Trend Inflection chart ✓ (Task 3)
- PNG export to `output/charts/` ✓ (Task 4)
- Tests use fixture DataFrames, no live rendering ✓ (all tasks)
- Graceful skip of malformed files ✓ (Task 1)
- Raises on empty directory ✓ (Task 1)
- TDD throughout ✓

**Additions from audit (accepted):**
- Normalization by company total prevents coverage-volume bias ✓ (Task 2)
- Data labels on bars for deck readability ✓ (Task 3)
- X-axis label rotation + shortened topic names prevent overlap ✓ (Task 3)
- Mean sentiment subtitle on divergence matrix adds second dimension ✓ (Task 3–4)
- Smoke test with explicit asymmetry validation criteria ✓ (Task 5)

**What this plan deliberately does NOT include:**
- Ground truth aggregation — marked "future iteration" in audit; YAGNI, adds a third stream path with no clear chart slot in current deck
- Date/time-series trend lines — Stage 2 produces no timestamps; would require upstream changes
- Interactive HTML output — static PNGs are specified by Stage 5 (renderer); scope creep
- Separate weighted-score chart — the sentiment subtitle on the divergence matrix carries the same message without a third PNG to manage

**Placeholder scan:** None found.

**Type consistency check:**
- `compute_topic_counts(df, stream, normalize=False)` → used in CLI as `compute_topic_counts(df, stream="perception", normalize=True)` ✓
- `build_divergence_matrix(counts_df, trend_df=None)` → called in CLI as `build_divergence_matrix(counts, trend_df=trend)` and in tests as `build_divergence_matrix(_counts_df())` and `build_divergence_matrix(_counts_df(), trend_df=_trend_df())` ✓
- `run_signal_engine(tags_dir, output_dir)` → consistent across implementation and tests ✓
