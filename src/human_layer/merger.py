from dataclasses import dataclass
import pandas as pd
from src.human_layer.schema import HumanInputs
from src.human_layer.summariser import extract_top_signals


@dataclass
class DeckInput:
    human: HumanInputs
    ai_signals: dict[str, list[dict]]
    divergence_matrix_path: str
    trend_inflection_path: str

    def to_dict(self) -> dict:
        return {
            "human": self.human.model_dump(),
            "ai_signals": self.ai_signals,
            "divergence_matrix_path": self.divergence_matrix_path,
            "trend_inflection_path": self.trend_inflection_path,
        }


def merge_inputs(
    human: HumanInputs,
    tag_df: pd.DataFrame,
    divergence_matrix_path: str,
    trend_inflection_path: str,
    top_n: int = 3,
) -> DeckInput:
    ai_signals = extract_top_signals(tag_df, n=top_n)
    return DeckInput(
        human=human,
        ai_signals=ai_signals,
        divergence_matrix_path=divergence_matrix_path,
        trend_inflection_path=trend_inflection_path,
    )
