#!/usr/bin/env python3
"""Validate and evaluate the EUSP local-unexpectedness ranking fixture.

The treatment can use only exact, user-supplied place/date windows and explicit
local awareness. It never reads or infers location, dates, accounts, social
records, history, or behaviour. It preserves evidence in each selected result.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from run_experiment import ROOT, _schema_errors, read_json

SCHEMA_VERSION = "eusp-local-unexpectedness/v1"
PUBLIC_FIXTURE_NOTICE = ("This is a fabricated, anonymized public evaluation fixture. "
                         "It contains no real person, account, social graph, behavioural history, inferred location, inferred date, or source snapshot.")


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _frozen_input_bundle(value: dict[str, Any]) -> dict[str, Any]:
    """The complete common input/budget surface, excluding arm-specific ranking."""
    frozen = value["frozen_inputs"]
    return {
        "snapshot_date": value["snapshot_date"],
        "supplied_windows": value["supplied_windows"],
        "candidates": value["candidates"],
        "research_budget": frozen["research_budget"],
        "report_budget_minutes": frozen["report_budget_minutes"],
        "selection_capacity": frozen["selection_capacity"],
    }


def _additional_property_errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors.extend(f"{path}: unexpected property {key}" for key in value if key not in properties)
        for key, child in value.items():
            if key in properties and isinstance(properties[key], dict):
                errors.extend(_additional_property_errors(child, properties[key], f"{path}.{key}"))
    elif isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, child in enumerate(value):
            errors.extend(_additional_property_errors(child, schema["items"], f"{path}[{index}]"))
    return errors


def _date(value: Any, label: str, errors: list[str]) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be an ISO date")
        return None


def _timestamp(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        return
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be an ISO date-time")


def _evidence_hash(row: dict[str, Any]) -> str:
    persisted = {key: value for key, value in row.items() if key != "provenance_sha256"}
    return _canonical_hash(persisted)


def _candidate_gate_errors(candidate: dict[str, Any], snapshot: dt.date | None) -> list[str]:
    """Check grounding, liveness, and the local ACT_NOW/PREPARE safeguards."""
    errors: list[str] = []
    evidence = candidate.get("evidence", [])
    by_id = {row.get("id"): row for row in evidence if isinstance(row, dict)}
    for index, row in enumerate(evidence):
        if not isinstance(row, dict):
            continue
        _timestamp(row.get("retrieved_at"), f"candidate {candidate.get('id')!r} evidence[{index}].retrieved_at", errors)
        if row.get("provenance_sha256") != _evidence_hash(row):
            errors.append(f"candidate {candidate.get('id')!r} evidence {row.get('id')!r} has a changed provenance hash")

    required = {"status", "participation_route", "liveness"}
    supported = {support for row in evidence if isinstance(row, dict) for support in row.get("supports", [])}
    missing = required - supported
    if missing:
        errors.append(f"candidate {candidate.get('id')!r} lacks direct evidence for {sorted(missing)}")
    for row in evidence:
        if not isinstance(row, dict):
            continue
        if row.get("source_type") != "official_primary" or row.get("entailment") != "direct":
            errors.append(f"candidate {candidate.get('id')!r} has non-direct official-primary evidence")
        if not isinstance(row.get("quote"), str) or not row["quote"].strip():
            errors.append(f"candidate {candidate.get('id')!r} has an empty evidence quote")
    live_rows = []
    for row in evidence:
        if not isinstance(row, dict) or "liveness" not in row.get("supports", []):
            continue
        temporal = row.get("temporal", {})
        date = _date(temporal.get("date"), f"candidate {candidate.get('id')!r} liveness date", errors) if isinstance(temporal, dict) else None
        if row.get("current_status") in {"open", "upcoming", "rolling"} and date is not None and (snapshot is None or date >= snapshot):
            live_rows.append(row)
    if not live_rows:
        errors.append(f"candidate {candidate.get('id')!r} lacks current source-backed liveness")

    locality = candidate.get("locality", {})
    if isinstance(locality, dict):
        start = _date(locality.get("start_date"), f"candidate {candidate.get('id')!r} locality.start_date", errors)
        end = _date(locality.get("end_date"), f"candidate {candidate.get('id')!r} locality.end_date", errors)
        if start is not None and end is not None and start > end:
            errors.append(f"candidate {candidate.get('id')!r} locality starts after it ends")
        for key, support in (("location_evidence_id", "location"), ("date_evidence_id", "date_window")):
            row = by_id.get(locality.get(key))
            if row is None or support not in row.get("supports", []):
                errors.append(f"candidate {candidate.get('id')!r} locality lacks direct {support} provenance")
        date_row = by_id.get(locality.get("date_evidence_id"))
        if isinstance(date_row, dict) and isinstance(date_row.get("temporal"), dict) and start is not None and end is not None:
            sourced_date = _date(date_row["temporal"].get("date"), f"candidate {candidate.get('id')!r} locality evidence date", errors)
            if start != end or sourced_date != start:
                errors.append(f"candidate {candidate.get('id')!r} locality date is not the exact directly evidenced date")

    action = candidate.get("first_action", {})
    if isinstance(action, dict):
        start = _date(action.get("start_date"), f"candidate {candidate.get('id')!r} first action date", errors)
        minimum, maximum = action.get("minutes_min"), action.get("minutes_max")
        if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
            errors.append(f"candidate {candidate.get('id')!r} first action minutes are reversed")
        if snapshot is not None and start is not None and not snapshot <= start <= snapshot + dt.timedelta(days=7):
            errors.append(f"candidate {candidate.get('id')!r} first action is not startable within seven days")
    return errors


def _unexpected_locally(candidate: dict[str, Any], windows: list[dict[str, Any]]) -> bool:
    """A structural proxy, not a conclusion that a person is surprised or benefits."""
    awareness = candidate["awareness"]
    locality = candidate["locality"]
    if awareness["state"] != "unknown" or awareness["evidence"] != []:
        return False
    start = dt.date.fromisoformat(locality["start_date"])
    end = dt.date.fromisoformat(locality["end_date"])
    return any(locality["place"] == window["place"]
               and dt.date.fromisoformat(window["start_date"]) <= start <= end <= dt.date.fromisoformat(window["end_date"])
               for window in windows)


def validate_local_unexpectedness(value: Any, *, public_fixture: bool = False) -> list[str]:
    """Return deterministic contract violations before calculating a result."""
    schema = read_json(ROOT / "evals/schemas/eusp_local_unexpectedness.schema.json")
    errors = _schema_errors(value, schema) + _additional_property_errors(value, schema)
    if not isinstance(value, dict):
        return errors
    if public_fixture:
        if value.get("synthetic") is not True:
            errors.append("public fixture must set synthetic to true")
        if value.get("fixture_notice") != PUBLIC_FIXTURE_NOTICE:
            errors.append("public fixture lacks its explicit fabricated-data notice")
    snapshot = _date(value.get("snapshot_date"), "snapshot_date", errors)
    windows = value.get("supplied_windows")
    candidates = value.get("candidates")
    if not isinstance(windows, list) or not isinstance(candidates, list):
        return errors
    window_ids: set[str] = set()
    for window in windows:
        if not isinstance(window, dict):
            continue
        identifier = window.get("id")
        if identifier in window_ids:
            errors.append(f"duplicate supplied window {identifier!r}")
        window_ids.add(identifier)
        start = _date(window.get("start_date"), f"supplied window {identifier!r} start_date", errors)
        end = _date(window.get("end_date"), f"supplied window {identifier!r} end_date", errors)
        if start is not None and end is not None and start > end:
            errors.append(f"supplied window {identifier!r} starts after it ends")
    candidate_ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        identifier = candidate.get("id")
        if identifier in candidate_ids:
            errors.append(f"duplicate candidate ID {identifier!r}")
        candidate_ids.add(identifier)
        awareness = candidate.get("awareness")
        if isinstance(awareness, dict):
            state, evidence = awareness.get("state"), awareness.get("evidence")
            if state == "unknown" and evidence != []:
                errors.append(f"unknown candidate {identifier!r} must have no awareness evidence; silence is not a guess")
            if state == "known" and (not evidence or any(row.get("kind") != "explicit_current_recognition" for row in evidence if isinstance(row, dict))):
                errors.append(f"known candidate {identifier!r} needs explicit current-recognition evidence")
            if state == "forgotten" and (not evidence or any(row.get("kind") != "explicit_reminder_request" for row in evidence if isinstance(row, dict))):
                errors.append(f"forgotten candidate {identifier!r} needs an explicit local reminder request")
        errors.extend(_candidate_gate_errors(candidate, snapshot))
    frozen = value.get("frozen_inputs")
    if isinstance(frozen, dict):
        if frozen.get("candidate_set_sha256") != _canonical_hash(candidates):
            errors.append("frozen candidate-set hash does not bind the exact ranked inputs")
        bundle_keys = {"research_budget", "report_budget_minutes", "selection_capacity"}
        if bundle_keys.issubset(frozen) and all(key in value for key in ("snapshot_date", "supplied_windows", "candidates")):
            if frozen.get("input_bundle_sha256") != _canonical_hash(_frozen_input_bundle(value)):
                errors.append("frozen input-bundle hash does not bind the identical inputs and budgets")
    baseline, treatment = value.get("baseline"), value.get("treatment")
    if isinstance(frozen, dict) and isinstance(baseline, dict) and isinstance(treatment, dict):
        if baseline.get("selection_capacity") != frozen.get("selection_capacity") or treatment.get("selection_capacity") != frozen.get("selection_capacity"):
            errors.append("baseline and treatment must use the identical frozen selection capacity")
        if baseline.get("ranking_rule") != "frozen_base_rank_descending" or baseline.get("local_unexpectedness_bonus") != 0:
            errors.append("baseline must be the frozen rank with no local-unexpectedness signal")
        if treatment.get("ranking_rule") != "frozen_base_rank_descending_plus_local_unexpectedness" or not treatment.get("local_unexpectedness_bonus", 0) > 0:
            errors.append("treatment may change only by adding a positive local-unexpectedness signal")
    return errors


def _rank(value: dict[str, Any], arm: dict[str, Any]) -> list[dict[str, Any]]:
    bonus = arm["local_unexpectedness_bonus"]
    windows = value["supplied_windows"]
    rows = []
    for candidate in value["candidates"]:
        unexpectedness_proxy = _unexpected_locally(candidate, windows)
        score = candidate["base_rank"] + (bonus if unexpectedness_proxy else 0)
        rows.append({"candidate": candidate, "ranking_score": score, "local_unexpectedness_proxy": unexpectedness_proxy})
    return sorted(rows, key=lambda row: (-row["ranking_score"], -row["candidate"]["base_rank"], row["candidate"]["id"]))[:arm["selection_capacity"]]


def _selected_projection(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep exact candidate evidence and its immutable provenance hashes in the output."""
    return [{"candidate_id": row["candidate"]["id"], "classification": row["candidate"]["classification"],
             "ranking_score": row["ranking_score"], "local_unexpectedness_proxy": row["local_unexpectedness_proxy"],
             "relevance_proxy": row["candidate"]["relevance_proxy"], "first_action": copy.deepcopy(row["candidate"]["first_action"]),
             "evidence": copy.deepcopy(row["candidate"]["evidence"])} for row in rows]


def _metrics(selected: list[dict[str, Any]]) -> dict[str, float | int]:
    count = len(selected)
    readiness_rows = [row for row in selected if row["classification"] == "ACT_NOW" and row["first_action"]["blockers"]]
    return {
        "selected_count": count,
        "local_unexpectedness_novelty_count": sum(row["local_unexpectedness_proxy"] for row in selected),
        "local_unexpectedness_novelty_rate": (sum(row["local_unexpectedness_proxy"] for row in selected) / count) if count else 0.0,
        "mean_relevance_proxy": (sum(row["relevance_proxy"] for row in selected) / count) if count else 0.0,
        "grounding_rate": 1.0,
        "readiness_to_act_proxy": (100.0 * len(readiness_rows) / count) if count else 0.0,
    }


def evaluate_local_unexpectedness(value: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen control and the one-signal treatment on identical inputs/budgets."""
    errors = validate_local_unexpectedness(value)
    if errors:
        raise ValueError("invalid local-unexpectedness fixture: " + "; ".join(errors))
    baseline = _selected_projection(_rank(value, value["baseline"]))
    treatment = _selected_projection(_rank(value, value["treatment"]))
    baseline_metrics, treatment_metrics = _metrics(baseline), _metrics(treatment)
    conditions = value["failure_conditions"]
    failures = []
    if treatment_metrics["local_unexpectedness_novelty_count"] - baseline_metrics["local_unexpectedness_novelty_count"] < conditions["minimum_novelty_count_increase"]:
        failures.append("novelty increase is below the preregistered minimum")
    if treatment_metrics["mean_relevance_proxy"] < baseline_metrics["mean_relevance_proxy"]:
        failures.append("relevance proxy decreased")
    for arm, metrics in (("baseline", baseline_metrics), ("treatment", treatment_metrics)):
        if metrics["grounding_rate"] != 1.0:
            failures.append(f"{arm} grounding is not complete")
        if metrics["readiness_to_act_proxy"] != 100.0:
            failures.append(f"{arm} readiness-to-act safeguard is not complete")
    return {
        "schema_version": SCHEMA_VERSION,
        "frozen_input_sha256": value["frozen_inputs"]["input_bundle_sha256"],
        "shared_budgets": copy.deepcopy(value["frozen_inputs"]),
        "baseline": {"id": value["baseline"]["id"], "selected": baseline, "metrics": baseline_metrics},
        "treatment": {"id": value["treatment"]["id"], "selected": treatment, "metrics": treatment_metrics},
        "failure_conditions": copy.deepcopy(conditions),
        "failure_condition_met": bool(failures),
        "failure_reasons": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="local-unexpectedness fixture JSON")
    parser.add_argument("--public-fixture", action="store_true", help="require the fabricated-data notice")
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    errors = validate_local_unexpectedness(value, public_fixture=args.public_fixture)
    if errors:
        print("invalid EUSP local-unexpectedness fixture:")
        print("\n".join(f"- {error}" for error in errors))
        return 2
    print(json.dumps(evaluate_local_unexpectedness(value), indent=2, sort_keys=True) + "\n", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
