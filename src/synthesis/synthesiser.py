import json
import anthropic

from src.synthesis.schema import SynthesisOutput


def synthesise(prompt: str, model: str = "claude-sonnet-4-6") -> SynthesisOutput:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
        return SynthesisOutput(**data)
    except Exception as exc:
        raise ValueError(
            f"Failed to parse synthesis output: {exc}\n\nRaw response:\n{raw}"
        ) from exc
