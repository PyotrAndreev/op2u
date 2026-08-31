#!/usr/bin/env python3
"""Validate and evaluate the EUSP non-obvious participation-mode fixture.

This deterministic, fixture-only experiment preserves candidate/source provenance.
It does not browse, enrich a profile, infer eligibility, or observe user behaviour.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from run_experiment import ROOT, _schema_errors, read_json

SCHEMA_VERSION = "eusp-participation-mode/v1"
PUBLIC_FIXTURE_NOTICE = ("This is a fabricated, anonymized public evaluation fixture. "
                         "It contains no real person, profile, account, behaviour, or source snapshot.")
READINESS_CHECKS = frozenset({"profile_bridge", "local_deliverable", "seven_day_start", "bounded_effort", "blockers_disclosed"})


def _additional_property_errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Apply the repository's explicit additional-properties check recursively."""
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


def _current_route(evidence: dict[str, Any], snapshot: dt.date) -> bool:
    temporal = evidence.get("temporal")
    if evidence.get("current_status") not in {"open", "upcoming", "rolling"} or not isinstance(temporal, dict):
        return False
    try:
        if temporal.get("kind") in {"deadline", "event"}:
            return dt.date.fromisoformat(temporal["date"]) >= snapshot
        if temporal.get("kind") == "rolling":
            end = temporal.get("end_date")
            return end is None or dt.date.fromisoformat(end) >= snapshot
    except (KeyError, TypeError, ValueError):
        return False
    return False


def _route_evidence(candidate: dict[str, Any], snapshot: dt.date, *, mode_required: bool,
                    current_required: bool = True) -> bool:
    mode = candidate.get("participation_mode")
    mode_id = mode.get("id") if isinstance(mode, dict) else None
    for evidence in candidate.get("evidence", []):
        if not isinstance(evidence, dict):
            continue
        supports = evidence.get("supports", [])
        if (evidence.get("source_type") == "direct_official_primary"
                and evidence.get("url", "").startswith("https://")
                and "participation_route" in supports
                and (not current_required or _current_route(evidence, snapshot))
                and (not mode_required or f"participation_mode:{mode_id}" in supports)):
            return True
    return False


def _frozen_input_sha256(value: dict[str, Any]) -> str:
    """Hash exactly the snapshot and candidate ledger shared by both ranking arms."""
    frozen_input = {"snapshot_date": value.get("snapshot_date"), "candidates": value.get("candidates")}
    return hashlib.sha256(json.dumps(frozen_input, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _gate_eligible(candidate: dict[str, Any], snapshot: dt.date) -> bool:
    gates = candidate.get("gates")
    return (isinstance(gates, dict)
            and all(gates.get(gate) == "pass" for gate in ("grounding", "liveness", "actionability"))
            and _route_evidence(candidate, snapshot, mode_required=candidate["participation_mode"]["non_obvious"]))


def validate_participation_mode(value: Any, *, public_fixture: bool = False) -> list[str]:
    """Return contract violations without claiming that a mode is useful to a user."""
    schema = read_json(ROOT / "evals/schemas/eusp_participation_mode.schema.json")
    errors = _schema_errors(value, schema) + _additional_property_errors(value, schema)
    if not isinstance(value, dict):
        return errors
    if public_fixture:
        if value.get("synthetic") is not True:
            errors.append("public fixture must set synthetic to true")
        if value.get("fixture_notice") != PUBLIC_FIXTURE_NOTICE:
            errors.append("public fixture lacks its explicit fabricated-data notice")

    snapshot = _date(value.get("snapshot_date"), "snapshot_date", errors)
    candidates = value.get("candidates")
    seen: set[str] = set()
    priorities: set[int] = set()
    if isinstance(candidates, list):
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                continue
            identifier = candidate.get("id")
            if isinstance(identifier, str):
                if identifier in seen:
                    errors.append(f"duplicate candidate ID {identifier!r}")
                seen.add(identifier)
            priority = candidate.get("baseline_priority")
            if isinstance(priority, int) and not isinstance(priority, bool):
                if priority in priorities:
                    errors.append("baseline priorities must be unique for a deterministic frozen baseline")
                priorities.add(priority)
            mode = candidate.get("participation_mode")
            if not isinstance(mode, dict):
                continue
            non_obvious = mode.get("non_obvious")
            if snapshot is not None:
                has_direct_route = _route_evidence(candidate, snapshot, mode_required=non_obvious is True,
                                                       current_required=False)
                has_current_route = _route_evidence(candidate, snapshot, mode_required=non_obvious is True)
                gates = candidate.get("gates")
                if isinstance(gates, dict) and gates.get("grounding") == "pass" and not has_direct_route:
                    errors.append(f"grounding-pass candidate {identifier!r} lacks direct official-primary route evidence")
                if isinstance(gates, dict) and gates.get("liveness") == "pass" and not has_current_route:
                    errors.append(f"liveness-pass candidate {identifier!r} lacks a current direct official-primary route")
                if non_obvious is True and not has_direct_route:
                    errors.append(f"non-obvious mode {identifier!r} lacks direct official-primary mode and route evidence")
            for evidence_index, evidence in enumerate(candidate.get("evidence", [])):
                if not isinstance(evidence, dict):
                    continue
                _timestamp(evidence.get("retrieved_at"), f"candidate {identifier!r} evidence[{evidence_index}].retrieved_at", errors)
                temporal = evidence.get("temporal")
                if isinstance(temporal, dict):
                    for key in ("date", "end_date"):
                        if temporal.get(key) is not None:
                            _date(temporal[key], f"candidate {identifier!r} evidence[{evidence_index}].temporal.{key}", errors)
                if public_fixture and isinstance(evidence.get("url"), str) and not evidence["url"].startswith("https://example.test/"):
                    errors.append(f"public fixture evidence for {identifier!r} must use an example.test URL")
            checks = candidate.get("readiness_checks")
            if isinstance(checks, dict) and isinstance(gates, dict) and gates.get("actionability") == "pass":
                if set(checks) != READINESS_CHECKS or not all(checks.values()):
                    errors.append(f"actionability-pass candidate {identifier!r} must pass every readiness check")

    controls = value.get("controls")
    if isinstance(controls, dict):
        baseline, intervention = controls.get("baseline"), controls.get("intervention")
        if isinstance(baseline, dict) and isinstance(intervention, dict):
            for key in ("frozen_input_id", "frozen_input_sha256", "source_research_budget", "report_budget", "action_capacity", "weekly_minutes_cap"):
                if baseline.get(key) != intervention.get(key):
                    errors.append(f"baseline and intervention must use identical {key}")
            expected_hash = _frozen_input_sha256(value)
            for arm_name, arm in (("baseline", baseline), ("intervention", intervention)):
                if arm.get("frozen_input_sha256") != expected_hash:
                    errors.append(f"{arm_name} frozen_input_sha256 does not bind the snapshot and candidate ledger")
    return errors


def _ordered(candidates: list[dict[str, Any]], bonus: int) -> list[dict[str, Any]]:
    return sorted(candidates, key=lambda candidate: (
        -(candidate["baseline_priority"] + (bonus if candidate["participation_mode"]["non_obvious"] else 0)),
        candidate["id"],
    ))


def _mean(selected: list[dict[str, Any]], field: str) -> float:
    return sum(candidate[field] for candidate in selected) / len(selected) if selected else 0.0


def _arm(selected: list[dict[str, Any]], snapshot: dt.date, weekly_minutes_cap: int) -> dict[str, Any]:
    scheduled_minutes = sum(candidate["minutes_max"] for candidate in selected)
    hard_gates = {
        "grounding": all(_route_evidence(candidate, snapshot, mode_required=candidate["participation_mode"]["non_obvious"])
                         for candidate in selected),
        "liveness": all(candidate["gates"]["liveness"] == "pass" for candidate in selected),
        "actionability": all(candidate["gates"]["actionability"] == "pass" for candidate in selected),
        "classification_limits": (sum(candidate["classification"] == "ACT_NOW" for candidate in selected) <= 3
                                  and sum(candidate["classification"] == "PREPARE_NEXT" for candidate in selected) <= 4),
        "weekly_effort": scheduled_minutes <= weekly_minutes_cap,
    }
    return {
        "selected_ids": [candidate["id"] for candidate in selected],
        "selected_route_provenance": [
            {"candidate_id": candidate["id"], "evidence": candidate["evidence"]}
            for candidate in selected
        ],
        "scheduled_minutes": scheduled_minutes,
        "hard_gates": hard_gates,
    }


def evaluate_participation_mode(value: dict[str, Any]) -> dict[str, Any]:
    """Run the frozen-baseline comparison; only the declared mode bonus changes."""
    errors = validate_participation_mode(value)
    if errors:
        raise ValueError("invalid participation-mode fixture: " + "; ".join(errors))
    snapshot = dt.date.fromisoformat(value["snapshot_date"])
    controls = value["controls"]
    capacity = controls["baseline"]["action_capacity"]
    eligible = [candidate for candidate in value["candidates"] if _gate_eligible(candidate, snapshot)]
    baseline = _ordered(eligible, 0)[:capacity]
    bonus = controls["intervention"]["non_obvious_mode_bonus"]
    intervention = _ordered(eligible, bonus)[:capacity]
    baseline_arm = _arm(baseline, snapshot, controls["baseline"]["weekly_minutes_cap"])
    intervention_arm = _arm(intervention, snapshot, controls["intervention"]["weekly_minutes_cap"])

    def novelty(selected: list[dict[str, Any]]) -> float:
        return sum(candidate["participation_mode"]["non_obvious"] for candidate in selected) / len(selected) if selected else 0.0

    metrics = {
        "mode_novelty_proxy": {"baseline": novelty(baseline), "intervention": novelty(intervention)},
        "relevance_proxy": {"baseline": _mean(baseline, "relevance_proxy"), "intervention": _mean(intervention, "relevance_proxy")},
        "grounding_rate": {"baseline": float(baseline_arm["hard_gates"]["grounding"]), "intervention": float(intervention_arm["hard_gates"]["grounding"])},
        "readiness_to_act_proxy": {"baseline": _mean(baseline, "readiness_score"), "intervention": _mean(intervention, "readiness_score")},
    }
    for metric in metrics.values():
        metric["delta"] = metric["intervention"] - metric["baseline"]
    failure = value["failure_condition"]
    failure_reasons = []
    if metrics["mode_novelty_proxy"]["delta"] < failure["minimum_mode_novelty_delta"]:
        failure_reasons.append("mode novelty did not improve by the predeclared minimum")
    for name, threshold in (("relevance_proxy", failure["minimum_relevance_delta"]),
                            ("readiness_to_act_proxy", failure["minimum_readiness_delta"])):
        if metrics[name]["delta"] < threshold:
            failure_reasons.append(f"{name} fell below its non-degradation threshold")
    if metrics["grounding_rate"]["intervention"] < failure["minimum_grounding_rate"]:
        failure_reasons.append("intervention grounding rate fell below the required threshold")
    for arm_name, arm in (("baseline", baseline_arm), ("intervention", intervention_arm)):
        if not all(arm["hard_gates"].values()):
            failure_reasons.append(f"{arm_name} violated a preserved hard gate")
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline": baseline_arm,
        "non_obvious_participation_mode_treatment": intervention_arm,
        "metrics": metrics,
        "failure_condition_met": bool(failure_reasons),
        "failure_reasons": failure_reasons,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="participation-mode fixture JSON")
    parser.add_argument("--public-fixture", action="store_true", help="require the fabricated-data notice")
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    errors = validate_participation_mode(value, public_fixture=args.public_fixture)
    if errors:
        print("invalid EUSP participation-mode fixture:")
        print("\n".join(f"- {error}" for error in errors))
        return 2
    print(json.dumps(evaluate_participation_mode(value), indent=2, sort_keys=True) + "\n", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
