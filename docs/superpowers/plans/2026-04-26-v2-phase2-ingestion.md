# AgenticAlpha v2 — Phase 2: Ingestion Expansion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `policy` and `operations` as two new ingestion streams alongside the existing `perception` and `ground_truth` streams, and write YAML frontmatter (date, source, source_type, company, region) to every ingested markdown file so the tagger can extract structured metadata.

**Architecture:** `UrlConfig` gains `policy` and `operations` fields (defaulting to `[]`). `UrlEntry` gains optional `source` and `region` fields. The ingestion pipeline prepends a `_build_frontmatter()` helper output to each markdown file. The tagger CLI gains `--policy` and `--operations` arguments.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, existing `requests`/`markdownify` stack.

**Prerequisites:** None — this phase is independent of Phase 1 and can run in parallel.

**Next phase:** Phase 3 (Evidence Engine) depends on Phase 1 tag fields (`date`, `source_weight`) being present in tag JSON. Phase 2 only provides the raw markdown files that Phase 1 reads.

---

## File Map

- Modify: `src/ingestion/config.py` — add `policy`/`operations` to `UrlConfig`; add `source`, `region` to `UrlEntry`
- Modify: `src/ingestion/pipeline.py` — add `_build_frontmatter()`; prepend frontmatter on write
- Modify: `src/tagger/cli.py` — add `--policy` and `--operations` arguments
- Modify: `config/urls.yaml` — add `policy:` and `operations:` sections
- Modify: `tests/ingestion/test_config.py` — new stream + new field tests
- Modify: `tests/ingestion/test_pipeline.py` — frontmatter tests

---

## Task 4: Add policy/operations Streams to UrlConfig

**Files:**
- Modify: `src/ingestion/config.py`
- Modify: `config/urls.yaml`
- Modify: `tests/ingestion/test_config.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/ingestion/test_config.py`:

```python
from src.ingestion.config import load_url_config

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

def test_missing_policy_key_defaults_to_empty(tmp_path):
    cfg = tmp_path / "urls.yaml"
    cfg.write_text("perception: []\nground_truth: []\n")
    config = load_url_config(str(cfg))
    assert config.policy == []
    assert config.operations == []
```

```
pytest tests/ingestion/test_config.py -v
```

Expected: FAIL (`policy`/`operations` attributes absent, `source`/`region` absent).

- [ ] **Step 2: Rewrite `src/ingestion/config.py`**

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
    perception: list[UrlEntry] = []
    ground_truth: list[UrlEntry] = []
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
        data = yaml.safe_load(f) or {}
    return UrlConfig(**data)
```

- [ ] **Step 3: Add `policy:` and `operations:` sections to `config/urls.yaml`**

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
git commit -m "feat(ingestion): add policy/operations streams and source/region fields to UrlEntry

UrlConfig now supports four streams: perception, ground_truth, policy,
operations. UrlEntry gains optional source (e.g. 'Reuters') and region
(e.g. 'US') fields that feed into YAML frontmatter written by the
pipeline. config/urls.yaml seeded with two policy URLs."
```

---

## Task 5: Write YAML Frontmatter to Ingested Markdown

**Files:**
- Modify: `src/ingestion/pipeline.py`
- Modify: `src/tagger/cli.py`
- Modify: `tests/ingestion/test_pipeline.py`

- [ ] **Step 1: Read the current pipeline.py**

```bash
cat src/ingestion/pipeline.py
```

Identify: (a) the function that writes the markdown file to disk (`_ingest_stream()` or similar), (b) where `content` / `markdown_content` is written. Note the exact variable name holding the markdown string.

- [ ] **Step 2: Write failing tests**

Add to `tests/ingestion/test_pipeline.py`:

```python
import yaml
from src.ingestion.pipeline import _build_frontmatter

def test_build_frontmatter_contains_required_fields():
    fm = _build_frontmatter(
        company="CATL",
        source="Reuters",
        source_type="perception",
        region="US",
        date="2026-04-26",
    )
    # Strip the leading/trailing --- markers before parsing
    inner = fm.replace("---\n", "").strip()
    parsed = yaml.safe_load(inner)
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
    assert "source_type: ground_truth" in fm

def test_build_frontmatter_uses_today_when_date_none():
    import datetime
    fm = _build_frontmatter(company="CATL", source=None, source_type="policy", region=None, date=None)
    today = datetime.date.today().isoformat()
    assert today in fm
```

```
pytest tests/ingestion/test_pipeline.py::test_build_frontmatter_contains_required_fields tests/ingestion/test_pipeline.py::test_build_frontmatter_handles_none_source tests/ingestion/test_pipeline.py::test_build_frontmatter_uses_today_when_date_none -v
```

Expected: FAIL (`_build_frontmatter` not defined).

- [ ] **Step 3: Add `_build_frontmatter` to `src/ingestion/pipeline.py`**

Add near the top (after imports, before any existing functions):

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
        "",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Prepend frontmatter when writing markdown**

In `_ingest_stream()` (or wherever the markdown file is written), find the line that writes `content` to disk. Wrap it:

```python
frontmatter = _build_frontmatter(
    company=entry.company,
    source=entry.source,
    source_type=stream_name,   # e.g. "perception"
    region=entry.region,
    date=None,                 # uses today
)
content_to_write = frontmatter + markdown_content
# Replace: path.write_text(markdown_content)
# With:
path.write_text(content_to_write)
```

Where `stream_name` is the string key of the stream being processed (e.g. `"perception"`, `"policy"`).

- [ ] **Step 5: Update `src/tagger/cli.py` to accept `--policy` and `--operations`**

Read the current file:

```bash
cat src/tagger/cli.py
```

Add to the argument parser:

```python
parser.add_argument(
    "--policy", default="data/raw/policy",
    help="Directory containing policy markdown files",
)
parser.add_argument(
    "--operations", default="data/raw/operations",
    help="Directory containing operations markdown files",
)
```

Update `input_dirs` passed to `run_batch()`:

```python
input_dirs = {
    "perception":   [args.perception],
    "ground_truth": [args.ground_truth],
    "policy":       [args.policy],
    "operations":   [args.operations],
}
```

- [ ] **Step 6: Run all ingestion and tagger tests**

```
pytest tests/ingestion/ tests/tagger/ -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/ingestion/pipeline.py src/tagger/cli.py tests/ingestion/test_pipeline.py
git commit -m "feat(ingestion): write YAML frontmatter to ingested markdown; tagger CLI accepts policy/operations

Every ingested markdown file now starts with a YAML block containing
company, source, source_type, region, and date. The tagger batch
parser reads the date field (Phase 1 Task 3). The tagger CLI now
accepts --policy and --operations directory args alongside the
existing --perception and --ground-truth."
```

---

## Self-Review

**Spec coverage:**
- YAML frontmatter (date, source, source_type, company, region) — Task 5 ✓
- `policy` and `operations` streams — Tasks 4, 5 ✓
- `data/raw/policy/` and `data/raw/operations/` folder structure — created implicitly by ingestion ✓

**No placeholders present.**

**Type consistency:** `UrlEntry.source` and `UrlEntry.region` used in config.py are passed directly into `_build_frontmatter(source=..., region=...)` — consistent. `stream_name` string passed to `_build_frontmatter(source_type=...)` matches the `source_type` key read by the tagger's `parse_frontmatter_date()` (Phase 1 Task 3).
