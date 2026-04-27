import pytest
from pydantic import ValidationError
from src.synthesis.schema import SynthesisOutput

_REQUIRED = dict(
    research_question="Does CATL outperform LGES on globalization quality?",
    differentiation_matrix=[
        {
            "factor": "execution",
            "catl_evidence": "Strong.",
            "lges_evidence": "Weak.",
            "implication": "CATL wins.",
            "supporting_tags": "Capex_Execution",
        }
    ],
    strongest_supporting_evidence=["CATL margin 31.4%."],
    contrary_risk_evidence=["LGES IRA dependency."],
    overall_confidence="7/10 — good signal coverage.",
)


def test_synthesis_output_valid():
    out = SynthesisOutput(
        **_REQUIRED,
        executive_summary="CATL demonstrates superior globalization execution vs LGES.",
        why_now="Operational divergence accelerated materially in 2025–26.",
        differentiation_takeaway="CATL scores 2.5x higher on localization and execution vs LGES.",
        contradiction_summary="3 documents challenge the LGES IRA-benefit thesis.",
        risk_summary="Policy risk and capex overruns are the primary bear scenarios for LGES.",
        analyst_questions=[
            "What is Hungary plant utilization assuming IRA credit cap?",
            "How does CATL margin hold if ASP declines 15%?",
        ],
        limitations=[
            "Ground truth limited to public IR disclosures.",
            "Geo data relies on article self-reporting.",
        ],
    )
    assert out.executive_summary.startswith("CATL")
    assert len(out.analyst_questions) == 2
    assert len(out.limitations) == 2


def test_synthesis_output_rejects_empty_executive_summary():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            **_REQUIRED,
            executive_summary="",
            why_now="test",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=["Q1"],
            limitations=["L1"],
        )


def test_synthesis_output_rejects_whitespace_why_now():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            **_REQUIRED,
            executive_summary="Summary.",
            why_now="   ",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=["Q1"],
            limitations=["L1"],
        )


def test_synthesis_output_rejects_empty_analyst_questions():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            **_REQUIRED,
            executive_summary="Summary.",
            why_now="test",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=[],
            limitations=["L1"],
        )


def test_synthesis_output_rejects_empty_limitations():
    with pytest.raises(ValidationError):
        SynthesisOutput(
            **_REQUIRED,
            executive_summary="Summary.",
            why_now="test",
            differentiation_takeaway="test",
            contradiction_summary="test",
            risk_summary="test",
            analyst_questions=["Q1"],
            limitations=[],
        )


def test_synthesis_output_serializes_to_dict():
    out = SynthesisOutput(
        **_REQUIRED,
        executive_summary="Summary.",
        why_now="Now.",
        differentiation_takeaway="Diff.",
        contradiction_summary="Contra.",
        risk_summary="Risk.",
        analyst_questions=["Q1"],
        limitations=["L1"],
    )
    d = out.model_dump()
    assert d["executive_summary"] == "Summary."
    assert isinstance(d["analyst_questions"], list)
