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
