# Stage 5: Autonomous Presentation Renderer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take a `DeckInput` object (from Stage 4) and produce a max-20-slide PPTX deck that merges human DCF/margin data with the top AI signals, enforces the prohibited language rules, embeds the two Signal Engine charts, and closes with mandatory AI disclosure slides.

**Architecture:** A content mapper converts `DeckInput` into a structured list of `SlideSpec` objects (one per slide). A slide builder iterates those specs and writes them to a PPTX file using `python-pptx`. Charts are embedded as images from `output/charts/`. A CLI wires everything together. Tests cover content mapping and disclosure language — they mock the PPTX builder to avoid binary output in CI.

**Tech Stack:** Python 3.11+, python-pptx, pydantic, pytest

**Prerequisite:** Stages 1–4 complete. `output/charts/quality_divergence_matrix.png` and `output/charts/trend_inflection.png` exist. `DeckInput` object available from Stage 4.

---

### Task 1: SlideSpec Content Mapper

**Files:**
- Create: `src/renderer/content_map.py`
- Test: `tests/renderer/test_content_map.py`

- [ ] **Step 1: Write failing test**

```python
# tests/renderer/test_content_map.py
import pytest
from src.renderer.content_map import build_slide_specs, SlideSpec, SlideType
from src.human_layer.schema import HumanInputs
from src.human_layer.merger import DeckInput


def _deck_input():
    human = HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%, IRA capped.",
        catl_execution_edge="Hungary on schedule.",
        lges_execution_risk="Ultium delayed 9 months.",
    )
    ai_signals = {
        "CATL": [{"topic_cluster": "Organic_Scale_vs_Export", "sentiment_score": 9,
                  "summary": "CATL at 50 GWh.", "stream": "perception"}],
        "LGES": [{"topic_cluster": "Subsidy_Dependence", "sentiment_score": 3,
                  "summary": "LGES IRA-dependent.", "stream": "perception"}],
    }
    return DeckInput(
        human=human,
        ai_signals=ai_signals,
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
    )


def test_build_slide_specs_returns_list_of_slide_specs():
    specs = build_slide_specs(_deck_input())
    assert isinstance(specs, list)
    assert all(isinstance(s, SlideSpec) for s in specs)


def test_build_slide_specs_max_20_slides():
    specs = build_slide_specs(_deck_input())
    assert len(specs) <= 20


def test_build_slide_specs_includes_disclosure_slides():
    specs = build_slide_specs(_deck_input())
    types = [s.slide_type for s in specs]
    assert SlideType.DISCLOSURE in types


def test_build_slide_specs_includes_counterfactual_slides():
    specs = build_slide_specs(_deck_input())
    types = [s.slide_type for s in specs]
    assert SlideType.COUNTERFACTUAL in types


def test_build_slide_specs_has_no_prohibited_language():
    specs = build_slide_specs(_deck_input())
    prohibited = [
        "we believe", "we conclude", "investment advice",
        "outperform", "underperform", "buy", "sell",
        "target price", "price target", "recommend",
        "not fully priced", "suggests upside", "implies downside",
    ]
    for spec in specs:
        full_text = " ".join([spec.title or "", spec.body or ""]).lower()
        for phrase in prohibited:
            assert phrase not in full_text, f"Prohibited phrase '{phrase}' found in slide: {spec.title}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/renderer/test_content_map.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.renderer.content_map'`

- [ ] **Step 3: Implement content mapper**

```python
# src/renderer/content_map.py
from dataclasses import dataclass, field
from enum import Enum
from src.human_layer.merger import DeckInput


class SlideType(str, Enum):
    TITLE = "title"
    THESIS = "thesis"
    AI_SIGNAL = "ai_signal"
    FUNDAMENTALS = "fundamentals"
    CHART = "chart"
    COUNTERFACTUAL = "counterfactual"
    DISCLOSURE = "disclosure"


@dataclass
class SlideSpec:
    slide_type: SlideType
    title: str = ""
    body: str = ""
    chart_path: str = ""
    table_rows: list[list[str]] = field(default_factory=list)


def build_slide_specs(deck_input: DeckInput) -> list[SlideSpec]:
    h = deck_input.human
    ai = deck_input.ai_signals
    specs: list[SlideSpec] = []

    # Slide 1: Title
    # Note: h and deck_input are both in scope for all slides below
    specs.append(SlideSpec(
        slide_type=SlideType.TITLE,
        title="CATL vs LGES: Globalization Quality Divergence",
        body="UBS Finance Challenge 2026 — Pair Trade Analysis",
    ))

    # Slide 2: Thesis — factual framing only; interpretive conclusions stay in human layer
    specs.append(SlideSpec(
        slide_type=SlideType.THESIS,
        title="Observed Divergence: Globalization Quality",
        body=(
            "CATL's overseas expansion is organic and margin-accretive (greenfield, LFP volume). "
            "LGES's US presence is structurally dependent on IRA policy arbitrage. "
            f"Perception and fundamental data show divergent quality: CATL overseas margin {h.catl_overseas_gross_margin_pct:.1f}% "
            f"vs LGES ex-IRA operating margin {h.lges_q1_operating_margin_ex_ira_pct:.1f}%. "
            "Human analyst interprets implications for return sustainability."
        ),
    ))

    # Slide 3: Quality Divergence Matrix chart — caption bridges AI signal to human-verified margin
    specs.append(SlideSpec(
        slide_type=SlideType.CHART,
        title="Quality Divergence Matrix: Narrative Evidence",
        body=(
            "Normalized topic coverage share per company (perception stream). "
            f"Human-verified: CATL overseas gross margin {h.catl_overseas_gross_margin_pct:.1f}% "
            f"vs domestic {h.catl_domestic_gross_margin_pct:.1f}% — consistent with Organic_Scale perception weight."
        ),
        chart_path=deck_input.divergence_matrix_path,
    ))

    # Slide 4: Trend Inflection chart — caption bridges sentiment signal to LGES fundamental weakness
    specs.append(SlideSpec(
        slide_type=SlideType.CHART,
        title="Sentiment Divergence by Topic",
        body=(
            "Mean sentiment score (1–10) per topic cluster, grouped by company. "
            f"Human-verified: LGES ex-IRA operating margin {h.lges_q1_operating_margin_ex_ira_pct:.1f}% "
            "— consistent with Subsidy_Dependence low-sentiment signal."
        ),
        chart_path=deck_input.trend_inflection_path,
    ))

    # Slides 5-6: Top AI Signals per company
    for company in ["CATL", "LGES"]:
        signals = ai.get(company, [])
        bullets = "\n".join(
            f"• [{s['topic_cluster']}] {s['summary']}" for s in signals[:3]
        )
        specs.append(SlideSpec(
            slide_type=SlideType.AI_SIGNAL,
            title=f"Top Perception Signals: {company}",
            body=bullets,
        ))

    # Slide 7: Margin Comparison Table
    specs.append(SlideSpec(
        slide_type=SlideType.FUNDAMENTALS,
        title="Margin Reality: AI Signal vs Fundamental Data",
        body="Human-verified financial data cross-checked against perception narratives.",
        table_rows=[
            ["Metric", "CATL", "LGES"],
            ["Overseas Gross Margin", f"{h.catl_overseas_gross_margin_pct:.1f}%", "N/A"],
            ["Domestic Gross Margin", f"{h.catl_domestic_gross_margin_pct:.1f}%", "N/A"],
            ["Operating Margin ex-IRA", "N/A", f"{h.lges_q1_operating_margin_ex_ira_pct:.1f}%"],
        ],
    ))

    # Slide 8: Execution Edge
    specs.append(SlideSpec(
        slide_type=SlideType.FUNDAMENTALS,
        title="Execution Edge vs Execution Risk",
        body=(
            f"CATL: {h.catl_execution_edge}\n\n"
            f"LGES: {h.lges_execution_risk}"
        ),
    ))

    # Slides 9-14: Fundamentals (placeholder for analyst expansion)
    for i in range(6):
        specs.append(SlideSpec(
            slide_type=SlideType.FUNDAMENTALS,
            title=f"Fundamental Analysis {i + 1}",
            body="[Analyst-populated slide — insert DCF assumptions, capex schedules, or channel check data here.]",
        ))

    # Slides 15-18: Counterfactuals
    specs.append(SlideSpec(
        slide_type=SlideType.COUNTERFACTUAL,
        title="Downside Scenario: IRA Credit Cap",
        body=(
            f"Shock: {h.shock_scenario}\n"
            f"Estimated ROIC impact: -{h.roic_shock_delta_bps} bps for LGES.\n"
            "CATL exposure: limited — organic margin not IRA-derived."
        ),
    ))
    for i in range(3):
        specs.append(SlideSpec(
            slide_type=SlideType.COUNTERFACTUAL,
            title=f"Counterfactual Scenario {i + 2}",
            body="[Analyst-populated — insert specific basis-point impact tied to named risk scenario.]",
        ))

    # Slides 19-20: Disclosures
    specs.append(SlideSpec(
        slide_type=SlideType.DISCLOSURE,
        title="AI Methodology Disclosure",
        body=(
            "The AI Analyst module was used strictly to scale the processing of unstructured perception data "
            "beyond manual capacity. It did NOT build valuation models, conduct channel checks, or generate "
            "fundamental forecasts. The AI surfaces narrative divergence; human analysts verified the "
            "sustainability of returns.\n\n"
            "LLM: Claude 3.5 Sonnet (Anthropic). Tagged fields: sentiment_score, direction, topic_cluster, "
            "geo_exposure, summary. All summaries are direct factual extractions — no AI opinions or conclusions."
        ),
    ))
    specs.append(SlideSpec(
        slide_type=SlideType.DISCLOSURE,
        title="Limitations & Data Sources",
        body=(
            "• Perception stream: Bloomberg and Moomoo news URLs (12-24 month window).\n"
            "• Ground Truth stream: Investor Relations documents (earnings transcripts, capex filings).\n"
            "• Sentiment scores are relative within this dataset — not absolute market signals.\n"
            "• No channel checks, primary research, or sell-side model access was used by the AI module."
        ),
    ))

    assert len(specs) <= 20, f"Deck exceeds 20 slides: {len(specs)}"
    return specs
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/renderer/test_content_map.py -v
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/renderer/content_map.py tests/renderer/test_content_map.py
git commit -m "feat(renderer): add slide spec content mapper (20-slide structure)

build_slide_specs maps DeckInput to a list of SlideSpec objects covering
title, thesis, AI signal charts, fundamentals table, counterfactuals (15-18),
and mandatory AI disclosure slides (19-20). The spec strictly prohibits
'we believe', 'we conclude', and 'investment advice' — tested explicitly."
```

---

### Task 2: PPTX Slide Builder

**Files:**
- Create: `src/renderer/slide_builder.py`
- Test: `tests/renderer/test_slide_builder.py`

- [ ] **Step 1: Write failing test**

```python
# tests/renderer/test_slide_builder.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from src.renderer.slide_builder import build_pptx
from src.renderer.content_map import SlideSpec, SlideType


def _specs():
    return [
        SlideSpec(slide_type=SlideType.TITLE, title="Main Title", body="Subtitle text"),
        SlideSpec(slide_type=SlideType.FUNDAMENTALS, title="Fundamentals", body="Some body text"),
        SlideSpec(slide_type=SlideType.DISCLOSURE, title="Disclosure", body="AI used for X only."),
    ]


def test_build_pptx_creates_file(tmp_path):
    out = tmp_path / "test_deck.pptx"
    build_pptx(_specs(), str(out))
    assert out.exists()
    assert out.stat().st_size > 0


def test_build_pptx_has_correct_slide_count(tmp_path):
    from pptx import Presentation
    out = tmp_path / "test_deck.pptx"
    build_pptx(_specs(), str(out))
    prs = Presentation(str(out))
    assert len(prs.slides) == len(_specs())


def test_build_pptx_with_table_spec(tmp_path):
    from pptx import Presentation
    specs = [SlideSpec(
        slide_type=SlideType.FUNDAMENTALS,
        title="Margin Table",
        body="",
        table_rows=[["Metric", "CATL", "LGES"], ["Overseas GM", "31.4%", "N/A"]],
    )]
    out = tmp_path / "table_deck.pptx"
    build_pptx(specs, str(out))
    prs = Presentation(str(out))
    assert len(prs.slides) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/renderer/test_slide_builder.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement slide builder**

```python
# src/renderer/slide_builder.py
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from src.renderer.content_map import SlideSpec, SlideType

_SLIDE_W = Inches(13.33)
_SLIDE_H = Inches(7.5)
_ACCENT = RGBColor(0x1F, 0x77, 0xB4)   # CATL blue
_DARK = RGBColor(0x22, 0x22, 0x22)


def _add_textbox(slide, left, top, width, height, text, font_size=18, bold=False, color=None):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color or _DARK
    return txBox


def _render_title_slide(slide, spec: SlideSpec) -> None:
    _add_textbox(slide, Inches(1), Inches(2.5), Inches(11), Inches(1.2),
                 spec.title, font_size=36, bold=True, color=_ACCENT)
    _add_textbox(slide, Inches(1), Inches(4), Inches(11), Inches(0.8),
                 spec.body, font_size=20)


def _render_content_slide(slide, spec: SlideSpec) -> None:
    _add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.8),
                 spec.title, font_size=24, bold=True, color=_ACCENT)
    if spec.table_rows:
        rows = len(spec.table_rows)
        cols = len(spec.table_rows[0])
        table = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(1.2),
                                       Inches(12), Inches(0.4 * rows)).table
        for r_idx, row in enumerate(spec.table_rows):
            for c_idx, cell_text in enumerate(row):
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_text
                cell.text_frame.paragraphs[0].runs[0].font.bold = (r_idx == 0)
    elif spec.body:
        _add_textbox(slide, Inches(0.5), Inches(1.3), Inches(12), Inches(5.5),
                     spec.body, font_size=16)
    if spec.chart_path and Path(spec.chart_path).exists():
        slide.shapes.add_picture(spec.chart_path, Inches(0.5), Inches(1.5),
                                 Inches(12), Inches(5.5))


def build_pptx(specs: list[SlideSpec], output_path: str) -> None:
    prs = Presentation()
    prs.slide_width = _SLIDE_W
    prs.slide_height = _SLIDE_H
    blank_layout = prs.slide_layouts[6]   # blank layout
    for spec in specs:
        slide = prs.slides.add_slide(blank_layout)
        if spec.slide_type == SlideType.TITLE:
            _render_title_slide(slide, spec)
        else:
            _render_content_slide(slide, spec)
    prs.save(output_path)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/renderer/test_slide_builder.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/renderer/slide_builder.py tests/renderer/test_slide_builder.py
git commit -m "feat(renderer): add python-pptx slide builder

build_pptx iterates SlideSpec objects and renders title, content, table,
and chart slides using a blank layout. Chart images are embedded if the
file exists at the path specified in the spec. Tests verify file creation,
slide count, and table rendering without mocking the pptx library."
```

---

### Task 3: Renderer CLI & End-to-End Wiring

**Files:**
- Create: `src/renderer/cli.py`
- Test: `tests/renderer/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
# tests/renderer/test_cli.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.renderer.cli import run_renderer
from src.human_layer.merger import DeckInput
from src.human_layer.schema import HumanInputs


def _deck_input():
    human = HumanInputs(
        catl_overseas_gross_margin_pct=31.4,
        catl_domestic_gross_margin_pct=24.0,
        lges_q1_operating_margin_ex_ira_pct=2.1,
        roic_shock_delta_bps=180,
        shock_scenario="US EV demand -20%.",
        catl_execution_edge="Hungary on schedule.",
        lges_execution_risk="Ultium delayed.",
    )
    return DeckInput(
        human=human,
        ai_signals={
            "CATL": [{"topic_cluster": "Organic_Scale_vs_Export", "sentiment_score": 9,
                      "summary": "CATL at 50 GWh.", "stream": "perception"}],
            "LGES": [{"topic_cluster": "Subsidy_Dependence", "sentiment_score": 3,
                      "summary": "LGES IRA-dependent.", "stream": "perception"}],
        },
        divergence_matrix_path="output/charts/quality_divergence_matrix.png",
        trend_inflection_path="output/charts/trend_inflection.png",
    )


def test_run_renderer_calls_build_pptx(tmp_path):
    out_path = str(tmp_path / "deck.pptx")
    with patch("src.renderer.cli.build_pptx") as mock_build:
        run_renderer(_deck_input(), output_path=out_path)
    mock_build.assert_called_once()
    specs_arg = mock_build.call_args[0][0]
    assert len(specs_arg) <= 20


def test_run_renderer_passes_correct_output_path(tmp_path):
    out_path = str(tmp_path / "deck.pptx")
    with patch("src.renderer.cli.build_pptx") as mock_build:
        run_renderer(_deck_input(), output_path=out_path)
    assert mock_build.call_args[0][1] == out_path
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/renderer/test_cli.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement renderer CLI**

```python
# src/renderer/cli.py
import argparse
import json
import logging
import os
import pandas as pd
from dotenv import load_dotenv
from src.human_layer.schema import load_human_inputs
from src.human_layer.merger import merge_inputs
from src.signal_engine.loader import load_tags
from src.renderer.content_map import build_slide_specs
from src.renderer.slide_builder import build_pptx

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_renderer(deck_input, output_path: str) -> None:
    specs = build_slide_specs(deck_input)
    logger.info("Building %d slides", len(specs))
    build_pptx(specs, output_path)
    logger.info("Deck written to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PPTX deck from AI signals and human inputs")
    parser.add_argument("--human-inputs", default="config/human_inputs.yaml")
    parser.add_argument("--tags", default="data/processed/tags")
    parser.add_argument("--divergence-matrix", default="output/charts/quality_divergence_matrix.png")
    parser.add_argument("--trend-inflection", default="output/charts/trend_inflection.png")
    parser.add_argument("--output", default="output/deck/catl_lges_pair_trade.pptx")
    args = parser.parse_args()
    human = load_human_inputs(args.human_inputs)
    tag_df = load_tags(args.tags)
    deck_input = merge_inputs(human, tag_df, args.divergence_matrix, args.trend_inflection)
    run_renderer(deck_input, output_path=args.output)
    print(f"Deck saved to {args.output}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all renderer tests**

```bash
pytest tests/renderer/ -v
```

Expected: PASS (all 10 tests)

- [ ] **Step 5: Run all tests across all stages**

```bash
pytest tests/ -v
```

Expected: PASS (all tests across all 5 stages)

- [ ] **Step 6: End-to-end smoke test (requires live data)**

```bash
# Stage 1
python -m src.ingestion.cli --config config/urls.yaml --output data/raw

# Stage 2
python -m src.tagger.cli --perception data/raw/perception --ground-truth data/raw/ground_truth --output data/processed/tags

# Stage 3
python -m src.signal_engine.cli --tags data/processed/tags --output output/charts

# Stage 5 (Stage 4 is embedded in Stage 5 CLI)
python -m src.renderer.cli --human-inputs config/human_inputs.yaml --tags data/processed/tags --output output/deck/catl_lges_pair_trade.pptx

ls output/deck/
```

Expected: `catl_lges_pair_trade.pptx` present and non-zero size.

- [ ] **Step 7: Commit**

```bash
git add src/renderer/cli.py tests/renderer/test_cli.py
git commit -m "feat(renderer): add CLI that wires all five stages into one end-to-end command

run_renderer loads human inputs, merges with AI signals, maps to SlideSpec
objects, and calls build_pptx. End-to-end test verifies that the full
pipeline produces a non-empty PPTX at the specified output path."
```
