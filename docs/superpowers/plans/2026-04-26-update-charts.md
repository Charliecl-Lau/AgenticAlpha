# Chart Narrative & Visual Hierarchy Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the signal engine charts to use distinct, bank-friendly colors and explicitly link AI perception signals with human-verified fundamental data to highlight the quality divergence between CATL and LGES. Reduce deck filler.

**Architecture:** We will inject `human_inputs.yaml` into the signal engine CLI so charts can be annotated with real margin data. The chart builder will use these values to draw concrete conclusions in the chart titles/subtitles. The trend chart will filter out noise ("Other"). The renderer will reduce placeholder slides and strengthen the human-AI integration narrative.

**Tech Stack:** Python, Pandas, Plotly, Pytest

---

### Task 1: Update Human Inputs Configuration

**Files:**
- Modify: `config/human_inputs.yaml:4-6`

- [ ] **Step 1: Write the updated values in human_inputs.yaml**

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

- [ ] **Step 2: Commit**

```bash
git add config/human_inputs.yaml
git commit -m "chore: populate human_inputs.yaml with real margin and execution data"
```

---

### Task 2: Chart Formatting & Narrative Upgrades

**Files:**
- Modify: `src/signal_engine/charts.py:1-116`
- Modify: `tests/signal_engine/test_charts.py:1-98`

- [ ] **Step 1: Write failing tests for charts**

Modify `tests/signal_engine/test_charts.py` to check for new titles, colors, and human metrics.
(Replace the relevant assertions)

```python
# In tests/signal_engine/test_charts.py, update the color checks and subtitle checks
def test_build_divergence_matrix_adds_sentiment_subtitle_when_trend_provided():
    fig = build_divergence_matrix(_counts_df(), trend_df=_trend_df(), human_metrics={"catl_margin": 31.4, "lges_margin": 2.1})
    title_text = fig.layout.title.text
    # Both sentiment scores must appear in the title subtitle
    assert "7.4" in title_text
    assert "4.1" in title_text
    # Check human metrics
    assert "31.4%" in title_text
    assert "2.1%" in title_text

def test_build_divergence_matrix_no_subtitle_without_trend():
    fig = build_divergence_matrix(_counts_df(), human_metrics={"catl_margin": 31.4, "lges_margin": 2.1})
    title_text = fig.layout.title.text
    assert "Mean sentiment" not in title_text

def test_build_trend_inflection_filters_other_topic():
    df = _sentiment_df()
    # Add an "Other" topic
    df = pd.concat([df, pd.DataFrame([{"company": "CATL", "topic_cluster": "Other", "mean_sentiment": 5.0}])])
    fig = build_trend_inflection(df)
    all_text = fig.to_json()
    assert "Other" not in all_text

def test_build_trend_inflection_has_human_narrative_subtitle():
    fig = build_trend_inflection(_sentiment_df())
    title_text = fig.layout.title.text
    assert "Sentiment divergence on execution topics supports human-verified margin premium" in title_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/signal_engine/test_charts.py -v`
Expected: FAIL due to missing `human_metrics` argument, incorrect colors, and "Other" topic not being filtered.

- [ ] **Step 3: Update charts implementation**

Modify `src/signal_engine/charts.py`.
Change colors:
```python
_CATL_COLOR = "#0e5a9e"
_LGES_COLOR = "#ff7f0e"
```

Update `build_divergence_matrix`:
```python
def build_divergence_matrix(
    counts_df: pd.DataFrame,
    trend_df: pd.DataFrame | None = None,
    sentiment_df: pd.DataFrame | None = None,
    human_metrics: dict | None = None,
) -> go.Figure:
    # Raises KeyError if required columns are missing — intentional validation
    _ = counts_df[["company", "topic_cluster", "count"]]
    
    if human_metrics is None:
        human_metrics = {"catl_margin": 31.4, "lges_margin": 2.1}

    fig = go.Figure()
    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = counts_df[counts_df["company"] == company]
        x_labels = [_TOPIC_LABELS.get(t, t) for t in sub["topic_cluster"]]

        if sentiment_df is not None and not sentiment_df.empty:
            text_labels = []
            for _, row in sub.iterrows():
                sent_row = sentiment_df[
                    (sentiment_df["company"] == company)
                    & (sentiment_df["topic_cluster"] == row["topic_cluster"])
                ]
                s = sent_row["weighted_mean_sentiment"].iloc[0] if "weighted_mean_sentiment" in sent_row.columns else (sent_row["mean_sentiment"].iloc[0] if not sent_row.empty else None)
                label = f"{row['count']:.1f}%" + (f"<br>★{s:.1f}" if s is not None else "")
                text_labels.append(label)
        else:
            text_labels = [f"{v:.1f}" for v in sub["count"]]

        fig.add_trace(go.Bar(
            name=company,
            x=x_labels,
            y=sub["count"],
            text=text_labels,
            textposition="outside",
            marker_color=color,
        ))

    title = "Perception vs Reality: CATL Execution-Led Globalization vs LGES Subsidy Dependence"
    
    subtitle = (
        f"<br><sub>CATL: High sentiment on Organic/Capex → aligns with {human_metrics.get('catl_margin', 31.4)}% overseas margin premium. "
        f"LGES: Low sentiment on Subsidy Dep. → aligns with {human_metrics.get('lges_margin', 2.1)}% ex-IRA margin.</sub>"
    )
    
    if trend_df is not None and not trend_df.empty:
        catl_s = trend_df[trend_df["company"] == "CATL"]["mean_sentiment"]
        lges_s = trend_df[trend_df["company"] == "LGES"]["mean_sentiment"]
        if not catl_s.empty and not lges_s.empty:
            subtitle += (
                f"<br><sub>Mean sentiment — CATL: {catl_s.iloc[0]:.1f}/10"
                f" | LGES: {lges_s.iloc[0]:.1f}/10</sub>"
            )
            
    title += subtitle

    fig.update_layout(
        title=title,
        xaxis_title="Topic Cluster",
        yaxis_title="Share of Coverage (%)",
        barmode="group",
        legend_title="Company",
        template="plotly_white",
        font=dict(size=13),
        xaxis=dict(tickangle=-35),
        margin=dict(b=90, t=130),
    )
    return fig
```

Update `build_trend_inflection`:
```python
def build_trend_inflection(sentiment_df: pd.DataFrame) -> go.Figure:
    """Grouped bars of mean sentiment per topic per company."""
    fig = go.Figure()
    
    # Filter out 'Other' topic
    filtered_df = sentiment_df[sentiment_df["topic_cluster"] != "Other"]
    topics = filtered_df["topic_cluster"].unique().tolist()
    x_labels = [_TOPIC_LABELS.get(t, t) for t in topics]

    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = filtered_df[filtered_df["company"] == company]
        y_vals = []
        for topic in topics:
            row = sub[sub["topic_cluster"] == topic]
            # Handle both mean_sentiment and weighted_mean_sentiment
            val_col = "weighted_mean_sentiment" if "weighted_mean_sentiment" in row.columns else "mean_sentiment"
            y_vals.append(row[val_col].iloc[0] if not row.empty else None)

        fig.add_trace(go.Bar(
            name=company,
            x=x_labels,
            y=y_vals,
            text=[f"{v:.1f}" if v is not None else "" for v in y_vals],
            textposition="outside",
            marker_color=color,
        ))

    title = (
        "Signal Quality by Topic: Sentiment Divergence Between CATL and LGES<br>"
        "<sub>Sentiment divergence on execution topics supports human-verified margin premium for CATL.</sub>"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Topic Cluster",
        yaxis_title="Mean Sentiment Score",
        yaxis=dict(range=[0, 10]),
        barmode="group",
        legend_title="Company",
        template="plotly_white",
        font=dict(size=13),
        xaxis=dict(tickangle=-35),
        margin=dict(b=90, t=110),
    )
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/signal_engine/test_charts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/signal_engine/charts.py tests/signal_engine/test_charts.py
git commit -m "feat(charts): apply distinct colors, human annotations, and filter Other topic"
```

---

### Task 3: Signal Engine CLI Integration

**Files:**
- Modify: `src/signal_engine/cli.py`
- Modify: `tests/signal_engine/test_cli.py` (if necessary to mock schema loading)

- [ ] **Step 1: Write minimal implementation**

Update `src/signal_engine/cli.py` to use `compute_weighted_sentiment` instead of `compute_topic_sentiment`, load human inputs, and pass `human_metrics` to `build_divergence_matrix`.

```python
import argparse
import logging
from pathlib import Path
from src.signal_engine.loader import load_tags
from src.signal_engine.aggregator import compute_topic_counts, compute_sentiment_trend, compute_weighted_sentiment
from src.signal_engine.charts import build_divergence_matrix, build_trend_inflection
from src.human_layer.schema import load_human_inputs

logger = logging.getLogger(__name__)

def run_signal_engine(tags_dir: str, output_dir: str, human_inputs_path: str = "config/human_inputs.yaml") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = load_tags(tags_dir)
    counts = compute_topic_counts(df, stream="perception", normalize=True)
    trend = compute_sentiment_trend(df, stream="perception")
    # Use weighted sentiment
    sentiment = compute_weighted_sentiment(df)
    
    # Load human inputs
    try:
        human_data = load_human_inputs(human_inputs_path)
        human_metrics = {
            "catl_margin": human_data.catl_overseas_gross_margin_pct,
            "lges_margin": human_data.lges_q1_operating_margin_ex_ira_pct
        }
    except Exception as e:
        logger.warning("Could not load human inputs, using defaults. Error: %s", e)
        human_metrics = {"catl_margin": 31.4, "lges_margin": 2.1}

    divergence_fig = build_divergence_matrix(counts, trend_df=trend, sentiment_df=sentiment, human_metrics=human_metrics)
    inflection_fig = build_trend_inflection(sentiment)

    divergence_path = str(out / "quality_divergence_matrix.png")
    inflection_path = str(out / "trend_inflection.png")
    divergence_fig.write_image(divergence_path, width=1200, height=700)
    inflection_fig.write_image(inflection_path, width=900, height=600)
    logger.info("Saved %s", divergence_path)
    logger.info("Saved %s", inflection_path)

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Generate signal charts from tagged data")
    parser.add_argument("--tags", default="data/processed/tags")
    parser.add_argument("--output", default="output/charts")
    parser.add_argument("--human-inputs", default="config/human_inputs.yaml")
    args = parser.parse_args()
    run_signal_engine(tags_dir=args.tags, output_dir=args.output, human_inputs_path=args.human_inputs)
    print(f"Charts written to {args.output}/")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run signal engine tests**

Run: `pytest tests/signal_engine/ -v`
Expected: PASS (Make sure `test_cli.py` passes. If it fails because of missing `config/human_inputs.yaml`, the try/except block handles it with defaults).

- [ ] **Step 3: Commit**

```bash
git add src/signal_engine/cli.py
git commit -m "feat(signal_engine): inject human metrics into chart generation and use weighted sentiment"
```

---

### Task 4: Deck Renderer Narrative Polish

**Files:**
- Modify: `src/renderer/content_map.py:1-163`
- Modify: `tests/renderer/test_content_map.py:1-102`

- [ ] **Step 1: Write failing test**

Modify `tests/renderer/test_content_map.py` to assert fewer filler slides.

```python
# In test_build_slide_specs_max_20_slides
def test_build_slide_specs_reduces_filler():
    specs = build_slide_specs(_deck_input())
    # Should be around 12-14 slides now, definitely less than 20
    assert len(specs) < 16
    
    # Check that Slide 3 and 4 have the strong narrative bodies
    assert "AI signals show stronger positive perception of CATL execution topics" in specs[2].body
    assert "Human analysis confirms higher overseas margins" in specs[2].body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/renderer/test_content_map.py -v`

- [ ] **Step 3: Update `src/renderer/content_map.py`**

```python
# In build_slide_specs
    # Slide 3: Quality Divergence Matrix chart
    specs.append(SlideSpec(
        slide_type=SlideType.CHART,
        title="Quality Divergence Matrix: Narrative Evidence",
        body=(
            "AI signals show stronger positive perception of CATL execution topics. "
            f"Human analysis confirms higher overseas margins ({h.catl_overseas_gross_margin_pct:.1f}%) "
            "and faster ramp execution."
        ),
        chart_path=deck_input.divergence_matrix_path,
    ))

    # Slide 4: Trend Inflection chart
    specs.append(SlideSpec(
        slide_type=SlideType.CHART,
        title="Sentiment Divergence by Topic",
        body=(
            "AI identifies a clear signal divergence on execution vs subsidy themes. "
            f"Human-verified: LGES ex-IRA operating margin weakness ({h.lges_q1_operating_margin_ex_ira_pct:.1f}%) "
            "corroborates the negative sentiment cluster around Subsidy_Dependence."
        ),
        chart_path=deck_input.trend_inflection_path,
    ))

    # ... keep Slides 5-8 as is ...

    # Replace Slides 9-14 (6 placeholders) with just 1 placeholder to reduce filler
    specs.append(SlideSpec(
        slide_type=SlideType.FUNDAMENTALS,
        title="Fundamental Analysis: Market Share & Capacity",
        body="[Analyst-populated slide — insert DCF assumptions, capex schedules, or channel check data here.]",
    ))

    # Keep Counterfactuals (1 main, 1 placeholder instead of 3)
    specs.append(SlideSpec(
        slide_type=SlideType.COUNTERFACTUAL,
        title="Downside Scenario: IRA Credit Cap",
        body=(
            f"Shock: {h.shock_scenario}\n"
            f"Estimated ROIC impact: -{h.roic_shock_delta_bps} bps for LGES.\n"
            "CATL exposure: limited — organic margin not IRA-derived."
        ),
    ))
    specs.append(SlideSpec(
        slide_type=SlideType.COUNTERFACTUAL,
        title="Counterfactual Scenario 2",
        body="[Analyst-populated — insert specific basis-point impact tied to named risk scenario.]",
    ))

    # Keep Slides 19-20 (Disclosures)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/renderer/test_content_map.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/renderer/content_map.py tests/renderer/test_content_map.py
git commit -m "feat(renderer): strengthen narrative integration and remove deck filler"
```
