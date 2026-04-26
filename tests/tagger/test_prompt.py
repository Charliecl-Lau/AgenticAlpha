from src.tagger.prompt import build_system_prompt, build_user_message


def test_system_prompt_contains_json_schema():
    prompt = build_system_prompt()
    assert "sentiment_score" in prompt
    assert "topic_cluster" in prompt
    assert "geo_exposure" in prompt


def test_system_prompt_distinguishes_geopolitical_noise_from_capex():
    prompt = build_system_prompt()
    assert "Geopolitical_Noise" in prompt
    assert "Capex_Execution" in prompt


def test_build_user_message_includes_markdown_content():
    md = "CATL expanded its European operations significantly."
    msg = build_user_message(md, company="CATL", stream="perception")
    assert "CATL" in msg
    assert "CATL expanded its European operations" in msg


def test_build_user_message_includes_stream_context():
    msg = build_user_message("Some IR text.", company="LGES", stream="ground_truth")
    assert "ground_truth" in msg or "Ground Truth" in msg


# New v2 tests
def test_system_prompt_mentions_contradiction_flag():
    assert "contradiction_flag" in build_system_prompt()


def test_system_prompt_mentions_confidence():
    assert "confidence" in build_system_prompt()


def test_system_prompt_mentions_localization_score():
    assert "localization_score" in build_system_prompt()


def test_system_prompt_mentions_claim_summary():
    assert "claim_summary" in build_system_prompt()


def test_system_prompt_mentions_key_quote():
    assert "key_quote" in build_system_prompt()


def test_system_prompt_has_no_recommendation_rule():
    prompt = build_system_prompt()
    assert "do not make recommendations" in prompt.lower() or "do NOT make recommendations" in prompt


def test_user_message_contains_company_and_stream():
    msg = build_user_message("## CATL Q4\n\nBody.", company="CATL", stream="ground_truth")
    assert "CATL" in msg
    assert "ground_truth" in msg
