# AgenticAlpha v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AgenticAlpha from a tagging pipeline (v1) into a full Evidence Engine + Analyst Copilot (v2) by expanding the tagger schema, adding an Evidence Engine with 5 new aggregations and charts, introducing a Synthesis layer (one Claude call), and expanding the renderer to 15 slides.

**Architecture:** Keep the existing 5-stage pipeline skeleton intact. Phase 1 expands the tagger schema in place. Phase 2 widens ingestion to 4 streams. Phase 3 expands signal_engine → evidence_engine with 5 new aggregators. Phase 4 adds a new `src/synthesis/` module. Phase 5 expands the human layer and renderer. Phase 6 adds `src/audit/`. All stages remain independently CLI-invocable and TDD-tested.

**Tech Stack:** Python 3.11+, Pydantic v2, Pandas, Plotly (Kaleido for PNG export), python-pptx, Anthropic SDK (`anthropic`) for synthesis, Google Gemini (existing tagger), PyYAML.

---

## File Map

**Phase 1 — Rich Tagger:**
- Modify: `src/tagger/schema.py` — 12 new fields on `Tag`
- Modify: `src/tagger/prompt.py` — update system + user prompts for new fields
- Modify: `src/tagger/batch.py` — compute `source_weight`, parse date from frontmatter
- Modify: `tests/tagger/test_schema.py` — update for new fields
- Modify: `tests/tagger/test_batch.py` — update for `source_weight`, `date`

**Phase 2 — Ingestion Expansion:**
- Modify: `src/ingestion/config.py` — add `policy`/`operations` streams; add `source`, `region` to `UrlEntry`
- Modify: `src/ingestion/pipeline.py` — handle 4 streams; write YAML frontmatter to markdown output
- Modify: `src/tagger/cli.py` — add `--policy`, `--operations` args
- Modify: `config/urls.yaml` — add `policy:` and `operations:` sections
- Modify: `tests/ingestion/test_config.py` — tests for new streams and new UrlEntry fields

**Phase 3 — Evidence Engine:**
- Modify: `src/signal_engine/aggregator.py` — 5 new aggregation functions
- Modify: `src/signal_engine/charts.py` — 4 new chart functions
- Modify: `src/signal_engine/cli.py` — produce 5 additional PNG outputs
- Create: `tests/signal_engine/test_evidence_engine.py`
- Modify: `tests/signal_engine/test_cli.py`

**Phase 4 — Synthesis Layer:**
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

**Phase 5 — Human Layer & Renderer Expansion:**
- Modify: `src/human_layer/schema.py` — analyst action layer fields
- Modify: `src/human_layer/merger.py` — expand `DeckInput`; accept synthesis + 5 new chart paths
- Modify: `src/renderer/content_map.py` — expand to 15 slides
- Modify: `src/renderer/cli.py` — wire new chart paths and synthesis output
- Modify: `config/human_inputs.yaml` — add new analyst action layer fields
- Modify: `tests/human_layer/test_schema.py`
- Modify: `tests/human_layer/test_merger.py`
- Modify: `tests/renderer/test_content_map.py`

**Phase 6 — Audit Module:**
- Create: `src/audit/__init__.py`
- Create: `src/audit/trail.py`
- Create: `tests/audit/__init__.py`
- Create: `tests/audit/test_trail.py`

---

## Phase 1 — Rich Tagger

### Task 1: Expand ArticleTag Schema

**Files:**
- Modify: `src/tagger/schema.py`
- Modify: `tests/tagger/test_schema.py`

- [ ] **Step 1: Write failing tests for new schema fields**

```python
# tests/tagger/test_schema.py — add these tests (keep existing ones)
import pytest
from pydantic import ValidationError
from src.tagger.schema import Tag

def test_full_tag_with_all_new_fields():
    tag = Tag(
        sentiment_score=7.5,
        direction="positive",
        confidence=0.85,
        topic_cluster="Organic_Scale_vs_Export",
        geo_exposure=["US"],
        globalization_model="export-led",
        localization_score=8,
        subsidy_dependency=3,
        execution_quality=9,
        margin_signal=7,
        capex_signal=8,
        ROIC_signal=7,
        contradiction_flag=False,
        contradiction_reason=None,
        claim_summary="CATL shows strong execution in overseas markets.",
        key_quote="Revenue per MWh up 12% QoQ.",
    )
    assert tag.confidence == 0.85
    assert tag.localization_score == 8
    assert tag.contradiction_flag is False
    assert tag.key_quote == "Revenue per MWh up 12% QoQ."

def test_sentiment_score_is_float():
    tag = Tag(
        sentiment_score=7.5,
        direction="positive",
        confidence=0.85,
        topic_cluster="Capex_Execution",
        geo_exposure=["EU"],
        globalization_model="hybrid",
        localization_score=5,
        subsidy_dependency=5,
        execution_quality=5,
        margin_signal=5,
        capex_signal=5,
        ROIC_signal=5,
        contradiction_flag=False,
        contradiction_reason=None,
        claim_summary="Mixed signals on capex.",
        key_quote=None,
    )
    assert isinstance(tag.sentiment_score, float)

def test_confidence_must_be_0_to_1():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0,
            direction="neutral",
            confidence=1.5,  # invalid
            topic_cluster="Other",
            geo_exposure=["China"],
            globalization_model="unclear",
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="Some claim.",
            key_quote=None,
        )

def test_contradiction_reason_required_when_flagged():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=3.0,
            direction="negative",
            confidence=0.7,
            topic_cluster="Subsidy_Dependence",
            geo_exposure=["US"],
            globalization_model="localization-driven",
            localization_score=3,
            subsidy_dependency=9,
            execution_quality=4,
            margin_signal=3,
            capex_signal=4,
            ROIC_signal=3,
            contradiction_flag=True,
            contradiction_reason=None,  # must not be None when flag is True
            claim_summary="LGES depends heavily on IRA credits.",
            key_quote=None,
        )

def test_numeric_scores_must_be_1_to_10():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0,
            direction="neutral",
            confidence=0.5,
            topic_cluster="Other",
            geo_exposure=["EU"],
            globalization_model="hybrid",
            localization_score=11,  # out of range
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="Test.",
            key_quote=None,
        )

def test_claim_summary_must_not_be_empty():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0,
            direction="neutral",
            confidence=0.5,
            topic_cluster="Other",
            geo_exposure=["EU"],
            globalization_model="hybrid",
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="   ",  # whitespace only
            key_quote=None,
        )

def test_globalization_model_enum_rejects_invalid():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0,
            direction="neutral",
            confidence=0.5,
            topic_cluster="Other",
            geo_exposure=["EU"],
            globalization_model="unknown-model",  # invalid enum
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="Test.",
            key_quote=None,
        )
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/tagger/test_schema.py -v
```

Expected: multiple FAILED with `ImportError` or `ValidationError` not raised / field not found.

- [ ] **Step 3: Implement expanded schema in `src/tagger/schema.py`**

Replace the entire file with:

```python
from enum import Enum
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional


class Direction(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class TopicCluster(str, Enum):
    Organic_Scale_vs_Export = "Organic_Scale_vs_Export"
    Subsidy_Dependence = "Subsidy_Dependence"
    Geopolitical_Noise = "Geopolitical_Noise"
    Capex_Execution = "Capex_Execution"
    Other = "Other"


class GeoRegion(str, Enum):
    US = "US"
    EU = "EU"
    ASEAN = "ASEAN"
    LATAM = "LATAM"
    China = "China"


class GlobalizationModel(str, Enum):
    export_led = "export-led"
    localization_driven = "localization-driven"
    hybrid = "hybrid"
    unclear = "unclear"


class Tag(BaseModel):
    sentiment_score: float
    direction: Direction
    confidence: float

    topic_cluster: TopicCluster
    geo_exposure: list[GeoRegion]
    globalization_model: GlobalizationModel

    localization_score: int
    subsidy_dependency: int
    execution_quality: int
    margin_signal: int
    capex_signal: int
    ROIC_signal: int

    contradiction_flag: bool
    contradiction_reason: Optional[str] = None

    claim_summary: str
    key_quote: Optional[str] = None

    @field_validator("sentiment_score")
    @classmethod
    def validate_sentiment(cls, v: float) -> float:
        if not (1.0 <= v <= 10.0):
            raise ValueError("sentiment_score must be between 1.0 and 10.0")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @field_validator(
        "localization_score", "subsidy_dependency", "execution_quality",
        "margin_signal", "capex_signal", "ROIC_signal",
    )
    @classmethod
    def validate_score_1_to_10(cls, v: int) -> int:
        if not (1 <= v <= 10):
            raise ValueError("score must be between 1 and 10")
        return v

    @field_validator("claim_summary")
    @classmethod
    def validate_claim_summary(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("claim_summary must not be empty or whitespace")
        return v

    @model_validator(mode="after")
    def validate_contradiction_reason(self) -> "Tag":
        if self.contradiction_flag and not self.contradiction_reason:
            raise ValueError(
                "contradiction_reason is required when contradiction_flag is True"
            )
        return self
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/tagger/test_schema.py -v
```

Expected: all NEW tests PASS. Any old tests referencing `summary=` need updating (rename `summary` → `claim_summary` and add missing required fields).

- [ ] **Step 5: Fix any old tests that reference deprecated `summary` field**

In `tests/tagger/test_schema.py`, find every `Tag(...)` constructor call that uses `summary=` and replace with `claim_summary=`. Also add the new required fields with placeholder-valid values (e.g., `confidence=0.5`, `globalization_model="hybrid"`, all integer scores as `5`, `contradiction_flag=False`, `contradiction_reason=None`, `key_quote=None`).

Run again:

```
pytest tests/tagger/test_schema.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/tagger/schema.py tests/tagger/test_schema.py
git commit -m "feat(tagger): expand ArticleTag schema with 12 new fields for v2 evidence engine"
```

---

### Task 2: Update Tagger Prompts for New Schema

**Files:**
- Modify: `src/tagger/prompt.py`

- [ ] **Step 1: Read the current prompt file**

```bash
cat src/tagger/prompt.py
```

Note the existing JSON schema in the system prompt and the user message template.

- [ ] **Step 2: Write a failing test verifying new fields appear in prompt**

Add to `tests/tagger/test_prompt.py` (create if absent):

```python
from src.tagger.prompt import build_system_prompt, build_user_message

def test_system_prompt_mentions_contradiction_flag():
    prompt = build_system_prompt()
    assert "contradiction_flag" in prompt

def test_system_prompt_mentions_confidence():
    prompt = build_system_prompt()
    assert "confidence" in prompt

def test_system_prompt_mentions_localization_score():
    prompt = build_system_prompt()
    assert "localization_score" in prompt

def test_system_prompt_mentions_claim_summary():
    prompt = build_system_prompt()
    assert "claim_summary" in prompt
    assert "summary" in prompt  # claim_summary contains "summary"

def test_system_prompt_mentions_key_quote():
    prompt = build_system_prompt()
    assert "key_quote" in prompt

def test_user_message_contains_markdown(tmp_path):
    md = "## CATL Q4 2025\n\nCAT reported strong overseas margins."
    msg = build_user_message(md, company="CATL", stream="ground_truth")
    assert "CATL" in msg
    assert "ground_truth" in msg
```

```
pytest tests/tagger/test_prompt.py -v
```

Expected: FAIL (fields not yet in prompt).

- [ ] **Step 3: Update `src/tagger/prompt.py`**

Replace the `build_system_prompt()` return value with the expanded JSON schema. The function must return a string containing the following schema instruction block (keep any existing preamble about being a financial analyst):

```python
def build_system_prompt() -> str:
    return """You are a financial research analyst tagging investment research documents.

Return a JSON object that strictly matches this schema. Do NOT add fields, do NOT omit fields.

{
  "sentiment_score": <float 1.0-10.0, where 1=extremely bearish, 10=extremely bullish>,
  "direction": <"positive" | "negative" | "neutral">,
  "confidence": <float 0.0-1.0, your confidence in the tag given the evidence quality>,
  "topic_cluster": <"Organic_Scale_vs_Export" | "Subsidy_Dependence" | "Geopolitical_Noise" | "Capex_Execution" | "Other">,
  "geo_exposure": <list of "US" | "EU" | "ASEAN" | "LATAM" | "China">,
  "globalization_model": <"export-led" | "localization-driven" | "hybrid" | "unclear">,
  "localization_score": <int 1-10, where 1=local-only operations, 10=fully globalized>,
  "subsidy_dependency": <int 1-10, where 1=no subsidy reliance, 10=fully subsidy-dependent>,
  "execution_quality": <int 1-10, where 1=poor execution evidence, 10=excellent execution evidence>,
  "margin_signal": <int 1-10, where 1=severe margin compression, 10=strong margin expansion>,
  "capex_signal": <int 1-10, where 1=capex misfire or delays, 10=capex on-track or efficient>,
  "ROIC_signal": <int 1-10, where 1=ROIC deteriorating, 10=ROIC improving>,
  "contradiction_flag": <bool, true if this evidence challenges the prevailing bullish thesis>,
  "contradiction_reason": <string explaining the contradiction, or null if contradiction_flag is false>,
  "claim_summary": <string, one factual sentence summarizing the key claim in the document>,
  "key_quote": <string, the single most evidentially significant verbatim quote, or null if none>
}

Rules:
- Do NOT make recommendations. Do NOT infer unsupported facts.
- contradiction_flag must be true only when the evidence materially challenges the primary investment thesis.
- claim_summary must be a single factual sentence. Do not begin with "The document" or "This article".
- key_quote must be verbatim from the document, not paraphrased. Set to null if no strong quote exists.
"""


def build_user_message(markdown: str, company: str, stream: str) -> str:
    return f"""Company: {company}
Stream: {stream}

Document:
{markdown}

Return only the JSON object. No explanation, no markdown fences."""
```

- [ ] **Step 4: Run tests**

```
pytest tests/tagger/test_prompt.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/tagger/prompt.py tests/tagger/test_prompt.py
git commit -m "feat(tagger): update prompts to elicit new v2 tag fields including contradiction and scores"
```

---

### Task 3: Add source_weight and date Metadata in Batch Output

**Files:**
- Modify: `src/tagger/batch.py`
- Modify: `tests/tagger/test_batch.py`

- [ ] **Step 1: Read the current batch.py to understand `_parse_header()` and output format**

```bash
cat src/tagger/batch.py
```

Note: the function saves tag JSON with extra fields (`stream`, `company`, `source_file`). We need to also save `source_weight` (computed from stream) and `date` (parsed from YAML frontmatter if present).

- [ ] **Step 2: Write failing tests**

Add to `tests/tagger/test_batch.py`:

```python
import json, pathlib, pytest
from unittest.mock import patch, MagicMock
from src.tagger.batch import source_weight_for_stream, parse_frontmatter_date

def test_source_weight_perception():
    assert source_weight_for_stream("perception") == 1.0

def test_source_weight_ground_truth():
    assert source_weight_for_stream("ground_truth") == 2.0

def test_source_weight_policy():
    assert source_weight_for_stream("policy") == 1.5

def test_source_weight_operations():
    assert source_weight_for_stream("operations") == 2.0

def test_source_weight_unknown_defaults_to_1():
    assert source_weight_for_stream("unknown") == 1.0

def test_parse_frontmatter_date_extracts_date():
    markdown = "---\ndate: 2025-11-15\ncompany: CATL\n---\nBody text here."
    assert parse_frontmatter_date(markdown) == "2025-11-15"

def test_parse_frontmatter_date_returns_none_when_absent():
    markdown = "# CATL Report\n\nBody text here."
    assert parse_frontmatter_date(markdown) is None

def test_batch_output_includes_source_weight(tmp_path):
    # Create a minimal perception markdown file
    md_file = tmp_path / "catl_test.md"
    md_file.write_text("---\ndate: 2025-06-01\ncompany: CATL\n---\nCAT posted strong results.")

    fake_tag = {
        "sentiment_score": 7.5, "direction": "positive", "confidence": 0.8,
        "topic_cluster": "Organic_Scale_vs_Export", "geo_exposure": ["US"],
        "globalization_model": "export-led", "localization_score": 8,
        "subsidy_dependency": 3, "execution_quality": 9, "margin_signal": 7,
        "capex_signal": 8, "ROIC_signal": 7, "contradiction_flag": False,
        "contradiction_reason": None, "claim_summary": "CATL posted strong results.",
        "key_quote": None,
    }

    out_dir = tmp_path / "tags"
    out_dir.mkdir()

    with patch("src.tagger.batch.tag_document", return_value=MagicMock(**fake_tag, model_dump=lambda: fake_tag)):
        from src.tagger.batch import run_batch
        run_batch(
            input_dirs={"perception": [str(tmp_path)]},
            output_dir=str(out_dir),
            model=MagicMock(),
        )

    output_files = list(out_dir.glob("*.json"))
    assert len(output_files) == 1
    data = json.loads(output_files[0].read_text())
    assert data["source_weight"] == 1.0
    assert data["date"] == "2025-06-01"
```

```
pytest tests/tagger/test_batch.py -v
```

Expected: FAIL (functions not defined).

- [ ] **Step 3: Implement `source_weight_for_stream` and `parse_frontmatter_date` in `src/tagger/batch.py`**

Add near the top of `src/tagger/batch.py` (after imports):

```python
import re

_STREAM_WEIGHTS: dict[str, float] = {
    "perception": 1.0,
    "ground_truth": 2.0,
    "policy": 1.5,
    "operations": 2.0,
}


def source_weight_for_stream(stream: str) -> float:
    return _STREAM_WEIGHTS.get(stream, 1.0)


def parse_frontmatter_date(markdown: str) -> str | None:
    match = re.match(r"^---\n(.*?)\n---\n", markdown, re.DOTALL)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith("date:"):
            return line.split(":", 1)[1].strip()
    return None
```

Then, in the section of `run_batch()` / `_process_file()` where the tag JSON is written, add `source_weight` and `date` to the output dict:

```python
output = tag.model_dump()
output["stream"] = stream
output["company"] = company
output["source_file"] = str(source_file)
output["source_weight"] = source_weight_for_stream(stream)
output["date"] = parse_frontmatter_date(markdown_text)  # None if no frontmatter
```

Where `markdown_text` is the raw text read from the file.

- [ ] **Step 4: Run tests**

```
pytest tests/tagger/test_batch.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/tagger/batch.py tests/tagger/test_batch.py
git commit -m "feat(tagger): add source_weight and frontmatter date to tag output for evidence attribution"
```

---

## Phase 2 — Ingestion Expansion

### Task 4: Add policy/operations Streams to UrlConfig

**Files:**
- Modify: `src/ingestion/config.py`
- Modify: `config/urls.yaml`
- Modify: `tests/ingestion/test_config.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/ingestion/test_config.py`:

```python
from src.ingestion.config import load_url_config, UrlConfig
import yaml, pathlib

def test_url_config_has_policy_stream(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception: []
ground_truth: []
policy:
  - url: https://www.irs.gov/credits-deductions/inflation-reduction-act
    company: CATL
    source: IRS
    region: US
operations: []
""")
    config = load_url_config(str(cfg))
    assert len(config.policy) == 1
    assert config.policy[0].company == "CATL"

def test_url_config_has_operations_stream(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception: []
ground_truth: []
policy: []
operations:
  - url: https://example.com/lges-commissioning
    company: LGES
    source: LGES IR
    region: EU
""")
    config = load_url_config(str(cfg))
    assert len(config.operations) == 1
    assert config.operations[0].region == "EU"

def test_url_entry_has_optional_source_and_region(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception:
  - url: https://example.com/article
    company: CATL
ground_truth: []
policy: []
operations: []
""")
    config = load_url_config(str(cfg))
    entry = config.perception[0]
    assert entry.source is None
    assert entry.region is None

def test_url_entry_source_and_region_populated_when_given(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("""
perception:
  - url: https://example.com/article
    company: CATL
    source: Reuters
    region: US
ground_truth: []
policy: []
operations: []
""")
    config = load_url_config(str(cfg))
    entry = config.perception[0]
    assert entry.source == "Reuters"
    assert entry.region == "US"
```

```
pytest tests/ingestion/test_config.py -v
```

Expected: FAIL (no `policy`/`operations` attributes, no `source`/`region`).

- [ ] **Step 2: Update `src/ingestion/config.py`**

```python
from typing import Optional
from pydantic import BaseModel, field_validator


class UrlEntry(BaseModel):
    url: str
    company: str
    source: Optional[str] = None
    region: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"URL must start with http:// or https://: {v}")
        return v


class UrlConfig(BaseModel):
    perception: list[UrlEntry]
    ground_truth: list[UrlEntry]
    policy: list[UrlEntry] = []
    operations: list[UrlEntry] = []

    @field_validator("perception", "ground_truth", "policy", "operations", mode="before")
    @classmethod
    def deduplicate(cls, v: list) -> list:
        seen: set[str] = set()
        out = []
        for item in v:
            url = item["url"] if isinstance(item, dict) else item.url
            if url not in seen:
                seen.add(url)
                out.append(item)
        return out


def load_url_config(path: str) -> UrlConfig:
    import yaml
    with open(path) as f:
        data = yaml.safe_load(f)
    return UrlConfig(**data)
```

- [ ] **Step 3: Update `config/urls.yaml`**

Append at the end of the existing file:

```yaml
policy:
  - url: https://home.treasury.gov/policy-issues/inflation-reduction-act
    company: CATL
    source: US Treasury
    region: US
  - url: https://taxation-customs.ec.europa.eu/topics/customs-multiannual-strategic-plan_en
    company: LGES
    source: EU Commission
    region: EU

operations: []
```

- [ ] **Step 4: Run tests**

```
pytest tests/ingestion/test_config.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ingestion/config.py config/urls.yaml tests/ingestion/test_config.py
git commit -m "feat(ingestion): add policy/operations streams and source/region metadata to UrlEntry"
```

---

### Task 5: Write YAML Frontmatter to Ingested Markdown

**Files:**
- Modify: `src/ingestion/pipeline.py`
- Modify: `src/tagger/cli.py`

- [ ] **Step 1: Read `src/ingestion/pipeline.py`**

```bash
cat src/ingestion/pipeline.py
```

Identify the function that writes the markdown file (likely inside `_ingest_stream()`). It writes `content` to a path like `data/raw/perception/catl_<hash>.md`.

- [ ] **Step 2: Write a failing test for frontmatter**

Add to `tests/ingestion/test_pipeline.py`:

```python
import pathlib, yaml
from unittest.mock import patch
from src.ingestion.pipeline import _build_frontmatter

def test_build_frontmatter_contains_required_fields():
    fm = _build_frontmatter(
        company="CATL",
        source="Reuters",
        source_type="perception",
        region="US",
        date="2026-04-26",
    )
    parsed = yaml.safe_load(fm.strip("---\n"))
    assert parsed["company"] == "CATL"
    assert parsed["source"] == "Reuters"
    assert parsed["source_type"] == "perception"
    assert parsed["region"] == "US"
    assert parsed["date"] == "2026-04-26"

def test_build_frontmatter_handles_none_source():
    fm = _build_frontmatter(
        company="LGES",
        source=None,
        source_type="ground_truth",
        region=None,
        date=None,
    )
    assert "---" in fm
    assert "company: LGES" in fm
```

```
pytest tests/ingestion/test_pipeline.py::test_build_frontmatter_contains_required_fields tests/ingestion/test_pipeline.py::test_build_frontmatter_handles_none_source -v
```

Expected: FAIL (`_build_frontmatter` not defined).

- [ ] **Step 3: Add `_build_frontmatter` to `src/ingestion/pipeline.py`**

Add this function (near the top, before `_ingest_stream`):

```python
import datetime as _dt

def _build_frontmatter(
    company: str,
    source: str | None,
    source_type: str,
    region: str | None,
    date: str | None,
) -> str:
    today = date or _dt.date.today().isoformat()
    lines = [
        "---",
        f"company: {company}",
        f"source: {source or 'unknown'}",
        f"source_type: {source_type}",
        f"region: {region or 'unknown'}",
        f"date: {today}",
        "---",
    ]
    return "\n".join(lines) + "\n"
```

Then, in `_ingest_stream()`, prepend the frontmatter before writing the markdown. Find the line that calls `cleaner.extract_article_text()` (or similar) and wrap the result:

```python
# After extracting markdown content:
frontmatter = _build_frontmatter(
    company=entry.company,
    source=entry.source,
    source_type=stream_name,
    region=entry.region,
    date=None,  # uses today
)
content_with_frontmatter = frontmatter + markdown_content
# Write content_with_frontmatter to file instead of markdown_content
```

- [ ] **Step 4: Update `src/tagger/cli.py` to accept `--policy` and `--operations` args**

Read `src/tagger/cli.py`:

```bash
cat src/tagger/cli.py
```

Add two new optional arguments to the argument parser:

```python
parser.add_argument("--policy", default="data/raw/policy",
                    help="Directory containing policy markdown files")
parser.add_argument("--operations", default="data/raw/operations",
                    help="Directory containing operations markdown files")
```

Then update the `input_dirs` dict passed to `run_batch()`:

```python
input_dirs = {
    "perception": [args.perception],
    "ground_truth": [args.ground_truth],
    "policy": [args.policy],
    "operations": [args.operations],
}
```

- [ ] **Step 5: Run tests**

```
pytest tests/ingestion/test_pipeline.py -v
pytest tests/tagger/ -v
```

Expected: new frontmatter tests PASS; existing tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/pipeline.py src/tagger/cli.py tests/ingestion/test_pipeline.py
git commit -m "feat(ingestion): write YAML frontmatter to ingested markdown; tagger CLI accepts policy/operations"
```

---

## Phase 3 — Evidence Engine

### Task 6: Differentiation Matrix Aggregator + Chart

**Files:**
- Modify: `src/signal_engine/aggregator.py`
- Modify: `src/signal_engine/charts.py`
- Create: `tests/signal_engine/test_evidence_engine.py`

- [ ] **Step 1: Write failing tests**

Create `tests/signal_engine/test_evidence_engine.py`:

```python
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
    empty = pd.DataFrame(columns=["company", "localization_score"])
    df = compute_differentiation_matrix(empty)
    assert len(df) == 0
```

```
pytest tests/signal_engine/test_evidence_engine.py -v
```

Expected: FAIL (`compute_differentiation_matrix` not imported).

- [ ] **Step 2: Implement `compute_differentiation_matrix` in `src/signal_engine/aggregator.py`**

Append to `src/signal_engine/aggregator.py`:

```python
_DIFF_FACTORS: dict[str, str] = {
    "localization": "localization_score",
    "subsidy_reliance": "subsidy_dependency",
    "execution": "execution_quality",
    "capex_efficiency": "capex_signal",
    "margin_quality": "margin_signal",
    "ROIC": "ROIC_signal",
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
import pathlib
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

Append to `src/signal_engine/charts.py`:

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

- [ ] **Step 5: Run all evidence engine tests**

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

### Task 7: Why Now Timeline Aggregator + Chart

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
    df = compute_timeline(_make_timeline_df())
    assert isinstance(df, pd.DataFrame)

def test_compute_timeline_has_required_columns():
    df = compute_timeline(_make_timeline_df())
    assert "quarter" in df.columns
    assert "company" in df.columns
    assert "topic" in df.columns
    assert "mention_count" in df.columns

def test_compute_timeline_no_date_column_returns_empty():
    df = compute_timeline(pd.DataFrame(columns=["company", "topic_cluster"]))
    assert len(df) == 0

def test_compute_timeline_assigns_quarters():
    df = compute_timeline(_make_timeline_df())
    quarters = df["quarter"].unique().tolist()
    assert any("2025" in q for q in quarters)
```

```
pytest tests/signal_engine/test_evidence_engine.py -k "timeline" -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `compute_timeline` in `src/signal_engine/aggregator.py`**

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
    # Topic mention counts
    for (quarter, company, topic), group in df2.groupby(["quarter", "company", "topic_cluster"]):
        rows.append({"quarter": quarter, "company": company, "topic": topic, "mention_count": len(group)})

    # Contradiction spike counts
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

```python
def build_why_now_timeline_chart(timeline_df: pd.DataFrame, output_path: str) -> None:
    import plotly.express as px

    if timeline_df.empty:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(title="Why Now Timeline (no data)", width=900, height=400)
        fig.write_image(output_path)
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

### Task 8: Contradiction Scanner Aggregator + Chart

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
         "claim_summary": "CATL margins fell sharply.", "contradiction_reason": "Challenges bull thesis on margins."},
        {"company": "CATL", "contradiction_flag": False, "sentiment_score": 8.0,
         "claim_summary": "CATL capacity on track.", "contradiction_reason": None},
        {"company": "LGES", "contradiction_flag": True, "sentiment_score": 2.0,
         "claim_summary": "LGES IRA credit at risk.", "contradiction_reason": "Policy risk not priced in."},
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
    no_flags = pd.DataFrame([
        {"company": "CATL", "contradiction_flag": False, "sentiment_score": 7.0,
         "claim_summary": "Good.", "contradiction_reason": None},
    ])
    df = compute_contradictions(no_flags)
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

```python
def compute_contradictions(df: pd.DataFrame) -> pd.DataFrame:
    if "contradiction_flag" not in df.columns:
        return pd.DataFrame(columns=["company", "claim_summary", "contradiction_reason", "sentiment_score"])
    flagged = df[df["contradiction_flag"] == True].copy()
    cols = [c for c in ["company", "claim_summary", "contradiction_reason", "sentiment_score", "contradiction_flag"] if c in flagged.columns]
    return flagged[cols].reset_index(drop=True)
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

```python
def build_contradiction_chart(contradictions_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if contradictions_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Contradiction Scanner (no contradictions identified)", width=900, height=300)
        fig.write_image(output_path)
        return

    catl = contradictions_df[contradictions_df["company"] == "CATL"]
    lges = contradictions_df[contradictions_df["company"] == "LGES"]

    fig = go.Figure()
    for company, sub, color in [("CATL", catl, "#2563EB"), ("LGES", lges, "#DC2626")]:
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["sentiment_score"],
            y=sub["claim_summary"].str[:60],
            mode="markers+text",
            name=company,
            marker=dict(size=14, color=color),
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

### Task 9: Risk Tree Aggregator + Chart

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
    catl_policy = df[(df["company"] == "CATL") & (df["risk_category"] == "policy_risk")]["likelihood"].values[0]
    lges_policy = df[(df["company"] == "LGES") & (df["risk_category"] == "policy_risk")]["likelihood"].values[0]
    assert lges_policy > catl_policy

def test_compute_risk_tree_empty_returns_empty():
    df = compute_risk_tree(pd.DataFrame(columns=["company"]))
    assert len(df) == 0
```

```
pytest tests/signal_engine/test_evidence_engine.py -k "risk" -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `compute_risk_tree` in `src/signal_engine/aggregator.py`**

```python
_RISK_MAP: dict[str, tuple[str, bool]] = {
    # (column, is_risk_when_high)
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

```python
def build_risk_tree_chart(risk_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if risk_df.empty:
        go.Figure().write_image(output_path)
        return

    fig = go.Figure()
    colors = {"CATL": "#2563EB", "LGES": "#DC2626"}
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

### Task 10: Evidence Attribution Aggregator + Chart

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

```python
def build_evidence_scale_chart(attribution_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if attribution_df.empty:
        go.Figure().write_image(output_path)
        return

    fig = go.Figure()
    colors = {"perception": "#60A5FA", "ground_truth": "#1D4ED8",
              "policy": "#A78BFA", "operations": "#34D399"}

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

### Task 11: Wire Evidence Engine into signal_engine CLI

**Files:**
- Modify: `src/signal_engine/cli.py`
- Modify: `tests/signal_engine/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add to `tests/signal_engine/test_cli.py`:

```python
def test_run_signal_engine_produces_five_new_charts(tmp_path):
    # Build a DataFrame with all v2 fields
    import pandas as pd, json
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

    from src.signal_engine.cli import run_signal_engine
    run_signal_engine(str(tags_dir), str(out_dir), human_inputs_path=None)

    expected_files = [
        "differentiation_matrix.png",
        "why_now_timeline.png",
        "contradictions.png",
        "risk_tree.png",
        "evidence_scale.png",
    ]
    for fname in expected_files:
        assert (out_dir / fname).exists(), f"Missing: {fname}"
```

```
pytest tests/signal_engine/test_cli.py::test_run_signal_engine_produces_five_new_charts -v
```

Expected: FAIL.

- [ ] **Step 2: Update `src/signal_engine/cli.py`**

In `run_signal_engine()`, after the existing chart generation calls, append:

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
import os

# ... after existing aggregations ...

diff_df = compute_differentiation_matrix(tag_df)
build_differentiation_matrix_chart(diff_df, os.path.join(output_dir, "differentiation_matrix.png"))

timeline_df = compute_timeline(tag_df)
build_why_now_timeline_chart(timeline_df, os.path.join(output_dir, "why_now_timeline.png"))

contra_df = compute_contradictions(tag_df)
build_contradiction_chart(contra_df, os.path.join(output_dir, "contradictions.png"))

risk_df = compute_risk_tree(tag_df)
build_risk_tree_chart(risk_df, os.path.join(output_dir, "risk_tree.png"))

attrib_df = compute_evidence_attribution(tag_df)
build_evidence_scale_chart(attrib_df, os.path.join(output_dir, "evidence_scale.png"))
```

Move imports to top of file (not inside function).

- [ ] **Step 3: Run tests**

```
pytest tests/signal_engine/ -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/signal_engine/cli.py tests/signal_engine/test_cli.py
git commit -m "feat(signal_engine): wire all 5 evidence engine charts into CLI output"
```

---

## Phase 4 — Synthesis Layer

### Task 12: Synthesis Schema

**Files:**
- Create: `src/synthesis/__init__.py`
- Create: `src/synthesis/schema.py`
- Create: `tests/synthesis/__init__.py`
- Create: `tests/synthesis/test_schema.py`

- [ ] **Step 1: Write failing test**

Create `tests/synthesis/__init__.py` (empty) and `tests/synthesis/test_schema.py`:

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
```

```
pytest tests/synthesis/test_schema.py -v
```

Expected: FAIL (module not found).

- [ ] **Step 2: Create `src/synthesis/__init__.py` and `src/synthesis/schema.py`**

`src/synthesis/__init__.py`: empty file.

`src/synthesis/schema.py`:

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

    @field_validator("executive_summary", "why_now", "differentiation_takeaway",
                     "contradiction_summary", "risk_summary")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty")
        return v

    @field_validator("analyst_questions", "limitations")
    @classmethod
    def must_have_at_least_one(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("list must contain at least one item")
        return v
```

- [ ] **Step 3: Run tests**

```
pytest tests/synthesis/test_schema.py -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/synthesis/__init__.py src/synthesis/schema.py tests/synthesis/__init__.py tests/synthesis/test_schema.py
git commit -m "feat(synthesis): add SynthesisOutput schema with validation"
```

---

### Task 13: Synthesis Prompt Builder

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
        {"company": "LGES", "claim_summary": "IRA credit at risk.", "contradiction_reason": "Policy change.", "sentiment_score": 2.0},
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

def test_prompt_includes_no_recommendation_instruction():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={},
    )
    assert "do NOT make recommendations" in prompt.lower() or "do not make recommendations" in prompt.lower()

def test_prompt_includes_json_schema():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={},
    )
    assert "executive_summary" in prompt
    assert "analyst_questions" in prompt
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
    diff_section = _format_diff_df(diff_df)
    contra_section = _format_contradictions(contradictions_df)
    signals_section = _format_signals(top_signals)

    return f"""You are a quantitative research analyst synthesizing structured AI-generated evidence about CATL and LGES for an institutional equity research report.

RULES:
- Do NOT make investment recommendations (no buy/sell/hold).
- Do NOT infer facts not supported by the evidence below.
- Summarize asymmetry only. Be specific and precise.
- Analyst questions must be concrete, verifiable, and forward-looking.
- Limitations must be genuine methodological constraints, not generic disclaimers.

DIFFERENTIATION MATRIX (mean scores 1–10):
{diff_section}

CONTRADICTIONS IDENTIFIED:
{contra_section}

TOP SIGNALS BY COMPANY:
{signals_section}

Return a JSON object matching this schema exactly. No markdown fences, no explanation:
{{
  "executive_summary": "<2-3 sentences on the key asymmetry>",
  "why_now": "<1-2 sentences on what has changed in 2025-26 to make this pair trade relevant>",
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
        lines.append(f"  [{row['company']}] {row['claim_summary']} — {row.get('contradiction_reason', '')}")
    return "\n".join(lines)


def _format_signals(signals: dict[str, list[dict]]) -> str:
    lines = []
    for company, sigs in signals.items():
        lines.append(f"  {company}:")
        for sig in sigs[:3]:
            lines.append(f"    - {sig.get('claim_summary', sig.get('summary', ''))}")
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
git commit -m "feat(synthesis): add prompt builder for Claude synthesis call"
```

---

### Task 14: Synthesiser + CLI

**Files:**
- Create: `src/synthesis/synthesiser.py`
- Create: `src/synthesis/cli.py`
- Create: `tests/synthesis/test_synthesiser.py`
- Create: `tests/synthesis/test_cli.py`

- [ ] **Step 1: Write failing tests**

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

def test_synthesise_raises_on_invalid_json():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not valid json")]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        with pytest.raises(ValueError, match="Failed to parse synthesis output"):
            synthesise("test prompt")
```

Create `tests/synthesis/test_cli.py`:

```python
import json, pathlib
from unittest.mock import patch, MagicMock
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
```

```
pytest tests/synthesis/ -v
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
        raise ValueError(f"Failed to parse synthesis output: {exc}\n\nRaw response:\n{raw}") from exc
```

- [ ] **Step 3: Implement `src/synthesis/cli.py`**

```python
import argparse
import json
import os
import sys

import pandas as pd

from src.signal_engine.loader import load_tags
from src.signal_engine.aggregator import (
    compute_differentiation_matrix,
    compute_contradictions,
)
from src.human_layer.summariser import extract_top_signals
from src.synthesis.prompt_builder import build_synthesis_prompt
from src.synthesis.synthesiser import synthesise


def run_synthesis(
    tags_dir: str,
    charts_dir: str,
    output_path: str,
    model: str = "claude-sonnet-4-6",
) -> None:
    tag_df = load_tags(tags_dir) if os.path.isdir(tags_dir) and any(
        f.endswith(".json") for f in os.listdir(tags_dir)
    ) else pd.DataFrame()

    diff_df = compute_differentiation_matrix(tag_df)
    contra_df = compute_contradictions(tag_df)
    top_signals = extract_top_signals(tag_df, top_n=3) if not tag_df.empty else {}

    prompt = build_synthesis_prompt(
        diff_df=diff_df,
        contradictions_df=contra_df,
        top_signals=top_signals,
    )

    output = synthesise(prompt, model=model)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output.model_dump(), f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthesis layer (single Claude call)")
    parser.add_argument("--tags",    default="data/processed/tags", help="Directory of tag JSON files")
    parser.add_argument("--charts",  default="output/charts", help="Directory of chart PNG files")
    parser.add_argument("--output",  default="output/synthesis.json", help="Output path for synthesis JSON")
    parser.add_argument("--model",   default="claude-sonnet-4-6", help="Claude model ID")
    args = parser.parse_args()
    run_synthesis(args.tags, args.charts, args.output, args.model)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests**

```
pytest tests/synthesis/ -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/synthesis/synthesiser.py src/synthesis/cli.py tests/synthesis/test_synthesiser.py tests/synthesis/test_cli.py
git commit -m "feat(synthesis): add synthesiser (one Claude call) and CLI entry point"
```

---

## Phase 5 — Human Layer & Renderer Expansion

### Task 15: Expand HumanInputs and DeckInput

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

- [ ] **Step 2: Write failing tests for expanded HumanInputs**

Add to `tests/human_layer/test_schema.py`:

```python
from src.human_layer.schema import HumanInputs, load_human_inputs
import yaml, pathlib, pytest

def test_human_inputs_has_analyst_action_layer(tmp_path):
    cfg = tmp_path / "human_inputs.yaml"
    cfg.write_text("""
catl_overseas_gross_margin_pct: 31.4
catl_domestic_gross_margin_pct: 28.0
lges_q1_operating_margin_ex_ira_pct: 2.1
roic_shock_delta_bps: -150
shock_scenario: "IRA credit cap reduces LGES ROIC by 150bps"
catl_execution_edge: "CATL commissioned 4 overseas plants on schedule in 2025"
lges_execution_risk: "LGES Hungary ramp delayed by 6 months vs initial guidance"
why_now_takeaway: "Operational divergence accelerated in 2025-26"
why_now_followup: "Verify Hungary utilization assumptions"
differentiation_takeaway: "CATL execution consistently 2x LGES on our scoring"
differentiation_followup: "Check if CATL localization data captures JV structures"
contradiction_takeaway: "IRA exposure risk more acute than consensus models"
contradiction_followup: "Model IRA cliff scenario for LGES 2026 guidance"
""")
    inputs = load_human_inputs(str(cfg))
    assert inputs.why_now_takeaway == "Operational divergence accelerated in 2025-26"
    assert inputs.why_now_followup == "Verify Hungary utilization assumptions"
    assert inputs.differentiation_takeaway == "CATL execution consistently 2x LGES on our scoring"
    assert inputs.contradiction_takeaway == "IRA exposure risk more acute than consensus models"
```

```
pytest tests/human_layer/test_schema.py -v
```

Expected: FAIL (new fields not defined).

- [ ] **Step 3: Expand `src/human_layer/schema.py`**

Add to the `HumanInputs` class (after existing fields):

```python
    # Analyst action layer
    why_now_takeaway: str
    why_now_followup: str
    differentiation_takeaway: str
    differentiation_followup: str
    contradiction_takeaway: str
    contradiction_followup: str
```

Add validators for the new fields (no placeholders, no empty strings) using the same pattern as existing `catl_execution_edge` validator.

- [ ] **Step 4: Update `config/human_inputs.yaml`**

Append:

```yaml
why_now_takeaway: "Operational divergence accelerated materially in 2025-26"
why_now_followup: "Verify Hungary plant utilization assumptions for 2026"
differentiation_takeaway: "CATL scores ~2.5x higher than LGES on execution and localization"
differentiation_followup: "Confirm CATL JV structures are captured in localization scoring"
contradiction_takeaway: "IRA exposure risk is more acute than consensus models price in"
contradiction_followup: "Model IRA cliff scenario for LGES 2026 margin guidance"
```

- [ ] **Step 5: Write failing test for expanded DeckInput**

Add to `tests/human_layer/test_merger.py`:

```python
from src.human_layer.merger import DeckInput

def test_deck_input_has_new_chart_paths():
    # DeckInput must accept five new chart path fields
    import dataclasses
    fields = {f.name for f in dataclasses.fields(DeckInput)}
    assert "differentiation_matrix_path" in fields
    assert "why_now_timeline_path" in fields
    assert "contradictions_path" in fields
    assert "risk_tree_path" in fields
    assert "evidence_scale_path" in fields

def test_deck_input_has_synthesis_field():
    import dataclasses
    fields = {f.name for f in dataclasses.fields(DeckInput)}
    assert "synthesis" in fields
```

```
pytest tests/human_layer/test_merger.py -v
```

Expected: FAIL.

- [ ] **Step 6: Expand `DeckInput` in `src/human_layer/merger.py`**

```python
from dataclasses import dataclass, field
from typing import Optional
from src.human_layer.schema import HumanInputs
from src.synthesis.schema import SynthesisOutput


@dataclass
class DeckInput:
    human: HumanInputs
    ai_signals: dict[str, list[dict]]
    synthesis: Optional[SynthesisOutput]
    divergence_matrix_path: str
    trend_inflection_path: str
    differentiation_matrix_path: str
    why_now_timeline_path: str
    contradictions_path: str
    risk_tree_path: str
    evidence_scale_path: str
```

Update `merge_inputs()` signature to accept the five new chart paths and optional synthesis:

```python
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
    synthesis: Optional[SynthesisOutput] = None,
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

- [ ] **Step 7: Run tests**

```
pytest tests/human_layer/ -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/human_layer/schema.py src/human_layer/merger.py config/human_inputs.yaml tests/human_layer/
git commit -m "feat(human_layer): expand HumanInputs with analyst action layer; expand DeckInput with 5 new chart paths + synthesis"
```

---

### Task 16: Expand Renderer to 15 Slides

**Files:**
- Modify: `src/renderer/content_map.py`
- Modify: `src/renderer/cli.py`
- Modify: `tests/renderer/test_content_map.py`

- [ ] **Step 1: Write failing tests for new slide structure**

Add to `tests/renderer/test_content_map.py`:

```python
from src.renderer.content_map import build_slide_specs, SlideType

def _make_full_deck_input(tmp_path):
    from src.human_layer.schema import HumanInputs
    from src.human_layer.merger import DeckInput
    from src.synthesis.schema import SynthesisOutput

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
    synthesis = SynthesisOutput(
        executive_summary="CATL leads on globalization.",
        why_now="Divergence accelerated in 2025Q4.",
        differentiation_takeaway="Execution gap is 4pts.",
        contradiction_summary="IRA dependency challenged by 3 docs.",
        risk_summary="Policy reversal is primary bear case.",
        analyst_questions=["What is LGES Hungary utilization at IRA cap?"],
        limitations=["Evidence limited to public disclosures."],
    )

    # Create dummy chart PNGs
    for name in ["div_matrix.png", "trend.png", "diff.png", "why_now.png", "contra.png", "risk.png", "evidence.png"]:
        (tmp_path / name).write_bytes(b"PNG")

    return DeckInput(
        human=human,
        ai_signals={"CATL": [{"claim_summary": "Strong."}], "LGES": [{"claim_summary": "Weak."}]},
        synthesis=synthesis,
        divergence_matrix_path=str(tmp_path / "div_matrix.png"),
        trend_inflection_path=str(tmp_path / "trend.png"),
        differentiation_matrix_path=str(tmp_path / "diff.png"),
        why_now_timeline_path=str(tmp_path / "why_now.png"),
        contradictions_path=str(tmp_path / "contra.png"),
        risk_tree_path=str(tmp_path / "risk.png"),
        evidence_scale_path=str(tmp_path / "evidence.png"),
    )

def test_slide_count_is_15(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    assert len(specs) == 15

def test_differentiation_matrix_slide_present(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    titles = [s.title for s in specs]
    assert any("Differentiation" in t for t in titles)

def test_why_now_slide_present(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    titles = [s.title for s in specs]
    assert any("Why Now" in t for t in titles)

def test_contradiction_scanner_slide_present(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    titles = [s.title for s in specs]
    assert any("Contradiction" in t for t in titles)

def test_risk_tree_slide_present(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    titles = [s.title for s in specs]
    assert any("Risk" in t for t in titles)

def test_analyst_questions_slide_uses_synthesis(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    q_slide = next((s for s in specs if "Analyst" in s.title and "Question" in s.title), None)
    assert q_slide is not None
    assert "Hungary" in q_slide.body

def test_no_prohibited_language(tmp_path):
    deck = _make_full_deck_input(tmp_path)
    specs = build_slide_specs(deck)
    forbidden = {"buy", "sell", "hold", "we believe", "we recommend", "outperform", "underperform"}
    for spec in specs:
        text = (spec.title + " " + spec.body).lower()
        for word in forbidden:
            assert word not in text, f"Prohibited language '{word}' found in slide '{spec.title}'"
```

```
pytest tests/renderer/test_content_map.py -v
```

Expected: failures on slide count and new slides.

- [ ] **Step 2: Rewrite `build_slide_specs` in `src/renderer/content_map.py`**

Replace the slide list in `build_slide_specs()` to produce exactly 15 slides:

```python
def build_slide_specs(deck_input: DeckInput) -> list[SlideSpec]:
    h = deck_input.human
    s = deck_input.synthesis
    signals = deck_input.ai_signals

    catl_signals_body = "\n".join(
        f"• {sig.get('claim_summary', sig.get('summary', ''))}"
        for sig in signals.get("CATL", [])
    )
    lges_signals_body = "\n".join(
        f"• {sig.get('claim_summary', sig.get('summary', ''))}"
        for sig in signals.get("LGES", [])
    )

    analyst_questions_body = (
        "\n".join(f"• {q}" for q in s.analyst_questions) if s else
        "• [Add analyst questions here]"
    )
    limitations_body = (
        "\n".join(f"• {l}" for l in s.limitations) if s else
        "• Evidence limited to public IR disclosures and news media."
    )
    why_now_body = (
        f"{s.why_now}\n\nAnalyst takeaway: {h.why_now_takeaway}\n\nFollow-up: {h.why_now_followup}"
        if s else h.why_now_takeaway
    )
    diff_body = (
        f"{s.differentiation_takeaway}\n\nAnalyst takeaway: {h.differentiation_takeaway}\n\nFollow-up: {h.differentiation_followup}"
        if s else h.differentiation_takeaway
    )
    contra_body = (
        f"{s.contradiction_summary}\n\nAnalyst takeaway: {h.contradiction_takeaway}\n\nFollow-up: {h.contradiction_followup}"
        if s else h.contradiction_takeaway
    )

    specs = [
        # 1
        SlideSpec(slide_type=SlideType.TITLE, title="CATL vs LGES: Globalization Quality Divergence",
                  body="AI-Assisted Institutional Research | AgenticAlpha v2"),
        # 2
        SlideSpec(slide_type=SlideType.THESIS, title="Pair Thesis: Quality of Globalization",
                  body=(
                      f"CATL overseas gross margin: {h.catl_overseas_gross_margin_pct:.1f}%\n"
                      f"LGES operating margin ex-IRA: {h.lges_q1_operating_margin_ex_ira_pct:.1f}%\n\n"
                      f"{s.executive_summary if s else ''}"
                  )),
        # 3
        SlideSpec(slide_type=SlideType.AI_SIGNAL, title="AI Workflow: Evidence Engine Architecture",
                  body=(
                      "AI pipeline: Ingestion → Rich Tagger → Evidence Engine → Synthesis\n"
                      "Human layer: Analyst inputs + takeaways layered on top\n"
                      "All LLM outputs validated against structured schemas. No valuation or buy/sell signals."
                  )),
        # 4
        SlideSpec(slide_type=SlideType.CHART, title="Differentiation Matrix: Factor Scores (1–10)",
                  body=diff_body,
                  chart_path=deck_input.differentiation_matrix_path),
        # 5
        SlideSpec(slide_type=SlideType.CHART, title="Why Now: Topic Frequency Timeline",
                  body=why_now_body,
                  chart_path=deck_input.why_now_timeline_path),
        # 6
        SlideSpec(slide_type=SlideType.CHART, title="Contradiction Scanner: Evidence Challenging Thesis",
                  body=contra_body,
                  chart_path=deck_input.contradictions_path),
        # 7
        SlideSpec(slide_type=SlideType.CHART, title="Evidence Scale: Document Attribution by Stream",
                  body="Corroboration across perception, ground truth, policy, and operations streams.",
                  chart_path=deck_input.evidence_scale_path),
        # 8
        SlideSpec(slide_type=SlideType.AI_SIGNAL, title="Top Perception Signals: CATL",
                  body=catl_signals_body or "• No CATL signals tagged."),
        # 9
        SlideSpec(slide_type=SlideType.AI_SIGNAL, title="Top Perception Signals: LGES",
                  body=lges_signals_body or "• No LGES signals tagged."),
        # 10
        SlideSpec(slide_type=SlideType.FUNDAMENTALS, title="Margin Bridge: AI Signal vs Fundamental Data",
                  table_rows=[
                      ["Metric", "CATL", "LGES"],
                      ["Overseas Gross Margin", f"{h.catl_overseas_gross_margin_pct:.1f}%", "N/A"],
                      ["Domestic Gross Margin", f"{h.catl_domestic_gross_margin_pct:.1f}%", "N/A"],
                      ["Operating Margin ex-IRA", "N/A", f"{h.lges_q1_operating_margin_ex_ira_pct:.1f}%"],
                  ]),
        # 11
        SlideSpec(slide_type=SlideType.CHART, title="Risk Tree: Likelihood × Impact Matrix",
                  body="Policy risk, execution risk, capex mismatch, and ROIC deterioration.",
                  chart_path=deck_input.risk_tree_path),
        # 12
        SlideSpec(slide_type=SlideType.COUNTERFACTUAL, title="Downside Scenario: IRA Credit Cap",
                  body=(
                      f"Scenario: {h.shock_scenario}\n"
                      f"ROIC impact: {h.roic_shock_delta_bps:+d} bps\n"
                      f"Execution risk: {h.lges_execution_risk}"
                  )),
        # 13
        SlideSpec(slide_type=SlideType.AI_SIGNAL, title="Analyst Questions for Follow-Up",
                  body=analyst_questions_body),
        # 14
        SlideSpec(slide_type=SlideType.DISCLOSURE, title="Methodology Limitations",
                  body=limitations_body),
        # 15
        SlideSpec(slide_type=SlideType.DISCLOSURE, title="AI Methodology Disclosure",
                  body=(
                      "Evidence collected via automated ingestion from public sources.\n"
                      "Tags generated by LLM (Google Gemini) with schema validation.\n"
                      "Synthesis generated by Claude (Anthropic) — one call, no recommendations.\n"
                      "No valuation analysis, channel checks, or non-public information."
                  )),
    ]

    assert len(specs) <= 20, f"Slide count {len(specs)} exceeds maximum of 20"
    return specs
```

- [ ] **Step 3: Run tests**

```
pytest tests/renderer/test_content_map.py -v
```

Expected: all PASS.

- [ ] **Step 4: Update `src/renderer/cli.py` to pass new chart paths**

Read `src/renderer/cli.py` first:

```bash
cat src/renderer/cli.py
```

Add arguments and pass them to `merge_inputs()`:

```python
parser.add_argument("--differentiation-matrix",  default="output/charts/differentiation_matrix.png")
parser.add_argument("--why-now-timeline",         default="output/charts/why_now_timeline.png")
parser.add_argument("--contradictions",           default="output/charts/contradictions.png")
parser.add_argument("--risk-tree",                default="output/charts/risk_tree.png")
parser.add_argument("--evidence-scale",           default="output/charts/evidence_scale.png")
parser.add_argument("--synthesis",                default="output/synthesis.json",
                    help="Path to synthesis JSON output")
```

Load synthesis (optional — skip gracefully if file absent):

```python
import json, pathlib
from src.synthesis.schema import SynthesisOutput

synthesis = None
if pathlib.Path(args.synthesis).exists():
    synthesis = SynthesisOutput(**json.loads(pathlib.Path(args.synthesis).read_text()))

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

- [ ] **Step 5: Run full renderer tests**

```
pytest tests/renderer/ -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/renderer/content_map.py src/renderer/cli.py tests/renderer/test_content_map.py
git commit -m "feat(renderer): expand to 15 slides with differentiation matrix, contradiction scanner, risk tree, analyst questions"
```

---

## Phase 6 — Audit Module

### Task 17: Audit Trail Module

**Files:**
- Create: `src/audit/__init__.py`
- Create: `src/audit/trail.py`
- Create: `tests/audit/__init__.py`
- Create: `tests/audit/test_trail.py`

- [ ] **Step 1: Write failing tests**

Create `tests/audit/__init__.py` (empty) and `tests/audit/test_trail.py`:

```python
import pandas as pd
from src.audit.trail import build_audit_table, format_audit_table_rows

def _make_df():
    return pd.DataFrame([
        {"company": "CATL", "claim_summary": "CATL shipped 12 GWh overseas.",
         "source_file": "catl_abc.md", "confidence": 0.9, "contradiction_reason": None,
         "stream": "ground_truth"},
        {"company": "LGES", "claim_summary": "LGES IRA credit may be capped.",
         "source_file": "lges_xyz.md", "confidence": 0.7,
         "contradiction_reason": "Challenges IRA dependency thesis.", "stream": "policy"},
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

def test_audit_row_caveat_none_identified_when_no_contradiction():
    result = build_audit_table(_make_df())
    catl_row = next(r for r in result if "CATL" in r["claim"])
    assert catl_row["caveat"] == "None identified"

def test_format_audit_table_rows_for_pptx():
    rows = build_audit_table(_make_df())
    table_rows = format_audit_table_rows(rows)
    # First row must be the header
    assert table_rows[0] == ["Claim", "Source", "Confidence", "Caveat"]
    assert len(table_rows) == 3  # header + 2 data rows
```

```
pytest tests/audit/test_trail.py -v
```

Expected: FAIL.

- [ ] **Step 2: Implement `src/audit/__init__.py` and `src/audit/trail.py`**

`src/audit/__init__.py`: empty.

`src/audit/trail.py`:

```python
import pandas as pd


def build_audit_table(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in df.iterrows():
        conf = row.get("confidence")
        conf_str = f"{conf:.0%}" if conf is not None else "unknown"
        caveat = row.get("contradiction_reason") or "None identified"
        rows.append({
            "claim": str(row.get("claim_summary", "")),
            "docs": str(row.get("source_file", "")),
            "confidence": conf_str,
            "caveat": str(caveat),
        })
    return rows


def format_audit_table_rows(audit_rows: list[dict]) -> list[list[str]]:
    header = ["Claim", "Source", "Confidence", "Caveat"]
    data = [
        [r["claim"][:80], r["docs"], r["confidence"], r["caveat"][:60]]
        for r in audit_rows
    ]
    return [header] + data
```

- [ ] **Step 3: Run tests**

```
pytest tests/audit/ -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/audit/__init__.py src/audit/trail.py tests/audit/__init__.py tests/audit/test_trail.py
git commit -m "feat(audit): add audit trail module — claim/docs/confidence/caveat table for appendix"
```

---

## Final Verification

- [ ] **Run full test suite**

```
pytest tests/ -v --tb=short
```

Expected: all tests PASS. No new failures.

- [ ] **Smoke test the full CLI pipeline**

```bash
# Step 1: Ingestion (uses existing URLs)
python -m src.ingestion.cli --config config/urls.yaml --output data/raw

# Step 2: Tagger (uses Gemini; requires API key in env)
python -m src.tagger.cli \
  --perception data/raw/perception \
  --ground-truth data/raw/ground_truth \
  --policy data/raw/policy \
  --operations data/raw/operations \
  --output data/processed/tags

# Step 3: Evidence Engine
python -m src.signal_engine.cli \
  --tags data/processed/tags \
  --output output/charts \
  --human-inputs config/human_inputs.yaml

# Step 4: Synthesis (requires ANTHROPIC_API_KEY)
python -m src.synthesis.cli \
  --tags data/processed/tags \
  --charts output/charts \
  --output output/synthesis.json

# Step 5: Renderer
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

- [ ] **Verify output deck exists and has correct slide count**

```bash
python -c "
from pptx import Presentation
prs = Presentation('output/deck/catl_lges_pair_trade_v2.pptx')
print(f'Slide count: {len(prs.slides)}')
assert len(prs.slides) == 15, f'Expected 15 slides, got {len(prs.slides)}'
print('OK')
"
```

- [ ] **Final commit**

```bash
git add -A
git commit -m "chore: final smoke test verification — AgenticAlpha v2 complete"
```

---

## Self-Review Against Spec

### Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| YAML frontmatter (date, source, source_type, company, region) | Task 5 |
| `policy` and `operations` streams | Task 4, 5 |
| Expanded `ArticleTag` (13 new fields) | Task 1, 2, 3 |
| Source weighting (perception=1, ground_truth=2, policy=1.5, operations=2) | Task 3 |
| Contradiction flag + prompt | Task 1, 2 |
| `compute_differentiation_matrix()` + heatmap/bar chart | Task 6 |
| `compute_timeline()` + line chart | Task 7 |
| `compute_contradictions()` + severity heatmap | Task 8 |
| Risk Tree (likelihood × impact) + chart | Task 9 |
| Evidence Attribution + chart | Task 10 |
| `src/synthesis/` with prompt_builder, synthesiser, schema, CLI | Tasks 12–14 |
| `SynthesisOutput` schema with all 7 fields | Task 12 |
| "Do NOT make recommendations" rule in prompt | Task 13 |
| Expanded `DeckInput` with all new artifacts | Task 15 |
| Analyst action layer (takeaway + followup per artifact) | Task 15 |
| 15-slide renderer | Task 16 |
| Audit module | Task 17 |
| `python -m src.synthesis.cli` entry point | Task 14 |

**No spec requirements without a corresponding task.**
