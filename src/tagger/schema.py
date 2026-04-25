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
