import json
import pytest
from unittest.mock import MagicMock, patch
from src.tagger.tagger import tag_document
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion

_VALID_JSON = json.dumps({
    "sentiment_score": 8,
    "direction": "positive",
    "confidence": 0.9,
    "topic_cluster": "Organic_Scale_vs_Export",
    "geo_exposure": ["EU"],
    "globalization_model": "export-led",
    "localization_score": 8,
    "subsidy_dependency": 2,
    "execution_quality": 9,
    "margin_signal": 7,
    "capex_signal": 9,
    "ROIC_signal": 8,
    "contradiction_flag": False,
    "contradiction_reason": None,
    "claim_summary": "CATL's Hungary plant reached 50 GWh annual capacity in Q3 2024.",
    "key_quote": None,
})

_FENCED_JSON = f"```json\n{_VALID_JSON}\n```"


def _mock_model(response_text: str):
    mock_response = MagicMock()
    mock_response.text = response_text
    model = MagicMock()
    model.generate_content.return_value = mock_response
    return model


def test_tag_document_returns_tag_object():
    model = _mock_model(_VALID_JSON)
    tag = tag_document(model, "CATL expanded in EU.", company="CATL", stream="perception")
    assert isinstance(tag, Tag)
    assert tag.sentiment_score == 8
    assert tag.direction == Direction.positive
    assert GeoRegion.EU in tag.geo_exposure


def test_tag_document_strips_markdown_fences():
    model = _mock_model(_FENCED_JSON)
    tag = tag_document(model, "CATL expanded in EU.", company="CATL", stream="perception")
    assert isinstance(tag, Tag)
    assert tag.sentiment_score == 8


def test_tag_document_raises_on_invalid_json():
    model = _mock_model("This is not JSON at all.")
    with patch("src.tagger.tagger.time.sleep"):
        with pytest.raises(ValueError, match="Failed to parse"):
            tag_document(model, "Some text.", company="CATL", stream="perception")


def test_tag_document_retries_on_transient_error():
    success_response = MagicMock()
    success_response.text = _VALID_JSON
    model = MagicMock()
    model.generate_content.side_effect = [
        Exception("503 Service Unavailable"),
        Exception("503 Service Unavailable"),
        success_response,
    ]
    with patch("src.tagger.tagger.time.sleep"):
        tag = tag_document(model, "Some text.", company="CATL", stream="perception")
    assert tag.sentiment_score == 8
    assert model.generate_content.call_count == 3


def test_tag_document_raises_after_max_retries():
    model = MagicMock()
    model.generate_content.side_effect = Exception("429 Quota exceeded")
    with patch("src.tagger.tagger.time.sleep"):
        with pytest.raises(Exception, match="429"):
            tag_document(model, "Some text.", company="CATL", stream="perception")
    assert model.generate_content.call_count == 3


def test_tag_document_truncates_long_content():
    model = _mock_model(_VALID_JSON)
    long_md = "x" * 20_000
    tag_document(model, long_md, company="CATL", stream="perception")
    called_content = model.generate_content.call_args.args[0]
    assert "[TRUNCATED]" in called_content
    assert len(called_content) < 12_000
