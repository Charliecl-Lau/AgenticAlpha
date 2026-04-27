import pytest
from unittest.mock import patch, MagicMock
from src.synthesis.synthesiser import synthesise
from src.synthesis.schema import SynthesisOutput

_FAKE_JSON = """{
  "research_question": "Does CATL outperform LGES on globalization quality?",
  "executive_summary": "CATL leads on globalization; LGES faces subsidy cliff.",
  "differentiation_matrix": [
    {
      "factor": "execution",
      "catl_evidence": "Strong capex discipline.",
      "lges_evidence": "Hungary delay.",
      "implication": "CATL execution premium.",
      "supporting_tags": "Capex_Execution"
    }
  ],
  "why_now": "IRA policy uncertainty accelerated in 2025Q4.",
  "differentiation_takeaway": "CATL scores 3pt higher on execution.",
  "contradiction_summary": "Two documents challenge IRA dependency assumptions.",
  "risk_summary": "Policy reversal and capex overrun are primary bear cases.",
  "strongest_supporting_evidence": ["CATL overseas margin 31.4%."],
  "contrary_risk_evidence": ["LGES IRA credit dependency."],
  "analyst_questions": ["What is LGES Hungary utilization at IRA cap?"],
  "overall_confidence": "7/10 — good coverage, limited ground truth.",
  "limitations": ["Evidence limited to public disclosures."]
}"""


def _make_mock_response():
    mock_response = MagicMock()
    mock_response.text = _FAKE_JSON
    return mock_response


def test_synthesise_returns_synthesis_output():
    with patch("src.synthesis.synthesiser.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = _make_mock_response()
        result = synthesise("test prompt")

    assert isinstance(result, SynthesisOutput)
    assert "CATL" in result.executive_summary


def test_synthesise_passes_correct_model():
    with patch("src.synthesis.synthesiser.genai.Client") as MockClient:
        mock_generate = MockClient.return_value.models.generate_content
        mock_generate.return_value = _make_mock_response()
        synthesise("test prompt", model="gemma-4-31b-it")
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["model"] == "gemma-4-31b-it"


def test_synthesise_raises_on_invalid_json():
    bad_response = MagicMock()
    bad_response.text = "not valid json at all"

    with patch("src.synthesis.synthesiser.genai.Client") as MockClient:
        MockClient.return_value.models.generate_content.return_value = bad_response
        with pytest.raises(ValueError, match="Failed to parse synthesis output"):
            synthesise("test prompt")
