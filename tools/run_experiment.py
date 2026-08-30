#!/usr/bin/env python3
"""Run immutable opportunity-discovery experiments or judge saved artifacts only.

This tool deliberately never reads evals/holdout.yaml.  It uses only the Python
standard library and invokes pi as a subprocess for real model calls.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("openai-codex/gpt-5.6-luna", "openai-codex/gpt-5.6-terra")
ROLES = ("actionability", "evidence", "personalization")
ALL_ROLES = ROLES + ("breadth", "academic_depth", "readiness")
STAGED = ("profile", "triggers", "search_plan", "discovery", "verification", "actionability", "ranking", "report")
VARIANTS = {
    "V0": {"prompt": "prompts/find_opportunities_baseline.md", "stages": ("report",), "mode": "monolithic"},
    # Priority-1 evaluation arms share only this report-stage serialization contract.
    # P1_V0 remains one monolithic call and P1_FRONTIER remains the staged frontier.
    "P1_V0": {"prompt": "prompts/find_opportunities_baseline.md", "report_addenda": ["prompts/variants/P1_REPORT_SERIALIZATION_ADDENDUM.md"], "stages": ("report",), "mode": "monolithic"},
    "P1_FRONTIER": {"prompt": "prompts/find_opportunities_general_recommended.md", "report_addenda": ["prompts/variants/P1_REPORT_SERIALIZATION_ADDENDUM.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "V1": {"prompt": "prompts/variants/V1.md", "stages": ("report",), "mode": "monolithic"},
    "V2": {"prompt": "prompts/variants/V2.md", "stages": ("report",), "mode": "monolithic"},
    "V3": {"prompt": "prompts/variants/V3.md", "stages": ("report",), "mode": "monolithic"},
    "V4": {"prompt": "prompts/variants/V4.md", "stages": STAGED, "mode": "staged"},
    "V5": {"prompt": "prompts/variants/V5.md", "stages": STAGED, "mode": "staged"},
    "V6": {"prompt": "prompts/variants/V6.md", "stages": STAGED, "mode": "staged"},
    "V7": {"prompt": "prompts/variants/V7.md", "stages": STAGED, "mode": "staged"},
    "G1_M1": {"prompt": "prompts/variants/G1_M1.md", "stages": STAGED, "mode": "staged"},
    "G1_M2": {"prompt": "prompts/variants/G1_M2.md", "stages": STAGED, "mode": "staged"},
    "G1_M3": {"prompt": "prompts/variants/G1_M3.md", "stages": STAGED, "mode": "staged"},
    "G2_M1": {"prompt": "prompts/variants/G2_M1.md", "stages": STAGED, "mode": "staged"},
    "G3_M1": {"prompt": "prompts/variants/G3_M1.md", "stages": STAGED, "mode": "staged"},
    "G3_M2": {"prompt": "prompts/variants/G3_M2.md", "stages": STAGED, "mode": "staged"},
    "G3_M3": {"prompt": "prompts/variants/G3_M3.md", "stages": STAGED, "mode": "staged"},
    "PROD": {"prompt": "prompts/find_opportunities_recommended.md", "stages": STAGED, "mode": "staged"},
    "BREADTH": {"prompt": "prompts/find_opportunities_breadth.md", "stages": STAGED, "mode": "staged"},
    "BREADTH_V2": {"prompt": "prompts/find_opportunities_breadth_v2.md", "stages": STAGED, "mode": "staged"},
    "BH1": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md"], "stages": STAGED, "mode": "staged"},
    "BH2": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md", "prompts/variants/BH2.md"], "stages": STAGED, "mode": "staged"},
    "BH3": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md", "prompts/variants/BH2.md", "prompts/variants/BH3.md"], "stages": STAGED, "mode": "staged"},
    "BH4": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md", "prompts/variants/BH2.md", "prompts/variants/BH4.md"], "stages": STAGED, "mode": "staged"},
    "BH5": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md", "prompts/variants/BH2.md", "prompts/variants/BH4.md", "prompts/variants/BH5.md"], "stages": STAGED, "mode": "staged"},
    "BH6": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md", "prompts/variants/BH2.md", "prompts/variants/BH4.md", "prompts/variants/BH5.md", "prompts/variants/BH6.md"], "stages": STAGED, "mode": "staged"},
    "BH7": {"prompt": "prompts/find_opportunities_breadth_v2.md", "addenda": ["prompts/variants/BH1.md", "prompts/variants/BH2.md", "prompts/variants/BH4.md", "prompts/variants/BH5.md", "prompts/variants/BH6.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True},
    "T1_GENERAL": {"prompt": "prompts/find_opportunities_general_v1.md", "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T2_DECISION_DEPTH": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T2_DECISION_DEPTH.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T3_ANCHOR_VERIFICATION": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T2_DECISION_DEPTH.md", "prompts/variants/T3_ANCHOR_VERIFICATION.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T4_FOCUSED_DEPTH": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T4_FOCUSED_DEPTH.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T5_DECISION_COMPLETENESS": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T4_FOCUSED_DEPTH.md", "prompts/variants/T5_DECISION_COMPLETENESS.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T6_RECORD_PROJECTION": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T4_FOCUSED_DEPTH.md", "prompts/variants/T5_DECISION_COMPLETENESS.md", "prompts/variants/T6_RECORD_PROJECTION.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T7_TEMPORAL_SCOPE": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T4_FOCUSED_DEPTH.md", "prompts/variants/T7_TEMPORAL_SCOPE.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T8_DECISION_MAP": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T4_FOCUSED_DEPTH.md", "prompts/variants/T5_DECISION_COMPLETENESS.md", "prompts/variants/T6_RECORD_PROJECTION.md", "prompts/variants/T8_DECISION_MAP.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T9_STAGE_PROVENANCE": {"prompt": "prompts/find_opportunities_general_v1.md", "addenda": ["prompts/variants/T4_FOCUSED_DEPTH.md", "prompts/variants/T5_DECISION_COMPLETENESS.md", "prompts/variants/T6_RECORD_PROJECTION.md", "prompts/variants/T8_DECISION_MAP.md", "prompts/variants/T9_STAGE_PROVENANCE.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T10_RECORD_CONTRACT": {"prompt": "prompts/find_opportunities_general_v2.md", "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T11_QUOTED_TIME": {"prompt": "prompts/find_opportunities_general_v2.md", "addenda": ["prompts/variants/T11_QUOTED_TIME.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T12_SEVEN_DAY_ACTION": {"prompt": "prompts/find_opportunities_general_v2.md", "addenda": ["prompts/variants/T11_QUOTED_TIME.md", "prompts/variants/T12_SEVEN_DAY_ACTION.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T13_FUNDING_COMPONENTS": {"prompt": "prompts/find_opportunities_general_v2.md", "addenda": ["prompts/variants/T11_QUOTED_TIME.md", "prompts/variants/T12_SEVEN_DAY_ACTION.md", "prompts/variants/T13_FUNDING_COMPONENTS.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
    "T14_QUOTED_GEOGRAPHY": {"prompt": "prompts/find_opportunities_general_v2.md", "addenda": ["prompts/variants/T11_QUOTED_TIME.md", "prompts/variants/T12_SEVEN_DAY_ACTION.md", "prompts/variants/T13_FUNDING_COMPONENTS.md", "prompts/variants/T14_QUOTED_GEOGRAPHY.md"], "stages": STAGED, "mode": "staged", "normalize_ledger": True, "production_contract": True},
}
PRODUCTION_VARIANTS = {"PROD", "BREADTH", "BREADTH_V2", "BH1", "BH2", "BH3", "BH4", "BH5", "BH6", "BH7"} | {
    name for name, config in VARIANTS.items() if config.get("production_contract")
}


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def jdump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def atomic_write(path: Path, text: str) -> None:
    """Write once. A run artifact is never silently replaced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"immutable artifact already exists: {path}")
    temporary = path.with_name(path.name + f".tmp-{uuid.uuid4().hex}")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, jdump(value))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_APPEND makes each small registry/cost record a single append operation.
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def git_revision() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def variant_instruction_paths(variant: str, stage: str | None = None) -> list[Path]:
    """Return immutable prompt parts, adding report-only parts only to final rendering."""
    config = VARIANTS[variant]
    paths = [ROOT / config["prompt"]]
    paths.extend(ROOT / part for part in config.get("addenda", []))
    if stage is None or stage == "report":
        paths.extend(ROOT / part for part in config.get("report_addenda", []))
    return paths


def variant_instructions(variant: str, stage: str | None = None) -> str:
    """Compose variant instructions; snapshots include the final-report contract."""
    return "\n\n---\n\n".join(path.read_text(encoding="utf-8")
                              for path in variant_instruction_paths(variant, stage))


def snapshot_inputs(run: Path, variant: str, profile_path: Path | None = None,
                    direction_path: Path | None = None, rubric_path: Path | None = None) -> dict[str, str]:
    """Copy the explicitly permitted, non-secret inputs and record content hashes."""
    sources = {
        "profile.md": profile_path or ROOT / "usr/profile.md",
        "direction.yaml": direction_path or ROOT / "evals/direction.yaml",
        "known_cases.yaml": ROOT / "evals/known_cases.yaml",
        "rubric.yaml": rubric_path or ROOT / "evals/rubric.yaml",
    }
    # Schemas are contracts, not model training/optimization data.
    for item in sorted((ROOT / "evals/schemas").glob("*.json")):
        sources[f"schemas/{item.name}"] = item
    hashes: dict[str, str] = {}
    for relative, source in sources.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = run / "inputs" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(destination, source.read_text(encoding="utf-8"))
        hashes[relative] = sha256_file(destination)
    # The snapshot commits to the complete final report contract, including parts
    # deliberately withheld from non-report staged calls.
    prompt_content = variant_instructions(variant)
    prompt_destination = run / "inputs/prompt.md"
    atomic_write(prompt_destination, prompt_content)
    hashes["prompt.md"] = sha256_file(prompt_destination)
    write_json(run / "inputs/hashes.json", hashes)
    return hashes


def stage_contract(stage: str) -> str:
    contracts = {
        "profile": "profile_interpretation.schema.json: an object describing only supplied profile facts and explicit unknowns",
        "triggers": "trigger_hypotheses.schema.json: a JSON array of profile-signal intersection hypotheses",
        "search_plan": "object with queries array; each query has a trigger reference, track, rationale, and intended primary-source targets",
        "discovery": "object with candidates array; every named candidate needs an official_url and discovery rationale",
        "verification": "object with candidates array and evidence records; every source record includes source_type=official_primary|secondary, exact quote, official URL, checked_at/retrieved_at, status, deadline/event_date/rolling_window, eligibility/unknown; only official_primary direct records may support selected actions",
        "actionability": "object with candidates array; each has bridge, blockers, effort and an executable first action within seven days",
        "ranking": "object with ranked_candidates array, score components, penalties, diversity decisions and classification",
        "report": "object with report_markdown, candidates, citations, unknowns and methodology",
    }
    return contracts.get(stage, "a JSON object")


def model_prompt(stage: str, payload: dict[str, Any]) -> str:
    return f"""You are executing the {stage} stage of an opportunity-discovery experiment.
Return ONLY one valid JSON value, with no Markdown fence or commentary.
Variant instructions are included in input. Respect exclusions (especially jobs), use primary
sources for status/deadline claims, and mark uncertainty rather than inventing facts.
When calling web_search, always set workflow to auto-summary or none; never use interactive summary-review.
In verification, every evidence row MUST include source_type (official_primary or secondary).
In report, evidence_ledger MUST contain only directly entailing official_primary rows copied exactly
from verification; keep uncertain, secondary, partial, or non-entailing evidence outside the ledger
as explicit uncertainty. Never put entailment=uncertain or an empty supports list in evidence_ledger.
Stage contract: {"the exact JSON output specified by the standalone production prompt, including evidence ledger and any breadth fields" if payload.get("variant") in PRODUCTION_VARIANTS and stage == "report" else stage_contract(stage)}.
A status-only or source-trace-only acknowledgment is invalid. Return the complete stage artifact now.
If pipeline_mode is monolithic, perform the complete live workflow now: interpret the profile,
plan searches, use the available web tools for broad discovery, verify shortlisted facts on official
primary sources, rank, and report. An empty prior_artifacts object is expected in monolithic mode
and is NOT a reason to skip research. If pipeline_mode is staged, use only supplied prior artifacts
except that discovery and verification stages must use the available web tools and persist their
source trace in output. Do not claim hidden state.
INPUT JSON:
{jdump(payload)}"""


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def parse_pi_output(raw: str) -> tuple[Any | None, str | None, dict[str, Any] | None]:
    """Accept ordinary JSON, JSONL event streams, and pi's JSON-mode text envelopes."""
    values: list[Any] = []
    try:
        values.append(json.loads(raw))
    except json.JSONDecodeError:
        for line in raw.splitlines():
            try:
                values.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    text_candidates: list[str] = []
    assistant_final_texts: list[str] = []
    usage: dict[str, Any] | None = None
    for value in values:
        if isinstance(value, dict) and value.get("type") == "message_end":
            message = value.get("message")
            if isinstance(message, dict) and message.get("role") == "assistant":
                for part in message.get("content", []):
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        assistant_final_texts.append(part["text"])
        for node in _walk_json(value):
            if any(k in node for k in ("usage", "input_tokens", "output_tokens", "total_tokens", "cost")):
                possible = node.get("usage") if isinstance(node.get("usage"), dict) else node
                if isinstance(possible, dict):
                    # Keep provider metadata verbatim while normalizing common field spellings.
                    usage = dict(possible)
                    aliases = {"input_tokens": ("input_tokens", "inputTokens", "prompt_tokens"),
                               "output_tokens": ("output_tokens", "outputTokens", "completion_tokens"),
                               "total_tokens": ("total_tokens", "totalTokens", "tokens"),
                               "cost": ("cost", "cost_usd", "costUSD", "estimated_cost")}
                    for normalized, names in aliases.items():
                        for field in names:
                            if field in possible:
                                usage[normalized] = possible[field]
                                break
            for key in ("text", "content", "output", "message"):
                candidate = node.get(key)
                if isinstance(candidate, str):
                    text_candidates.append(candidate)
    # A direct JSON response may itself be the requested result rather than an event.
    if len(values) == 1 and isinstance(values[0], (dict, list)):
        direct = values[0]
        if not (isinstance(direct, dict) and any(key in direct for key in ("type", "event", "text", "content", "message")) and text_candidates):
            return direct, None, usage
    parsed_texts: list[tuple[int, Any]] = []
    for text in (assistant_final_texts or text_candidates):
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
        try:
            parsed_texts.append((len(cleaned), json.loads(cleaned)))
        except json.JSONDecodeError:
            continue
    # Async web-tool completion notifications can append tiny {"status":"complete"}
    # turns after the substantive final JSON. Prefer report-shaped output and then
    # the richest valid result rather than blindly selecting the last turn.
    reports = [(size, value) for size, value in parsed_texts
               if isinstance(value, dict) and "report_markdown" in value]
    if reports:
        return max(reports, key=lambda item: item[0])[1], None, usage
    substantive = [(size, value) for size, value in parsed_texts
                   if not (isinstance(value, dict) and set(value) <= {"status"})]
    if substantive:
        return max(substantive, key=lambda item: item[0])[1], None, usage
    # Some providers ignore --mode json but return a bare JSON final line. Never
    # mistake pi lifecycle events (for example {"type":"agent_settled"}) for output.
    for line in reversed(raw.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and any(key in value for key in ("type", "event", "message")):
            continue
        if isinstance(value, (dict, list)):
            return value, None, usage
    return None, "no assistant JSON result found in pi output", usage


def call_pi(prompt: str, model: str, timeout: float, dry_run: bool,
            output_mode: str = "json") -> dict[str, Any]:
    """One bounded pi invocation. The caller persists all returned fields immediately."""
    started = utcnow()
    before = time.monotonic()
    command = ["pi", "--model", model, "--mode", output_mode, "--print", "--no-session",
               "--no-context-files", "--tools",
               "web_search,source_check,fetch_content,get_search_content"]
    if dry_run:
        return {"started_at": started, "duration_seconds": 0.0, "exit_code": 0,
                "stdout": "", "stderr": "", "result": {"dry_run": True}, "parse_error": None,
                "usage": None, "command": command}
    try:
        # Pi print mode merges piped stdin into the initial prompt. Using stdin avoids
        # Android/Linux ARG_MAX failures as persisted staged artifacts grow.
        completed = subprocess.run(command, cwd=ROOT, text=True, input=prompt,
                                   capture_output=True, timeout=max(1, timeout))
        stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        stderr += f"\nTIMED OUT after {timeout:.1f} seconds"
        code = 124
    result, parse_error, usage = parse_pi_output(stdout)
    return {"started_at": started, "duration_seconds": round(time.monotonic() - before, 3),
            "exit_code": code, "stdout": stdout, "stderr": stderr, "result": result,
            "parse_error": parse_error, "usage": usage, "command": command}


def stage_result_error(stage: str, result: Any, p1_packet: bool = False) -> str | None:
    """Reject lifecycle acknowledgments and structurally incomplete stage artifacts."""
    if not isinstance(result, (dict, list)):
        return f"{stage} result is not a JSON object or array"
    if isinstance(result, dict) and set(result) <= {"status", "source_trace", "response_id"}:
        return f"{stage} returned a status/source-trace acknowledgment instead of the stage artifact"
    required_arrays = {
        "search_plan": ("queries",),
        "discovery": ("candidates",),
        "verification": ("candidates",),
        "actionability": ("candidates",),
        "ranking": ("ranked_candidates",),
    }
    if stage in required_arrays:
        if not isinstance(result, dict):
            return f"{stage} result is not an object"
        production_shaped_ranking = (stage == "ranking"
                                     and isinstance(result.get("candidates"), list)
                                     and isinstance(result.get("selected_ids"), dict)
                                     and isinstance(result.get("weekly_allocation"), dict))
        if not production_shaped_ranking:
            for key in required_arrays[stage]:
                if not isinstance(result.get(key), list):
                    return f"{stage} result lacks required array {key}"
    if stage == "verification" and not any(isinstance(result.get(key), list)
                                             for key in ("evidence_records", "evidence_ledger")):
        return "verification result lacks evidence_records/evidence_ledger array"
    if stage == "report":
        required = ({"snapshot_date", "candidates", "selected_ids", "weekly_allocation", "evidence_ledger"}
                    if p1_packet else {"snapshot_date", "profile_state", "candidates", "selected_ids",
                                        "weekly_allocation", "evidence_ledger"})
        if not isinstance(result, dict) or not required <= set(result):
            return "report result lacks the required final artifact fields"
    return None


def cost_record(run_id: str, name: str, role: str, model: str, call: dict[str, Any]) -> dict[str, Any]:
    usage = call.get("usage") or {}
    return {"run_id": run_id, "stage": name, "role": role, "model": model,
            "started_at": call["started_at"], "duration_seconds": call["duration_seconds"],
            "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "estimated_cost": usage.get("cost", usage.get("estimated_cost")),
            "usage_source": "provider_metadata" if usage else "unknown", "exit_code": call["exit_code"]}


def status_for(call: dict[str, Any], skipped: str | None = None) -> dict[str, Any]:
    if skipped:
        return {"state": "skipped", "reason": skipped, "finished_at": utcnow()}
    if call["exit_code"] != 0:
        return {"state": "failed", "reason": f"pi exit {call['exit_code']}", "finished_at": utcnow()}
    if call["parse_error"]:
        return {"state": "failed", "reason": call["parse_error"], "finished_at": utcnow()}
    return {"state": "complete", "finished_at": utcnow()}


def persist_call(folder: Path, name: str, input_data: dict[str, Any], prompt: str,
                 call: dict[str, Any], role: str, run_id: str, model: str) -> dict[str, Any]:
    """Flat, complete call artifacts. No artifact is overwritten."""
    atomic_write(folder / f"{name}.prompt.txt", prompt)
    atomic_write(folder / "prompts" / f"{name}.txt", prompt)
    write_json(folder / f"{name}.input.json", input_data)
    atomic_write(folder / f"{name}.stdout.txt", call["stdout"])
    atomic_write(folder / f"{name}.stderr.txt", call["stderr"])
    write_json(folder / f"{name}.call.json", {k: call[k] for k in ("started_at", "duration_seconds", "exit_code", "parse_error", "usage", "command")})
    status = status_for(call)
    if call["result"] is not None:
        write_json(folder / f"{name}.result.json", call["result"])
    write_json(folder / f"{name}.status.json", status)
    append_jsonl(folder / "costs.jsonl", cost_record(run_id, name, role, model, call))
    append_jsonl(folder / "events.jsonl", {"at": utcnow(), "name": name, "role": role, **status})
    return status


def remaining(deadline_at: float, reserve: float) -> float:
    return deadline_at - time.monotonic() - reserve


def completed_result(folder: Path, name: str) -> Path | None:
    """Return the newest successful immutable attempt for an artifact name."""
    candidates = [folder / name]
    candidates.extend(Path(str(path)[: -len(".status.json")])
                      for path in sorted(folder.glob(f"{name}.attempt-*.status.json")))
    for base in reversed(candidates):
        status, result = Path(str(base) + ".status.json"), Path(str(base) + ".result.json")
        if status.is_file() and result.is_file() and read_json(status).get("state") == "complete":
            return result
    return None


def next_attempt_name(folder: Path, name: str) -> str:
    """Use the base name once; retries are distinct artifacts, never replacements."""
    if not any(folder.glob(f"{name}.*")):
        return name
    numbers = [1]
    for path in folder.glob(f"{name}.attempt-*.status.json"):
        match = re.search(r"\.attempt-(\d+)\.status\.json$", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"{name}.attempt-{max(numbers) + 1:02d}"


def next_versioned_file(folder: Path, stem: str, suffix: str = ".json") -> Path:
    candidate = folder / f"{stem}{suffix}"
    if not candidate.exists():
        return candidate
    numbers = [1]
    for path in folder.glob(f"{stem}.attempt-*{suffix}"):
        match = re.search(r"\.attempt-(\d+)" + re.escape(suffix) + r"$", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return folder / f"{stem}.attempt-{max(numbers) + 1:02d}{suffix}"


def _items(value: Any, key: str) -> list[Any]:
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return value[key]
    return value if isinstance(value, list) else []


def materialize_required_artifacts(run: Path, results: dict[str, Any]) -> None:
    """Create the stable public artifact contract from raw immutable call artifacts."""
    mappings = {
        "profile_interpretation.json": ("profile", {}),
        "trigger_hypotheses.json": ("triggers", []),
        "search_queries.json": ("search_plan", {"queries": []}),
        "ranking.json": ("ranking", {"ranked_candidates": []}),
    }
    for filename, (stage, empty) in mappings.items():
        path = run / filename
        if not path.exists():
            write_json(path, results.get(stage, {"not_available_in_pipeline": True, "value": empty}))
    for filename, stage in (("candidates.jsonl", "discovery"),
                            ("verified_candidates.jsonl", "verification")):
        path = run / filename
        if not path.exists():
            rows = _items(results.get(stage), "candidates")
            atomic_write(path, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
    trace = run / "search_trace.jsonl"
    if not trace.exists():
        rows = []
        for stage in ("search_plan", "discovery", "verification"):
            if stage in results:
                rows.append({"stage": stage, "artifact": f"{stage}.result.json", "recorded_at": utcnow()})
        atomic_write(trace, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
    report = results.get("report")
    report_text = report.get("report_markdown") if isinstance(report, dict) else None
    if not isinstance(report_text, str):
        report_text = "# Opportunity report\n\n```json\n" + jdump(report if report is not None else {"status": "not_available"}) + "```\n"
    if not (run / "report.md").exists():
        atomic_write(run / "report.md", report_text.rstrip() + "\n")
    if not (run / "evaluation.json").exists():
        write_json(run / "evaluation.json", {"status": "pending_external_judges"})
    for filename in ("judge_outputs.jsonl", "errors.jsonl"):
        if not (run / filename).exists():
            atomic_write(run / filename, "")
    records = []
    costs_jsonl = run / "costs.jsonl"
    if costs_jsonl.is_file():
        for line in costs_jsonl.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not (run / "costs.json").exists():
        write_json(run / "costs.json", {"calls": records})


def _schema_errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON-Schema subset used by production_output.schema.json."""
    errors: list[str] = []
    expected = schema.get("type")
    types = expected if isinstance(expected, list) else [expected] if expected else []
    matches = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
               "string": lambda x: isinstance(x, str), "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
               "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
               "boolean": lambda x: isinstance(x, bool), "null": lambda x: x is None}
    if types and not any(kind in matches and matches[kind](value) for kind in types):
        return [f"{path}: expected type {expected}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value does not equal const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value is not in enum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        for key, child in value.items():
            if key in properties:
                errors.extend(_schema_errors(child, properties[key], f"{path}.{key}"))
    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems")
        if isinstance(schema.get("maxItems"), int) and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems")
        if isinstance(schema.get("items"), dict):
            for index, child in enumerate(value):
                errors.extend(_schema_errors(child, schema["items"], f"{path}[{index}]"))
    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength")
        if isinstance(schema.get("pattern"), str) and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: does not match pattern")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(schema.get("minimum"), (int, float)) and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if isinstance(schema.get("maximum"), (int, float)) and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors


def direction_scalar(direction: str, key: str) -> str | None:
    """Read a simple top-level YAML scalar without adding a YAML dependency."""
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*([^#\n]+?)\s*$", direction)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def direction_effort_cap(direction: str) -> int:
    """Read an explicit shared weekly cap from the immutable direction snapshot."""
    value = direction_scalar(direction, "max_scheduled_minutes_per_week")
    if value and value.isdecimal():
        cap = int(value)
        if 0 < cap <= 10080:
            return cap
    return 360


def direction_snapshot_metadata(direction: str) -> tuple[str | None, str | None]:
    """Return the date and timezone that make a run's liveness judgment reproducible."""
    return direction_scalar(direction, "snapshot_date"), direction_scalar(direction, "timezone")


def direction_bool(direction: str, key: str) -> bool | None:
    value = direction_scalar(direction, key)
    if value is None:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return None


def direction_integer(direction: str, key: str) -> int | None:
    value = direction_scalar(direction, key)
    return int(value) if value is not None and value.isdecimal() else None


def direction_string_list(direction: str, key: str) -> list[str]:
    """Read a simple indented YAML string list from the saved direction fixture."""
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*$", direction)
    if match is None:
        return []
    values: list[str] = []
    for line in direction[match.end():].splitlines():
        item = re.match(r"^\s*-\s+([^#\n]+?)\s*$", line)
        if item is None:
            if line.strip():
                break
            continue
        values.append(item.group(1))
    return values


def _string_or_null(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _integer_or_null(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def build_eusp_p1_judge_packet(profile_markdown: str, direction_yaml: str,
                                report: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project a final report into the P1 packet without consulting pipeline artifacts.

    The deliberately lossy projection has stable replacement IDs, so report-stage IDs
    and staged-pipeline provenance cannot act as treatment hints for a readiness judge.
    """
    snapshot_date, timezone = direction_snapshot_metadata(direction_yaml)
    candidates = report.get("candidates", []) if isinstance(report, dict) else []
    candidates = [item for item in candidates if isinstance(item, dict)]
    selected_ids = report.get("selected_ids", {}) if isinstance(report, dict) else {}
    ordered_ids: list[tuple[Any, str]] = []
    if isinstance(selected_ids, dict):
        for bucket, classification in (("act_now", "ACT_NOW"), ("prepare_next", "PREPARE_NEXT")):
            if isinstance(selected_ids.get(bucket), list):
                ordered_ids.extend((source_id, classification) for source_id in selected_ids[bucket])
    by_id = {item.get("candidate_id", item.get("id")): item for item in candidates
             if item.get("candidate_id", item.get("id")) is not None}
    selected_source: list[tuple[Any, dict[str, Any], str]] = []
    selection_errors: list[str] = []
    seen_ids: set[str] = set()
    for source_id, classification in ordered_ids:
        candidate = by_id.get(source_id)
        marker = str(source_id)
        if marker in seen_ids:
            selection_errors.append(f"duplicate selected candidate: {marker}")
        elif candidate is None:
            selection_errors.append(f"selected candidate missing from report: {marker}")
        else:
            selected_source.append((source_id, candidate, classification))
            seen_ids.add(marker)
    # A report may use classifications but omit selected_ids; this does not add a
    # candidate that was explicitly rejected, and keeps evidence absence visible.
    if not ordered_ids:
        for candidate in candidates:
            classification = _string_or_null(candidate.get("status", candidate.get("classification")))
            if classification in {"ACT_NOW", "PREPARE_NEXT"}:
                source_id = candidate.get("candidate_id", candidate.get("id"))
                marker = str(source_id)
                if marker not in seen_ids:
                    selected_source.append((source_id, candidate, classification))
                    seen_ids.add(marker)

    ledger = report.get("evidence_ledger", report.get("evidence", [])) if isinstance(report, dict) else []
    ledger = [item for item in ledger if isinstance(item, dict)] if isinstance(ledger, list) else []
    selected: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for number, (source_id, candidate, selected_classification) in enumerate(selected_source, 1):
        candidate_ref = f"c{number}"
        original_claim_ids = {str(item) for item in candidate.get("claim_ids", []) if isinstance(item, str)}
        linked_rows = [row for row in ledger
                       if str(row.get("candidate_id", row.get("candidate_ref", ""))) == str(source_id)
                       or str(row.get("claim_id", "")) in original_claim_ids]
        evidence_ids: list[str] = []
        evidence_ids_by_source_claim: dict[str, list[str]] = {}
        for row in linked_rows:
            evidence_id = f"e{len(evidence) + 1}"
            source_type = _string_or_null(row.get("source_type"))
            if source_type not in {"official_primary", "secondary"}:
                source_type = None
            evidence.append({
                "id": evidence_id, "candidate_ref": candidate_ref,
                "claim": _string_or_null(row.get("claim")), "source_type": source_type,
                "entailment": _string_or_null(row.get("entailment")),
                "quote": _string_or_null(row.get("quote", row.get("exact_quote"))),
                "url": _string_or_null(row.get("url", row.get("official_url"))),
                "retrieved_at": _string_or_null(row.get("retrieved_at", row.get("checked_at"))),
                "current_status": _string_or_null(row.get("current_status", row.get("status"))),
                "temporal": row.get("temporal") if isinstance(row.get("temporal"), dict) else {
                    "kind": _string_or_null(row.get("temporal_kind")),
                    "date": _string_or_null(row.get("deadline_date", row.get("event_date"))),
                    "start_date": _string_or_null(row.get("window_start_date")),
                    "end_date": _string_or_null(row.get("window_end_date")),
                },
                "supports": _string_list(row.get("supports")),
            })
            evidence_ids.append(evidence_id)
            source_claim_id = _string_or_null(row.get("claim_id"))
            if source_claim_id:
                evidence_ids_by_source_claim.setdefault(source_claim_id, []).append(evidence_id)
        source_material_claims = candidate.get("material_claims")
        source_material_claims = source_material_claims if isinstance(source_material_claims, list) else []
        material_claims = []
        for claim_number, material in enumerate(source_material_claims, 1):
            material = material if isinstance(material, dict) else {}
            source_claim_id = _string_or_null(material.get("id", material.get("claim_id")))
            material_claims.append({
                "id": f"m{number}-{claim_number}",
                "kind": _string_or_null(material.get("kind")),
                "evidence_ids": list(evidence_ids_by_source_claim.get(source_claim_id or "", [])),
            })
        bridge = candidate.get("profile_bridge", candidate.get("bridge", []))
        bridge = bridge if isinstance(bridge, list) else []
        first = candidate.get("first_action") if isinstance(candidate.get("first_action"), dict) else {}
        effort = candidate.get("scheduled_week_effort_minutes")
        effort = effort if isinstance(effort, dict) else {}
        selected.append({
            "id": candidate_ref, "rank": number,
            "title": _string_or_null(candidate.get("title")),
            "organization": _string_or_null(candidate.get("organization")),
            "type": _string_or_null(candidate.get("type")),
            # Bucket membership is authoritative; the reported status is retained only
            # to make a missing or conflicting report status fail closed in preflight.
            "classification": selected_classification,
            "reported_classification": _string_or_null(candidate.get("status", candidate.get("classification"))),
            "profile_bridge": [{"signal": _string_or_null(item.get("signal", item.get("profile_signal"))),
                                "why": _string_or_null(item.get("why", item.get("why_it_matters")))}
                               for item in bridge if isinstance(item, dict)],
            "first_action": {"action": _string_or_null(first.get("action")),
                             "deliverable": _string_or_null(first.get("deliverable")),
                             "start_by_or_trigger": _string_or_null(first.get("start_by_or_trigger")),
                             "start_date": _string_or_null(first.get("start_date", first.get("start_by_date"))),
                             "minutes_min": _integer_or_null(first.get("minutes_min")),
                             "minutes_max": _integer_or_null(first.get("minutes_max"))},
            "scheduled_week_effort_minutes": {"min": _integer_or_null(effort.get("min")),
                                                "max": _integer_or_null(effort.get("max"))},
            "blockers": _string_list(candidate.get("blockers")),
            "uncertainties": _string_list(candidate.get("uncertainties")),
            "blockers_disclosed": isinstance(candidate.get("blockers"), list),
            "uncertainties_disclosed": isinstance(candidate.get("uncertainties"), list),
            "evidence_ids": evidence_ids,
            "material_claims": material_claims,
        })
    allocation = report.get("weekly_allocation") if isinstance(report, dict) and isinstance(report.get("weekly_allocation"), dict) else {}
    packet = {
        "schema_version": "eusp-p1-judge-packet/v1",
        "evaluation_context": {
            "snapshot_date": snapshot_date, "timezone": timezone,
            "profile_markdown": profile_markdown,
            "direction": {"jobs_explicitly_requested": direction_bool(direction_yaml, "explicitly_requested"),
                          "max_act_now": direction_integer(direction_yaml, "max_act_now"),
                          "max_prepare_next": direction_integer(direction_yaml, "max_prepare_next"),
                          "max_scheduled_minutes_per_week": direction_integer(direction_yaml, "max_scheduled_minutes_per_week"),
                          "first_action_within_days": direction_integer(direction_yaml, "first_action_must_start_within_days"),
                          "first_action_max_minutes": direction_integer(direction_yaml, "first_action_max_minutes"),
                          "allowed_job_types": direction_string_list(direction_yaml, "allowed_types"),
                          "excluded_job_types": direction_string_list(direction_yaml, "exclude")},
        },
        "portfolio": {"selected": selected,
                      "weekly_allocation": {"cap_minutes": _integer_or_null(allocation.get("cap_minutes")),
                                            "scheduled_min_minutes": _integer_or_null(allocation.get("scheduled_min_minutes")),
                                            "scheduled_max_minutes": _integer_or_null(allocation.get("scheduled_max_minutes")),
                                            "residual_upper_minutes": _integer_or_null(allocation.get("residual_upper_minutes"))}},
        "evidence": evidence,
    }
    schema = read_json(ROOT / "evals/schemas/eusp_p1_judge_packet.schema.json")
    schema_errors = _schema_errors(packet, schema)
    diagnostics = {"schema_version": "eusp-p1-judge-packet-validation/v1",
                   "valid": not (schema_errors or selection_errors),
                   "errors": schema_errors + selection_errors}
    return packet, diagnostics


def normalize_report_ledger(report: dict[str, Any], verification: Any,
                            verification_hash: str, expected_cap: int = 360) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project model claims onto exact persisted verification rows, fail-closed."""
    import copy
    normalized = copy.deepcopy(report)
    triples: dict[tuple[str, str, str], dict[str, Any]] = {}
    official_urls: set[str] = set()
    for node in _walk_json(verification):
        quote = node.get("quote", node.get("exact_quote"))
        url = node.get("url", node.get("official_url"))
        retrieved = node.get("retrieved_at", node.get("checked_at", node.get("retrieved")))
        if str(node.get("source_type", "")).lower() == "official_primary" and isinstance(url, str):
            official_urls.add(url)
        if all(isinstance(item, str) for item in (quote, url, retrieved)):
            current = triples.get((quote, url, retrieved))
            if current is None or "official" in str(node.get("source_type", "")).lower():
                triples[(quote, url, retrieved)] = node
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    supports_by_candidate: dict[str, set[str]] = {}
    for index, row in enumerate(normalized.get("evidence_ledger", [])):
        if not isinstance(row, dict):
            removed.append({"index": index, "reason": "not_object"}); continue
        triple = (row.get("quote"), row.get("url"), row.get("retrieved_at"))
        source = triples.get(triple)
        official = source is not None and ("official" in str(source.get("source_type", "")).lower()
                                            or str(row.get("url")) in official_urls
                                            or isinstance(source.get("official_url"), str))
        direct = row.get("entailment") == "direct" and isinstance(row.get("supports"), list) and bool(row["supports"])
        claim_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(row.get("claim", ""))))
        quote_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(row.get("quote", ""))))
        temporal_scope_ok = not (claim_years - quote_years)
        if not official or not direct or not temporal_scope_ok:
            reason = ("claim_year_absent_from_exact_quote" if not temporal_scope_ok
                      else "no_exact_official_direct_verification_match")
            removed.append({"index": index, "candidate_id": row.get("candidate_id"),
                            "claim_id": row.get("claim_id"), "reason": reason,
                            "unsupported_years": sorted(claim_years - quote_years)})
            continue
        clean = copy.deepcopy(row)
        clean["verification_artifact_hash"] = verification_hash
        clean["source_type"] = "official_primary"
        kept.append(clean)
        supports_by_candidate.setdefault(str(clean.get("candidate_id")), set()).update(
            item for item in clean.get("supports", []) if isinstance(item, str))
    normalized["evidence_ledger"] = kept
    valid_claims = {str(row.get("claim_id")) for row in kept}
    candidates = {str(item.get("candidate_id")): item for item in normalized.get("candidates", [])
                  if isinstance(item, dict) and item.get("candidate_id") is not None}
    selected = normalized.get("selected_ids") if isinstance(normalized.get("selected_ids"), dict) else {}
    rows_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in kept:
        rows_by_candidate.setdefault(str(row.get("candidate_id")), []).append(row)
    for candidate_id, candidate in candidates.items():
        candidate["claim_ids"] = [claim for claim in candidate.get("claim_ids", []) if str(claim) in valid_claims]
        supports = supports_by_candidate.get(candidate_id, set())
        deadline_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(candidate.get("deadline", ""))))
        quoted_deadline_years = {year for row in rows_by_candidate.get(candidate_id, [])
                                 if "deadline" in row.get("supports", [])
                                 for year in re.findall(r"\b(?:19|20)\d{2}\b", str(row.get("quote", "")))}
        if deadline_years - quoted_deadline_years:
            candidate["deadline"] = None
            candidate.setdefault("uncertainties", []).append(
                "A model-supplied deadline year was removed because it was absent from the exact official quote.")
        actionable_evidence = "status" in supports and bool(supports & {"deadline", "event_date", "rolling_window"})
        if candidate.get("status") in {"ACT_NOW", "PREPARE_NEXT"} and not actionable_evidence:
            candidate["status"] = "MONITOR"
            for bucket in ("act_now", "prepare_next"):
                selected[bucket] = [item for item in selected.get(bucket, []) if item != candidate_id]
            if candidate_id not in selected.setdefault("monitor", []):
                selected["monitor"].append(candidate_id)
            candidate["scheduled_week_effort_minutes"] = {"min": 0, "max": 0}
            first = candidate.get("first_action") if isinstance(candidate.get("first_action"), dict) else {}
            candidate["first_action"] = {**first, "action": "No action this week; temporal or current-route evidence is incomplete.",
                                           "deliverable": "", "minutes_min": 0, "minutes_max": 0,
                                           "start_by_or_trigger": "Trigger: exact official status plus temporal evidence."}
    # Keep only directly supported current/temporal opportunities in the verified horizon.
    horizon = []
    demoted_leads = []
    for item in normalized.get("opportunity_horizon", []):
        if not isinstance(item, dict):
            continue
        candidate_id = str(item.get("candidate_id"))
        supports = supports_by_candidate.get(candidate_id, set())
        if "status" in supports and supports & {"deadline", "event_date", "rolling_window"}:
            horizon.append(item)
        else:
            demoted_leads.append({**item, "missing_evidence": "no exact official status plus temporal trigger"})
    normalized["opportunity_horizon"] = horizon
    normalized.setdefault("exploration_leads", []).extend(demoted_leads)
    verified_families = sorted({str(item.get("family")) for item in horizon if item.get("family")})
    breadth_summary = normalized.setdefault("breadth_summary", {})
    breadth_summary["families_with_verified_candidates"] = verified_families
    breadth_summary["materially_distinct_families_in_horizon"] = len(verified_families)
    breadth_summary["normalization_note"] = "Verified counts exclude exploration leads removed by exact evidence projection."
    action_ids = [item for key in ("act_now", "prepare_next") for item in selected.get(key, [])]
    total_min = total_max = 0
    allocations = []
    for candidate_id in action_ids:
        effort = candidates.get(str(candidate_id), {}).get("scheduled_week_effort_minutes", {})
        lower, upper = effort.get("min"), effort.get("max")
        if isinstance(lower, int) and isinstance(upper, int):
            total_min += lower; total_max += upper
            allocations.append({"candidate_id": candidate_id, "lower_minutes": lower, "upper_minutes": upper})
    normalized["weekly_allocation"] = {**normalized.get("weekly_allocation", {}),
        "cap_minutes": expected_cap, "scheduled_min_minutes": total_min,
        "scheduled_max_minutes": total_max, "residual_upper_minutes": expected_cap - total_max,
        "allocations": allocations}
    audit = {"kept_rows": len(kept), "removed_rows": removed,
             "demoted_horizon_items": [item.get("candidate_id") for item in demoted_leads],
             "normalized_at": utcnow()}
    return normalized, audit


def validate_production_output(report: Any, verification: Any, verification_hash: str | None,
                               expected_cap: int = 360) -> list[str]:
    """Fail-closed checks for the standalone production contract.

    This intentionally validates security-critical cross-artifact invariants in code;
    JSON Schema alone cannot prove quote equality or artifact-hash provenance.
    """
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["production report is not an object"]
    schema_path = ROOT / "evals/schemas/production_output.schema.json"
    try:
        schema = read_json(schema_path)
        errors.extend(f"schema: {message}" for message in _schema_errors(report, schema))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot load production schema: {error}"]
    required = {"snapshot_date", "profile_state", "trigger_hypotheses", "candidates",
                "selected_ids", "weekly_allocation", "evidence_ledger",
                "rejected_candidates", "uncertainty_summary"}
    errors.extend(f"missing required field: {key}" for key in sorted(required - set(report)))
    candidates = report.get("candidates") if isinstance(report.get("candidates"), list) else []
    ledger = report.get("evidence_ledger") if isinstance(report.get("evidence_ledger"), list) else []
    selected = report.get("selected_ids") if isinstance(report.get("selected_ids"), dict) else {}
    allocation = report.get("weekly_allocation") if isinstance(report.get("weekly_allocation"), dict) else {}
    if len(selected.get("act_now", [])) > 3:
        errors.append("ACT_NOW count exceeds 3")
    if len(selected.get("prepare_next", [])) > 4:
        errors.append("PREPARE_NEXT count exceeds 4")
    if allocation.get("cap_minutes") != expected_cap:
        errors.append(f"weekly cap must equal direction-declared {expected_cap}")
    maximum = allocation.get("scheduled_max_minutes")
    if not isinstance(maximum, int) or maximum < 0 or maximum > expected_cap:
        errors.append(f"scheduled_max_minutes must be an integer in 0..{expected_cap}")
    ledger_ids: set[str] = set()
    claim_ids: dict[str, dict[str, Any]] = {}
    source_triples: dict[tuple[str, str, str], dict[str, Any]] = {}
    verification_primary_required = any(node.get("primary_sources_required") is True
                                        for node in _walk_json(verification))
    official_urls = {str(node.get("official_url", node.get("url")))
                     for node in _walk_json(verification)
                     if str(node.get("source_type", "")).lower() == "official_primary"
                     and isinstance(node.get("official_url", node.get("url")), str)}
    for node in _walk_json(verification):
        quote = node.get("quote", node.get("exact_quote"))
        url = node.get("url", node.get("official_url"))
        retrieved = node.get("retrieved_at", node.get("checked_at", node.get("retrieved")))
        if all(isinstance(item, str) for item in (quote, url, retrieved)):
            source_triples[(quote, url, retrieved)] = node
    expected_hash = verification_hash or ""
    for index, row in enumerate(ledger):
        if not isinstance(row, dict):
            errors.append(f"ledger row {index} is not an object")
            continue
        lid, cid = row.get("ledger_id"), row.get("claim_id")
        if not isinstance(lid, str) or not lid or lid in ledger_ids:
            errors.append(f"ledger row {index} has missing/duplicate ledger_id")
        else:
            ledger_ids.add(lid)
        if not isinstance(cid, str) or not cid or cid in claim_ids:
            errors.append(f"ledger row {index} has missing/duplicate claim_id")
        else:
            claim_ids[cid] = row
        triple = (row.get("quote"), row.get("url"), row.get("retrieved_at"))
        source_node = source_triples.get(triple)
        if source_node is None:
            errors.append(f"ledger row {index} quote/url/retrieved_at does not exactly match verification")
        else:
            source_type = str(source_node.get("source_type", source_node.get("type", ""))).lower()
            explicit_official_url = isinstance(source_node.get("official_url"), str)
            if ("official" not in source_type and not explicit_official_url
                    and str(triple[1]) not in official_urls):
                errors.append(f"ledger row {index} is not marked as an official source in verification")
        supplied_hash = str(row.get("verification_artifact_hash", "")).removeprefix("sha256:")
        if not expected_hash or supplied_hash != expected_hash:
            errors.append(f"ledger row {index} verification artifact hash mismatch")
        if row.get("entailment") != "direct":
            errors.append(f"ledger row {index} entailment is not direct")
        claim_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(row.get("claim", ""))))
        quote_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(row.get("quote", ""))))
        if claim_years - quote_years:
            errors.append(f"ledger row {index} claim year is absent from exact quote: {sorted(claim_years - quote_years)}")
    candidate_by_id = {item.get("candidate_id"): item for item in candidates
                       if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)}
    for index, row in enumerate(ledger):
        if isinstance(row, dict) and row.get("candidate_id") not in candidate_by_id:
            errors.append(f"ledger row {index} references unknown candidate")
    scheduled_sum = 0
    for cid in selected.get("act_now", []) + selected.get("prepare_next", []):
        item = candidate_by_id.get(cid)
        if item is None:
            errors.append(f"selected candidate missing from candidates: {cid}")
            continue
        effort = item.get("scheduled_week_effort_minutes", {})
        if isinstance(effort, dict) and isinstance(effort.get("max"), int):
            scheduled_sum += effort["max"]
        else:
            errors.append(f"selected candidate has no integer scheduled max: {cid}")
    if isinstance(maximum, int) and scheduled_sum != maximum:
        errors.append(f"scheduled candidate sum {scheduled_sum} != allocation maximum {maximum}")
    for cid in selected.get("monitor", []):
        item = candidate_by_id.get(cid, {})
        if item.get("scheduled_week_effort_minutes", {}).get("max") != 0:
            errors.append(f"MONITOR candidate schedules weekly effort: {cid}")
    for cid in selected.get("act_now", []) + selected.get("prepare_next", []):
        item = candidate_by_id.get(cid, {})
        deadline_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(item.get("deadline", ""))))
        if deadline_years:
            referenced = [claim_ids[ref] for ref in item.get("claim_ids", []) if ref in claim_ids]
            quoted_years = {year for row in referenced if "deadline" in row.get("supports", [])
                            for year in re.findall(r"\b(?:19|20)\d{2}\b", str(row.get("quote", "")))}
            if deadline_years - quoted_years:
                errors.append(f"selected deadline year lacks exact quote support: {cid} {sorted(deadline_years - quoted_years)}")
    for cid in selected.get("act_now", []):
        item = candidate_by_id.get(cid, {})
        refs = item.get("claim_ids") if isinstance(item.get("claim_ids"), list) else []
        rows = [claim_ids[ref] for ref in refs if ref in claim_ids]
        supports = {kind for row in rows for kind in row.get("supports", []) if isinstance(kind, str)}
        temporal_support = {"deadline", "event_date", "rolling_window"} & supports
        if not refs or "status" not in supports or not temporal_support:
            errors.append(f"ACT_NOW lacks ledger-backed status and temporal trigger: {cid}")
    return errors


def run_research(args: argparse.Namespace) -> int:
    config = VARIANTS[args.variant]
    runs_root = Path(args.runs_dir).resolve()
    if args.resume:
        run = Path(args.resume).resolve()
        manifest_path = run / "manifest.json"
        if not manifest_path.is_file():
            raise SystemExit(f"--resume requires an existing run manifest: {manifest_path}")
        manifest = read_json(manifest_path)
        if manifest.get("variant") != args.variant:
            raise SystemExit("--variant must match resumed manifest")
        run_id = manifest["run_id"]
    else:
        run_id = f"{utcnow().replace(':', '').replace('+00:00', 'Z')}-{uuid.uuid4().hex[:12]}"
        run = runs_root / run_id
        run.mkdir(parents=True, exist_ok=False)
        profile_path = Path(args.profile_path).expanduser().resolve() if args.profile_path else None
        direction_path = Path(args.direction_path).expanduser().resolve() if args.direction_path else None
        rubric_path = Path(args.rubric_path).expanduser().resolve() if args.rubric_path else None
        hashes = snapshot_inputs(run, args.variant, profile_path, direction_path, rubric_path)
        manifest = {"run_id": run_id, "created_at": utcnow(), "variant": args.variant,
                    "input_sources": {"profile": str(profile_path or ROOT / 'usr/profile.md'),
                                      "direction": str(direction_path or ROOT / 'evals/direction.yaml'),
                                      "rubric": str(rubric_path or ROOT / 'evals/rubric.yaml')},
                    "reused_artifacts_from": args.reuse_run, "start_stage": args.start_stage,
                    "pipeline_mode": config["mode"], "stages": list(config["stages"]),
                    "success_or_failure_state": "pending; final state is immutable summary.json",
                    "generation": args.generation, "repeat": args.repeat, "parent_run_ids": args.parent_run,
                    "worker_model": args.worker_model, "judge_model": args.judge_model,
                    "seed": args.seed, "git_revision": git_revision(), "input_hashes": hashes,
                    "timeouts": {"per_call_seconds": args.timeout, "deadline_seconds": args.deadline_seconds,
                                 "finalization_reserve_seconds": args.finalization_reserve},
                    "dry_run": args.dry_run}
        write_json(run / "manifest.json", manifest)
        atomic_write(run / "pipeline.yaml", "variant: " + args.variant + "\nmode: " + config["mode"] + "\nstages:\n" + "".join(f"  - {stage}\n" for stage in config["stages"]))
        # Required immutable snapshot name; inputs/ remains the runner's canonical copy.
        snapshot = run / "input_snapshot"
        snapshot.mkdir(parents=True, exist_ok=False)
        for source in sorted((run / "inputs").rglob("*")):
            if source.is_file():
                relative = source.relative_to(run / "inputs")
                destination = snapshot / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(destination, source.read_text(encoding="utf-8"))
        append_jsonl(run / "events.jsonl", {"at": utcnow(), "state": "created", "run_id": run_id})
    direction_snapshot = (run / "inputs/direction.yaml").read_text(encoding="utf-8")
    snapshot_date, timezone = direction_snapshot_metadata(direction_snapshot)
    if args.variant.startswith("P1_") and (not snapshot_date or not timezone):
        raise SystemExit("P1 runs require snapshot_date and timezone in the saved direction snapshot")
    deadline_at = time.monotonic() + args.deadline_seconds
    previous: dict[str, Any] = {}
    failed = False
    reuse_run = Path(args.reuse_run).resolve() if args.reuse_run else None
    if args.start_stage and args.start_stage not in config["stages"]:
        raise SystemExit(f"--start-stage must be one of: {', '.join(config['stages'])}")
    start_index = config["stages"].index(args.start_stage) if args.start_stage else 0
    for stage in config["stages"]:
        stage_index = config["stages"].index(stage)
        prior_stages = config["stages"][:stage_index]
        if reuse_run is not None and stage_index < start_index:
            source = completed_result(reuse_run, stage)
            if source is None:
                raise SystemExit(f"reuse source has no completed {stage}: {reuse_run}")
            value = read_json(source)
            previous[stage] = value
            write_json(run / f"{stage}.result.json", value)
            write_json(run / f"{stage}.status.json", {"state": "complete", "finished_at": utcnow(),
                                                        "reused_from": str(source), "source_hash": sha256_file(source),
                                                        "model_call": False})
            append_jsonl(run / "events.jsonl", {"at": utcnow(), "name": stage, "state": "complete",
                                                 "reused_from": str(source), "model_call": False})
            continue
        result_file = None if stage in args.force_stage else completed_result(run, stage)
        if result_file is not None:
            previous[stage] = read_json(result_file)
            continue
        artifact_name = next_attempt_name(run, stage)
        if any(prior not in previous for prior in prior_stages):
            # Dependency failure: preserve an explicit skipped attempt, never fabricate a result.
            write_json(run / f"{artifact_name}.status.json", status_for({}, "prior stage did not complete"))
            append_jsonl(run / "events.jsonl", {"at": utcnow(), "name": artifact_name, "role": "worker", "state": "skipped", "reason": "prior stage did not complete"})
            failed = True
            continue
        left = remaining(deadline_at, args.finalization_reserve)
        if left <= 0:
            write_json(run / f"{artifact_name}.status.json", status_for({}, "global deadline reached"))
            append_jsonl(run / "events.jsonl", {"at": utcnow(), "name": artifact_name, "role": "worker", "state": "skipped", "reason": "global deadline reached"})
            failed = True
            continue
        payload = {"run_id": run_id, "stage": stage, "variant": args.variant,
                   "pipeline_mode": config["mode"],
                   # Report-only serialization instructions must not alter upstream staged work.
                   "variant_instructions": variant_instructions(args.variant, stage),
                   "profile": (run / "inputs/profile.md").read_text(encoding="utf-8"),
                   "direction": direction_snapshot,
                   "snapshot_date": snapshot_date, "timezone": timezone,
                   "prior_artifacts": previous,
                   "prior_artifact_hashes": {prior: sha256_file(completed_result(run, prior))
                                              for prior in prior_stages if completed_result(run, prior) is not None},
                   "input_hashes": manifest["input_hashes"],
                   "schema_contract": stage_contract(stage)}
        prompt = model_prompt(stage, payload)
        call = call_pi(prompt, args.worker_model, min(args.timeout, left), args.dry_run,
                       args.pi_output_mode)
        if not args.dry_run and call.get("parse_error") is None:
            call["parse_error"] = stage_result_error(stage, call.get("result"), args.variant.startswith("P1_"))
        normalization_audit = None
        if (stage == "report" and config.get("normalize_ledger") and isinstance(call.get("result"), dict)
                and "verification" in previous):
            verification_path = completed_result(run, "verification")
            if verification_path is not None:
                write_json(run / f"{artifact_name}.model_result.json", call["result"])
                expected_cap = direction_effort_cap((run / "inputs/direction.yaml").read_text(encoding="utf-8"))
                call["result"], normalization_audit = normalize_report_ledger(
                    call["result"], previous["verification"], sha256_file(verification_path), expected_cap)
        status = persist_call(run, artifact_name, payload, prompt, call, "worker", run_id, args.worker_model)
        if normalization_audit is not None:
            write_json(run / f"{artifact_name}.normalization.json", normalization_audit)
        if status["state"] == "complete":
            previous[stage] = call["result"]
        else:
            failed = True
    if args.variant in PRODUCTION_VARIANTS and not args.dry_run:
        verification_file = completed_result(run, "verification")
        expected_cap = direction_effort_cap((run / "inputs/direction.yaml").read_text(encoding="utf-8"))
        validation_errors = validate_production_output(previous.get("report"), previous.get("verification"),
                                                       sha256_file(verification_file) if verification_file else None,
                                                       expected_cap)
        write_json(next_versioned_file(run, "production_validation"),
                   {"valid": not validation_errors, "errors": validation_errors,
                    "checked_at": utcnow(),
                    "schema": "evals/schemas/production_output.schema.json"})
        for message in validation_errors:
            append_jsonl(run / "errors.jsonl", {"at": utcnow(), "stage": "production_validation", "error": message})
        failed |= bool(validation_errors)
    if args.variant.startswith("P1_"):
        # A packet is derived only from a completed report. Its external diagnostics
        # bind both immutable artifacts without exposing report/pipeline metadata to
        # the blinded judge. A resumed, replaced report gets a versioned packet.
        report_file = completed_result(run, "report")
        if report_file is not None:
            report_hash = sha256_file(report_file)
            current_packet = latest_versioned_artifact(run, "judge_packet")
            current_diagnostics = (current_packet.with_name(current_packet.name.replace("judge_packet", "judge_packet_validation", 1))
                                   if current_packet is not None else None)
            already_bound = False
            if current_diagnostics is not None and current_diagnostics.is_file():
                diagnostics = read_json(current_diagnostics)
                already_bound = isinstance(diagnostics, dict) and diagnostics.get("report_sha256") == report_hash
            if not already_bound:
                packet, packet_diagnostics = build_eusp_p1_judge_packet(
                    (run / "inputs/profile.md").read_text(encoding="utf-8"), direction_snapshot,
                    read_json(report_file))
                packet_path = next_versioned_file(run, "judge_packet")
                diagnostics_path = packet_path.with_name(packet_path.name.replace("judge_packet", "judge_packet_validation", 1))
                if diagnostics_path.exists():
                    raise FileExistsError(f"packet diagnostics already exist: {diagnostics_path}")
                write_json(packet_path, packet)
                packet_diagnostics["report_sha256"] = report_hash
                packet_diagnostics["packet_sha256"] = sha256_file(packet_path)
                write_json(diagnostics_path, packet_diagnostics)
    summary = {"run_id": run_id, "variant": args.variant, "path": str(run), "state": "partial" if failed else "complete",
               "completed_stages": sorted(previous), "finished_at": utcnow(), "dry_run": args.dry_run}
    # Finalization gets separate immutable records, leaving raw calls and manifest untouched.
    materialize_required_artifacts(run, previous)
    write_json(next_versioned_file(run, "summary"), summary)
    append_jsonl(ROOT / "experiments/registry.jsonl", {"kind": "research_run", **summary,
                                                       "worker_model": args.worker_model, "generation": args.generation, "repeat": args.repeat})
    print(jdump(summary), end="")
    return 0 if not failed else 2


def latest_versioned_artifact(folder: Path, stem: str) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    base = folder / f"{stem}.json"
    if base.is_file():
        candidates.append((1, base))
    for path in folder.glob(f"{stem}.attempt-*.json"):
        match = re.fullmatch(re.escape(stem) + r"\.attempt-(\d+)\.json", path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    return max(candidates, default=(-1, None))[1]


def load_saved_bundle(run: Path, target: str) -> dict[str, Any]:
    manifest = read_json(run / "manifest.json")
    report = completed_result(run, target)
    if report is None:
        raise FileNotFoundError(f"no completed saved artifact for: {target}")
    artifacts: dict[str, Any] = {target: read_json(report)}
    artifact_paths: dict[str, Path] = {target: report}
    # Judges can inspect persisted evidence without any research call.
    for stage in ("verification", "actionability", "ranking"):
        path = completed_result(run, stage)
        if path is not None and stage != target:
            artifacts[stage] = read_json(path)
            artifact_paths[stage] = path
    validation = latest_versioned_artifact(run, "production_validation")
    if validation is not None:
        artifacts["production_validation"] = read_json(validation)
        artifact_paths["production_validation"] = validation
    return {"artifact_hashes": {name: sha256_file(path) for name, path in artifact_paths.items()},
            "artifacts": artifacts, "run_created_at": manifest.get("created_at")}


def judge_prompt(role: str, bundle: dict[str, Any], rubric: str) -> str:
    focus = {
        "evidence": "Own only evidence/liveness and hard factual gates. Unsupported breadth earns zero; do not reward plausible prose.",
        "actionability": "Own only selected-action quality, effort reconciliation, and real safe stretch action quality.",
        "personalization": "Own only profile bridges, adaptation/belonging value, identity expansion, genericity, and strategy.",
        "breadth": "Own only evidence-backed family diversity, dated geographic-window coverage, participation-role diversity, awareness value, and anti-collapse quality. Do not count unsupported monitors.",
        "academic_depth": "Own only graduate-route depth, complete funding analysis, TOEFL/language path quality, and academic anchor-decision completeness. Do not browse or infer admissions, funding, or exam facts.",
        "readiness": "Own only P1 gate-first readiness to act: grounding and liveness are hard gates, then score the five equal selected-action readiness checks. Do not reward list length.",
    }[role]
    return f"""You are the {role} judge. {focus}
This is evaluation only: do NOT research, browse, add facts, or infer facts outside the supplied
saved artifacts. Assess evidence and uncertainty only from this material. Return ONLY valid JSON
with judge_role set exactly to "{role}", hard_failures, owned_dimension_scores, penalties,
verdict (accept|conditional|reject), reasoning, failure_tags. Do not emit an overall score unless
all rubric dimensions are owned by your role; use null for unowned dimensions.
Rubric snapshot:\n{rubric}\nSAVED ARTIFACT BUNDLE:\n{jdump(bundle)}"""


def run_judge(args: argparse.Namespace) -> int:
    run = Path(args.run).resolve()
    manifest = read_json(run / "manifest.json")
    bundle = load_saved_bundle(run, args.target)
    rubric_path = (Path(args.rubric_path).expanduser().resolve()
                   if args.rubric_path else run / "inputs/rubric.yaml")
    if not rubric_path.is_file():
        raise SystemExit("judge-only mode requires a saved or explicit rubric")
    rubric = rubric_path.read_text(encoding="utf-8")
    judge_id = f"judge-{utcnow().replace(':', '').replace('+00:00', 'Z')}-{uuid.uuid4().hex[:8]}"
    folder = run / "judges" / judge_id
    folder.mkdir(parents=True, exist_ok=False)
    write_json(folder / "manifest.json", {"judge_id": judge_id, "parent_run_id": manifest["run_id"],
                                           "target": args.target, "roles": args.roles, "model": args.judge_model,
                                           "created_at": utcnow(), "artifact_hashes": bundle["artifact_hashes"],
                                           "rubric_path": str(rubric_path), "rubric_hash": sha256_file(rubric_path),
                                           "dry_run": args.dry_run})
    deadline_at = time.monotonic() + args.deadline_seconds
    failures = False
    outputs: list[dict[str, Any]] = []
    for index, role in enumerate(args.roles, 1):
        left = remaining(deadline_at, args.finalization_reserve)
        if left <= 0:
            write_json(folder / f"{index:02d}-{role}.status.json", status_for({}, "global deadline reached"))
            failures = True
            continue
        input_data = {"judge_role": role, "bundle": bundle, "rubric": rubric}
        prompt = judge_prompt(role, bundle, rubric)
        call = call_pi(prompt, args.judge_model, min(args.timeout, left), args.dry_run,
                       args.pi_output_mode)
        status = persist_call(folder, f"{index:02d}-{role}", input_data, prompt, call, "judge", manifest["run_id"], args.judge_model)
        if status["state"] == "complete" and isinstance(call.get("result"), dict):
            record = {"judge_id": judge_id, "role": role, "model": args.judge_model,
                      "artifact_hashes": bundle["artifact_hashes"], "result": call["result"]}
            outputs.append(record)
            append_jsonl(run / "judge_outputs.jsonl", record)
        failures |= status["state"] != "complete"
    evaluation = {"judge_id": judge_id, "parent_run_id": manifest["run_id"],
                  "artifact_hashes": bundle["artifact_hashes"], "outputs": outputs,
                  "state": "partial" if failures else "complete"}
    write_json(run / f"evaluation.{judge_id}.json", evaluation)
    summary = {"kind": "judge_run", "judge_id": judge_id, "parent_run_id": manifest["run_id"],
               "path": str(folder), "state": "partial" if failures else "complete", "finished_at": utcnow()}
    write_json(folder / "summary.json", summary)
    append_jsonl(ROOT / "experiments/registry.jsonl", summary)
    print(jdump(summary), end="")
    return 0 if not failures else 2


def add_common_limits(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=float, default=900, help="maximum seconds for one pi call")
    parser.add_argument("--deadline-seconds", type=float, default=10800, help="global wall-clock budget")
    parser.add_argument("--finalization-reserve", type=float, default=60, help="seconds reserved for artifact writing")
    parser.add_argument("--dry-run", action="store_true", help="write smoke artifacts but make no model calls")
    parser.add_argument("--pi-output-mode", choices=("json", "text"), default="json",
                        help="text avoids quadratic JSON streaming artifacts for large final responses")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research", help="create one immutable research run (V0-V7)")
    research.add_argument("--variant", choices=VARIANTS, default="V0")
    research.add_argument("--runs-dir", default=str(ROOT / "runs"))
    research.add_argument("--worker-model", choices=MODELS, default=MODELS[0])
    research.add_argument("--judge-model", choices=MODELS, default=MODELS[0], help="recorded for later judge calls")
    research.add_argument("--generation", type=int, default=0)
    research.add_argument("--repeat", type=int, default=1)
    research.add_argument("--seed", type=int, default=None)
    research.add_argument("--parent-run", action="append", default=[])
    research.add_argument("--resume", help="only fill missing artifacts in this existing immutable run")
    research.add_argument("--profile-path", help="profile snapshot to copy into a new run; defaults to immutable usr/profile.md")
    research.add_argument("--direction-path", help="direction snapshot to copy into a new run; defaults to evals/direction.yaml")
    research.add_argument("--rubric-path", help="rubric snapshot to copy into a new run; defaults to evals/rubric.yaml")
    research.add_argument("--reuse-run", help="reuse persisted prefix artifacts from this run for a controlled downstream-stage experiment")
    research.add_argument("--start-stage", help="first stage to execute when --reuse-run is set")
    research.add_argument("--force-stage", action="append", default=[], choices=STAGED,
                          help="rerun a completed stage as a new immutable attempt")
    add_common_limits(research)
    research.set_defaults(func=run_research)
    judge = sub.add_parser("judge", help="judge saved artifacts only; never starts research")
    judge.add_argument("--run", required=True, help="path to an existing immutable run")
    judge.add_argument("--target", default="report", help="saved artifact name to judge")
    judge.add_argument("--roles", nargs="+", choices=ALL_ROLES, default=list(ROLES), help="independent blinded roles")
    judge.add_argument("--judge-model", choices=MODELS, default=MODELS[0])
    judge.add_argument("--rubric-path", help="explicit evaluation rubric; hash is persisted in judge manifest")
    add_common_limits(judge)
    judge.set_defaults(func=run_judge)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
