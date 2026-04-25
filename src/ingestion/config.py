# src/ingestion/config.py
from pathlib import Path
from pydantic import BaseModel, field_validator
import yaml


class UrlEntry(BaseModel):
    url: str
    company: str

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"url must start with http:// or https://, got: {v!r}")
        return v


class UrlConfig(BaseModel):
    perception: list[UrlEntry]
    ground_truth: list[UrlEntry]

    @field_validator("perception", "ground_truth", mode="before")
    @classmethod
    def deduplicate_urls(cls, entries: list) -> list:
        seen: set[str] = set()
        deduped = []
        for e in entries:
            url = e["url"] if isinstance(e, dict) else e.url
            if url not in seen:
                seen.add(url)
                deduped.append(e)
        return deduped


def load_url_config(path: str) -> UrlConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(p) as f:
        data = yaml.safe_load(f)
    return UrlConfig(**data)
