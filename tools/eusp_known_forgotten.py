#!/usr/bin/env python3
"""Validate and evaluate the EUSP local known-versus-forgotten fixture.

This deterministic experiment uses only explicit local, user-supplied awareness
statements. It does not read accounts, browsing history, contacts, calendars,
or behavioural logs, and it never infers awareness from silence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from run_experiment import ROOT, _schema_errors, read_json

SCHEMA_VERSION = "eusp-known-forgotten/v1"
PUBLIC_FIXTURE_NOTICE = ("This is a fabricated, anonymized public evaluation fixture. "
                         "It contains no real person, account, history, contact, calendar, or source snapshot.")


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


def _ids(candidates: Any, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    if not isinstance(candidates, list):
        return seen
    for candidate in candidates:
        identifier = candidate.get("id") if isinstance(candidate, dict) else None
        if not isinstance(identifier, str):
            continue
        if identifier in seen:
            errors.append(f"duplicate candidate ID {identifier!r}")
        seen.add(identifier)
    return seen


def _gate_eligible(candidate: dict[str, Any]) -> bool:
    gates = candidate.get("gates")
    return isinstance(gates, dict) and all(gates.get(gate) == "pass"
                                           for gate in ("grounding", "liveness", "actionability"))


def validate_known_forgotten(value: Any, *, public_fixture: bool = False) -> list[str]:
    """Return contract violations; silence remains the literal ``unknown`` state."""
    schema = read_json(ROOT / "evals/schemas/eusp_known_forgotten.schema.json")
    errors = _schema_errors(value, schema) + _additional_property_errors(value, schema)
    if not isinstance(value, dict):
        return errors
    if public_fixture:
        if value.get("synthetic") is not True:
            errors.append("public fixture must set synthetic to true")
        if value.get("fixture_notice") != PUBLIC_FIXTURE_NOTICE:
            errors.append("public fixture lacks its explicit fabricated-data notice")

    candidates = value.get("candidates")
    candidate_ids = _ids(candidates, errors)
    priorities: set[int] = set()
    forgotten_ids: set[str] = set()
    eligible_forgotten_ids: set[str] = set()
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            identifier = candidate.get("id")
            priority = candidate.get("action_priority")
            if isinstance(priority, int) and not isinstance(priority, bool):
                if priority in priorities:
                    errors.append(f"action_priority {priority!r} is not deterministic; priorities must be unique")
                priorities.add(priority)
            awareness = candidate.get("awareness")
            if not isinstance(awareness, dict):
                continue
            state, evidence = awareness.get("state"), awareness.get("evidence")
            rows = [row for row in evidence if isinstance(row, dict)] if isinstance(evidence, list) else []
            if state == "unknown":
                if evidence != []:
                    errors.append(f"unknown candidate {identifier!r} must have no awareness evidence; do not guess")
            elif state == "known":
                if not rows or any(row.get("kind") != "explicit_current_recognition" for row in rows):
                    errors.append(f"known candidate {identifier!r} needs only explicit current-recognition evidence")
            elif state == "forgotten":
                if not rows or any(row.get("kind") != "explicit_reminder_request" for row in rows):
                    errors.append(f"forgotten candidate {identifier!r} needs only an explicit local reminder request")
                if isinstance(identifier, str):
                    forgotten_ids.add(identifier)
                    if _gate_eligible(candidate):
                        eligible_forgotten_ids.add(identifier)

    evaluation = value.get("evaluation")
    if isinstance(evaluation, dict):
        useful_ids = evaluation.get("reminder_useful_ids")
        if isinstance(useful_ids, list):
            if len(useful_ids) != len(set(useful_ids)):
                errors.append("reminder_useful_ids must be unique")
            for identifier in useful_ids:
                if identifier not in candidate_ids:
                    errors.append(f"reminder usefulness oracle references unknown candidate {identifier!r}")
                elif identifier not in forgotten_ids:
                    errors.append(f"reminder usefulness oracle must reference a forgotten candidate, not {identifier!r}")
                elif identifier not in eligible_forgotten_ids:
                    errors.append(f"reminder usefulness oracle cannot treat a gate-failed candidate as a live reminder: {identifier!r}")
    return errors


def _ordered(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(candidates, key=lambda candidate: (-candidate["action_priority"], candidate["id"]))


def evaluate_known_forgotten(value: dict[str, Any]) -> dict[str, Any]:
    """Run the fixed synthetic comparison without changing action rank or eligibility."""
    errors = validate_known_forgotten(value)
    if errors:
        raise ValueError("invalid known-versus-forgotten fixture: " + "; ".join(errors))
    candidates = value["candidates"]
    evaluation = value["evaluation"]
    eligible = _ordered([candidate for candidate in candidates if _gate_eligible(candidate)])
    capacity = evaluation["action_capacity"]

    # The treatment is deliberately not a score adjustment: both action portfolios
    # are the same eligibility-gated priority ordering. Awareness only projects
    # separate labels/lanes after that selection is fixed.
    baseline_actions = eligible[:capacity]
    treatment_actions = eligible[:capacity]
    novelty = [candidate for candidate in eligible if candidate["awareness"]["state"] == "unknown"]
    reminders = [candidate for candidate in eligible if candidate["awareness"]["state"] == "forgotten"]
    known = [candidate for candidate in eligible if candidate["awareness"]["state"] == "known"]

    threshold = evaluation["high_value_priority_at_least"]
    baseline_high_value_ids = {candidate["id"] for candidate in baseline_actions
                               if candidate["action_priority"] >= threshold}
    treatment_action_ids = {candidate["id"] for candidate in treatment_actions}
    suppressed = sorted(baseline_high_value_ids - treatment_action_ids)
    false_suppression = len(suppressed) / len(baseline_high_value_ids) if baseline_high_value_ids else 0.0

    reminder_ids = {candidate["id"] for candidate in reminders}
    useful_ids = set(evaluation["reminder_useful_ids"])
    true_positive = reminder_ids & useful_ids
    precision = len(true_positive) / len(reminder_ids) if reminder_ids else 0.0
    recall = len(true_positive) / len(useful_ids) if useful_ids else 0.0
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline": {"action_selected_ids": [candidate["id"] for candidate in baseline_actions]},
        "known_reminder_treatment": {
            "action_selected_ids": [candidate["id"] for candidate in treatment_actions],
            "known_label_ids": [candidate["id"] for candidate in known],
            "novelty_lane_ids": [candidate["id"] for candidate in novelty],
            "reminder_lane_ids": [candidate["id"] for candidate in reminders],
        },
        "metrics": {
            "false_suppression_count": len(suppressed),
            "false_suppression_rate": false_suppression,
            "suppressed_high_value_ids": suppressed,
            "reminder_usefulness_proxy": {
                "true_positive_count": len(true_positive),
                "precision": precision,
                "recall": recall,
                "useful_reminder_ids": sorted(true_positive),
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="known-versus-forgotten fixture JSON")
    parser.add_argument("--public-fixture", action="store_true", help="require the fabricated-data notice")
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    errors = validate_known_forgotten(value, public_fixture=args.public_fixture)
    if errors:
        print("invalid EUSP known-versus-forgotten fixture:")
        print("\n".join(f"- {error}" for error in errors))
        return 2
    print(json.dumps(evaluate_known_forgotten(value), indent=2, sort_keys=True) + "\n", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
