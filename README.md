# AgenticAlpha

An AI-powered research synthesis pipeline that analyzes competing companies in the global battery/EV market and generates investment-grade presentation decks. The current use case is a **CATL vs LG Energy Solutions (LGES) pair-trade analysis**, automated end-to-end from raw web sources to a 15-slide PowerPoint briefing.

## What It Does

The system answers a specific research question: *Is CATL's localization-driven model and execution edge creating a sustainable competitive moat versus LGES's export-led, subsidy-dependent operations?*

It automates five stages:

1. **Ingest** — Fetch and convert URLs (news, press releases, IR filings) to structured Markdown
2. **Tag** — Extract structured signals from each document using a Gemma LLM (sentiment, topic cluster, geography, six quantitative scores)
3. **Signal Engine** — Aggregate tags into charts: quality divergence matrix, trend inflection, differentiation matrix, contradiction scanner, risk tree, evidence scale, why-now timeline
4. **Synthesize** — Single LLM call to generate a narrative brief and structured output from all aggregated evidence
5. **Render** — Combine charts, synthesis, and human expert inputs into a 15-slide `.pptx` deck

## Project Structure

```
AgenticAlpha/
├── config/
│   ├── urls.yaml           # 55+ verified source URLs (perception + ground_truth streams)
│   └── human_inputs.yaml   # Analyst-supplied margins, execution judgments, open questions
├── src/
│   ├── ingestion/          # Stage 1: HTML fetch → Markdown
│   ├── tagger/             # Stage 2: LLM-based structured tag extraction
│   ├── signal_engine/      # Stage 3: Aggregation + Plotly charts
│   ├── synthesis/          # Stage 4: LLM narrative synthesis
│   ├── renderer/           # Stage 5: python-pptx deck builder
│   ├── human_layer/        # Schema + merger for human analyst inputs
│   └── audit/              # Claim/evidence/confidence audit trail
├── data/
│   ├── raw/                # Markdown files from ingestion
│   └── processed/tags/     # JSON tag files from tagger
├── output/
│   ├── charts/             # PNG exports from signal engine
│   ├── synthesis.json      # Structured synthesis output
│   ├── synthesis.md        # Human-readable synthesis brief
│   ├── briefing/           # Analyst brief (JSON + Markdown)
│   └── deck/               # Final .pptx output
├── docs/
│   └── errors.md           # Known issues and fixes
├── tests/
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.11+
- A Google API key with access to Gemma models (via Google AI Studio)

### Install

```bash
git clone <repo-url>
cd AgenticAlpha
pip install -r requirements.txt
```

### Configure

1. Copy `.env.example` to `.env` and add your key:

```env
GOOGLE_API_KEY=your_key_here
```

2. Fill in `config/human_inputs.yaml` with real analyst data. Placeholder values (`TBD`, `TODO`) are rejected at runtime by Pydantic validation — the pipeline requires genuine inputs to proceed.

## Running the Pipeline

Run each stage in order. All stages use standard `python -m` entry points.

### Stage 1 — Ingest

```bash
python -m src.ingestion.cli \
  --config config/urls.yaml \
  --output data/raw
```

Fetches HTML from all URLs in `urls.yaml`, converts to Markdown with YAML frontmatter, and writes files to `data/raw/{perception,ground_truth}/`.

### Stage 2 — Tag

```bash
python -m src.tagger.cli \
  --perception data/raw/perception \
  --ground-truth data/raw/ground_truth \
  --output data/processed/tags
```

Calls Gemma to extract per-document tags: sentiment, topic cluster, geographic region, globalization model, and six quantitative signal scores (localization, subsidy dependency, execution quality, margins, capex, ROIC). Outputs one JSON file per source document.

### Stage 3 — Signal Engine

```bash
python -m src.signal_engine.cli \
  --tags data/processed/tags \
  --output output/charts \
  --human-inputs config/human_inputs.yaml
```

Aggregates all tags and exports seven PNG charts to `output/charts/`.

### Stage 4 — Synthesize

```bash
python -m src.synthesis.cli \
  --tags data/processed/tags \
  --charts output/charts \
  --output output/synthesis.json \
  --model gemma-4-31b-it \
  --human-inputs config/human_inputs.yaml
```

Builds a rich prompt from all aggregated evidence and makes a single LLM call. Outputs `synthesis.json`, `synthesis.md`, and `briefing/analyst_brief.{json,md}`.

### Stage 5 — Render

```bash
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
  --output output/deck/catl_lges_pair_trade.pptx
```

Produces the final 15-slide deck at `output/deck/catl_lges_pair_trade.pptx`.

## Configuration Reference

### `config/urls.yaml`

Lists all data sources. Each entry has:

| Field | Description |
|-------|-------------|
| `url` | Source URL |
| `company` | `CATL` or `LGES` |
| `stream` | `perception` (news/media) or `ground_truth` (IR/official) |
| `description` | Optional label |
| `source` | Publication name |
| `region` | Geographic region |

### `config/human_inputs.yaml`

Analyst-supplied data required before synthesis and rendering. Key fields:

| Field | Example | Description |
|-------|---------|-------------|
| `catl_overseas_gross_margin_pct` | `31.4` | CATL overseas gross margin (%) |
| `catl_domestic_gross_margin_pct` | `24.0` | CATL domestic gross margin (%) |
| `lges_q1_operating_margin_ex_ira_pct` | `2.1` | LGES operating margin excluding IRA credits |
| `roic_shock_delta_bps` | `180` | ROIC change in basis points under stress scenario |
| `shock_scenario` | string | Description of macro risk scenario |
| `catl_execution_edge` | string | CATL's key execution differentiator |
| `lges_execution_risk` | string | LGES's execution vulnerability |
| `why_now_takeaway` | string | Timing rationale for the trade |
| `contradiction_takeaway` | string | Summary of key data conflicts found |

All fields are validated with Pydantic. Empty or placeholder strings cause a hard error.

## Dependencies

| Package | Purpose |
|---------|---------|
| `google-genai` | Gemma model inference (Stages 2, 4) |
| `anthropic` | Claude API (available for future synthesis expansion) |
| `pydantic` | Schema validation throughout |
| `plotly` + `kaleido` | Chart generation and PNG export |
| `python-pptx` | PowerPoint deck construction |
| `beautifulsoup4` + `markdownify` | HTML → Markdown conversion |
| `pandas` | Aggregation and data manipulation |
| `pyyaml` | YAML config parsing |

## Known Issues

**`kaleido` hangs on Windows 11** with version `0.2.x` due to a deadlock in the Chromium subprocess pipe. The `requirements.txt` pins `kaleido==0.1.0post1` which resolves this. Do not upgrade kaleido without testing chart export on Windows first.

## Running Tests

```bash
pytest tests/
```

## License

Private research tool. Not licensed for redistribution.
