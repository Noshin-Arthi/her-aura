"""Failure triage agent: reads the Playwright JSON report and suggests a cause and fix for each failure.

It never edits code. It writes a markdown report; a human decides what to apply.
That "human in the loop" step is the point: AI suggestions are often plausible and wrong.

Usage (after a failed run):
  python -m ai.failure_triage                        # reads e2e/test-results/results.json
  python -m ai.failure_triage --report path/to/results.json
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Failure(BaseModel):
    title: str
    file: str
    project: str
    error: str


class Diagnosis(BaseModel):
    category: Literal["app-bug", "locator-changed", "timing", "test-data", "environment", "test-logic"]
    confidence: Literal["high", "medium", "low"]
    evidence: str = Field(description="Quote the exact error lines or code that support the category")
    suggested_fix: str = Field(description="A concrete change, e.g. which locator in which page object, or 'report a bug: ...'")
    verify_by: str = Field(description="How a human can confirm this diagnosis before applying the fix")


def collect_failures(report: dict) -> list[Failure]:
    """Walk the Playwright JSON report tree and return failed tests. Pure function: unit tested."""
    failures: list[Failure] = []

    def walk(suite: dict, file: str) -> None:
        file = suite.get("file", file)
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                results = test.get("results", [])
                if test.get("status") == "unexpected" or (results and results[-1].get("status") in ("failed", "timedOut")):
                    last = results[-1] if results else {}
                    message = "\n".join(e.get("message", "") for e in last.get("errors", [])) or last.get("error", {}).get("message", "")
                    failures.append(Failure(title=spec["title"], file=file, project=test.get("projectName", ""),
                                            error=ANSI.sub("", message)[:4000]))
        for child in suite.get("suites", []):
            walk(child, file)

    for suite in report.get("suites", []):
        walk(suite, suite.get("file", ""))
    return failures


def related_source(failure: Failure) -> str:
    """Give the model the spec and the page objects it uses, so it can point at real lines."""
    spec_path = ROOT / "e2e" / "tests" / Path(failure.file).name
    parts = []
    if spec_path.exists():
        parts.append(f"--- {spec_path.relative_to(ROOT)} ---\n{spec_path.read_text(encoding='utf-8')}")
    for page_object in sorted((ROOT / "e2e" / "pages").glob("*.ts")):
        parts.append(f"--- {page_object.relative_to(ROOT)} ---\n{page_object.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", default=str(ROOT / "e2e" / "test-results" / "results.json"))
    args = parser.parse_args()

    failures = collect_failures(json.loads(Path(args.report).read_text(encoding="utf-8")))
    if not failures:
        print("No failures in the report.")
        return

    from ai.llm import ask_structured  # imported here so collect_failures can be tested without the SDK

    system = (Path(__file__).parent / "prompts" / "triage_system.md").read_text(encoding="utf-8")
    lines = [f"# Failure triage ({datetime.now():%Y-%m-%d %H:%M})", "",
             "> AI suggestions. Verify each one before changing code.", ""]
    for f in failures:
        print(f"Diagnosing: {f.title} [{f.project}]")
        d = ask_structured(system, f"<failure>\n{f.model_dump_json(indent=2)}\n</failure>\n\n<source>\n{related_source(f)}\n</source>", Diagnosis)
        lines += [f"## {f.title} ({f.project})", f"- **Category:** {d.category} ({d.confidence} confidence)",
                  f"- **Evidence:** {d.evidence}", f"- **Suggested fix:** {d.suggested_fix}",
                  f"- **Verify by:** {d.verify_by}", "", "<details><summary>Raw error</summary>", "",
                  "```", f.error, "```", "</details>", ""]

    out_dir = ROOT / "ai" / "reports"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"triage-{datetime.now():%Y%m%d-%H%M%S}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
