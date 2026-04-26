import pytest
from pydantic import ValidationError
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion


def test_full_tag_with_all_new_fields():
    tag = Tag(
        sentiment_score=7.5,
        direction="positive",
        confidence=0.85,
        topic_cluster="Organic_Scale_vs_Export",
        geo_exposure=["US"],
        globalization_model="export-led",
        localization_score=8,
        subsidy_dependency=3,
        execution_quality=9,
        margin_signal=7,
        capex_signal=8,
        ROIC_signal=7,
        contradiction_flag=False,
        contradiction_reason=None,
        claim_summary="CATL shows strong execution in overseas markets.",
        key_quote="Revenue per MWh up 12% QoQ.",
    )
    assert tag.confidence == 0.85
    assert tag.localization_score == 8
    assert tag.contradiction_flag is False
    assert tag.key_quote == "Revenue per MWh up 12% QoQ."


def test_sentiment_score_is_float():
    tag = Tag(
        sentiment_score=7.5,
        direction="positive",
        confidence=0.85,
        topic_cluster="Capex_Execution",
        geo_exposure=["EU"],
        globalization_model="hybrid",
        localization_score=5,
        subsidy_dependency=5,
        execution_quality=5,
        margin_signal=5,
        capex_signal=5,
        ROIC_signal=5,
        contradiction_flag=False,
        contradiction_reason=None,
        claim_summary="Mixed signals on capex.",
        key_quote=None,
    )
    assert isinstance(tag.sentiment_score, float)


def test_confidence_must_be_0_to_1():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=1.5,
            topic_cluster="Other", geo_exposure=["China"],
            globalization_model="unclear", localization_score=5,
            subsidy_dependency=5, execution_quality=5, margin_signal=5,
            capex_signal=5, ROIC_signal=5, contradiction_flag=False,
            contradiction_reason=None, claim_summary="Some claim.", key_quote=None,
        )


def test_contradiction_reason_required_when_flagged():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=3.0, direction="negative", confidence=0.7,
            topic_cluster="Subsidy_Dependence", geo_exposure=["US"],
            globalization_model="localization-driven", localization_score=3,
            subsidy_dependency=9, execution_quality=4, margin_signal=3,
            capex_signal=4, ROIC_signal=3, contradiction_flag=True,
            contradiction_reason=None,  # must not be None when flag is True
            claim_summary="LGES depends heavily on IRA credits.", key_quote=None,
        )


def test_numeric_scores_must_be_1_to_10():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=0.5,
            topic_cluster="Other", geo_exposure=["EU"],
            globalization_model="hybrid", localization_score=11,  # out of range
            subsidy_dependency=5, execution_quality=5, margin_signal=5,
            capex_signal=5, ROIC_signal=5, contradiction_flag=False,
            contradiction_reason=None, claim_summary="Test.", key_quote=None,
        )


def test_claim_summary_must_not_be_empty():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=0.5,
            topic_cluster="Other", geo_exposure=["EU"],
            globalization_model="hybrid", localization_score=5,
            subsidy_dependency=5, execution_quality=5, margin_signal=5,
            capex_signal=5, ROIC_signal=5, contradiction_flag=False,
            contradiction_reason=None, claim_summary="   ", key_quote=None,
        )


def test_globalization_model_enum_rejects_invalid():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5.0, direction="neutral", confidence=0.5,
            topic_cluster="Other", geo_exposure=["EU"],
            globalization_model="unknown-model",  # invalid
            localization_score=5, subsidy_dependency=5, execution_quality=5,
            margin_signal=5, capex_signal=5, ROIC_signal=5,
            contradiction_flag=False, contradiction_reason=None,
            claim_summary="Test.", key_quote=None,
        )


def test_tag_accepts_valid_data():
    tag = Tag(
        sentiment_score=7,
        direction=Direction.positive,
        confidence=0.8,
        topic_cluster=TopicCluster.Organic_Scale_vs_Export,
        geo_exposure=[GeoRegion.EU, GeoRegion.China],
        globalization_model="export-led",
        localization_score=8,
        subsidy_dependency=2,
        execution_quality=8,
        margin_signal=7,
        capex_signal=8,
        ROIC_signal=7,
        contradiction_flag=False,
        contradiction_reason=None,
        claim_summary="CATL expanded European gigafactory capacity by 30% in Q3 2024.",
        key_quote=None,
    )
    assert tag.sentiment_score == 7
    assert tag.direction == Direction.positive


def test_tag_rejects_sentiment_out_of_range():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=11,
            direction=Direction.positive,
            confidence=0.5,
            topic_cluster=TopicCluster.Other,
            geo_exposure=[GeoRegion.US],
            globalization_model="unclear",
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="Some claim.",
            key_quote=None,
        )


def test_tag_rejects_empty_summary():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5,
            direction=Direction.neutral,
            confidence=0.5,
            topic_cluster=TopicCluster.Other,
            geo_exposure=[],
            globalization_model="unclear",
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="",
            key_quote=None,
        )


def test_tag_serialises_to_dict():
    tag = Tag(
        sentiment_score=3,
        direction=Direction.negative,
        confidence=0.6,
        topic_cluster=TopicCluster.Subsidy_Dependence,
        geo_exposure=[GeoRegion.US],
        globalization_model="localization-driven",
        localization_score=3,
        subsidy_dependency=9,
        execution_quality=4,
        margin_signal=3,
        capex_signal=4,
        ROIC_signal=3,
        contradiction_flag=False,
        contradiction_reason=None,
        claim_summary="LGES revenue tied 62% to IRA tax credits in Q2 2024.",
        key_quote=None,
    )
    d = tag.model_dump()
    assert d["direction"] == "negative"
    assert d["topic_cluster"] == "Subsidy_Dependence"


def test_tag_rejects_sentiment_score_zero():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=0,
            direction=Direction.neutral,
            confidence=0.5,
            topic_cluster=TopicCluster.Other,
            geo_exposure=[],
            globalization_model="unclear",
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="Some summary.",
            key_quote=None,
        )


def test_tag_rejects_whitespace_only_summary():
    with pytest.raises(ValidationError):
        Tag(
            sentiment_score=5,
            direction=Direction.neutral,
            confidence=0.5,
            topic_cluster=TopicCluster.Other,
            geo_exposure=[],
            globalization_model="unclear",
            localization_score=5,
            subsidy_dependency=5,
            execution_quality=5,
            margin_signal=5,
            capex_signal=5,
            ROIC_signal=5,
            contradiction_flag=False,
            contradiction_reason=None,
            claim_summary="   ",
            key_quote=None,
        )
