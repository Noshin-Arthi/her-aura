"""The AI tools have deterministic parts that must work without calling any model. Test those."""
from ai.failure_triage import collect_failures
from ai.test_planner import TestCase, TestPlan, acceptance_criteria_ids, extract_story, uncovered_acs

REQUIREMENTS = """# Requirements

## US-05 Book an appointment
- AC1: patient books an open slot
- AC2: a booked slot is not offered again

## US-06 Cancel
- AC1: patient cancels
"""


def make_case(covers):
    return TestCase(id="TC-1", title="t", covers=covers, technique="positive", layer="api",
                    priority="P1", preconditions=[], steps=["s"], expected="e")


def test_extract_story_stops_at_next_story():
    story = extract_story(REQUIREMENTS, "US-05")
    assert "AC2" in story and "US-06" not in story


def test_acceptance_criteria_ids():
    assert acceptance_criteria_ids(extract_story(REQUIREMENTS, "US-05"), "US-05") == ["US-05 AC1", "US-05 AC2"]


def test_uncovered_acs_found():
    plan = TestPlan(story_id="US-05", risks=[], open_questions=[], test_cases=[make_case(["US-05 AC1"])])
    assert uncovered_acs(plan, ["US-05 AC1", "US-05 AC2"]) == ["US-05 AC2"]


def test_collect_failures_from_playwright_report():
    report = {"suites": [{"file": "booking.spec.ts", "specs": [], "suites": [{"specs": [
        {"title": "books a slot", "tests": [{"projectName": "chromium", "status": "unexpected",
                                             "results": [{"status": "failed", "errors": [{"message": "\x1b[31mTimeout\x1b[39m waiting for #btn-book"}]}]}]},
        {"title": "passes", "tests": [{"projectName": "chromium", "status": "expected", "results": [{"status": "passed"}]}]},
    ]}]}]}
    failures = collect_failures(report)
    assert len(failures) == 1
    assert failures[0].file == "booking.spec.ts"
    assert failures[0].error == "Timeout waiting for #btn-book"  # ANSI colours stripped
