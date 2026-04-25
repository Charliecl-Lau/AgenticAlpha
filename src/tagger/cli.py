import argparse
import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.tagger.batch import run_batch
from src.tagger.prompt import build_system_prompt

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

_MODEL_NAME = "gemma-3-27b-it"


def _make_model():
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=build_system_prompt(),
        generation_config=genai.GenerationConfig(
            max_output_tokens=512,
            temperature=0.0,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Tag ingested Markdown files with LLM extraction")
    parser.add_argument("--perception", default="data/raw/perception")
    parser.add_argument("--ground-truth", default="data/raw/ground_truth")
    parser.add_argument("--output", default="data/processed/tags")
    args = parser.parse_args()

    model = _make_model()
    run_batch(
        input_dirs={"perception": args.perception, "ground_truth": args.ground_truth},
        output_dir=args.output,
        model=model,
    )
    print(f"JSON files written to {args.output}/")


if __name__ == "__main__":
    main()
