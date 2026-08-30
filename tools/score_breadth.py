#!/usr/bin/env python3
"""Deterministically score breadth diagnostics from saved run artifacts.

This tool uses only the Python standard library.  It never invokes a model,
network, browser, or validation service, and it never reads holdout inputs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REQUIRED_REPORT_KEYS = {
    "snapshot_date", "profile_state", "trigger_hypotheses", "candidates",
    "selected_ids", "weekly_allocation", "evidence_ledger",
    "rejected_candidates", "uncertainty_summary",
}
WINDOWS = (
    ("hong_kong_2026-08-25_2026-09-06", ("hong kong",), "2026-08-25", "2026-09-06"),
    ("shanghai_2026-09-06_2026-09-10", ("shanghai",), "2026-09-06", "2026-09-10"),
    ("shanghai_2026-09-20_2026-09-25", ("shanghai",), "2026-09-20", "2026-09-25"),
    ("south_africa_2026-09-25_2026-12-31", ("south africa", "cape town"), "2026-09-25", "2026-12-31"),
)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NON_ACTION_RE = re.compile(r"\b(?:monitor|save|wait|check later|retain|review later)\b", re.I)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def latest_validation(run: Path) -> tuple[Path | None, Any | None]:
    """Return the highest numbered immutable validation attempt, else the base file."""
    attempts: list[tuple[int, Path]] = []
    for path in run.glob("production_validation.attempt-*.json"):
        match = re.fullmatch(r"production_validation\.attempt-(\d+)\.json", path.name)
        if match:
            attempts.append((int(match.group(1)), path))
    path = max(attempts, default=(-1, run / "production_validation.json"))[1]
    if not path.is_file():
        return None, None
    try:
        return path, read_json(path)
    except (OSError, json.JSONDecodeError):
        return path, None


def as_objects(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def local_contract_errors(report: Any) -> list[str]:
    """A stable stdlib-only subset of the production output contract."""
    if not isinstance(report, dict):
        return ["report is not an object"]
    errors = [f"missing top-level key: {key}" for key in sorted(REQUIRED_REPORT_KEYS - set(report))]
    for key in ("candidates", "trigger_hypotheses", "evidence_ledger", "rejected_candidates", "uncertainty_summary"):
        if key in report and not isinstance(report[key], list):
            errors.append(f"{key} is not an array")
    selected = report.get("selected_ids")
    if not isinstance(selected, dict):
        errors.append("selected_ids is not an object")
    else:
        for key, limit in (("act_now", 3), ("prepare_next", 4), ("monitor", None)):
            value = selected.get(key)
            if not isinstance(value, list):
                errors.append(f"selected_ids.{key} is not an array")
            elif limit is not None and len(value) > limit:
                errors.append(f"selected_ids.{key} exceeds {limit}")
    allocation = report.get("weekly_allocation")
    if not isinstance(allocation, dict):
        errors.append("weekly_allocation is not an object")
    else:
        if allocation.get("cap_minutes") != 360:
            errors.append("weekly_allocation.cap_minutes is not 360")
        maximum = allocation.get("scheduled_max_minutes")
        if not isinstance(maximum, int) or not 0 <= maximum <= 360:
            errors.append("weekly_allocation.scheduled_max_minutes is not an integer in 0..360")
    for index, candidate in enumerate(as_objects(report.get("candidates"))):
        if not isinstance(candidate.get("candidate_id"), str) or not candidate["candidate_id"]:
            errors.append(f"candidates[{index}] has no candidate_id")
        if candidate.get("status") not in {"ACT_NOW", "PREPARE_NEXT", "MONITOR", "REJECT"}:
            errors.append(f"candidates[{index}] has invalid status")
        effort = candidate.get("scheduled_week_effort_minutes")
        if not isinstance(effort, dict) or not all(isinstance(effort.get(k), int) and effort[k] >= 0 for k in ("min", "max")):
            errors.append(f"candidates[{index}] has invalid scheduled effort")
    return errors


def evidence_by_candidate(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in as_objects(report.get("evidence_ledger")):
        candidate_id = row.get("candidate_id")
        if isinstance(candidate_id, str):
            rows[candidate_id].append(row)
    return rows


def direct_evidence(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("entailment") == "direct" and all(isinstance(row.get(key), str) and row[key]
               for key in ("quote", "url", "retrieved_at")) for row in rows)


def event_evidence(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("entailment") == "direct" and isinstance(row.get("supports"), list)
               and bool({"event_date", "rolling_window"} & set(row["supports"])) for row in rows)


def date_range(value: Any) -> tuple[dt.date, dt.date] | None:
    if not isinstance(value, str):
        return None
    values = DATE_RE.findall(value)
    if not values:
        return None
    try:
        start = dt.date.fromisoformat(values[0])
        end = dt.date.fromisoformat(values[-1])
    except ValueError:
        return None
    return (start, end) if start <= end else None


def geographic_hits(horizon: list[dict[str, Any]], evidence: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in horizon:
        candidate_id, description = item.get("candidate_id"), item.get("geographic_window")
        dates = date_range(item.get("event_dates"))
        if not isinstance(candidate_id, str) or not isinstance(description, str) or dates is None:
            continue
        if "unverified" in description.lower() or not event_evidence(evidence.get(candidate_id, [])):
            continue
        for window_id, places, start_text, end_text in WINDOWS:
            start, end = dt.date.fromisoformat(start_text), dt.date.fromisoformat(end_text)
            if any(place in description.lower() for place in places) and dates[0] <= end and start <= dates[1]:
                key = (candidate_id, window_id)
                if key not in seen:
                    seen.add(key)
                    hits.append({"candidate_id": candidate_id, "window": window_id})
    return sorted(hits, key=lambda item: (item["window"], item["candidate_id"]))


def duplicate_groups(values: dict[str, str | None]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for candidate_id, value in values.items():
        if value:
            groups[value].append(candidate_id)
    return [{"value": value, "candidate_ids": sorted(ids), "extra_items": len(ids) - 1}
            for value, ids in sorted(groups.items()) if len(ids) > 1]


def stretch_metric(report: dict[str, Any], candidates: dict[str, dict[str, Any]], evidence: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    stretch = report.get("stretch_challenge")
    if not isinstance(stretch, dict) or stretch.get("candidate_id") is None:
        return {"status": "EMPTY", "real_action": False, "reasons": []}
    candidate_id = stretch.get("candidate_id")
    candidate = candidates.get(candidate_id) if isinstance(candidate_id, str) else None
    reasons: list[str] = []
    if candidate is None:
        reasons.append("candidate_id does not resolve")
    else:
        action = candidate.get("first_action") if isinstance(candidate.get("first_action"), dict) else {}
        text = action.get("action", "")
        maximum = action.get("minutes_max")
        trigger = action.get("start_by_or_trigger", "")
        if candidate.get("status") not in {"ACT_NOW", "PREPARE_NEXT"}:
            reasons.append("candidate is not an actionable selected status")
        if not isinstance(text, str) or not text.strip() or NON_ACTION_RE.search(text):
            reasons.append("first action is monitor/save/wait-like or absent")
        if not isinstance(maximum, int) or not 0 < maximum <= 60:
            reasons.append("first action is not bounded to 1..60 minutes")
        trigger_ok = isinstance(trigger, str) and bool(re.search(r"within (?:the )?seven days|next seven days", trigger, re.I))
        if isinstance(trigger, str) and not trigger_ok:
            trigger_dates = DATE_RE.findall(trigger)
            snapshot = report.get("snapshot_date")
            try:
                trigger_ok = bool(trigger_dates) and isinstance(snapshot, str) and (
                    dt.date.fromisoformat(snapshot) <= dt.date.fromisoformat(trigger_dates[0])
                    <= dt.date.fromisoformat(snapshot) + dt.timedelta(days=7))
            except ValueError:
                trigger_ok = False
        if not trigger_ok:
            reasons.append("seven-day trigger is not explicit")
        if not direct_evidence(evidence.get(candidate_id, [])):
            reasons.append("candidate lacks direct evidence")
    for key in ("fear_source", "growth_upside", "reversible_first_step"):
        if not isinstance(stretch.get(key), str) or not stretch[key].strip():
            reasons.append(f"{key} is absent")
    if not isinstance(stretch.get("safety_constraints"), list) or not stretch["safety_constraints"]:
        reasons.append("safety_constraints are absent")
    return {"status": "PASS" if not reasons else "FAIL", "real_action": not reasons,
            "candidate_id": candidate_id, "reasons": reasons}


def latest_report(run: Path) -> Path:
    attempts: list[tuple[int, Path]] = []
    for path in run.glob("report.attempt-*.result.json"):
        match = re.fullmatch(r"report\.attempt-(\d+)\.result\.json", path.name)
        if match:
            status = run / path.name.replace(".result.json", ".status.json")
            try:
                complete = status.is_file() and read_json(status).get("state") == "complete"
            except (OSError, json.JSONDecodeError):
                complete = False
            if complete:
                attempts.append((int(match.group(1)), path))
    if attempts:
        return max(attempts)[1]
    return run / "report.result.json"


def evaluate(run: Path) -> dict[str, Any]:
    report_path = latest_report(run)
    report = read_json(report_path)
    if not isinstance(report, dict):
        raise ValueError("report.result.json must contain an object")
    validation_path, validation = latest_validation(run)
    local_errors = local_contract_errors(report)
    persisted_valid = isinstance(validation, dict) and validation.get("valid") is True
    persisted_errors = validation.get("errors", []) if isinstance(validation, dict) else []
    schema_errors = [item for item in persisted_errors if isinstance(item, str) and item.startswith("schema:")]

    candidates_list = as_objects(report.get("candidates"))
    candidates = {item["candidate_id"]: item for item in candidates_list if isinstance(item.get("candidate_id"), str)}
    horizon = as_objects(report.get("opportunity_horizon"))
    evidence = evidence_by_candidate(report)
    families: dict[str, str] = {}
    geographies: dict[str, str | None] = {}
    verified_family_ids: set[str] = set()
    for item in horizon:
        candidate_id, family = item.get("candidate_id"), item.get("family")
        if not isinstance(candidate_id, str) or not isinstance(family, str) or not family.strip():
            continue
        normalized = family.strip().lower()
        families[candidate_id] = normalized
        geographic = item.get("geographic_window")
        geographies[candidate_id] = geographic.strip().lower() if isinstance(geographic, str) and geographic.strip() else None
        candidate = candidates.get(candidate_id, {})
        rejected = str(candidate.get("downgrade_or_rejection_reason") or "").lower()
        supports = {support for row in evidence.get(candidate_id, [])
                    if isinstance(row.get("supports"), list) for support in row["supports"]}
        actionable = candidate.get("status") in {"ACT_NOW", "PREPARE_NEXT"}
        temporal = bool({"deadline", "event_date", "rolling_window"} & supports)
        if (direct_evidence(evidence.get(candidate_id, [])) and actionable and temporal
                and not any(word in rejected for word in ("unsupported", "stale", "closed"))):
            verified_family_ids.add(normalized)
    selected = report.get("selected_ids") if isinstance(report.get("selected_ids"), dict) else {}
    action_ids = [item for key in ("act_now", "prepare_next") for item in selected.get(key, []) if isinstance(item, str)]
    all_ids = action_ids + [item for item in selected.get("monitor", []) if isinstance(item, str)]
    hits = geographic_hits(horizon, evidence)

    declared = report.get("weekly_allocation") if isinstance(report.get("weekly_allocation"), dict) else {}
    computed = sum(candidate.get("scheduled_week_effort_minutes", {}).get("max", 0)
                   for candidate_id in action_ids
                   for candidate in [candidates.get(candidate_id, {})]
                   if isinstance(candidate.get("scheduled_week_effort_minutes", {}).get("max"), int))
    monitor_ids = {item.get("candidate_id") for item in candidates_list if item.get("status") == "MONITOR"}
    monitor_ids.update(item for item in selected.get("monitor", []) if isinstance(item, str))
    monitor_violations = []
    for candidate_id in sorted(monitor_ids):
        candidate = candidates.get(candidate_id)
        maximum = candidate.get("scheduled_week_effort_minutes", {}).get("max") if candidate else None
        if not isinstance(maximum, int) or maximum != 0:
            monitor_violations.append({"candidate_id": candidate_id, "scheduled_max_minutes": maximum})

    candidate_uncertainties = [item.get("uncertainties") for item in candidates_list]
    uncertainty_total = sum(len(value) for value in candidate_uncertainties if isinstance(value, list))
    uncertainty_candidates = sum(bool(value) for value in candidate_uncertainties if isinstance(value, list))
    status_counts = Counter(str(item.get("status", "MISSING")) for item in candidates_list)
    action_family = {candidate_id: families.get(candidate_id, str(candidates.get(candidate_id, {}).get("type", "")).lower() or None)
                     for candidate_id in dict.fromkeys(action_ids)}
    action_geography = {candidate_id: geographies.get(candidate_id) for candidate_id in dict.fromkeys(action_ids)}
    all_family = {candidate_id: families.get(candidate_id, str(candidates.get(candidate_id, {}).get("type", "")).lower() or None)
                  for candidate_id in dict.fromkeys(all_ids)}
    all_geography = {candidate_id: geographies.get(candidate_id) for candidate_id in dict.fromkeys(all_ids)}

    return {
        "schema_validity": {
            "report_file": report_path.name,
            "valid": not local_errors and persisted_valid and not schema_errors,
            "local_contract_valid": not local_errors,
            "local_contract_errors": local_errors,
            "production_validation_valid": persisted_valid,
            "production_validation_schema_errors": schema_errors,
            "production_validation_file": validation_path.name if validation_path else None,
        },
        "candidate_and_horizon_counts": {
            "candidates": len(candidates_list), "horizon": len(horizon),
            "candidate_statuses": dict(sorted(status_counts.items())),
        },
        "distinct_families": {
            "horizon": sorted(set(families.values())),
            "horizon_count": len(set(families.values())),
            "verified_actionable": sorted(verified_family_ids),
            "verified_actionable_count": len(verified_family_ids),
        },
        "verified_geographic_windows": {"count": len(hits), "hits": hits},
        "selected_family_geography_duplication": {
            "action_portfolio": {"family": duplicate_groups(action_family), "geography": duplicate_groups(action_geography)},
            "all_selected_including_monitor": {"family": duplicate_groups(all_family), "geography": duplicate_groups(all_geography)},
        },
        "scheduled_effort": {
            "cap_minutes": declared.get("cap_minutes"),
            "declared_max_minutes": declared.get("scheduled_max_minutes"),
            "computed_selected_action_max_minutes": computed,
            "matches_declared": declared.get("scheduled_max_minutes") == computed,
            "within_cap": isinstance(declared.get("cap_minutes"), int) and computed <= declared["cap_minutes"],
        },
        "stretch_real_action_status": stretch_metric(report, candidates, evidence),
        "monitor_effort_violations": {"count": len(monitor_violations), "items": monitor_violations},
        "uncertainty_counts": {
            "report_summary": len(report.get("uncertainty_summary", [])) if isinstance(report.get("uncertainty_summary"), list) else 0,
            "profile_unknowns": len(report.get("profile_state", {}).get("unknowns", [])) if isinstance(report.get("profile_state"), dict) and isinstance(report["profile_state"].get("unknowns"), list) else 0,
            "candidate_uncertainties": uncertainty_total,
            "candidates_with_uncertainties": uncertainty_candidates,
        },
    }


def self_test() -> None:
    """Exercise the resolver and core metrics without external fixtures or calls."""
    report = {
        "snapshot_date": "2026-08-03", "profile_state": {"unknowns": ["budget"]}, "trigger_hypotheses": [],
        "candidates": [
            {"candidate_id": "a", "status": "ACT_NOW", "claim_ids": ["c1"], "first_action": {}, "scheduled_week_effort_minutes": {"min": 10, "max": 20}, "uncertainties": []},
            {"candidate_id": "b", "status": "MONITOR", "claim_ids": ["c2"], "first_action": {}, "scheduled_week_effort_minutes": {"min": 0, "max": 0}, "uncertainties": ["access"]},
        ],
        "selected_ids": {"act_now": ["a"], "prepare_next": [], "monitor": ["b"]},
        "weekly_allocation": {"cap_minutes": 360, "scheduled_max_minutes": 20},
        "evidence_ledger": [
            {"candidate_id": "a", "quote": "date", "url": "https://example.test/a", "retrieved_at": "2026-08-03T00:00:00Z", "entailment": "direct", "supports": ["event_date"]},
            {"candidate_id": "b", "quote": "community", "url": "https://example.test/b", "retrieved_at": "2026-08-03T00:00:00Z", "entailment": "direct", "supports": ["status"]},
        ],
        "rejected_candidates": [], "uncertainty_summary": ["access"],
        "opportunity_horizon": [
            {"candidate_id": "a", "family": "place_event", "geographic_window": "Shanghai 2026-09-06 to 2026-09-10", "event_dates": "2026-09-07 to 2026-09-09"},
            {"candidate_id": "b", "family": "community", "geographic_window": "Cape Town from 2026-09-25", "event_dates": None},
        ],
        "stretch_challenge": {"candidate_id": None},
    }
    with tempfile.TemporaryDirectory() as temporary:
        run = Path(temporary)
        (run / "report.result.json").write_text(json.dumps(report), encoding="utf-8")
        (run / "production_validation.attempt-02.json").write_text(json.dumps({"valid": True, "errors": []}), encoding="utf-8")
        metrics = evaluate(run)
    assert metrics["schema_validity"]["valid"]
    assert metrics["candidate_and_horizon_counts"]["horizon"] == 2
    assert metrics["verified_geographic_windows"]["count"] == 1
    assert metrics["scheduled_effort"]["matches_declared"]
    assert metrics["stretch_real_action_status"]["status"] == "EMPTY"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, help="saved immutable run directory containing report.result.json")
    parser.add_argument("--self-test", action="store_true", help="run the embedded no-network smoke test")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print(json.dumps({"self_test": "PASS"}, sort_keys=True))
        return 0
    if args.run is None:
        parser.error("--run is required unless --self-test is used")
    try:
        print(json.dumps(evaluate(args.run.resolve()), indent=2, sort_keys=True) )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
