from pydantic import BaseModel, field_validator


class DiffMatrixRow(BaseModel):
    factor: str
    catl_evidence: str
    lges_evidence: str
    implication: str
    supporting_tags: str


class SynthesisOutput(BaseModel):
    research_question: str
    executive_summary: str
    differentiation_matrix: list[DiffMatrixRow]
    why_now: str
    differentiation_takeaway: str
    contradiction_summary: str
    risk_summary: str
    strongest_supporting_evidence: list[str]
    contrary_risk_evidence: list[str]
    analyst_questions: list[str]
    overall_confidence: str
    limitations: list[str]

    @field_validator(
        "research_question", "executive_summary", "why_now", "differentiation_takeaway",
        "contradiction_summary", "risk_summary", "overall_confidence",
    )
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field must not be empty or whitespace")
        return v

    @field_validator(
        "analyst_questions", "limitations",
        "strongest_supporting_evidence", "contrary_risk_evidence",
    )
    @classmethod
    def must_have_at_least_one(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("list must contain at least one item")
        return v

    @field_validator("differentiation_matrix")
    @classmethod
    def must_have_matrix_rows(cls, v: list[DiffMatrixRow]) -> list[DiffMatrixRow]:
        if not v:
            raise ValueError("differentiation_matrix must contain at least one row")
        return v
