# Breadth evaluation design

## Scope and inputs

This evaluation is for the expanded profile and `direction_breadth_v2.yaml`. It evaluates only persisted run artifacts. `tools/score_breadth.py --run RUN_DIR` reads `report.result.json` and the highest numbered `production_validation.attempt-*.json` (or `production_validation.json` when no attempt exists). It is a stdlib-only diagnostic: it makes no model, browser, or web calls and cannot repair a report.

The breadth rubric is `evals/rubric_breadth.yaml`. It separates the small scheduled action portfolio from the opportunity horizon. The latter is useful only when it preserves evidence-backed alternatives; it is not a quota for links.

## Measurement and gates

Run the deterministic diagnostics before judging:

```sh
python3 tools/score_breadth.py --run runs/RUN_ID
```

Record schema/validation state, candidate and horizon counts, raw and evidence-backed family counts, dated geographic-window hits, selected family/geography duplication, effort reconciliation, stretch status, monitor-effort violations, and uncertainty counts. Counts are diagnostic rather than a scalar reward.

A report is ineligible for promotion if the latest persisted production validation fails, selected ACT_NOW claims lack liveness evidence, selected effort exceeds or fails to reconcile to 360 minutes, a monitor schedules effort, or a non-empty stretch is merely monitor/save/wait. Geographic credit requires direct dated overlap, not a location name.

## Promotion policy

Promote only when all of the following hold:

1. At least two valid repeats pass every hard gate.
2. Evidence/liveness does not regress against the incumbent.
3. The candidate is not Pareto-dominated on gated quality, verified family diversity, verified geographic coverage, actionable quality, adaptation/belonging value, and persisted cost/duration.
4. Blinded pairwise results are order-stable.
5. The aggregate breadth-rubric improvement is at least five points, unless a hard-gate repair is the sole change.

Cost is a tie-breaker only among equivalently gated candidates. Missing provider cost remains unknown; it must not be converted into a cheapness reward.

## Pareto policy

Compare candidates using a vector, not horizon length:

- evidence/liveness and hard-gate status first;
- actionable quality and reconciled weekly effort;
- evidence-backed distinct families and dated geographic windows;
- identity-role expansion plus adaptation/belonging value;
- valid optional stretch quality;
- genericity control; and
- persisted cost and duration.

A run is dominated when another run is at least as good on every applicable axis, strictly better on one, and has no evidence/liveness regression. A larger horizon with unsupported entries never dominates a smaller, fully supported horizon.

## Convergence policy

Stop after two generations without a promotable variant, after three wall-clock hours, or earlier if remaining changes only add unsupported breadth. Report incomplete repeats, failed validations, and unknown cost explicitly. Do not infer hidden-holdout performance from this profile-scoped evaluation.

## Anti-reward warnings

Do **not** reward any of the following:

- family labels, role labels, or geography strings without direct evidence;
- undated Cape Town/South Africa organization descriptions as geographic-window coverage;
- `MONITOR`, `save`, `wait`, or `check later` as a stretch action;
- multiple variants of one event/program as family diversity;
- generic networking prose as identity expansion or belonging;
- zero-effort monitors as verified participation pathways; or
- extra links that obscure uncertainty, stale status, eligibility gaps, or a failed production validation.

Empty family, geography, and stretch slots are valid outcomes when the saved evidence cannot support them. The evaluator should prefer an explicit search gap over unsupported breadth.
