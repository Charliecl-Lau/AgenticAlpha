from dataclasses import dataclass
from typing import Optional
import pandas as pd

from src.human_layer.schema import HumanInputs
from src.human_layer.summariser import extract_top_signals


@dataclass
class DeckInput:
    """Single source of truth consumed by the Stage 5 deck renderer."""
    human: HumanInputs
    ai_signals: dict[str, list[dict]]
    synthesis: Optional[object]
    divergence_matrix_path: str
    trend_inflection_path: str
    differentiation_matrix_path: str
    why_now_timeline_path: str
    contradictions_path: str
    risk_tree_path: str
    evidence_scale_path: str


def merge_inputs(
    human: HumanInputs,
    tag_df: pd.DataFrame,
    divergence_matrix_path: str,
    trend_inflection_path: str,
    differentiation_matrix_path: str,
    why_now_timeline_path: str,
    contradictions_path: str,
    risk_tree_path: str,
    evidence_scale_path: str,
    synthesis=None,
    top_n: int = 3,
) -> DeckInput:
    """Package validated human inputs, top-N AI signals, chart paths, and optional synthesis into a DeckInput for Stage 5."""
    ai_signals = extract_top_signals(tag_df, n=top_n)
    return DeckInput(
        human=human,
        ai_signals=ai_signals,
        synthesis=synthesis,
        divergence_matrix_path=divergence_matrix_path,
        trend_inflection_path=trend_inflection_path,
        differentiation_matrix_path=differentiation_matrix_path,
        why_now_timeline_path=why_now_timeline_path,
        contradictions_path=contradictions_path,
        risk_tree_path=risk_tree_path,
        evidence_scale_path=evidence_scale_path,
    )
