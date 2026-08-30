#!/usr/bin/env python3
"""Blind, saved-artifact A/B comparisons for immutable experiment runs."""
from __future__ import annotations

import argparse
import json
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


def load_candidate(run: Path, target: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest = read_json(run / "manifest.json")
    result = completed_result(run, target)
    rubric = run / "inputs/rubric.yaml"
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
    return manifest, artifacts, rubric.read_text(encoding="utf-8")


def pair_prompt(role: str, entries: dict[str, Any], rubric: str) -> str:
    return f"""You are the {role} member of a blinded A/B evaluation panel.
This is judging only: do NOT research, browse, add outside facts, or infer identity from missing
metadata. Use exclusively these anonymized saved artifacts and the rubric. Compare A and B.
Return ONLY one JSON object with judge_role, winner (A|B|tie), scores (object with A and B),
hard_failures (object with A and B arrays), reasons (array), failure_tags (array), and confidence (0..1).
Do not mention variants, run IDs, models, or paths.
RUBRIC:\n{rubric}\nANONYMIZED ARTIFACTS:\n{jdump(entries)}"""


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


def run(args: argparse.Namespace) -> int:
    left_path, right_path = Path(args.a).resolve(), Path(args.b).resolve()
    left_manifest, left, left_rubric = load_candidate(left_path, args.target)
    right_manifest, right, right_rubric = load_candidate(right_path, args.target)
    if left_rubric != right_rubric:
        raise SystemExit("runs have different saved rubric snapshots; comparison would be confounded")
    comparison_id = f"compare-{utcnow().replace(':', '').replace('+00:00', 'Z')}-{uuid.uuid4().hex[:10]}"
    folder = Path(args.output_dir).resolve() / comparison_id
    folder.mkdir(parents=True, exist_ok=False)
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**63)
    rng = random.Random(seed)
    candidates = {
        "left": (left_path, left_manifest, left),
        "right": (right_path, right_manifest, right),
    }
    # Keep both label mappings private.  The randomized first orientation prevents a
    # fixed label bias, and its inverse tests whether presentation order changed a vote.
    first = ["left", "right"]
    rng.shuffle(first)
    orientations = {
        "forward": {"A": first[0], "B": first[1]},
        "reversed": {"A": first[1], "B": first[0]},
    }
    private_mappings = {
        orientation: {
            label: {"identity": identity, "run_id": candidates[identity][1].get("run_id"),
                    "path": str(candidates[identity][0])}
            for label, identity in labels.items()
        }
        for orientation, labels in orientations.items()
    }
    write_json(folder / "mapping.private.json", {"seed": seed, "orientations": private_mappings})
    write_json(folder / "manifest.json", {"comparison_id": comparison_id, "created_at": utcnow(), "target": args.target,
                                           "roles": args.roles, "repeats": args.repeats, "judge_model": args.judge_model,
                                           "dry_run": args.dry_run, "input_hashes": {
                                               "left": sha256_file(completed_result(left_path, args.target)),
                                               "right": sha256_file(completed_result(right_path, args.target))}})
    secrets = [str(left_path), str(right_path), left_manifest.get("run_id", ""), right_manifest.get("run_id", "")]
    deadline = time.monotonic() + args.deadline_seconds
    failures = False
    calls: list[dict[str, Any]] = []
    for repeat in range(1, args.repeats + 1):
        for role in args.roles:
            for orientation, labels in orientations.items():
                # Orientation stays out of the input and prompt: judges see only A and B.
                entries = {label: sanitize(candidates[identity][2], secrets)
                           for label, identity in labels.items()}
                name = f"{repeat:02d}-{role}-{orientation}"
                left_seconds = remaining(deadline, args.finalization_reserve)
                if left_seconds <= 0:
                    write_json(folder / f"{name}.status.json", status_for({}, "global deadline reached"))
                    calls.append({"name": name, "repeat": repeat, "role": role, "orientation": orientation,
                                  "winner_by_blinded_label": None, "mapped_winner": "invalid", "status": "skipped"})
                    failures = True
                    continue
                input_data = {"judge_role": role, "repeat": repeat, "entries": entries, "rubric": left_rubric}
                prompt = pair_prompt(role, entries, left_rubric)
                call = call_pi(prompt, args.judge_model, min(args.timeout, left_seconds),
                               args.dry_run, args.pi_output_mode)
                status = persist(folder, name, input_data, prompt, call, comparison_id, args.judge_model)
                winner = parse_winner(folder / f"{name}.result.json")
                mapped_winner = labels[winner] if winner in {"A", "B"} else ("tie" if winner == "tie" else "invalid")
                calls.append({"name": name, "repeat": repeat, "role": role, "orientation": orientation,
                              "winner_by_blinded_label": winner, "mapped_winner": mapped_winner,
                              "status": status["state"]})
                failures |= status["state"] != "complete"

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

    aggregate = {"calls": calls, "mapped_votes_by_stable_identity": mapped_votes,
                 "repeat_role_results": pair_results, "stable_pairwise_wins": stable_wins}
    # This contains mapped outcomes only; the run/path mappings remain in mapping.private.json.
    write_json(folder / "aggregate.private.json", aggregate)
    summary = {"comparison_id": comparison_id, "path": str(folder), "state": "partial" if failures else "complete",
               "calls": calls, "wins_by_blinded_label": blinded_wins,
               "mapped_votes_by_stable_identity": mapped_votes, "repeat_role_results": pair_results,
               "stable_pairwise_wins": stable_wins,
               "valid_calls": sum(blinded_wins[x] for x in ("A", "B", "tie")), "finished_at": utcnow()}
    write_json(folder / "summary.json", summary)
    append_jsonl(ROOT / "experiments/registry.jsonl", {"kind": "comparison", **summary})
    print(jdump(summary), end="")
    return 0 if not failures else 2


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--a", required=True, help="first saved run directory")
    result.add_argument("--b", required=True, help="second saved run directory")
    result.add_argument("--target", default="report")
    result.add_argument("--roles", nargs="+", choices=ALL_ROLES, default=list(ROLES))
    result.add_argument("--repeats", type=int, default=1)
    result.add_argument("--judge-model", choices=MODELS, default=MODELS[0])
    result.add_argument("--timeout", type=float, default=900)
    result.add_argument("--deadline-seconds", type=float, default=10800)
    result.add_argument("--finalization-reserve", type=float, default=60)
    result.add_argument("--seed", type=int)
    result.add_argument("--output-dir", default=str(ROOT / "experiments/comparisons"))
    result.add_argument("--dry-run", action="store_true", help="write comparison artifacts without model calls")
    result.add_argument("--pi-output-mode", choices=("json", "text"), default="json")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(run(parser().parse_args()))
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
