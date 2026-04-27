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
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return UrlConfig(**data)
