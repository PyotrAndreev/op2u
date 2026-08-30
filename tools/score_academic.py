#!/usr/bin/env python3
"""Deterministic transfer diagnostics for the academic profile; no network or model calls."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

PEOPLE = ("axel cleeremans", "ivan ivanchei", "inès mentec")
ROUTES = {
    "direct_phd", "research_masters", "predoc_or_research_assistant",
    "person_specific_research_connection", "methods_school_or_research_visit",
    "conference_or_poster", "language_exam_and_practice",
}
FUNDING_RE = re.compile(r"\b(?:funding|funded|scholarship|stipend|tuition|living costs?|fee waiver|grant)\b", re.I)
TOEFL_RE = re.compile(r"\bTOEFL\b", re.I)
SCORE_RE = re.compile(r"\b(?:score|minimum|required|requirement)\b|\b\d{2,3}\b", re.I)
DATE_RE = re.compile(r"\b2026-(\d{2})-(\d{2})\b")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def latest(run: Path, stem: str) -> Path:
    found = [(1, run / f"{stem}.json")]
    for path in run.glob(f"{stem}.attempt-*.json"):
        m = re.search(r"attempt-(\d+)\.json$", path.name)
        if m: found.append((int(m.group(1)), path))
    return max((x for x in found if x[1].is_file()), default=(-1, run / f"{stem}.json"))[1]


def report_path(run: Path) -> Path:
    candidates = [(1, run / "report.result.json")]
    for path in run.glob("report.attempt-*.result.json"):
        m = re.search(r"attempt-(\d+)\.result\.json$", path.name)
        if m: candidates.append((int(m.group(1)), path))
    return max((x for x in candidates if x[1].is_file()), default=(-1, run / "report.result.json"))[1]


def text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def evaluate(run: Path) -> dict[str, Any]:
    report = load(report_path(run))
    validation_path = latest(run, "production_validation")
    validation = load(validation_path) if validation_path.is_file() else None
    candidates = [x for x in report.get("candidates", []) if isinstance(x, dict)]
    ledger = [x for x in report.get("evidence_ledger", []) if isinstance(x, dict)]
    selected = report.get("selected_ids", {})
    action_ids = set(selected.get("act_now", []) + selected.get("prepare_next", []))
    by_id = {x.get("candidate_id"): x for x in candidates}
    allocation = report.get("weekly_allocation", {})
    computed = sum(by_id.get(cid, {}).get("scheduled_week_effort_minutes", {}).get("max", 0) for cid in action_ids)
    overlong = []
    for cid in action_ids:
        maximum = by_id.get(cid, {}).get("first_action", {}).get("minutes_max")
        if not isinstance(maximum, int) or maximum > 60:
            overlong.append({"candidate_id": cid, "minutes_max": maximum})

    horizon = [x for x in report.get("opportunity_horizon", []) if isinstance(x, dict)]
    route_values = {str(x.get("type")) for x in candidates if str(x.get("type")) in ROUTES}
    verified_ids = {str(x.get("candidate_id")) for x in horizon}
    verified_routes = {str(by_id.get(cid, {}).get("type")) for cid in verified_ids if str(by_id.get(cid, {}).get("type")) in ROUTES}

    funding_rows = [x for x in ledger if FUNDING_RE.search(text(x))]
    toefl_rows = [x for x in ledger if TOEFL_RE.search(text(x))]
    toefl_requirement_rows = [x for x in toefl_rows if SCORE_RE.search(str(x.get("quote", "")) + " " + str(x.get("claim", "")))]
    people_results = {}
    whole = text(report).lower()
    for person in PEOPLE:
        mentions = person in whole
        direct_rows = [x.get("ledger_id") for x in ledger if person in text(x).lower()]
        people_results[person] = {"mentioned": mentions, "direct_evidence_rows": direct_rows}

    irrelevant = []
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        candidate_rows = [row for row in ledger if row.get("candidate_id") == cid]
        blob = (text(candidate) + " " + text(candidate_rows)).lower()
        dates = [(int(m.group(1)), int(m.group(2))) for m in DATE_RE.finditer(blob)]
        cape_specific = ("south africa" in blob or "cape town" in blob
                         or "university of cape town" in blob
                         or re.search(r"\buct\b", blob) is not None)
        if cape_specific and dates and not any(month == 10 for month, _ in dates):
            if candidate.get("status") in {"ACT_NOW", "PREPARE_NEXT"}:
                irrelevant.append({"candidate_id": cid, "reason": "selected South Africa item outside supplied October Cape Town window"})
    branches = report.get("breadth_summary", {}).get("branches_attempted", [])
    if any("south_africa_2026-09-25" in str(x) for x in branches):
        irrelevant.append({"candidate_id": None, "reason": "inherited original-profile South Africa branch"})

    anchors = report.get("anchor_decisions")
    route_portfolio = report.get("route_portfolio")
    return {
        "production_validation": {"valid": isinstance(validation, dict) and validation.get("valid") is True,
                                  "file": validation_path.name if validation_path.is_file() else None,
                                  "errors": validation.get("errors", []) if isinstance(validation, dict) else ["missing"]},
        "direction_contract": {"expected_cap_minutes": 240, "declared_cap_minutes": allocation.get("cap_minutes"),
                               "computed_selected_max_minutes": computed,
                               "matches_cap": allocation.get("cap_minutes") == 240,
                               "within_cap": computed <= 240,
                               "first_actions_over_60_minutes": overlong},
        "profile_leakage": {"pass": not irrelevant, "items": irrelevant},
        "route_depth": {"candidate_routes": sorted(route_values), "candidate_route_count": len(route_values),
                        "verified_routes": sorted(verified_routes), "verified_route_count": len(verified_routes),
                        "route_portfolio_present": isinstance(route_portfolio, (list, dict))},
        "anchor_depth": {"anchor_decisions_present": isinstance(anchors, list) and bool(anchors),
                         "anchor_count": len(anchors) if isinstance(anchors, list) else 0},
        "funding_completeness": {"direct_funding_evidence_rows": [x.get("ledger_id") for x in funding_rows],
                                 "has_direct_funding_evidence": bool(funding_rows)},
        "language_exam_depth": {"direct_toefl_rows": [x.get("ledger_id") for x in toefl_rows],
                                "direct_requirement_rows": [x.get("ledger_id") for x in toefl_requirement_rows]},
        "named_people": people_results,
        "portfolio": {"candidate_count": len(candidates), "verified_horizon_count": len(horizon),
                      "act_now_count": len(selected.get("act_now", [])),
                      "prepare_next_count": len(selected.get("prepare_next", []))},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.run.resolve()), indent=2, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
