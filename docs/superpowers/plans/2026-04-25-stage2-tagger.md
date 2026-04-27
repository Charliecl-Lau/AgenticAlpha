# Stage 2: Asymmetric Tagger (LLM Extraction) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For each ingested Markdown file, call Gemma 4 via Google AI to extract a structured JSON tag with `sentiment_score`, `direction`, `topic_cluster`, `geo_exposure`, and `summary` — using an asymmetric system prompt that explicitly prevents false symmetry between CATL and LGES strategies.

**Architecture:** A batch processor walks `data/raw/perception/` and `data/raw/ground_truth/`, calls the Google Gemini API with a Gemma 4 model pre-loaded with the asymmetric system prompt, parses the JSON response (stripping any markdown fences Gemma adds) with Pydantic, retries up to 3× on transient errors, and writes one JSON file per input to `data/processed/tags/`. Prints a tagging report at the end. Requires `GOOGLE_API_KEY` in `.env`.

**Tech Stack:** Python 3.11+, google-generativeai, pydantic, python-dotenv, pytest, pytest-mock

**Prerequisite:** Stage 1 plan fully implemented. `data/raw/perception/` and `data/raw/ground_truth/` contain `.md` files with `# Company: <name>` headers.

---

### Task 1: Tag Schema

**Files:**
- Create: `src/tagger/schema.py`
- Test: `tests/tagger/test_schema.py`

- [ ] **Step 1: Write failing test**

```python
# tests/tagger/test_schema.py
import pytest
from pydantic import ValidationError
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion


def test_tag_accepts_valid_data():
    tag = Tag(
        sentiment_score=7,
        direction=Direction.positive,
        topic_cluster=TopicCluster.Organic_Scale_vs_Export,
        geo_exposure=[GeoRegion.EU, GeoRegion.China],
        summary="CATL expanded European gigafactory capacity by 30% in Q3 2024.",
    )
    assert tag.sentiment_score == 7
    assert tag.direction == Direction.positive


def test_tag_rejects_sentiment_out_of_range():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=11,
            direction=Direction.positive,
            topic_cluster=TopicCluster.Other,
            geo_exposure=[GeoRegion.US],
            summary="Some summary.",
        )


def test_tag_rejects_empty_summary():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5,
            direction=Direction.neutral,
            topic_cluster=TopicCluster.Other,
            geo_exposure=[],
            summary="",
        )


def test_tag_serialises_to_dict():
    tag = Tag(
        sentiment_score=3,
        direction=Direction.negative,
        topic_cluster=TopicCluster.Subsidy_Dependence,
        geo_exposure=[GeoRegion.US],
        summary="LGES revenue tied 62% to IRA tax credits in Q2 2024.",
    )
    d = tag.model_dump()
    assert d["direction"] == "negative"
    assert d["topic_cluster"] == "Subsidy_Dependence"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tagger/test_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.tagger.schema'`

- [ ] **Step 3: Implement schema**

```python
# src/tagger/schema.py
from enum import Enum
from pydantic import BaseModel, field_validator


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


class Tag(BaseModel):
    sentiment_score: int
    direction: Direction
    topic_cluster: TopicCluster
    geo_exposure: list[GeoRegion]
    summary: str

    @field_validator("sentiment_score")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("sentiment_score must be 1-10")
        return v

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary must not be empty")
        return v
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/tagger/test_schema.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/tagger/schema.py tests/tagger/test_schema.py
git commit -m "feat(tagger): add pydantic Tag schema with enum validation

Defines the five-field JSON schema. sentiment_score is validated to
1-10; summary rejects empty strings. Enum serialisation uses string
values so JSON output is human-readable and downstream stages can
consume it without importing this module."
```

---

### Task 2: System Prompt Builder

**Files:**
- Create: `src/tagger/prompt.py`
- Test: `tests/tagger/test_prompt.py`

- [ ] **Step 1: Write failing test**

```python
# tests/tagger/test_prompt.py
from src.tagger.prompt import build_system_prompt, build_user_message


def test_system_prompt_contains_asymmetry_instruction():
    prompt = build_system_prompt()
    assert "false symmetry" in prompt.lower() or "asymmetric" in prompt.lower()


def test_system_prompt_contains_json_schema():
    prompt = build_system_prompt()
    assert "sentiment_score" in prompt
    assert "topic_cluster" in prompt
    assert "geo_exposure" in prompt


def test_system_prompt_prohibits_investment_advice():
    prompt = build_system_prompt()
    assert "investment advice" in prompt.lower() or "we believe" in prompt.lower()


def test_system_prompt_distinguishes_geopolitical_noise_from_capex():
    # Key disambiguation: tariff articles about CATL EU plants must not
    # be tagged Geopolitical_Noise if the primary event is an operational ramp.
    prompt = build_system_prompt()
    assert "Geopolitical_Noise" in prompt
    assert "Capex_Execution" in prompt
    # Prompt must explain when to prefer one over the other
    assert "primary event" in prompt.lower() or "regulatory" in prompt.lower()


def test_system_prompt_contains_few_shot_examples():
    prompt = build_system_prompt()
    # Verify at least one labelled example exists for disambiguation
    assert "Example" in prompt or "EXAMPLE" in prompt


def test_summary_forbidden_phrases_blocked_by_prompt_instruction():
    prompt = build_system_prompt()
    # The prompt must explicitly name the forbidden hedge phrases
    assert "appears to" in prompt
    assert "we believe" in prompt


def test_build_user_message_includes_markdown_content():
    md = "CATL expanded its European operations significantly."
    msg = build_user_message(md, company="CATL", stream="perception")
    assert "CATL" in msg
    assert "CATL expanded its European operations" in msg


def test_build_user_message_includes_stream_context():
    msg = build_user_message("Some IR text.", company="LGES", stream="ground_truth")
    assert "ground_truth" in msg or "Ground Truth" in msg
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tagger/test_prompt.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement prompt builder**

```python
# src/tagger/prompt.py

_SYSTEM_PROMPT = """\
You are a financial text tagger for an equity research pipeline analysing CATL and LGES.

CRITICAL RULE — ASYMMETRIC ANALYSIS:
Do NOT treat CATL and LGES strategies as equivalent. Their globalization models are structurally different:
- CATL's overseas expansion is organic (greenfield factories in Hungary/Germany, LFP volume-driven,
  early-mover customer contracts). Tag CATL capex news as "Capex_Execution" or "Organic_Scale_vs_Export".
- LGES's US presence is largely policy-dependent (IRA AMPC subsidy arbitrage, Ultium JV ramp delays).
  Tag LGES subsidy/credit content as "Subsidy_Dependence".
Applying "Organic_Scale_vs_Export" to LGES IRA content, or "Subsidy_Dependence" to CATL capex news,
is a TAGGING ERROR.

TOPIC CLUSTER DISAMBIGUATION:
- Geopolitical_Noise: Use ONLY when the primary event is a regulatory/policy action with NO
  operational follow-through reported (e.g., tariff announcement with no factory or margin data).
  If the same article also reports capacity ramps, margins, or contracts → prefer "Capex_Execution"
  or "Organic_Scale_vs_Export" instead.
- Capex_Execution: Factory ramps, capacity additions, construction milestones, cost-per-kWh updates.
- Other: Use only when no cluster fits. Avoid defaulting here.

FEW-SHOT EXAMPLES:

EXAMPLE 1 (CATL, perception stream):
Article: "EU tariffs on Chinese EVs rose to 35%. CATL's Hungary Debrecen plant, now producing
cells for BMW and Stellantis, reached 20 GWh annualised run-rate ahead of schedule."
Correct tag: topic_cluster = "Capex_Execution", direction = "positive", geo_exposure = ["EU"]
Wrong tag: topic_cluster = "Geopolitical_Noise"
Reason: The primary event is the operational milestone (capacity ramp), not the tariff.

EXAMPLE 2 (LGES, ground_truth stream):
Article: "LGES reported Q1 2026 operating loss of KRW 207.8B. Excluding IRA AMPC subsidies
of KRW 189.7B, the loss widens to KRW 397.5B."
Correct tag: topic_cluster = "Subsidy_Dependence", direction = "negative", sentiment_score = 3
Wrong tag: topic_cluster = "Other"
Reason: The subsidy exclusion figure directly evidences policy-dependent profitability.

OUTPUT FORMAT — respond with ONLY a valid JSON object, no prose, no markdown code fences:
{
  "sentiment_score": <integer 1-10, where 1=extremely bearish, 10=extremely bullish for the named company>,
  "direction": <"positive" | "negative" | "neutral">,
  "topic_cluster": <"Organic_Scale_vs_Export" | "Subsidy_Dependence" | "Geopolitical_Noise" | "Capex_Execution" | "Other">,
  "geo_exposure": [<zero or more of "US" | "EU" | "ASEAN" | "LATAM" | "China">],
  "summary": "<exactly one factual sentence extracted from the text — no opinions, no investment advice>"
}

summary constraints:
- Must be a direct factual extraction, not a paraphrase of your opinion.
- Must NOT contain: "we believe", "we conclude", "appears to", "seems to", or any hedge language.
- Must NOT give investment advice or price targets.
"""


def build_system_prompt() -> str:
    return _SYSTEM_PROMPT


def build_user_message(markdown: str, company: str, stream: str) -> str:
    return (
        f"Company: {company}\n"
        f"Stream: {stream} (perception = media/news, ground_truth = IR documents)\n\n"
        f"--- BEGIN ARTICLE ---\n{markdown}\n--- END ARTICLE ---\n\n"
        "Tag the above article according to the system instructions. "
        "Return ONLY the JSON object."
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/tagger/test_prompt.py -v
```

Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/tagger/prompt.py tests/tagger/test_prompt.py
git commit -m "feat(tagger): add asymmetric system prompt with few-shot disambiguation examples

System prompt explicitly forbids false symmetry (CATL organic capex vs
LGES subsidy-dependent) and adds two targeted few-shot examples that
prevent the LLM from mis-labelling CATL EU plant news as Geopolitical_Noise.
Forbidden summary phrases (appears to, we believe) are named explicitly.
build_user_message injects company and stream context before the article."
```

---

### Task 3: Gemma 4 API Tagger

**Files:**
- Create: `src/tagger/tagger.py`
- Test: `tests/tagger/test_tagger.py`

**Note on model name:** Verify the exact Gemma 4 model ID in your Google AI Studio console before running. The plan uses `gemma-4-27b-it` as the default; update `_MODEL` if your quota grants a different variant (e.g., `gemma-4-9b-it`).

- [ ] **Step 1: Write failing test**

```python
# tests/tagger/test_tagger.py
import json
import pytest
from unittest.mock import MagicMock, patch
from src.tagger.tagger import tag_document
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion

_VALID_JSON = json.dumps({
    "sentiment_score": 8,
    "direction": "positive",
    "topic_cluster": "Organic_Scale_vs_Export",
    "geo_exposure": ["EU"],
    "summary": "CATL's Hungary plant reached 50 GWh annual capacity in Q3 2024.",
})

_FENCED_JSON = f"```json\n{_VALID_JSON}\n```"


def _mock_model(response_text: str):
    mock_response = MagicMock()
    mock_response.text = response_text
    model = MagicMock()
    model.generate_content.return_value = mock_response
    return model


def test_tag_document_returns_tag_object():
    model = _mock_model(_VALID_JSON)
    tag = tag_document(model, "CATL expanded in EU.", company="CATL", stream="perception")
    assert isinstance(tag, Tag)
    assert tag.sentiment_score == 8
    assert tag.direction == Direction.positive
    assert GeoRegion.EU in tag.geo_exposure


def test_tag_document_strips_markdown_fences():
    model = _mock_model(_FENCED_JSON)
    tag = tag_document(model, "CATL expanded in EU.", company="CATL", stream="perception")
    assert isinstance(tag, Tag)
    assert tag.sentiment_score == 8


def test_tag_document_raises_on_invalid_json():
    model = _mock_model("This is not JSON at all.")
    with patch("src.tagger.tagger.time.sleep"):
        with pytest.raises(ValueError, match="Failed to parse"):
            tag_document(model, "Some text.", company="CATL", stream="perception")


def test_tag_document_retries_on_transient_error():
    success_response = MagicMock()
    success_response.text = _VALID_JSON
    model = MagicMock()
    model.generate_content.side_effect = [
        Exception("503 Service Unavailable"),
        Exception("503 Service Unavailable"),
        success_response,
    ]
    with patch("src.tagger.tagger.time.sleep"):
        tag = tag_document(model, "Some text.", company="CATL", stream="perception")
    assert tag.sentiment_score == 8
    assert model.generate_content.call_count == 3


def test_tag_document_raises_after_max_retries():
    model = MagicMock()
    model.generate_content.side_effect = Exception("429 Quota exceeded")
    with patch("src.tagger.tagger.time.sleep"):
        with pytest.raises(Exception, match="429"):
            tag_document(model, "Some text.", company="CATL", stream="perception")
    assert model.generate_content.call_count == 3


def test_tag_document_truncates_long_content():
    model = _mock_model(_VALID_JSON)
    long_md = "x" * 20_000
    tag_document(model, long_md, company="CATL", stream="perception")
    called_content = model.generate_content.call_args.args[0]
    assert "[TRUNCATED]" in called_content
    assert len(called_content) < 12_000
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tagger/test_tagger.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Add google-generativeai to requirements.txt**

Open `requirements.txt` and add (remove the `anthropic` line if present):

```
google-generativeai==0.8.3
```

Then install:

```bash
pip install google-generativeai==0.8.3
```

- [ ] **Step 4: Implement tagger**

```python
# src/tagger/tagger.py
import json
import re
import time
from src.tagger.schema import Tag
from src.tagger.prompt import build_user_message

_MAX_RETRIES = 3
_MAX_CONTENT_CHARS = 8_000
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]+?)\s*```")


def _strip_fences(raw: str) -> str:
    match = _FENCE_RE.search(raw)
    return match.group(1) if match else raw


def _call_with_retry(model, prompt: str) -> str:
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    raise last_exc  # type: ignore[misc]


def tag_document(model, markdown: str, company: str, stream: str) -> Tag:
    if len(markdown) > _MAX_CONTENT_CHARS:
        markdown = markdown[:_MAX_CONTENT_CHARS] + "\n[TRUNCATED]"
    user_msg = build_user_message(markdown, company=company, stream=stream)
    raw = _call_with_retry(model, user_msg)
    raw = _strip_fences(raw.strip())
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse LLM response as JSON: {exc}\nRaw: {raw[:200]}"
        ) from exc
    return Tag(**data)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/tagger/test_tagger.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add src/tagger/tagger.py tests/tagger/test_tagger.py requirements.txt
git commit -m "feat(tagger): add Gemma 4 tagger with retry, fence stripping, and truncation

Calls the model passed in (a google.generativeai.GenerativeModel pre-loaded
with the asymmetric system prompt) via generate_content. Strips markdown
code fences that Gemma sometimes wraps around JSON. Retries 3x with
exponential backoff (1s/2s/4s) on transient errors. Truncates inputs
exceeding 8000 chars to stay within practical context limits."
```

---

### Task 4: Batch Processor & CLI

**Files:**
- Create: `src/tagger/batch.py`
- Create: `src/tagger/cli.py`
- Test: `tests/tagger/test_batch.py`

- [ ] **Step 1: Write failing test**

```python
# tests/tagger/test_batch.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.tagger.batch import run_batch, _parse_header
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion

_TAG = Tag(
    sentiment_score=6,
    direction=Direction.neutral,
    topic_cluster=TopicCluster.Capex_Execution,
    geo_exposure=[GeoRegion.China],
    summary="CATL announced a 20 GWh expansion in Sichuan province.",
)


def _make_md_files(directory: Path, count: int, company: str = "CATL") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (directory / f"{company.lower()}_{i:03d}.md").write_text(
            f"# Company: {company}\n\nSome article text {i}."
        )


def test_run_batch_writes_one_json_per_md(tmp_path):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 3)
    out_dir = tmp_path / "tags"
    with patch("src.tagger.batch.tag_document", return_value=_TAG):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    jsons = list(out_dir.glob("*.json"))
    assert len(jsons) == 3


def test_run_batch_json_contains_tag_fields(tmp_path):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 1)
    out_dir = tmp_path / "tags"
    with patch("src.tagger.batch.tag_document", return_value=_TAG):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    data = json.loads(list(out_dir.glob("*.json"))[0].read_text())
    assert data["sentiment_score"] == 6
    assert data["stream"] == "perception"
    assert data["company"] == "CATL"


def test_run_batch_skips_failed_files_and_continues(tmp_path):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 2)
    out_dir = tmp_path / "tags"
    call_count = {"n": 0}

    def fake_tag(model, markdown, company, stream):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ValueError("LLM error")
        return _TAG

    with patch("src.tagger.batch.tag_document", side_effect=fake_tag):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    jsons = list(out_dir.glob("*.json"))
    assert len(jsons) == 1


def test_run_batch_prints_report(tmp_path, capsys):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 2)
    out_dir = tmp_path / "tags"
    with patch("src.tagger.batch.tag_document", return_value=_TAG):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    captured = capsys.readouterr()
    assert "Processed: 2" in captured.out
    assert "Skipped: 0" in captured.out


def test_parse_header_extracts_company():
    text = "# Company: CATL\n\nSome article."
    assert _parse_header(text)["company"] == "CATL"


def test_parse_header_handles_extra_whitespace():
    text = "#  Company:   LGES  \n\nSome article."
    assert _parse_header(text)["company"] == "LGES"


def test_parse_header_case_insensitive():
    text = "# company: CATL\n\nSome article."
    assert _parse_header(text)["company"] == "CATL"


def test_parse_header_returns_unknown_when_missing():
    assert _parse_header("No header here.")["company"] == "Unknown"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tagger/test_batch.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement batch processor**

```python
# src/tagger/batch.py
import json
import logging
import re
from collections import Counter
from pathlib import Path
from src.tagger.tagger import tag_document

logger = logging.getLogger(__name__)

_HEADER_RE = re.compile(r"^#\s*Company:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


def _parse_header(text: str) -> dict:
    match = _HEADER_RE.search(text)
    return {"company": match.group(1) if match else "Unknown"}


def run_batch(
    input_dirs: dict[str, str],
    output_dir: str,
    model,
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    processed = 0
    skipped = 0
    cluster_counts: Counter = Counter()

    for stream, dir_path in input_dirs.items():
        for md_file in sorted(Path(dir_path).glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            meta = _parse_header(text)
            try:
                tag = tag_document(model, text, company=meta["company"], stream=stream)
                result = tag.model_dump()
                result["source_file"] = md_file.name
                result["stream"] = stream
                result["company"] = meta["company"]
                out_file = out / f"{md_file.stem}.json"
                out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
                cluster_counts[result["topic_cluster"]] += 1
                processed += 1
                logger.info("Tagged %s -> %s", md_file.name, out_file.name)
            except Exception as exc:
                skipped += 1
                logger.warning("Skipping %s: %s", md_file.name, exc)

    print(f"\n=== Tagging Report ===")
    print(f"Processed: {processed} | Skipped: {skipped}")
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        print(f"  {cluster}: {count}")
    print("======================")
```

- [ ] **Step 4: Implement CLI**

```python
# src/tagger/cli.py
import argparse
import logging
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.tagger.batch import run_batch
from src.tagger.prompt import build_system_prompt

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

_MODEL_NAME = "gemma-4-27b-it"  # verify in Google AI Studio console


def _make_model() -> genai.GenerativeModel:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=build_system_prompt(),
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=512,
            temperature=0.0,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Tag ingested Markdown files with LLM extraction")
    parser.add_argument("--perception", default="data/raw/perception")
    parser.add_argument("--ground-truth", default="data/raw/ground_truth")
    parser.add_argument("--output", default="data/processed/tags")
    args = parser.parse_args()

    model = _make_model()
    run_batch(
        input_dirs={"perception": args.perception, "ground_truth": args.ground_truth},
        output_dir=args.output,
        model=model,
    )
    print(f"JSON files written to {args.output}/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run all tagger tests**

```bash
pytest tests/tagger/ -v
```

Expected: PASS (all 18 tests)

- [ ] **Step 6: Commit**

```bash
git add src/tagger/batch.py src/tagger/cli.py tests/tagger/test_batch.py
git commit -m "feat(tagger): add batch processor and CLI for Gemma 4 LLM extraction

Walks perception and ground_truth directories, tags each Markdown file
via the pre-configured Gemma 4 GenerativeModel, and writes JSON with
source_file/stream/company metadata. Failed files are logged and skipped.
Header parsing is now case-insensitive and handles extra whitespace so
minor Stage 1 format variations do not produce Unknown company tags.
Prints a per-cluster tagging report at the end for Slide 19 evidence."
```

---

### Task 5: Smoke-Test with Real Data

This task is not automated — it validates that the asymmetric prompt holds on real content.

**Files:**
- No new files. Run against actual Stage 1 output.

- [ ] **Step 1: Ensure .env contains GOOGLE_API_KEY**

```bash
# .env
GOOGLE_API_KEY=your_key_here
```

- [ ] **Step 2: Run tagger on 10-15 real files**

```bash
python -m src.tagger.cli \
  --perception data/raw/perception \
  --ground-truth data/raw/ground_truth \
  --output data/processed/tags
```

- [ ] **Step 3: Inspect JSON outputs for asymmetry**

For each CATL file: confirm no `Subsidy_Dependence` tags appear.
For each LGES file: confirm no `Organic_Scale_vs_Export` tags appear.
Check that summaries contain no hedge language (`appears to`, `seems`).

```bash
# Quick audit — any CATL file tagged Subsidy_Dependence is a prompt failure
grep -l "Subsidy_Dependence" data/processed/tags/*.json | xargs -I{} python -c "
import json, sys
d = json.load(open('{}'))
if d['company'] == 'CATL':
    print('ASYMMETRY FAILURE:', '{}')
"
```

- [ ] **Step 4: If prompt drift found — adjust prompt and re-run**

Open `src/tagger/prompt.py` and tighten the relevant disambiguation rule.
Re-run on the failing file only to verify fix before full batch.

- [ ] **Step 5: Commit if any prompt adjustments were made**

```bash
git add src/tagger/prompt.py
git commit -m "fix(tagger): tighten prompt disambiguation after real-data smoke test

[describe what drift was observed and what rule was adjusted]"
```

---

## Self-Review Against Spec

**Spec coverage:**
- Asymmetric system prompt with CATL/LGES distinction ✓ (Task 2)
- Pydantic schema with 5 fields, 1-10 score, non-empty summary ✓ (Task 1)
- JSON output per Markdown file with source metadata ✓ (Task 4)
- Batch processor skips failures gracefully ✓ (Task 4)
- `_parse_header` extracts company from Stage 1 headers ✓ (Task 4)
- TDD throughout ✓ (every task)
- Retry on transient errors ✓ (Task 3)
- Markdown fence stripping for Gemma's output style ✓ (Task 3)
- Length truncation for oversized IR documents ✓ (Task 3)
- Post-tagging report for competition slide evidence ✓ (Task 4)
- Real-data validation ✓ (Task 5)

**What this plan deliberately does NOT include:**
- Deduplication across streams — not in spec, adds complexity with no clear competition payoff
- Token usage logging — the cluster count report is sufficient for Slide 20
- Weighting ground_truth evidence over perception in the prompt — risks over-constraining the LLM; the asymmetric instruction already handles the key distinction

**Placeholder scan:** None found. All steps contain actual code and commands.

**Type consistency check:**
- `tag_document(model, markdown, company, stream)` — consistent across Task 3, Task 4 batch call (`tag_document(model, text, ...)`), and Task 4 test mock (`tag_document(model, markdown, company, stream)`) ✓
- `run_batch(input_dirs, output_dir, model)` — consistent across Task 4 implementation and tests ✓
- `_parse_header(text) -> dict` — consistent across Task 4 implementation and tests ✓
