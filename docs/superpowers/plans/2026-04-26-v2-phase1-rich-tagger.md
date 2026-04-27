# AgenticAlpha v2 — Phase 1: Rich Tagger

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the `Tag` schema from 5 fields to 17, update Gemini prompts to elicit the new fields, and enrich batch output with `source_weight` and `date` metadata.

**Architecture:** All changes are confined to `src/tagger/`. The schema, prompt, and batch modules are updated in place. No new modules created. The expanded tag JSON is backward-compatible with the signal engine loader (new fields are simply additive columns in the DataFrame).

**Tech Stack:** Python 3.11+, Pydantic v2, Google Gemini (existing).

**Prerequisites:** None — this is the first phase.

**Next phase:** Phase 2 (Ingestion Expansion) is independent and can run in parallel. Phase 3 (Evidence Engine) depends on this phase's new tag fields being present in JSON output.

---

## File Map

- Modify: `src/tagger/schema.py` — expand `Tag` with 12 new fields
- Modify: `src/tagger/prompt.py` — update system + user prompts
- Modify: `src/tagger/batch.py` — add `source_weight_for_stream()`, `parse_frontmatter_date()`, emit both into tag JSON
- Modify: `tests/tagger/test_schema.py` — new field tests + fix old `summary` → `claim_summary` references
- Modify: `tests/tagger/test_prompt.py` — new field presence tests
- Modify: `tests/tagger/test_batch.py` — `source_weight` and `date` in output

---

## Task 1: Expand ArticleTag Schema

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
            sentiment_score=5.0, direction="neutral", confidence=1.5,
            topic_cluster="Other", geo_exposure=["China"],
            globalization_model="unclear", localization_score=5,
            subsidy_dependency=5, execution_quality=5, margin_signal=5,
            capex_signal=5, ROIC_signal=5, contradiction_flag=False,
            contradiction_reason=None, claim_summary="Some claim.", key_quote=None,
        )

def test_contradiction_reason_required_when_flagged():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=3.0, direction="negative", confidence=0.7,
            topic_cluster="Subsidy_Dependence", geo_exposure=["US"],
            globalization_model="localization-driven", localization_score=3,
            subsidy_dependency=9, execution_quality=4, margin_signal=3,
            capex_signal=4, ROIC_signal=3, contradiction_flag=True,
            contradiction_reason=None,  # must not be None when flag is True
            claim_summary="LGES depends heavily on IRA credits.", key_quote=None,
        )

def test_numeric_scores_must_be_1_to_10():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=0.5,
            topic_cluster="Other", geo_exposure=["EU"],
            globalization_model="hybrid", localization_score=11,  # out of range
            subsidy_dependency=5, execution_quality=5, margin_signal=5,
            capex_signal=5, ROIC_signal=5, contradiction_flag=False,
            contradiction_reason=None, claim_summary="Test.", key_quote=None,
        )

def test_claim_summary_must_not_be_empty():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=0.5,
            topic_cluster="Other", geo_exposure=["EU"],
            globalization_model="hybrid", localization_score=5,
            subsidy_dependency=5, execution_quality=5, margin_signal=5,
            capex_signal=5, ROIC_signal=5, contradiction_flag=False,
            contradiction_reason=None, claim_summary="   ", key_quote=None,
        )

def test_globalization_model_enum_rejects_invalid():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=0.5,
            topic_cluster="Other", geo_exposure=["EU"],
            globalization_model="unknown-model",  # invalid
            localization_score=5, subsidy_dependency=5, execution_quality=5,
            margin_signal=5, capex_signal=5, ROIC_signal=5,
            contradiction_flag=False, contradiction_reason=None,
            claim_summary="Test.", key_quote=None,
        )
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/tagger/test_schema.py -v
```

Expected: multiple FAILED — fields not found, validators not triggered.

- [ ] **Step 3: Implement expanded schema in `src/tagger/schema.py`**

Replace the entire file:

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


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

- [ ] **Step 4: Run tests**

```
pytest tests/tagger/test_schema.py -v
```

Expected: all new tests PASS. Any old tests using `summary=` will fail — fix those in the next step.

- [ ] **Step 5: Fix old tests referencing deprecated `summary` field**

In `tests/tagger/test_schema.py`, find every `Tag(...)` call using `summary=` and:
- Rename to `claim_summary=`
- Add the new required fields: `confidence=0.5`, `globalization_model="hybrid"`, all integer scores as `5`, `contradiction_flag=False`, `contradiction_reason=None`, `key_quote=None`

Run again:

```
pytest tests/tagger/test_schema.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/tagger/schema.py tests/tagger/test_schema.py
git commit -m "feat(tagger): expand ArticleTag schema with 12 new fields for v2 evidence engine

Adds confidence, globalization_model, six 1-10 numeric signal scores
(localization, subsidy_dependency, execution_quality, margin_signal,
capex_signal, ROIC_signal), contradiction_flag + contradiction_reason,
claim_summary (replaces summary), and key_quote. Validators enforce
ranges, non-empty claim_summary, and contradiction_reason presence when
flag is True."
```

---

## Task 2: Update Tagger Prompts for New Schema

**Files:**
- Modify: `src/tagger/prompt.py`
- Modify: `tests/tagger/test_prompt.py`

- [ ] **Step 1: Read the current prompt file**

```bash
cat src/tagger/prompt.py
```

Note the existing JSON schema in the system prompt and the user message template. Keep the same function signatures.

- [ ] **Step 2: Write failing tests**

Create or add to `tests/tagger/test_prompt.py`:

```python
from src.tagger.prompt import build_system_prompt, build_user_message

def test_system_prompt_mentions_contradiction_flag():
    assert "contradiction_flag" in build_system_prompt()

def test_system_prompt_mentions_confidence():
    assert "confidence" in build_system_prompt()

def test_system_prompt_mentions_localization_score():
    assert "localization_score" in build_system_prompt()

def test_system_prompt_mentions_claim_summary():
    assert "claim_summary" in build_system_prompt()

def test_system_prompt_mentions_key_quote():
    assert "key_quote" in build_system_prompt()

def test_system_prompt_has_no_recommendation_rule():
    prompt = build_system_prompt()
    assert "do not make recommendations" in prompt.lower() or "do NOT make recommendations" in prompt

def test_user_message_contains_company_and_stream():
    msg = build_user_message("## CATL Q4\n\nBody.", company="CATL", stream="ground_truth")
    assert "CATL" in msg
    assert "ground_truth" in msg
```

```
pytest tests/tagger/test_prompt.py -v
```

Expected: FAIL (fields not yet in prompt).

- [ ] **Step 3: Replace `build_system_prompt()` in `src/tagger/prompt.py`**

```python
def build_system_prompt() -> str:
    return """You are a financial research analyst tagging investment research documents.

Return a JSON object that strictly matches this schema. Do NOT add fields, do NOT omit fields.

{
  "sentiment_score": <float 1.0-10.0, where 1=extremely bearish, 10=extremely bullish>,
  "direction": <"positive" | "negative" | "neutral">,
  "confidence": <float 0.0-1.0, your confidence in the tag given evidence quality>,
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
  "claim_summary": <string, one factual sentence summarizing the key claim>,
  "key_quote": <string, the single most evidentially significant verbatim quote, or null>
}

Rules:
- Do NOT make recommendations. Do NOT infer unsupported facts.
- contradiction_flag must be true only when the evidence materially challenges the primary investment thesis.
- claim_summary must be a single factual sentence. Do not begin with "The document" or "This article".
- key_quote must be verbatim from the document. Set to null if no strong quote exists.
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
git commit -m "feat(tagger): update prompts to elicit new v2 tag fields

Adds all 12 new fields to the JSON schema instruction block.
Adds explicit rule: do NOT make recommendations. Sets claim_summary
to replace old 'summary' field in the LLM contract."
```

---

## Task 3: Add source_weight and date Metadata in Batch Output

**Files:**
- Modify: `src/tagger/batch.py`
- Modify: `tests/tagger/test_batch.py`

- [ ] **Step 1: Read the current batch.py**

```bash
cat src/tagger/batch.py
```

Identify: (a) where the tag JSON dict is assembled before writing, (b) what `_parse_header()` currently does, (c) how `markdown_text` is read from each file.

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
    md = "---\ndate: 2025-11-15\ncompany: CATL\n---\nBody text here."
    assert parse_frontmatter_date(md) == "2025-11-15"

def test_parse_frontmatter_date_returns_none_when_absent():
    assert parse_frontmatter_date("# CATL Report\n\nBody text here.") is None

def test_batch_output_includes_source_weight(tmp_path):
    md_file = tmp_path / "catl_test.md"
    md_file.write_text("---\ndate: 2025-06-01\ncompany: CATL\n---\nCAT posted strong results.")

    fake_tag_dict = {
        "sentiment_score": 7.5, "direction": "positive", "confidence": 0.8,
        "topic_cluster": "Organic_Scale_vs_Export", "geo_exposure": ["US"],
        "globalization_model": "export-led", "localization_score": 8,
        "subsidy_dependency": 3, "execution_quality": 9, "margin_signal": 7,
        "capex_signal": 8, "ROIC_signal": 7, "contradiction_flag": False,
        "contradiction_reason": None, "claim_summary": "CATL posted strong results.",
        "key_quote": None,
    }
    mock_tag = MagicMock()
    mock_tag.model_dump.return_value = fake_tag_dict

    out_dir = tmp_path / "tags"
    out_dir.mkdir()

    with patch("src.tagger.batch.tag_document", return_value=mock_tag):
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

Expected: FAIL (`source_weight_for_stream` and `parse_frontmatter_date` not defined).

- [ ] **Step 3: Add helper functions to `src/tagger/batch.py`**

Add near the top (after imports):

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

- [ ] **Step 4: Enrich the tag output dict in `run_batch()` / `_process_file()`**

In the section where `output = tag.model_dump()` is assembled (before writing to JSON), add:

```python
output["stream"] = stream
output["company"] = company
output["source_file"] = str(source_file)
output["source_weight"] = source_weight_for_stream(stream)
output["date"] = parse_frontmatter_date(markdown_text)
```

Where `markdown_text` is the raw string read from the markdown file and `stream` is the stream name string (e.g. `"perception"`).

- [ ] **Step 5: Run all tagger tests**

```
pytest tests/tagger/ -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/tagger/batch.py tests/tagger/test_batch.py
git commit -m "feat(tagger): add source_weight and frontmatter date to tag JSON output

source_weight encodes stream reliability: ground_truth=2.0,
operations=2.0, policy=1.5, perception=1.0. date is parsed from YAML
frontmatter written by the ingestion pipeline (Phase 2). Both fields
are stored alongside stream/company/source_file in the tag JSON."
```

---

## Self-Review

**Spec coverage:**
- Expanded `ArticleTag` schema (13 new fields) — Task 1 ✓
- Contradiction flag + prompt question — Tasks 1, 2 ✓
- Source weighting (perception=1, ground_truth=2, policy=1.5, operations=2) — Task 3 ✓
- `claim_summary` replaces `summary` — Tasks 1, 2 ✓
- `key_quote` — Task 1 ✓
- `globalization_model` — Task 1 ✓

**No placeholders present.**

**Type consistency:** `Tag.claim_summary` used in Task 1 schema, prompt in Task 2 uses `claim_summary`, batch in Task 3 emits `claim_summary` from `tag.model_dump()` — consistent.
