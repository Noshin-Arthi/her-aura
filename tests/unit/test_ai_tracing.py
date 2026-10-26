"""Observability for the AI tools: every model call leaves a trace, including failures and fallbacks.
No real API calls: the Anthropic client is replaced with a fake."""
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from ai import llm, tracing


@pytest.fixture(autouse=True)
def trace_to_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("HERAURA_TRACE_FILE", str(tmp_path / "calls.jsonl"))


class Answer(BaseModel):
    text: str


def fake_client(response=None, error=None):
    def parse(**kwargs):
        if error:
            raise error
        return response
    return lambda: SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))


def make_response(model="claude-opus-5-5", stop="end_turn", parsed=Answer(text="ok")):
    return SimpleNamespace(model=model, stop_reason=stop, stop_details=None, parsed_output=parsed,
                           usage=SimpleNamespace(input_tokens=1000, output_tokens=500))


def test_successful_call_is_traced_with_tokens_cost_and_prompt_version(monkeypatch):
    monkeypatch.setattr(llm.anthropic, "Anthropic", fake_client(make_response()))
    assert llm.ask_structured("system v1", "hi", Answer, tool="test_planner").text == "ok"
    s = tracing.summarize()
    assert s["calls"] == 1 and s["failure_rate"] == 0 and s["tokens"] == 1500
    assert s["cost_usd"] == pytest.approx(0.014)          # 1000 × $4/M + 500 × $20/M
    assert s["by_tool"] == {"test_planner": 1}
    assert s["prompt_versions"] == [f"test_planner:{tracing.prompt_version('system v1')}"]


def test_changing_the_prompt_changes_its_version():
    assert tracing.prompt_version("rules A") != tracing.prompt_version("rules B")
    assert tracing.prompt_version("rules A") == tracing.prompt_version("rules A")


def test_refusal_is_traced_as_a_failure(monkeypatch):
    monkeypatch.setattr(llm.anthropic, "Anthropic", fake_client(make_response(stop="refusal", parsed=None)))
    with pytest.raises(llm.AIRefused):
        llm.ask_structured("sys", "hi", Answer)
    assert tracing.summarize()["failure_rate"] == 1


def test_exception_is_traced_and_re_raised(monkeypatch):
    monkeypatch.setattr(llm.anthropic, "Anthropic", fake_client(error=TimeoutError("network")))
    with pytest.raises(TimeoutError):
        llm.ask_structured("sys", "hi", Answer)
    row = tracing.summarize()
    assert row["calls"] == 1 and row["failure_rate"] == 1


def test_fallback_model_is_counted(monkeypatch):
    monkeypatch.setattr(llm.anthropic, "Anthropic", fake_client(make_response(model="claude-opus-5")))
    llm.ask_structured("sys", "hi", Answer)
    assert tracing.summarize()["fallback_used"] == 1


def test_no_traces_yet():
    assert tracing.summarize() == {"calls": 0}
