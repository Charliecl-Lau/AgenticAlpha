import pytest
from unittest.mock import patch, MagicMock
from src.synthesis.synthesiser import synthesise
from src.synthesis.schema import SynthesisOutput

_FAKE_JSON = """{
  "executive_summary": "CATL leads on globalization; LGES faces subsidy cliff.",
  "why_now": "IRA policy uncertainty accelerated in 2025Q4.",
  "differentiation_takeaway": "CATL scores 3pt higher on execution.",
  "contradiction_summary": "Two documents challenge IRA dependency assumptions.",
  "risk_summary": "Policy reversal and capex overrun are primary bear cases.",
  "analyst_questions": ["What is LGES Hungary utilization at IRA cap?"],
  "limitations": ["Evidence limited to public disclosures."]
}"""

def test_synthesise_returns_synthesis_output():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_FAKE_JSON)]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        result = synthesise("test prompt")

    assert isinstance(result, SynthesisOutput)
    assert "CATL" in result.executive_summary

def test_synthesise_passes_correct_model():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_FAKE_JSON)]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        mock_create = MockClient.return_value.messages.create
        mock_create.return_value = mock_message
        synthesise("test prompt", model="claude-haiku-4-5-20251001")
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"

def test_synthesise_raises_on_invalid_json():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not valid json at all")]

    with patch("src.synthesis.synthesiser.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        with pytest.raises(ValueError, match="Failed to parse synthesis output"):
            synthesise("test prompt")
