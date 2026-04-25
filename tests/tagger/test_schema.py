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
