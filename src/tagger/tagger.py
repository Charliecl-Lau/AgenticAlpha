import json
import re
import time
from typing import Optional
from src.tagger.schema import Tag
from src.tagger.prompt import build_user_message

_MAX_RETRIES = 3
_MAX_CONTENT_CHARS = 8_000
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]+?)\s*```")


def _strip_fences(raw: str) -> str:
    match = _FENCE_RE.search(raw)
    return match.group(1) if match else raw


def _call_with_retry(model, prompt: str) -> str:
    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    raise last_exc


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
