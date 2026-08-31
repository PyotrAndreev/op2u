# EUSP priority-1 discovery/ranking experiment charter

## Objective and scope

EUSP P1 determines whether the current staged discovery/ranking frontier produces a more **ready-to-act** Discovery MVP portfolio than the one-shot baseline under one identical, synthetic-neutral input snapshot. Its comparison hypothesis is: **given the common P1 report contract and fixed research conditions, `P1_FRONTIER` will produce an eligible portfolio with readiness-to-act at least five points higher than `P1_V0`.**

This is a comparison of complete pipelines, not an attribution study for any one stage. It may support retaining or rejecting the tested frontier for this fixture; it cannot establish a causal effect of staging, search, verification, ranking, or a prompt clause in isolation. The deterministic claim-map checks additionally test that unsupported, stale, closed, or expired selections fail closed.

The experiment remains within the [Discovery MVP specification](../product/discovery-mvp.md): it evaluates discovery, verification, ranking, and bounded next actions only. It does not evaluate applications, submissions, bookings, authentication to third-party services, status tracking, outreach, legal/eligibility determinations, or any future product capability.

> **No non-experimental MVP changes.** This charter does not change Discovery MVP requirements or authorize a production/MVP change. Prompts, schemas, runners, and report contracts may be changed only as a declared experimental treatment or measurement control. Any requirement, automation, consent/privacy, or product-scope change requires a separate product decision and evaluation; it must not be smuggled in as an EUSP result.

## Fixed arms and sequence

Freeze the input bundle and the versions of the prompts, schemas, runner, and comparator before the first run. The shared P1 report-serialization addendum is a **measurement control** applied only while each arm renders its final report; it is not a treatment and must not cause either arm to revisit discovery, verification, ranking, or selection.

| Sequence | Arm | Definition |
|---|---|---|
| 1 | `P1_V0` (baseline) | `prompts/find_opportunities_baseline.md` in one monolithic `report` call. |
| 2 | `P1_FRONTIER` (variant) | `prompts/find_opportunities_general_recommended.md` through `profile`, `triggers`, `search_plan`, `discovery`, `verification`, `actionability`, `ranking`, and `report`. |
| 3 | Paired evaluation | Create a treatment-neutral final-report packet for each complete arm, run deterministic preflight, then judge two paired repeats in both presentation orders. |

There are no intermediate P1 arms and no prompt mutation after a run, score, or judge result. A subsequent change to ranking or path selection starts a new declared experiment with its own hypothesis, baseline, and immutable inputs; it is not appended to this comparison.

## Inputs, outputs, and controls

The input bundle is an anonymized synthetic-neutral profile containing only explicit facts, plus these versioned files:

- [`evals/direction_eusp_p1.yaml`](../../evals/direction_eusp_p1.yaml), including the 2026-08-30 UTC snapshot and job exclusions;
- [`evals/rubric_eusp_p1.yaml`](../../evals/rubric_eusp_p1.yaml);
- the two arm prompts and [`prompts/variants/P1_REPORT_SERIALIZATION_ADDENDUM.md`](../../prompts/variants/P1_REPORT_SERIALIZATION_ADDENDUM.md);
- the P1 judge-packet schema, other output schemas, and the runner/comparator revision; and
- the same worker/judge model configuration, source-access environment, source/research budget, report budget, stage timeout, and snapshot date for both arms.

Hash and save the exact profile, direction, rubric, prompt composition, and schema bundle with each immutable run. A comparison is invalid when the two saved profile, direction, or rubric snapshots differ byte-for-byte. The holdout is not read by workers, judges, or this protocol. Provider usage/cost and retrieval failures are recorded as observed; there is no invented token or monetary figure.

Each arm produces immutable stage artifacts, a final report, and a P1 packet projected only from that final report. The packet replaces source IDs with stable neutral IDs and excludes pipeline/run/model/path metadata. Its validation record must bind the packet hash to the completed report hash. Judges receive only those packets and the rubric; they do not browse, add facts, or repair evidence. Preserve failed and partial artifacts for diagnosis, while keeping profiles and raw traces local as required by the repository privacy convention.

## Budgets and invariants

- One comparison batch has a three-hour wall-clock ceiling. The runner's global deadline is 10,800 seconds; its default per-call timeout is 900 seconds with a 60-second finalization reserve. Stop and record incomplete work at the wall.
- Run exactly two paired repeats. Each repeat is judged in forward and reversed presentation order by the readiness role: four blinded judge calls total.
- The direction allows at most three `ACT_NOW`, four `PREPARE_NEXT`, and 360 scheduled upper-bound minutes per week.
- Every selected first action must be user-controlled, start no later than seven days after the saved snapshot, and take at most 60 minutes. `MONITOR` receives no scheduled effort.
- Jobs are not requested for this fixture. Excluded job types remain excluded; unresolved eligibility never becomes permission to act.

These limits are gates, not optimization targets. An empty portfolio is valid; padding the portfolio, action budget, or evidence ledger to improve a score is a failure.

## Metrics and gates

The primary metric is `portfolio_readiness_to_act` on a 0–100 scale. For every selected `ACT_NOW` or `PREPARE_NEXT` item, score five equally weighted checks (20 points each): explicit profile bridge; atomic verb-led user-controlled action; tangible deliverable; action startable within seven days without reply, eligibility, or acceptance; and bounded effort with blockers/unknowns disclosed. The portfolio score is the mean; an empty selected set scores zero.

Report, but never trade against the primary metric, these hard-gate outcomes:

1. **Grounding:** every selected status, timing, and participation-route claim is explicitly mapped to direct official-primary evidence with an exact quote, HTTPS URL, and retrieval time.
2. **Liveness:** every selected item has source-backed current/open status and participation route, plus a nonexpired deadline, dated event, or current rolling window at the saved snapshot. Stale, closed, expired, or unmapped selections fail.
3. **Limits and effort:** classification limits and the 360-minute scheduled upper bound hold.
4. **Seven-day action and job policy:** every selected action meets the user-control, timing, effort, and exact job-policy constraints.

Record the individual readiness checks, selected count, scheduled minutes, invalid/missing artifacts, elapsed time, and provider-reported usage alongside the score. A judge score or polished report never repairs a deterministic gate failure.

## Promotion and failure conditions

`P1_FRONTIER` is promotable only when all of the following are true:

1. both run manifests are exactly the declared P1 arms, both runs are complete, their packets are schema-valid and hash-bound to their completed reports, and all compared input snapshots match;
2. all four blinded calls complete with valid readiness results, and deterministic preflight finds **both arms** eligible in every call (grounding, liveness, and all other gates pass);
3. in each repeat, forward and reversed judgments name `P1_FRONTIER` as the same applied winner; the five-point readiness margin is met in each applied comparison; and
4. the two repeat-level winners are order-stable and both are `P1_FRONTIER`.

This is intentionally stricter than a single favorable run. The current P1 promotion procedure requires both arms to be eligible in every paired call, so it does not grant a hard-gate-repair exception. A promotion is only a recorded recommendation to retain the tested experimental frontier; it is not an MVP or product promotion.

An attempt is invalid and non-promotable on any snapshot mismatch, wrong arm/stage manifest, malformed or unbound packet, schema/parse error, missing artifact, timeout, incomplete run, or deterministic gate failure. A completed comparison is a non-promotion when it ties, is order-sensitive, lacks the five-point frontier advantage, or does not repeat. Preserve the baseline, failed attempt, measurements, and reason; do not mutate an arm within the batch to chase the result.

The synthetic fixture and live-source variability limit conclusions to this protocol. It does not demonstrate generalization to a person, geography, preference set, application outcome, participation, satisfaction, or any future automation.

## Related records

- [Evaluation conventions](evaluation.md)
- [P1 synthetic-neutral record](../../experiments/analyses/eusp_p1_synthetic_neutral_record.md)
- [Synthetic evaluator-only hidden-traits protocol](eusp-p1-hidden-traits-protocol.md)
- [Discovery MVP specification](../product/discovery-mvp.md)
- [Future execution approval boundary](../product/future-execution-approval-boundary.md) — future-design only; not an EUSP treatment or MVP change
