from pydantic import BaseModel, field_validator


class SynthesisOutput(BaseModel):
    executive_summary: str
    why_now: str
    differentiation_takeaway: str
    contradiction_summary: str
    risk_summary: str
    analyst_questions: list[str]
    limitations: list[str]

    @field_validator(
        "executive_summary", "why_now", "differentiation_takeaway",
        "contradiction_summary", "risk_summary",
    )
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty or whitespace")
        return v

    @field_validator("analyst_questions", "limitations")
    @classmethod
    def must_have_at_least_one(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("list must contain at least one item")
        return v
