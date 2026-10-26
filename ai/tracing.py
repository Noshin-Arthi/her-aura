"""Observability for Her Aura's AI tools: one JSON line per model call.

Every call records what you need to debug and to watch quality, latency and cost over time:
timestamp, which tool, model actually used, prompt version (a hash of the system prompt, so you can
tell which prompt produced which result), tokens, latency, stop reason and errors.

  python -m ai.tracing            # summary of all recorded calls
Traces go to ai/traces/llm_calls.jsonl (git-ignored), or HERAURA_TRACE_FILE if set.
"""
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILE = Path(__file__).parent / "traces" / "llm_calls.jsonl"
# USD per million tokens (input, output). Update when prices change.
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-4-5": (1.0, 5.0)}


def trace_file() -> Path:
    return Path(os.getenv("HERAURA_TRACE_FILE", DEFAULT_FILE))


def prompt_version(system_prompt: str) -> str:
    """Short, stable id for a prompt text: change the prompt, the version changes."""
    return hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:10]


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    price = PRICES.get(model)
    if price is None:
        return None
    return round((input_tokens * price[0] + output_tokens * price[1]) / 1_000_000, 6)


def record(**fields) -> dict:
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
    path = trace_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


@contextmanager
def traced_call(tool: str, system_prompt: str, requested_model: str):
    """Wrap a model call. Put the API response in `t["response"]`; usage and errors are recorded either way."""
    t = {"response": None}
    start = time.perf_counter()
    error = None
    try:
        yield t
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        r = t["response"]
        usage = getattr(r, "usage", None)
        inp, out = getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0
        model = getattr(r, "model", None) or requested_model   # with fallbacks, the serving model can differ
        record(tool=tool, model=model, requested_model=requested_model, prompt_version=prompt_version(system_prompt),
               input_tokens=inp, output_tokens=out, cost_usd=estimate_cost(model, inp, out),
               latency_ms=round((time.perf_counter() - start) * 1000), stop_reason=getattr(r, "stop_reason", None),
               ok=error is None and getattr(r, "stop_reason", None) not in ("refusal", "max_tokens"), error=error)


def summarize(path: Path | None = None) -> dict:
    path = path or trace_file()
    if not path.exists():
        return {"calls": 0}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    latencies = sorted(r["latency_ms"] for r in rows)
    p95 = latencies[min(len(latencies) - 1, int(round(0.95 * (len(latencies) - 1))))] if latencies else 0
    by_tool: dict[str, int] = {}
    for r in rows:
        by_tool[r["tool"]] = by_tool.get(r["tool"], 0) + 1
    return {
        "calls": len(rows),
        "failure_rate": round(sum(not r["ok"] for r in rows) / len(rows), 3),
        "p95_latency_ms": p95,
        "tokens": sum(r["input_tokens"] + r["output_tokens"] for r in rows),
        "cost_usd": round(sum(r["cost_usd"] or 0 for r in rows), 4),
        "fallback_used": sum(r["model"] != r["requested_model"] for r in rows),
        "by_tool": by_tool,
        "prompt_versions": sorted({f"{r['tool']}:{r['prompt_version']}" for r in rows}),
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(summarize(), indent=2))
