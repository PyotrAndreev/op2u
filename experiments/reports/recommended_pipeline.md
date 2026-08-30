# Recommended pipeline

Use the following as the production architecture, with a runner that persists and validates every stage.

## Stages

1. **Profile state:** extract durable facts, active trajectories, current context, reusable assets, constraints, decisions, explicit unknowns, and source/profile locations.
2. **Triggers:** derive dated events, changes, windows, and context intersections; distinguish hypotheses from facts.
3. **Discovery:** search broadly and cheaply across grants, CFPs, communities, collaborations, and other allowed opportunity types. Exclude jobs and generic employment moves.
4. **Verification:** use official primary sources where possible. Capture status, deadline, eligibility, retrieval time, and exact quotes. Do not infer legal, visa, citizenship, authorization, medical, or compensation facts from silence.
5. **Actionability:** create a causal bridge from at least two profile signals or reusable assets to each serious candidate. Define an atomic tangible first action startable within seven days, with a minute range and blocker/uncertainty.
6. **Ranking/allocation:** apply hard gates before scores. Permit `ACT_NOW` only with official live/upcoming status and deadline evidence, a profile bridge, and a feasible first action. Allocate the upper bound of every action actually scheduled in the next seven days; keep first-action, scheduled-week, and total-completion effort separate. Select no more than three `ACT_NOW`, four `PREPARE_NEXT`, and six hours/360 minutes of scheduled effort. `MONITOR` receives no weekly action. `PREPARE_NEXT` requires a verified upcoming-window artifact reason before consuming weekly budget. Allow at most one constrained serendipity item, subject to the same gates.
7. **Report:** render only selected, supported claims; retain explicit unknowns and downgrade or omit unsupported claims.

## Runner-enforced exact-quote evidence ledger

This is a schema and validation requirement. The model's prose cannot satisfy it by assertion, and a judge cannot repair a missing record. Every material factual claim in a candidate or final report must reference one or more `evidence_ledger` rows. The runner must validate that the quote, URL, and retrieval timestamp are byte-for-byte copied from a persisted verification artifact, that the verification artifact hash matches, and that the claim is directly entailed by the quote. A missing, altered, paraphrased, or unmatched row is a schema failure; the claim must be removed/downgraded and the candidate cannot be `ACT_NOW`.

Minimum row shape:

```json
{
  "ledger_id": "ev-001",
  "claim_id": "claim-canopie-status",
  "candidate_id": "canopie-2026",
  "claim": "The official call is open and closes on the stated date.",
  "quote": "exact verbatim quote from the saved verification artifact",
  "url": "https://official.example/source",
  "retrieved_at": "2026-08-02T12:00:00Z",
  "verification_artifact": "verification.result.json",
  "verification_artifact_hash": "sha256:...",
  "entailment": "direct",
  "supports": ["status", "deadline"]
}
```

The runner must also require: unique IDs; HTTPS or explicitly recorded official URLs; ISO timestamps; non-empty exact quotes for status/deadline/eligibility claims; claim-to-ledger references in every candidate; and a final report claim map. It must fail closed on malformed JSON, absent ledger rows, hash mismatch, quote mismatch, unsupported `ACT_NOW` status/deadline/eligibility, stale status, count overflow, or scheduled effort over 360 minutes. Preserve raw stdout/stderr and partial artifacts for diagnosis.

## Ranking evidence and comparisons

Keep evidence correctness, liveness/eligibility, bridge quality, first-step execution, strategic value, context intersection, diversity, uncertainty hygiene, effort, time, and judge disagreement as separate fields. Do not collapse role-owned scores into a naive median: role score coverage and scales are inconsistent. Prefer hard-gate outcomes, owned dimensions, repeat ranges, and order-stable blinded pairwise comparisons.

Judges read saved artifacts only and never research. Pairwise comparisons must randomize labels and presentation order, preserve mappings privately, and mark order-sensitive outcomes as non-wins. Uncontrolled repeats describe search variance; they do not establish a ranking effect.

## Output contracts

Persist `profile`, `triggers`, `discovery`, `verification`, `actionability`, `ranking`, `report`, and `evidence_ledger` separately. The final report must include selected IDs, statuses, first actions, scheduled-minute allocation (lower/upper bounds), total upper-bound scheduled minutes, residual budget, downgrade reasons, source URLs, exact quote references, retrieval times, and unresolved uncertainty. Empty is valid when no candidate passes.

## Runtime and replay limitations

The runner exposes the standalone prompt as variant `PROD`. For `PROD`, `production_validation.json` is generated and any missing ledger, quote/URL/timestamp mismatch, verification hash mismatch, unsupported ACT_NOW status/deadline reference, count overflow, MONITOR effort, or weekly-allocation mismatch makes the run partial/failed. The validator has a deterministic smoke test, but the standalone production prompt itself has not received a live research evaluation; the empirical evidence belongs to the tested `G2_M1` variant prompt.

Saved-artifact judging and pairwise comparison are reproducible without research. Controlled downstream replay is supported with `--reuse-run` and `--start-stage`. A completed historical live-research run cannot currently be cloned from its snapshot as a fully new exact replay; a fresh full run uses repository-current inputs and live web state. Add a snapshot-clone command before claiming exact research reruns.

This pipeline is an auditable best-observed configuration, not a claim of conversion improvement or convergence beyond the evaluated profile.
