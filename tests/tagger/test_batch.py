import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.tagger.batch import run_batch, _parse_header
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion

_TAG = Tag(
    sentiment_score=6,
    direction=Direction.neutral,
    confidence=0.7,
    topic_cluster=TopicCluster.Capex_Execution,
    geo_exposure=[GeoRegion.China],
    globalization_model="export-led",
    localization_score=7,
    subsidy_dependency=2,
    execution_quality=7,
    margin_signal=6,
    capex_signal=8,
    ROIC_signal=6,
    contradiction_flag=False,
    contradiction_reason=None,
    claim_summary="CATL announced a 20 GWh expansion in Sichuan province.",
    key_quote=None,
)


def _make_md_files(directory: Path, count: int, company: str = "CATL") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (directory / f"{company.lower()}_{i:03d}.md").write_text(
            f"# Company: {company}\n\nSome article text {i}."
        )


def test_run_batch_writes_one_json_per_md(tmp_path):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 3)
    out_dir = tmp_path / "tags"
    with patch("src.tagger.batch.tag_document", return_value=_TAG):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    jsons = list(out_dir.glob("*.json"))
    assert len(jsons) == 3


def test_run_batch_json_contains_tag_fields(tmp_path):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 1)
    out_dir = tmp_path / "tags"
    with patch("src.tagger.batch.tag_document", return_value=_TAG):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    data = json.loads(list(out_dir.glob("*.json"))[0].read_text())
    assert data["sentiment_score"] == 6
    assert data["stream"] == "perception"
    assert data["company"] == "CATL"


def test_run_batch_skips_failed_files_and_continues(tmp_path):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 2)
    out_dir = tmp_path / "tags"
    call_count = {"n": 0}

    def fake_tag(model, markdown, company, stream):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ValueError("LLM error")
        return _TAG

    with patch("src.tagger.batch.tag_document", side_effect=fake_tag):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    jsons = list(out_dir.glob("*.json"))
    assert len(jsons) == 1


def test_run_batch_prints_report(tmp_path, capsys):
    perception_dir = tmp_path / "perception"
    _make_md_files(perception_dir, 2)
    out_dir = tmp_path / "tags"
    with patch("src.tagger.batch.tag_document", return_value=_TAG):
        run_batch(
            input_dirs={"perception": str(perception_dir)},
            output_dir=str(out_dir),
            model=MagicMock(),
        )
    captured = capsys.readouterr()
    assert "Processed: 2" in captured.out
    assert "Skipped: 0" in captured.out


def test_parse_header_extracts_company():
    text = "# Company: CATL\n\nSome article."
    assert _parse_header(text)["company"] == "CATL"


def test_parse_header_handles_extra_whitespace():
    text = "#  Company:   LGES  \n\nSome article."
    assert _parse_header(text)["company"] == "LGES"


def test_parse_header_case_insensitive():
    text = "# company: CATL\n\nSome article."
    assert _parse_header(text)["company"] == "CATL"


def test_parse_header_returns_unknown_when_missing():
    assert _parse_header("No header here.")["company"] == "Unknown"


# New v2 tests
def test_source_weight_perception():
    from src.tagger.batch import source_weight_for_stream
    assert source_weight_for_stream("perception") == 1.0


def test_source_weight_ground_truth():
    from src.tagger.batch import source_weight_for_stream
    assert source_weight_for_stream("ground_truth") == 2.0


def test_source_weight_policy():
    from src.tagger.batch import source_weight_for_stream
    assert source_weight_for_stream("policy") == 1.5


def test_source_weight_operations():
    from src.tagger.batch import source_weight_for_stream
    assert source_weight_for_stream("operations") == 2.0


def test_source_weight_unknown_defaults_to_1():
    from src.tagger.batch import source_weight_for_stream
    assert source_weight_for_stream("unknown") == 1.0


def test_parse_frontmatter_date_extracts_date():
    from src.tagger.batch import parse_frontmatter_date
    md = "---\ndate: 2025-11-15\ncompany: CATL\n---\nBody text here."
    assert parse_frontmatter_date(md) == "2025-11-15"


def test_parse_frontmatter_date_returns_none_when_absent():
    from src.tagger.batch import parse_frontmatter_date
    assert parse_frontmatter_date("# CATL Report\n\nBody text here.") is None


def test_batch_output_includes_source_weight(tmp_path):
    md_file = tmp_path / "catl_test.md"
    md_file.write_text("---\ndate: 2025-06-01\ncompany: CATL\n---\nCAT posted strong results.")

    fake_tag_dict = {
        "sentiment_score": 7.5, "direction": "positive", "confidence": 0.8,
        "topic_cluster": "Organic_Scale_vs_Export", "geo_exposure": ["US"],
        "globalization_model": "export-led", "localization_score": 8,
        "subsidy_dependency": 3, "execution_quality": 9, "margin_signal": 7,
        "capex_signal": 8, "ROIC_signal": 7, "contradiction_flag": False,
        "contradiction_reason": None, "claim_summary": "CATL posted strong results.",
        "key_quote": None,
    }
    mock_tag = MagicMock()
    mock_tag.model_dump.return_value = fake_tag_dict

    out_dir = tmp_path / "tags"
    out_dir.mkdir()

    with patch("src.tagger.batch.tag_document", return_value=mock_tag):
        run_batch(
            input_dirs={"perception": [str(tmp_path)]},
            output_dir=str(out_dir),
            model=MagicMock(),
        )

    output_files = list(out_dir.glob("*.json"))
    assert len(output_files) == 1
    data = json.loads(output_files[0].read_text())
    assert data["source_weight"] == 1.0
    assert data["date"] == "2025-06-01"
