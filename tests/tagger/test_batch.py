import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.tagger.batch import run_batch, _parse_header
from src.tagger.schema import Tag, Direction, TopicCluster, GeoRegion

_TAG = Tag(
    sentiment_score=6,
    direction=Direction.neutral,
    topic_cluster=TopicCluster.Capex_Execution,
    geo_exposure=[GeoRegion.China],
    summary="CATL announced a 20 GWh expansion in Sichuan province.",
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
