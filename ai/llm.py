"""One place that talks to Claude. Every AI tool in this folder goes through `ask_structured`.

Why structured output: the model must return JSON that matches a Pydantic schema, so the rest of
the code can trust its shape (and a bad answer fails loudly instead of silently).
"""
import os
from typing import TypeVar

import anthropic
from pydantic import BaseModel

MODEL = os.getenv("HERAURA_AI_MODEL", "claude-opus-5-5")
T = TypeVar("T", bound=BaseModel)


class AIRefused(RuntimeError):
    """The model declined the request (stop_reason == "refusal")."""


def ask_structured(system: str, user: str, schema: type[T], max_tokens: int = 16000) -> T:
    # Reads ANTHROPIC_API_KEY (or an `ant auth login` profile) from the environment.
    client = anthropic.Anthropic()
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        # If the model declines on safety grounds, the API retries on a fallback model automatically.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise AIRefused(str(response.stop_details))
    if response.parsed_output is None:
        raise ValueError(f"Model did not return valid {schema.__name__} (stop_reason={response.stop_reason})")
    return response.parsed_output
