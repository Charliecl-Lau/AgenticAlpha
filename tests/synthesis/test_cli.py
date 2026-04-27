import json, pathlib
from unittest.mock import patch
from src.synthesis.schema import SynthesisOutput

_FAKE_OUTPUT = SynthesisOutput(
    executive_summary="CATL leads.",
    why_now="2025 divergence.",
    differentiation_takeaway="Execution gap.",
    contradiction_summary="Two contradictions.",
    risk_summary="Policy risk.",
    analyst_questions=["Q1?"],
    limitations=["L1."],
)

def test_synthesis_cli_writes_json(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir()
    out_path = tmp_path / "synthesis.json"

    with patch("src.synthesis.cli.synthesise", return_value=_FAKE_OUTPUT):
        from src.synthesis.cli import run_synthesis
        run_synthesis(
            tags_dir=str(tags_dir),
            charts_dir=str(charts_dir),
            output_path=str(out_path),
        )

    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["executive_summary"] == "CATL leads."
    assert isinstance(data["analyst_questions"], list)

def test_synthesis_cli_creates_parent_dirs(tmp_path):
    tags_dir = tmp_path / "tags"
    tags_dir.mkdir()
    out_path = tmp_path / "nested" / "output" / "synthesis.json"

    with patch("src.synthesis.cli.synthesise", return_value=_FAKE_OUTPUT):
        from src.synthesis.cli import run_synthesis
        run_synthesis(
            tags_dir=str(tags_dir),
            charts_dir=str(tmp_path),
            output_path=str(out_path),
        )

    assert out_path.exists()
