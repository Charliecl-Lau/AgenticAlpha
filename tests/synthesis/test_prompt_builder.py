import pandas as pd
from src.synthesis.prompt_builder import build_synthesis_prompt

def _make_diff_df():
    return pd.DataFrame([
        {"factor": "localization", "CATL": 7.5, "LGES": 4.5, "delta": 3.0},
        {"factor": "execution",    "CATL": 8.5, "LGES": 4.5, "delta": 4.0},
    ])

def _make_contra_df():
    return pd.DataFrame([
        {"company": "LGES", "claim_summary": "IRA credit at risk.",
         "contradiction_reason": "Policy change.", "sentiment_score": 2.0},
    ])

def test_prompt_contains_differentiation_data():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={"CATL": [{"claim_summary": "Strong execution."}], "LGES": []},
    )
    assert "localization" in prompt
    assert "3.0" in prompt

def test_prompt_contains_contradiction_data():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={"CATL": [], "LGES": []},
    )
    assert "IRA credit at risk" in prompt

def test_prompt_includes_no_recommendation_rule():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={},
    )
    lower = prompt.lower()
    assert "do not make recommendations" in lower or "do not make investment recommendations" in lower

def test_prompt_includes_json_schema_fields():
    prompt = build_synthesis_prompt(
        diff_df=_make_diff_df(),
        contradictions_df=_make_contra_df(),
        top_signals={},
    )
    assert "executive_summary" in prompt
    assert "analyst_questions" in prompt
    assert "limitations" in prompt

def test_prompt_handles_empty_dfs():
    prompt = build_synthesis_prompt(
        diff_df=pd.DataFrame(),
        contradictions_df=pd.DataFrame(),
        top_signals={},
    )
    assert "executive_summary" in prompt  # schema still present
