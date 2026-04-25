from src.tagger.prompt import build_system_prompt, build_user_message


def test_system_prompt_contains_asymmetry_instruction():
    prompt = build_system_prompt()
    assert "false symmetry" in prompt.lower() or "asymmetric" in prompt.lower()


def test_system_prompt_contains_json_schema():
    prompt = build_system_prompt()
    assert "sentiment_score" in prompt
    assert "topic_cluster" in prompt
    assert "geo_exposure" in prompt


def test_system_prompt_prohibits_investment_advice():
    prompt = build_system_prompt()
    assert "investment advice" in prompt.lower() or "we believe" in prompt.lower()


def test_system_prompt_distinguishes_geopolitical_noise_from_capex():
    prompt = build_system_prompt()
    assert "Geopolitical_Noise" in prompt
    assert "Capex_Execution" in prompt
    assert "primary event" in prompt.lower() or "regulatory" in prompt.lower()


def test_system_prompt_contains_few_shot_examples():
    prompt = build_system_prompt()
    assert "Example" in prompt or "EXAMPLE" in prompt


def test_summary_forbidden_phrases_blocked_by_prompt_instruction():
    prompt = build_system_prompt()
    assert "appears to" in prompt
    assert "we believe" in prompt


def test_build_user_message_includes_markdown_content():
    md = "CATL expanded its European operations significantly."
    msg = build_user_message(md, company="CATL", stream="perception")
    assert "CATL" in msg
    assert "CATL expanded its European operations" in msg


def test_build_user_message_includes_stream_context():
    msg = build_user_message("Some IR text.", company="LGES", stream="ground_truth")
    assert "ground_truth" in msg or "Ground Truth" in msg


def test_system_prompt_links_catl_to_organic_capex_and_lges_to_subsidy():
    prompt = build_system_prompt()
    # CATL must be associated with organic/capex clusters
    catl_section = prompt[prompt.lower().find("catl"):]
    assert "Organic_Scale_vs_Export" in catl_section or "Capex_Execution" in catl_section
    # LGES must be associated with subsidy dependence
    lges_section = prompt[prompt.lower().find("lges"):]
    assert "Subsidy_Dependence" in lges_section
