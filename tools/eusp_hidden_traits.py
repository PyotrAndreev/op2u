#!/usr/bin/env python3
"""Build and validate the synthetic EUSP P1 evaluator-only hidden-traits packet.

This module deliberately accepts a completed public report plus a separate synthetic
trait ledger.  It never invokes a worker or a judge.  The caller must run it only
after the worker has finished, so evaluator-only traits cannot be an input to the
pipeline.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from compare_variants import evaluate_eusp_p1_packet, eusp_p1_outcome
from run_experiment import (ROOT, _schema_errors, build_eusp_p1_judge_packet,
                            read_json)

PACKET_VERSION = "eusp-p1-hidden-traits-judge-packet/v1"
RESULT_VERSION = "eusp-p1-hidden-traits-judge-result/v1"
FORBIDDEN_PIPELINE_KEYS = frozenset({"hidden_traits", "evaluator_only", "leakage_marker"})


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate_traits(traits: Any) -> list[str]:
    """Validate the small, committed synthetic evaluator ledger."""
    schema = read_json(ROOT / "evals/schemas/eusp_p1_hidden_traits.schema.json")
    errors = _schema_errors(traits, schema)
    if not isinstance(traits, dict):
        return errors
    if traits.get("evaluator_only") is not True or traits.get("synthetic") is not True:
        errors.append("trait ledger must be synthetic and evaluator-only")
    unexpected = set(traits) - {"schema_version", "fixture_id", "synthetic", "evaluator_only", "not_for_pipeline", "traits"}
    if unexpected:
        errors.append(f"trait ledger has unexpected field(s): {', '.join(sorted(unexpected))}")
    seen_ids: set[str] = set()
    seen_markers: set[str] = set()
    for index, trait in enumerate(traits.get("traits", [])):
        if not isinstance(trait, dict):
            continue
        unexpected = set(trait) - {"id", "label", "evaluation_question", "leakage_marker"}
        if unexpected:
            errors.append(f"trait {index} has unexpected field(s): {', '.join(sorted(unexpected))}")
        trait_id, marker = trait.get("id"), trait.get("leakage_marker")
        if isinstance(trait_id, str):
            if trait_id in seen_ids:
                errors.append(f"duplicate hidden trait id: {trait_id}")
            seen_ids.add(trait_id)
        if isinstance(marker, str):
            if marker in seen_markers:
                errors.append(f"duplicate leakage marker: {marker}")
            seen_markers.add(marker)
    return errors


def leakage_errors(pipeline_values: list[tuple[str, Any]], traits: dict[str, Any]) -> list[str]:
    """Mechanically reject evaluator identifiers/markers and reserved keys in worker data.

    This is intentionally a lexical boundary, not a claim to detect semantic
    inference.  The protocol separately limits conclusions accordingly.
    """
    forbidden = {item for trait in traits.get("traits", []) if isinstance(trait, dict)
                 for item in (trait.get("id"), trait.get("leakage_marker")) if isinstance(item, str)}
    errors: list[str] = []
    for name, value in pipeline_values:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
        folded = text.casefold()
        for token in forbidden:
            if token.casefold() in folded:
                errors.append(f"{name} contains evaluator-only token {token!r}")
        for key in FORBIDDEN_PIPELINE_KEYS:
            if re.search(rf"\\b{re.escape(key)}\\b", folded):
                errors.append(f"{name} contains evaluator-only key {key!r}")
        for node in _walk(value):
            if isinstance(node, dict):
                leaked_keys = FORBIDDEN_PIPELINE_KEYS & set(node)
                if leaked_keys:
                    errors.append(f"{name} contains evaluator-only key(s): {', '.join(sorted(leaked_keys))}")
    return errors


def build_hidden_traits_packet(profile: str, direction: str, report: Any,
                               traits: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project a public P1 packet and evaluator-only traits into a judge-only packet."""
    trait_errors = validate_traits(traits)
    pipeline_packet, pipeline_diagnostics = build_eusp_p1_judge_packet(profile, direction, report)
    leaks = leakage_errors([("pipeline profile", profile), ("pipeline report", report),
                            ("public P1 packet", pipeline_packet)], traits)
    projected_traits = [{"id": trait["id"], "label": trait["label"],
                         "evaluation_question": trait["evaluation_question"]}
                        for trait in traits.get("traits", []) if isinstance(trait, dict)
                        and {"id", "label", "evaluation_question"} <= set(trait)]
    packet = {
        "schema_version": PACKET_VERSION,
        "fixture_id": traits.get("fixture_id"),
        "evaluator_only": True,
        "pipeline_packet_sha256": sha256_bytes(json.dumps(pipeline_packet, ensure_ascii=False,
                                                             sort_keys=True).encode()),
        "pipeline_packet": pipeline_packet,
        "hidden_traits": projected_traits,
        "measurement": {"primary_metric": "portfolio_readiness_to_act",
                        "trait_alignment_is_secondary": True},
    }
    schema = read_json(ROOT / "evals/schemas/eusp_p1_hidden_traits_judge_packet.schema.json")
    errors = trait_errors + pipeline_diagnostics["errors"] + leaks + _schema_errors(packet, schema)
    diagnostics = {"schema_version": "eusp-p1-hidden-traits-packet-validation/v1",
                   "valid": not errors, "errors": errors,
                   "pipeline_packet_sha256": packet["pipeline_packet_sha256"]}
    return packet, diagnostics


def hidden_traits_pair_prompt(entries: dict[str, Any], rubric: str) -> str:
    """Return the evaluator-only judge prompt; worker-facing prompts never use it."""
    return f'''You are the readiness member of a blinded synthetic EUSP priority-1 panel.
The hidden traits in each evaluator-only packet are calibration material for this
judge only. They were unavailable to the pipelines. Do not research, browse, add
facts, infer identity, or treat a trait as evidence of eligibility. Evaluate each
packet's P1 hard gates first. Then independently score readiness-to-act as the mean
of five equal checks per selected candidate: explicit profile bridge; atomic
user-controlled action; tangible deliverable; startable within seven days without
reply, eligibility, or acceptance; and bounded effort with disclosed blockers or
unknowns. Empty portfolios score 0. Trait alignment is a secondary annotation and
never repairs a gate failure or changes that arithmetic.
Return ONLY this JSON shape:
{{"schema_version":"{RESULT_VERSION}","judge_role":"readiness_hidden_traits","arms":{{"A":{{"grounding_gate":"pass|fail","liveness_gate":"pass|fail","other_hard_gate_failures":[],"per_candidate_readiness":[],"portfolio_readiness_to_act":0,"hidden_trait_matches":[{{"trait_id":"...","matched":true,"reason":"..."}}]}},"B":{{"grounding_gate":"pass|fail","liveness_gate":"pass|fail","other_hard_gate_failures":[],"per_candidate_readiness":[],"portfolio_readiness_to_act":0,"hidden_trait_matches":[]}}}},"winner":"A|B|tie","reasons":[]}}
The comparison runner applies eligibility and the five-point margin; do not claim
that this synthetic proxy measures real behaviour.
RUBRIC:\n{rubric}\nEVALUATOR-ONLY PACKETS:\n{json.dumps(entries, indent=2, sort_keys=True, ensure_ascii=False)}'''


def validate_hidden_traits_result(result: Any, packets: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """Validate trait annotations and reuse the P1 score/gate arithmetic exactly."""
    schema = read_json(ROOT / "evals/schemas/eusp_p1_hidden_traits_judge_result.schema.json")
    errors = _schema_errors(result, schema)
    if not isinstance(result, dict):
        return "invalid", {"reason": "invalid hidden-traits judge result", "errors": errors}
    normalized = copy.deepcopy({key: value for key, value in result.items() if key != "schema_version"})
    normalized["judge_role"] = "readiness"
    for label in ("A", "B"):
        arm = normalized.get("arms", {}).get(label) if isinstance(normalized.get("arms"), dict) else None
        packet = packets.get(label)
        if not isinstance(arm, dict) or not isinstance(packet, dict):
            errors.append(f"missing arm or packet {label}")
            continue
        matches = arm.pop("hidden_trait_matches", None)
        expected = {trait.get("id") for trait in packet.get("hidden_traits", []) if isinstance(trait, dict)}
        if (not isinstance(matches, list) or {row.get("trait_id") for row in matches if isinstance(row, dict)} != expected
                or len(matches) != len(expected)
                or any(not isinstance(row, dict) or not isinstance(row.get("matched"), bool)
                       or not isinstance(row.get("reason"), str) for row in matches)):
            errors.append(f"hidden trait annotations do not exactly match packet {label}")
    if errors:
        return "invalid", {"reason": "invalid hidden-traits judge result", "errors": errors}
    preflight = {label: evaluate_eusp_p1_packet(packet["pipeline_packet"])
                 for label, packet in packets.items() if label in {"A", "B"}}
    return eusp_p1_outcome(normalized, preflight)


def load_fixture(fixture: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build both committed evaluator packets and validate every public surface."""
    traits = _read_json(fixture / "evaluator_only/hidden_traits.json")
    errors = validate_traits(traits)
    packets: dict[str, Any] = {}
    for arm in ("P1_V0", "P1_FRONTIER"):
        profile = (fixture / "pipeline_input/profile.md").read_text(encoding="utf-8")
        direction = (fixture / "pipeline_input/direction.yaml").read_text(encoding="utf-8")
        report = _read_json(fixture / f"pipeline_outputs/{arm}.report.json")
        errors.extend(leakage_errors([(f"{arm} profile", profile), (f"{arm} direction", direction),
                                      (f"{arm} report", report)], traits))
        packet, diagnostics = build_hidden_traits_packet(profile, direction, report, traits)
        if not diagnostics["valid"]:
            errors.extend(f"{arm}: {error}" for error in diagnostics["errors"])
        packets[arm] = packet
    return packets, {"valid": not errors, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path,
                        default=ROOT / "evals/fixtures/eusp_p1_hidden_traits/v1")
    parser.add_argument("--write-packets", type=Path,
                        help="write deterministic evaluator-only packets after validation")
    args = parser.parse_args(argv)
    packets, diagnostics = load_fixture(args.fixture)
    if args.write_packets and diagnostics["valid"]:
        args.write_packets.mkdir(parents=True, exist_ok=True)
        for arm, packet in packets.items():
            (args.write_packets / f"{arm}.judge_packet.json").write_text(
                json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(diagnostics, indent=2, sort_keys=True), end="\n")
    return 0 if diagnostics["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
