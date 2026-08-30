#!/usr/bin/env python3
"""Blind, saved-artifact A/B comparisons for immutable experiment runs."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import random
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from run_experiment import (ALL_ROLES, MODELS, ROLES, ROOT, append_jsonl, atomic_write, call_pi,
                            completed_result, cost_record, jdump, latest_versioned_artifact, read_json, remaining, sha256_file,
                            status_for, utcnow, write_json)


# The shared P1 report contract reserves a complete non-job taxonomy. `other`
# keeps genuinely atypical opportunities eligible, but unrecognized encodings
# cannot masquerade as jobs outside the direction's exact allow-list.
NON_JOB_OPPORTUNITY_TYPES = frozenset({
    "grant", "fellowship", "cfp", "community", "research_collaboration",
    "residency", "accelerator", "travel_support", "other",
})


def sanitize(value: Any, secrets: list[str]) -> Any:
    """Remove run/variant/model/path identifiers before they ever enter a judge prompt."""
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[redacted]")
        value = re.sub(r"\bV[0-7]\b", "[redacted]", value)
        value = re.sub(r"(?:openai-codex/)?gpt-5\.6-(?:luna|terra)", "[redacted]", value, flags=re.I)
        return value
    if isinstance(value, list):
        return [sanitize(item, secrets) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, secrets) for key, item in value.items()
                if key not in {"run_id", "variant", "model", "path", "generation", "repeat", "parent_run_ids"}}
    return value


def _packet_validation_path(packet: Path) -> Path:
    return packet.with_name(packet.name.replace("judge_packet", "judge_packet_validation", 1))


def validate_eusp_p1_manifests(left: dict[str, Any], right: dict[str, Any]) -> None:
    """P1 is only the current-prompt frontier against the one-shot web baseline."""
    expected = {
        "P1_FRONTIER": {"pipeline_mode": "staged", "stages": ["profile", "triggers", "search_plan", "discovery", "verification", "actionability", "ranking", "report"]},
        "P1_V0": {"pipeline_mode": "monolithic", "stages": ["report"]},
    }
    variants = {left.get("variant"), right.get("variant")}
    if variants != set(expected):
        raise ValueError("eusp-p1 requires exactly P1_FRONTIER and P1_V0 manifests")
    for manifest in (left, right):
        contract = expected[manifest["variant"]]
        if manifest.get("pipeline_mode") != contract["pipeline_mode"] or manifest.get("stages") != contract["stages"]:
            raise ValueError(f"eusp-p1 manifest does not match the required {manifest['variant']} arm")


def load_candidate(run: Path, target: str, protocol: str = "standard") -> tuple[dict[str, Any], dict[str, Any], str, Path]:
    manifest = read_json(run / "manifest.json")
    rubric = run / "inputs/rubric.yaml"
    if protocol == "eusp-p1":
        packet = latest_versioned_artifact(run, "judge_packet")
        report = completed_result(run, "report")
        summary = latest_versioned_artifact(run, "summary")
        if target != "judge_packet" or packet is None or report is None or summary is None or not rubric.is_file():
            raise FileNotFoundError(f"{run} needs a complete report, bound judge packet, summary, and inputs/rubric.yaml for eusp-p1")
        diagnostics_path = _packet_validation_path(packet)
        if not diagnostics_path.is_file():
            raise ValueError(f"{run} judge packet has no matching validation diagnostics")
        diagnostics = read_json(diagnostics_path)
        if (not isinstance(diagnostics, dict) or diagnostics.get("valid") is not True
                or diagnostics.get("report_sha256") != sha256_file(report)
                or diagnostics.get("packet_sha256") != sha256_file(packet)):
            raise ValueError(f"{run} judge packet is invalid or not bound to its completed report")
        saved_summary = read_json(summary)
        if not isinstance(saved_summary, dict) or saved_summary.get("state") != "complete":
            raise ValueError(f"{run} is not a complete P1 run")
        return manifest, read_json(packet), rubric.read_text(encoding="utf-8"), packet
    result = completed_result(run, target)
    if result is None or not rubric.is_file():
        raise FileNotFoundError(f"{run} needs a completed saved {target} artifact and inputs/rubric.yaml")
    artifacts: dict[str, Any] = {target: read_json(result)}
    # Evaluation can use persisted evidence/ranking, but never launches research.
    for stage in ("verification", "actionability", "ranking"):
        file = completed_result(run, stage)
        if file is not None and stage != target:
            artifacts[stage] = read_json(file)
    validation = latest_versioned_artifact(run, "production_validation")
    if validation is not None:
        artifacts["production_validation"] = read_json(validation)
    return manifest, artifacts, rubric.read_text(encoding="utf-8"), result


def require_eusp_p1_snapshots(left: Path, right: Path) -> None:
    """P1 comparisons are valid only for exactly the same saved evaluation inputs."""
    for relative in ("inputs/profile.md", "inputs/direction.yaml", "inputs/rubric.yaml"):
        left_file, right_file = left / relative, right / relative
        if not left_file.is_file() or not right_file.is_file():
            raise FileNotFoundError(f"P1 comparison requires both saved snapshots: {relative}")
        if left_file.read_bytes() != right_file.read_bytes():
            raise ValueError(f"runs have different saved {relative} snapshots; comparison would be confounded")


def pair_prompt(role: str, entries: dict[str, Any], rubric: str) -> str:
    return f"""You are the {role} member of a blinded A/B evaluation panel.
This is judging only: do NOT research, browse, add outside facts, or infer identity from missing
metadata. Use exclusively these anonymized saved artifacts and the rubric. Compare A and B.
Return ONLY one JSON object with judge_role, winner (A|B|tie), scores (object with A and B),
hard_failures (object with A and B arrays), reasons (array), failure_tags (array), and confidence (0..1).
Do not mention variants, run IDs, models, or paths.
RUBRIC:\n{rubric}\nANONYMIZED ARTIFACTS:\n{jdump(entries)}"""


def eusp_p1_pair_prompt(entries: dict[str, Any], rubric: str) -> str:
    return f"""You are the readiness member of a blinded EUSP priority-1 A/B panel.
Judge only the two treatment-neutral packets below. Do not research, browse, add facts, infer
identity, or use any information not present in the packets and rubric. Evaluate hard gates first.
Grounding fails unless every selected status, timing, and participation-route material claim ID
is explicitly mapped to direct official-primary evidence with an exact quote, HTTPS URL, and retrieval
time. Liveness fails for every selected ACT_NOW and PREPARE_NEXT item when any mapped material
source is stale, closed, expired, or lacks source-backed current/open status and current timing.
Record every limits/effort, seven-day-action, and job-policy failure in other_hard_gate_failures.
For each selected candidate, assess five equal checks: explicit profile bridge; atomic verb-led,
user-controlled action; tangible deliverable; startable within seven days without reply, eligibility,
or acceptance; and bounded effort with disclosed blockers/unknowns. Score each portfolio as the
mean selected-item score from 0 to 100, or 0 when empty. A failed hard gate makes an arm ineligible.
Return ONLY this JSON shape:
{{"judge_role":"readiness","arms":{{"A":{{"grounding_gate":"pass|fail","liveness_gate":"pass|fail","other_hard_gate_failures":[],"per_candidate_readiness":[{{"candidate_id":"c1","explicit_profile_bridge":true,"atomic_user_controlled_action":true,"tangible_deliverable":true,"startable_within_7_days":true,"bounded_effort_and_disclosed_blockers":true}}],"portfolio_readiness_to_act":0}},"B":{{"grounding_gate":"pass|fail","liveness_gate":"pass|fail","other_hard_gate_failures":[],"per_candidate_readiness":[],"portfolio_readiness_to_act":0}}}},"winner":"A|B|tie","reasons":[]}}
The comparison runner, not you, applies eligibility and the five-point tie margin.
RUBRIC:\n{rubric}\nANONYMIZED PACKETS:\n{jdump(entries)}"""


def persist(folder: Path, name: str, input_data: dict[str, Any], prompt: str, call: dict[str, Any],
            comparison_id: str, model: str) -> dict[str, Any]:
    atomic_write(folder / f"{name}.prompt.txt", prompt)
    write_json(folder / f"{name}.input.json", input_data)
    atomic_write(folder / f"{name}.stdout.txt", call["stdout"])
    atomic_write(folder / f"{name}.stderr.txt", call["stderr"])
    write_json(folder / f"{name}.call.json", {key: call[key] for key in ("started_at", "duration_seconds", "exit_code", "parse_error", "usage", "command")})
    status = status_for(call)
    if call["result"] is not None:
        write_json(folder / f"{name}.result.json", call["result"])
    write_json(folder / f"{name}.status.json", status)
    append_jsonl(folder / "costs.jsonl", cost_record(comparison_id, name, "pairwise_judge", model, call))
    return status


def parse_winner(path: Path) -> str | None:
    if not path.is_file():
        return None
    value = read_json(path)
    if isinstance(value, dict):
        winner = value.get("winner", value.get("verdict"))
        return winner if winner in {"A", "B", "tie"} else None
    return None


def _iso_date(value: Any) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


MATERIAL_CLAIM_KINDS = frozenset({"status", "timing", "participation_route"})
TEMPORAL_CLAIM_KINDS = frozenset({"deadline", "event_date", "rolling_window"})
CURRENT_STATUSES = frozenset({"open", "current", "active"})


def _current_status(row: dict[str, Any]) -> bool:
    return str(row.get("current_status", "")).strip().lower() in CURRENT_STATUSES


def _temporal_is_current(row: dict[str, Any], snapshot: dt.date) -> bool:
    """Evaluate a source's dated window without silently treating absent time as current."""
    temporal = row.get("temporal")
    if not isinstance(temporal, dict):
        return False
    kind = temporal.get("kind")
    if kind in {"deadline", "event_date"}:
        date = _iso_date(temporal.get("date"))
        return date is not None and snapshot <= date
    if kind == "rolling_window":
        start, end = _iso_date(temporal.get("start_date")), _iso_date(temporal.get("end_date"))
        return start is not None and end is not None and start <= snapshot <= end
    return False



def _direct_official_primary(row: Any, candidate_id: Any) -> bool:
    return (isinstance(row, dict) and row.get("candidate_ref") == candidate_id
            and row.get("source_type") == "official_primary" and row.get("entailment") == "direct"
            and isinstance(row.get("quote"), str) and bool(row["quote"].strip())
            and isinstance(row.get("url"), str) and row["url"].startswith("https://")
            and isinstance(row.get("retrieved_at"), str) and bool(row["retrieved_at"].strip()))


def _material_claim_mappings(candidate: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], bool]:
    """Return explicit material-claim-to-evidence maps, rejecting partial links."""
    claims = candidate.get("material_claims")
    if not isinstance(claims, list):
        return {}, False
    mapped: dict[str, list[dict[str, Any]]] = {}
    claim_ids: set[str] = set()
    valid = True
    for claim in claims:
        if not isinstance(claim, dict):
            valid = False
            continue
        claim_id, kind, evidence_ids = claim.get("id"), claim.get("kind"), claim.get("evidence_ids")
        if (not isinstance(claim_id, str) or not claim_id or claim_id in claim_ids
                or kind not in MATERIAL_CLAIM_KINDS or not isinstance(evidence_ids, list)
                or not evidence_ids or len(evidence_ids) != len(set(evidence_ids))
                or not all(isinstance(evidence_id, str) for evidence_id in evidence_ids)):
            valid = False
            continue
        claim_ids.add(claim_id)
        rows = [evidence_by_id.get(evidence_id) for evidence_id in evidence_ids]
        if any(not _direct_official_primary(row, candidate.get("id")) for row in rows):
            valid = False
            continue
        direct_rows = [row for row in rows if isinstance(row, dict)]
        if kind == "status":
            supports_kind = all(isinstance(row.get("supports"), list) and "status" in row["supports"]
                                for row in direct_rows)
        elif kind == "timing":
            supports_kind = all(isinstance(row.get("supports"), list)
                                and isinstance(row.get("temporal"), dict)
                                and row["temporal"].get("kind") in TEMPORAL_CLAIM_KINDS
                                and row["temporal"]["kind"] in row["supports"]
                                for row in direct_rows)
        else:
            supports_kind = all(isinstance(row.get("supports"), list) and "participation_route" in row["supports"]
                                for row in direct_rows)
        if not supports_kind:
            valid = False
            continue
        mapped.setdefault(kind, []).extend(direct_rows)
    return mapped, valid and set(mapped) == MATERIAL_CLAIM_KINDS


def evaluate_eusp_p1_packet(packet: Any) -> dict[str, Any]:
    """Fail closed on packet-verifiable P1 gates and score observable readiness fields."""
    if not isinstance(packet, dict):
        return {"grounding_gate": "fail", "liveness_gate": "fail", "other_hard_gate_failures": ["invalid judge packet"],
                "per_candidate_readiness": [], "portfolio_readiness_to_act": 0.0}
    context = packet.get("evaluation_context", {})
    direction = context.get("direction", {}) if isinstance(context, dict) else {}
    snapshot = _iso_date(context.get("snapshot_date") if isinstance(context, dict) else None)
    portfolio = packet.get("portfolio", {})
    selected = portfolio.get("selected", []) if isinstance(portfolio, dict) else []
    allocation = portfolio.get("weekly_allocation", {}) if isinstance(portfolio, dict) else {}
    selected = selected if isinstance(selected, list) else []
    evidence = packet.get("evidence", []) if isinstance(packet.get("evidence"), list) else []
    evidence_by_id = {row.get("id"): row for row in evidence if isinstance(row, dict) and isinstance(row.get("id"), str)}
    grounding_fail = False
    liveness_fail = snapshot is None
    other: list[str] = []
    ids = [item.get("id") for item in selected if isinstance(item, dict)]
    if len(ids) != len(selected) or any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
        other.append("selected candidate IDs are missing or duplicate")
    act_now = [item for item in selected if isinstance(item, dict) and item.get("classification") == "ACT_NOW"]
    prepare = [item for item in selected if isinstance(item, dict) and item.get("classification") == "PREPARE_NEXT"]
    if any(not isinstance(item, dict) or item.get("classification") not in {"ACT_NOW", "PREPARE_NEXT"}
           or item.get("reported_classification") != item.get("classification") for item in selected):
        other.append("selected classification missing or conflicts with selected-ID bucket")
    if len(act_now) > (direction.get("max_act_now") if isinstance(direction.get("max_act_now"), int) else -1):
        other.append("ACT_NOW limit exceeded")
    if len(prepare) > (direction.get("max_prepare_next") if isinstance(direction.get("max_prepare_next"), int) else -1):
        other.append("PREPARE_NEXT limit exceeded")
    cap = direction.get("max_scheduled_minutes_per_week") if isinstance(direction.get("max_scheduled_minutes_per_week"), int) else None
    scheduled = allocation.get("scheduled_max_minutes") if isinstance(allocation, dict) else None
    if cap is None or type(scheduled) is not int or scheduled < 0 or scheduled > cap:
        other.append("weekly effort limit missing or exceeded")
    days = direction.get("first_action_within_days") if isinstance(direction.get("first_action_within_days"), int) else None
    first_cap = direction.get("first_action_max_minutes") if isinstance(direction.get("first_action_max_minutes"), int) else None
    allowed_jobs = set(direction.get("allowed_job_types", [])) if isinstance(direction.get("allowed_job_types"), list) else set()
    excluded_jobs = set(direction.get("excluded_job_types", [])) if isinstance(direction.get("excluded_job_types"), list) else set()
    checks: list[dict[str, Any]] = []
    for candidate in selected:
        if not isinstance(candidate, dict):
            grounding_fail = True
            continue
        evidence_ids = candidate.get("evidence_ids")
        rows = [evidence_by_id.get(eid) for eid in evidence_ids if isinstance(eid, str)] if isinstance(evidence_ids, list) else []
        if (not rows or not isinstance(evidence_ids, list) or len(rows) != len(evidence_ids)
                or any(not _direct_official_primary(row, candidate.get("id")) for row in rows)):
            grounding_fail = True
        material_rows, material_mapping_ok = _material_claim_mappings(candidate, evidence_by_id)
        if not material_mapping_ok:
            grounding_fail = True
        # Selection is live only while every material source is current and every
        # timing claim remains in its source-backed window. This applies equally to
        # ACT_NOW and PREPARE_NEXT; a closed, stale, or expired selection cannot be
        # promoted merely because it was placed in the latter bucket.
        all_material_rows = [row for kind in MATERIAL_CLAIM_KINDS for row in material_rows.get(kind, [])]
        if (snapshot is None or not material_mapping_ok or not all_material_rows
                or any(not _current_status(row) for row in all_material_rows)
                or any(isinstance(row.get("temporal"), dict)
                       and row["temporal"].get("kind") in TEMPORAL_CLAIM_KINDS
                       and not _temporal_is_current(row, snapshot)
                       for row in all_material_rows)
                or not all(_temporal_is_current(row, snapshot) for row in material_rows.get("timing", []))):
            liveness_fail = True
        bridge = candidate.get("profile_bridge")
        bridge_ok = isinstance(bridge, list) and any(isinstance(item, dict) and isinstance(item.get("signal"), str) and item["signal"].strip()
                                                       and isinstance(item.get("why"), str) and item["why"].strip() for item in bridge)
        first = candidate.get("first_action") if isinstance(candidate.get("first_action"), dict) else {}
        action = first.get("action") if isinstance(first.get("action"), str) else ""
        action_ok = bool(re.match(r"^[A-Za-z]+\b", action.strip())) and not action.strip().lower().startswith(("wait", "monitor", "check later"))
        deliverable_ok = isinstance(first.get("deliverable"), str) and bool(first["deliverable"].strip())
        start = first.get("start_by_or_trigger") if isinstance(first.get("start_by_or_trigger"), str) else ""
        start_date = _iso_date(first.get("start_date"))
        minutes_min, minutes_max = first.get("minutes_min"), first.get("minutes_max")
        seven_day_ok = (snapshot is not None and days is not None and days >= 0 and start_date is not None
                        and snapshot <= start_date <= snapshot + dt.timedelta(days=days)
                        and bool(start.strip()) and not any(word in start.lower() for word in ("reply", "eligibility", "acceptance"))
                        and type(minutes_min) is int and type(minutes_max) is int
                        and 0 <= minutes_min <= minutes_max and first_cap is not None and minutes_max <= first_cap)
        effort = candidate.get("scheduled_week_effort_minutes") if isinstance(candidate.get("scheduled_week_effort_minutes"), dict) else {}
        bounded_ok = (type(effort.get("min")) is int and type(effort.get("max")) is int
                      and 0 <= effort["min"] <= effort["max"]
                      and candidate.get("blockers_disclosed") is True
                      and candidate.get("uncertainties_disclosed") is True)
        if not (action_ok and deliverable_ok and seven_day_ok):
            other.append(f"selected item lacks a bounded seven-day user-controlled action: {candidate.get('id')}")
        item_type = candidate.get("type")
        # A job is valid only under its exact direction-listed type. Non-job
        # opportunities remain valid under the shared non-job taxonomy; every
        # other encoding fails closed rather than bypassing the job policy.
        job_type_allowed = (isinstance(item_type, str) and item_type in allowed_jobs
                            and direction.get("jobs_explicitly_requested") is True)
        non_job_type_allowed = isinstance(item_type, str) and item_type in NON_JOB_OPPORTUNITY_TYPES
        if (not isinstance(item_type, str) or item_type in excluded_jobs
                or not (job_type_allowed or non_job_type_allowed)):
            other.append(f"job-policy failure: {candidate.get('id')}")
        checks.append({"candidate_id": candidate.get("id"), "explicit_profile_bridge": bridge_ok,
                       "atomic_user_controlled_action": action_ok, "tangible_deliverable": deliverable_ok,
                       "startable_within_7_days": seven_day_ok,
                       "bounded_effort_and_disclosed_blockers": bounded_ok})
    score = sum(sum(bool(value) for key, value in row.items() if key != "candidate_id") * 20 for row in checks) / len(checks) if checks else 0.0
    return {"grounding_gate": "fail" if grounding_fail else "pass", "liveness_gate": "fail" if liveness_fail else "pass",
            "other_hard_gate_failures": other, "per_candidate_readiness": checks,
            "selected_candidate_ids": ids, "portfolio_readiness_to_act": score}


def eusp_p1_outcome(value: Any, preflight: dict[str, dict[str, Any]] | None = None) -> tuple[str, dict[str, Any]]:
    """Apply P1's gate-first rule; never trust a model winner over its own gates."""
    if (not isinstance(value, dict) or value.get("judge_role") != "readiness" or not isinstance(value.get("arms"), dict)
            or value.get("winner") not in {"A", "B", "tie"}
            or not isinstance(value.get("reasons"), list) or not all(isinstance(item, str) for item in value["reasons"])):
        return "invalid", {"reason": "invalid readiness result"}
    arms = value["arms"]
    eligible: dict[str, bool] = {}
    scores: dict[str, float] = {}
    for label in ("A", "B"):
        arm = arms.get(label)
        if not isinstance(arm, dict):
            return "invalid", {"reason": f"missing arm {label}"}
        score = arm.get("portfolio_readiness_to_act")
        failures = arm.get("other_hard_gate_failures")
        readiness = arm.get("per_candidate_readiness")
        readiness_keys = {"candidate_id", "explicit_profile_bridge", "atomic_user_controlled_action",
                          "tangible_deliverable", "startable_within_7_days", "bounded_effort_and_disclosed_blockers"}
        if (not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100
                or not isinstance(failures, list) or not all(isinstance(item, str) for item in failures)
                or not isinstance(readiness, list)
                or any(not isinstance(item, dict) or not readiness_keys <= set(item)
                       or not isinstance(item["candidate_id"], str)
                       or any(not isinstance(item[key], bool) for key in readiness_keys - {"candidate_id"})
                       for item in readiness)
                or arm.get("grounding_gate") not in {"pass", "fail"}
                or arm.get("liveness_gate") not in {"pass", "fail"}):
            return "invalid", {"reason": f"invalid arm {label}"}
        preflight_arm = (preflight or {}).get(label, {})
        preflight_failures = preflight_arm.get("other_hard_gate_failures", []) if isinstance(preflight_arm, dict) else []
        selected_ids = preflight_arm.get("selected_candidate_ids", []) if isinstance(preflight_arm, dict) else []
        if not isinstance(selected_ids, list) or not all(isinstance(item, str) for item in selected_ids):
            return "invalid", {"reason": f"invalid selected-candidate binding for arm {label}"}
        judged_ids = [item["candidate_id"] for item in readiness]
        if (len(judged_ids) != len(set(judged_ids)) or set(judged_ids) != set(selected_ids)
                or len(selected_ids) != len(set(selected_ids))):
            return "invalid", {"reason": f"readiness rows do not exactly match selected candidates for arm {label}"}
        recomputed = (sum(sum(item[key] for key in readiness_keys - {"candidate_id"}) * 20 for item in readiness) / len(readiness)
                      if readiness else 0.0)
        if not math.isclose(float(score), recomputed, rel_tol=0.0, abs_tol=1e-9):
            return "invalid", {"reason": f"readiness score does not equal five-check mean for arm {label}"}
        scores[label] = recomputed
        eligible[label] = (arm["grounding_gate"] == "pass" and arm["liveness_gate"] == "pass" and not failures
                           and preflight_arm.get("grounding_gate", "pass") == "pass"
                           and preflight_arm.get("liveness_gate", "pass") == "pass" and not preflight_failures)
    if eligible["A"] != eligible["B"]:
        winner = "A" if eligible["A"] else "B"
    elif not eligible["A"]:
        winner = "tie"
    elif abs(scores["A"] - scores["B"]) < 5:
        winner = "tie"
    else:
        winner = "A" if scores["A"] > scores["B"] else "B"
    return winner, {"eligibility": eligible, "readiness_scores": scores,
                    "model_winner": value.get("winner"), "applied_winner": winner,
                    "packet_preflight": preflight or {}}


def eusp_p1_promotion(calls: list[dict[str, Any]], pair_results: list[dict[str, Any]],
                      repeats: int) -> dict[str, Any] | None:
    """Return a promotion only when every paired call remains gate-eligible."""
    all_eligible = all(
        all(call.get("p1_decision", {}).get("eligibility", {}).get(label) is True for label in ("A", "B"))
        for call in calls
    )
    stable = [result.get("stable_pairwise_winner") for result in pair_results]
    if (all_eligible and len(pair_results) == repeats
            and all(winner in {"left", "right"} for winner in stable)
            and len(set(stable)) == 1):
        return {"winner": stable[0], "paired_repeats": repeats, "order_stable": True}
    return None


def run(args: argparse.Namespace) -> int:
    if args.protocol == "eusp-p1":
        if args.target != "judge_packet":
            raise SystemExit("eusp-p1 requires --target judge_packet")
        if args.roles != ["readiness"]:
            raise SystemExit("eusp-p1 requires --roles readiness")
        if args.repeats < 2:
            raise SystemExit("eusp-p1 requires at least two paired repeats")
    left_path, right_path = Path(args.a).resolve(), Path(args.b).resolve()
    if args.protocol == "eusp-p1":
        require_eusp_p1_snapshots(left_path, right_path)
    left_manifest, left, left_rubric, left_input = load_candidate(left_path, args.target, args.protocol)
    right_manifest, right, right_rubric, right_input = load_candidate(right_path, args.target, args.protocol)
    if args.protocol == "eusp-p1":
        validate_eusp_p1_manifests(left_manifest, right_manifest)
    if left_rubric != right_rubric:
        raise SystemExit("runs have different saved rubric snapshots; comparison would be confounded")
    comparison_id = f"compare-{utcnow().replace(':', '').replace('+00:00', 'Z')}-{uuid.uuid4().hex[:10]}"
    folder = Path(args.output_dir).resolve() / comparison_id
    folder.mkdir(parents=True, exist_ok=False)
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**63)
    rng = random.Random(seed)
    candidates = {"left": (left_path, left_manifest, left), "right": (right_path, right_manifest, right)}
    first = ["left", "right"]
    rng.shuffle(first)
    orientations = {"forward": {"A": first[0], "B": first[1]}, "reversed": {"A": first[1], "B": first[0]}}
    private_mappings = {orientation: {label: {"identity": identity, "run_id": candidates[identity][1].get("run_id"), "path": str(candidates[identity][0])}
                                      for label, identity in labels.items()}
                        for orientation, labels in orientations.items()}
    write_json(folder / "mapping.private.json", {"seed": seed, "orientations": private_mappings})
    # These are the exact immutable artifacts loaded above and presented to judges.
    # In P1, that may be a versioned retry packet rather than judge_packet.json.
    input_files = {"left": left_input, "right": right_input}
    write_json(folder / "manifest.json", {"comparison_id": comparison_id, "created_at": utcnow(), "protocol": args.protocol,
                                           "target": args.target, "roles": args.roles, "repeats": args.repeats, "judge_model": args.judge_model,
                                           "dry_run": args.dry_run, "input_hashes": {key: sha256_file(path) for key, path in input_files.items()}})
    secrets = [str(left_path), str(right_path), left_manifest.get("run_id", ""), right_manifest.get("run_id", "")]
    deadline = time.monotonic() + args.deadline_seconds
    failures = False
    calls: list[dict[str, Any]] = []
    for repeat in range(1, args.repeats + 1):
        for role in args.roles:
            for orientation, labels in orientations.items():
                entries = {label: sanitize(candidates[identity][2], secrets) for label, identity in labels.items()}
                name = f"{repeat:02d}-{role}-{orientation}"
                left_seconds = remaining(deadline, args.finalization_reserve)
                if left_seconds <= 0:
                    write_json(folder / f"{name}.status.json", status_for({}, "global deadline reached"))
                    calls.append({"name": name, "repeat": repeat, "role": role, "orientation": orientation,
                                  "winner_by_blinded_label": None, "mapped_winner": "invalid", "status": "skipped"})
                    failures = True
                    continue
                input_data = {"judge_role": role, "repeat": repeat, "entries": entries, "rubric": left_rubric}
                prompt = eusp_p1_pair_prompt(entries, left_rubric) if args.protocol == "eusp-p1" else pair_prompt(role, entries, left_rubric)
                call = call_pi(prompt, args.judge_model, min(args.timeout, left_seconds), args.dry_run, args.pi_output_mode)
                status = persist(folder, name, input_data, prompt, call, comparison_id, args.judge_model)
                result = call.get("result")
                if args.protocol == "eusp-p1":
                    preflight = {label: evaluate_eusp_p1_packet(candidates[identity][2])
                                 for label, identity in labels.items()}
                    winner, decision = eusp_p1_outcome(result, preflight)
                else:
                    winner, decision = parse_winner(folder / f"{name}.result.json"), {}
                mapped_winner = labels[winner] if winner in {"A", "B"} else ("tie" if winner == "tie" else "invalid")
                calls.append({"name": name, "repeat": repeat, "role": role, "orientation": orientation,
                              "winner_by_blinded_label": winner, "mapped_winner": mapped_winner,
                              "p1_decision": decision, "status": status["state"]})
                failures |= status["state"] != "complete" or winner == "invalid"

    blinded_wins = {"A": 0, "B": 0, "tie": 0, "invalid": 0}
    mapped_votes = {"left": 0, "right": 0, "tie": 0, "invalid": 0}
    for call in calls:
        blinded_wins[call["winner_by_blinded_label"] if call["winner_by_blinded_label"] in blinded_wins else "invalid"] += 1
        mapped_votes[call["mapped_winner"]] += 1
    pair_results: list[dict[str, Any]] = []
    stable_wins = {"left": 0, "right": 0, "tie": 0}
    for repeat in range(1, args.repeats + 1):
        for role in args.roles:
            pair_calls = [call for call in calls if call["repeat"] == repeat and call["role"] == role]
            outcomes = {call["orientation"]: call["mapped_winner"] for call in pair_calls}
            forward, reversed_ = outcomes.get("forward", "invalid"), outcomes.get("reversed", "invalid")
            if forward in stable_wins and forward == reversed_:
                stability = "order_stable"
                stable_wins[forward] += 1
            elif forward in stable_wins and reversed_ in stable_wins:
                stability = "ORDER_SENSITIVE"
            else:
                stability = "incomplete"
            pair_results.append({"repeat": repeat, "role": role, "order_stability": stability,
                                 "mapped_outcomes": outcomes,
                                 "stable_pairwise_winner": forward if stability == "order_stable" else None})
    promotion = (eusp_p1_promotion(calls, pair_results, args.repeats)
                 if args.protocol == "eusp-p1" else None)
    aggregate = {"calls": calls, "mapped_votes_by_stable_identity": mapped_votes,
                 "repeat_role_results": pair_results, "stable_pairwise_wins": stable_wins,
                 **({"promotion": promotion} if promotion is not None else {})}
    write_json(folder / "aggregate.private.json", aggregate)
    summary = {"comparison_id": comparison_id, "path": str(folder), "protocol": args.protocol,
               "state": "partial" if failures else "complete", "calls": calls, "wins_by_blinded_label": blinded_wins,
               "mapped_votes_by_stable_identity": mapped_votes, "repeat_role_results": pair_results,
               "stable_pairwise_wins": stable_wins, "valid_calls": sum(blinded_wins[x] for x in ("A", "B", "tie")),
               **({"promotion": promotion} if promotion is not None else {}), "finished_at": utcnow()}
    write_json(folder / "summary.json", summary)
    append_jsonl(ROOT / "experiments/registry.jsonl", {"kind": "comparison", **summary})
    print(jdump(summary), end="")
    return 0 if not failures else 2


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--a", required=True, help="first saved run directory")
    result.add_argument("--b", required=True, help="second saved run directory")
    result.add_argument("--protocol", choices=("standard", "eusp-p1"), default="standard")
    result.add_argument("--target", default="report")
    result.add_argument("--roles", nargs="+", choices=ALL_ROLES, default=list(ROLES))
    result.add_argument("--repeats", type=int, default=None,
                        help="paired repeats (default: 1 for standard, 2 for eusp-p1)")
    result.add_argument("--judge-model", choices=MODELS, default=MODELS[0])
    result.add_argument("--timeout", type=float, default=900)
    result.add_argument("--deadline-seconds", type=float, default=10800)
    result.add_argument("--finalization-reserve", type=float, default=60)
    result.add_argument("--seed", type=int)
    result.add_argument("--output-dir", default=str(ROOT / "experiments/comparisons"))
    result.add_argument("--dry-run", action="store_true", help="write comparison artifacts without model calls")
    result.add_argument("--pi-output-mode", choices=("json", "text"), default="json")
    original_parse_args = result.parse_args

    def parse_args(*args: Any, **kwargs: Any) -> argparse.Namespace:
        namespace = original_parse_args(*args, **kwargs)
        if namespace.repeats is None:
            namespace.repeats = 2 if namespace.protocol == "eusp-p1" else 1
        return namespace

    result.parse_args = parse_args  # type: ignore[method-assign]
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(run(parser().parse_args()))
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
