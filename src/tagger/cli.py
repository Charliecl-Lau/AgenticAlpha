import argparse
import logging
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from src.tagger.batch import run_batch
from src.tagger.prompt import build_system_prompt

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

_MODEL_NAME = "gemma-4-31b-it"


class _Model:
    def __init__(self, client, model_name: str, system_instruction: str):
        self._client = client
        self._model_name = model_name
        self._system_instruction = system_instruction

    def generate_content(self, prompt: str):
        return self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self._system_instruction,
                max_output_tokens=512,
                temperature=0.0,
            ),
        )


def _make_model() -> _Model:
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _Model(client, _MODEL_NAME, build_system_prompt())


def main() -> None:
    parser = argparse.ArgumentParser(description="Tag ingested Markdown files with LLM extraction")
    parser.add_argument("--perception", default="data/raw/perception")
    parser.add_argument("--ground-truth", default="data/raw/ground_truth")
    parser.add_argument("--policy", default="data/raw/policy",
                        help="Directory containing policy markdown files")
    parser.add_argument("--operations", default="data/raw/operations",
                        help="Directory containing operations markdown files")
    parser.add_argument("--output", default="data/processed/tags")
    args = parser.parse_args()

    model = _make_model()
    run_batch(
        input_dirs={
            "perception":   args.perception,
            "ground_truth": args.ground_truth,
            "policy":       args.policy,
            "operations":   args.operations,
        },
        output_dir=args.output,
        model=model,
    )
    print(f"JSON files written to {args.output}/")


if __name__ == "__main__":
    main()
