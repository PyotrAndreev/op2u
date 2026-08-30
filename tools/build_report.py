#!/usr/bin/env python3
"""Build a static experiment report from immutable run, judge, and comparison artifacts.

No model calls are made by this tool.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from run_experiment import ROOT, atomic_write, completed_result, utcnow


def read_json_if(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def latest_summary(folder: Path) -> Any:
    files = [folder / "summary.json"] + sorted(folder.glob("summary.attempt-*.json"))
    for path in reversed(files):
        value = read_json_if(path)
        if isinstance(value, dict):
            return value
    return {}


def cost_total(folder: Path) -> tuple[int, float, float | None]:
    calls = 0
    seconds = 0.0
    money = 0.0
    has_money = False
    files = [folder / "costs.jsonl"]
    for file in files:
        if not file.is_file():
            continue
        for line in file.read_text(encoding="utf-8").splitlines():
            value = read_json_line(line)
            if not isinstance(value, dict):
                continue
            calls += 1
            seconds += float(value.get("duration_seconds") or 0)
            estimated = value.get("estimated_cost")
            if isinstance(estimated, (int, float)):
                money += float(estimated)
                has_money = True
            elif isinstance(estimated, dict) and isinstance(estimated.get("total"), (int, float)):
                money += float(estimated["total"])
                has_money = True
    return calls, seconds, money if has_money else None


def read_json_line(line: str) -> Any:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def stage_state(run: Path, stage: str) -> str:
    if completed_result(run, stage) is not None:
        return "complete"
    statuses = [run / f"{stage}.status.json"] + sorted(run.glob(f"{stage}.attempt-*.status.json"))
    for path in reversed(statuses):
        value = read_json_if(path, {})
        if isinstance(value, dict) and "state" in value:
            return value["state"]
    return "missing"


def score_from(value: Any) -> str:
    if isinstance(value, dict) and isinstance(value.get("score"), (int, float)):
        return str(value["score"])
    return "—"


def build(args: argparse.Namespace) -> int:
    runs_dir = Path(args.runs_dir).resolve()
    comparisons_dir = Path(args.comparisons_dir).resolve()
    output = Path(args.output).resolve() if args.output else (Path(args.reports_dir).resolve() / f"experiment-report-{utcnow().replace(':', '').replace('+00:00', 'Z')}.md")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite report: {output}")
    runs: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    if runs_dir.is_dir():
        for directory in sorted(runs_dir.iterdir()):
            manifest, summary = read_json_if(directory / "manifest.json"), latest_summary(directory)
            if isinstance(manifest, dict):
                runs.append((directory, manifest, summary if isinstance(summary, dict) else {}))
    comparisons: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    if comparisons_dir.is_dir():
        for directory in sorted(comparisons_dir.iterdir()):
            manifest, summary = read_json_if(directory / "manifest.json"), latest_summary(directory)
            if isinstance(manifest, dict):
                comparisons.append((directory, manifest, summary if isinstance(summary, dict) else {}))
    lines = ["# Experiment report", "", f"Generated: {utcnow()}", "",
             "This report is an artifact inventory, not a claim of hidden-holdout performance.",
             "It is built solely from persisted runs and never makes model calls.", "",
             "## Research runs", "", "| Run | Variant | Mode | State | Worker model | Calls | Time (s) | Cost | Stages |", "|---|---|---|---|---|---:|---:|---:|---|"]
    if not runs:
        lines.append("| — | — | — | no runs | — | 0 | 0 | unknown | — |")
    total_calls, total_seconds, total_cost = 0, 0.0, 0.0
    known_cost = False
    for directory, manifest, summary in runs:
        calls, seconds, cost = cost_total(directory)
        total_calls += calls; total_seconds += seconds
        if cost is not None:
            total_cost += cost; known_cost = True
        stages = manifest.get("stages", [])
        rendered_stages = ", ".join(f"{stage}:{stage_state(directory, stage)}" for stage in stages)
        lines.append("| {id} | {variant} | {mode} | {state} | {model} | {calls} | {seconds:.1f} | {cost} | {stages} |".format(
            id=manifest.get("run_id", directory.name), variant=manifest.get("variant", "—"),
            mode=manifest.get("pipeline_mode", "—"), state=summary.get("state", "unfinished"),
            model=manifest.get("worker_model", "—"), calls=calls, seconds=seconds,
            cost="unknown" if cost is None else f"{cost:.6g}", stages=rendered_stages or "—"))
        judges = directory / "judges"
        if judges.is_dir():
            for judge in sorted(judges.iterdir()):
                judge_summary = latest_summary(judge)
                jc, js, jcost = cost_total(judge)
                total_calls += jc; total_seconds += js
                if jcost is not None:
                    total_cost += jcost; known_cost = True
                if isinstance(judge_summary, dict):
                    lines.append(f"| ↳ {judge_summary.get('judge_id', judge.name)} | judge | saved-artifact | {judge_summary.get('state', 'unfinished')} | — | {jc} | {js:.1f} | {'unknown' if jcost is None else f'{jcost:.6g}'} | roles persisted |")
    lines += ["", "## Blinded pairwise comparisons", "", "| Comparison | State | Valid votes | A wins | B wins | Ties |", "|---|---|---:|---:|---:|---:|"]
    if not comparisons:
        lines.append("| — | no comparisons | 0 | 0 | 0 | 0 |")
    for directory, manifest, summary in comparisons:
        calls, seconds, cost = cost_total(directory)
        total_calls += calls; total_seconds += seconds
        if cost is not None:
            total_cost += cost; known_cost = True
        wins = summary.get("wins_by_blinded_label", {})
        lines.append("| {id} | {state} | {valid} | {a} | {b} | {tie} |".format(
            id=manifest.get("comparison_id", directory.name), state=summary.get("state", "unfinished"),
            valid=summary.get("valid_calls", 0), a=wins.get("A", 0), b=wins.get("B", 0), tie=wins.get("tie", 0)))
    lines += ["", "## Accounting and limitations", "", f"- Persisted subprocess calls: {total_calls}", f"- Persisted subprocess time: {total_seconds:.1f} seconds",
             f"- Provider-reported/estimated cost total: {total_cost:.6g}" if known_cost else "- Provider-reported/estimated cost total: unknown",
             "- Missing usage remains unknown; it is not estimated from text.",
             "- Failed, timed-out, skipped, and malformed calls remain in their run directories.",
             "- Pairwise A/B mappings are intentionally kept in each comparison's `mapping.private.json`, not reproduced here.", ""]
    atomic_write(output, "\n".join(lines))
    print(output)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--runs-dir", default=str(ROOT / "runs"))
    result.add_argument("--comparisons-dir", default=str(ROOT / "experiments/comparisons"))
    result.add_argument("--reports-dir", default=str(ROOT / "experiments/reports"))
    result.add_argument("--output", help="new report path; existing paths are refused")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(build(parser().parse_args()))
    except (FileExistsError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
