# Evaluation experiment design

## Purpose and unit of evaluation

This plan evaluates the cumulative prompt ladder V1–V7 for opportunity discovery. The unit is one saved run: one immutable input snapshot, one variant, one worker configuration, its persisted artifacts, and zero or more independent judge records. The goal is to improve evidence-grounded meaningful first actions, not to optimize prose or claim downstream user conversion.

The ladder is cumulative and changes one capability at a time:

| Variant | Added capability |
|---|---|
| V1 | Dynamic profile state before research |
| V2 | Trigger/context hypotheses |
| V3 | Opportunity bridge and seven-day actionability gate |
| V4 | Staged persistence contracts |
| V5 | Blinded pairwise final ranking |
| V6 | Evidence-grounded judges with separate roles |
| V7 | At most one constrained serendipity slot |

The baseline policy, profile, direction, visible regression cases, rubric, snapshot date, source-access environment, output schemas, and report-length budget are fixed across comparisons. Variant text is the only intended treatment difference.

## E1–E12 matrix

Each experiment uses a controlled A/B comparison under the same profile snapshot, worker model, live-research access, and research budget. The three-hour cap applies to the suite, so screening runs precede repeats; incomplete cells remain `not_run`.

| ID | Controlled comparison | Hypothesis | Primary readout |
|---|---|---|---|
| E1 | Flat profile vs explicit durable facts, active trajectories, current context, reusable assets, constraints, and decisions | Dynamic-state extraction increases contextual actionability and reduces generic output | state completeness, actionable top-3 precision, genericity |
| E2 | Direct profile search vs trigger synthesis before search | Trigger synthesis improves bridge recall and non-obvious discovery | valid triggers, bridge recall, candidate recall |
| E3 | Category-first vs event/change-driven search | Event-driven search finds more temporally privileged opportunities | timing advantage, context intersections, liveness |
| E4 | Profile-fit ranking vs mandatory concrete bridge for ACT_NOW | Bridge-first ranking lowers first-action effort and genericity | bridge quality, effort, ACT_NOW gate failures |
| E5 | Monolithic agent vs explicit persisted stages | Staging improves provenance, diagnosability, and preservation of discoveries | artifact completeness, source continuity, final/artifact consistency |
| E6 | Exhaustive research vs broad low-cost discovery followed by selective verification | A budgeted funnel improves actionable discoveries per cost without reducing top-3 quality | actionable candidates per token/cost, top-3 score |
| E7 | Independent 0–5 scoring vs pairwise shortlist tournament | Pairwise ranking improves top-3 stability | order stability, dominated selections, A/B agreement |
| E8 | Report-only judge vs judge receiving profile, evidence, eligibility, effort, bridge, and artifacts | Grounded judging reduces prose/style bias and unsupported high scores | evidence hard failures, score shifts, judge disagreement |
| E9 | Action label only vs executable action packet | Action packets improve first-step executability | atomic action, deliverable, effort/blocker/internal deadline completeness |
| E10 | Obvious maximum fit only vs at most one constrained serendipitous item | Constrained serendipity increases useful novelty without evidence/actionability regression | qualified novelty, diversity, hard-gate rate |
| E11 | Synthetic isolated temporal/causal perturbations | Rankings respond monotonically to relevant changes and remain invariant to irrelevant changes | causal sensitivity, monotonicity, irrelevant-field invariance |
| E12 | Binary relevant/irrelevant feedback vs funnel-stage likelihoods | Funnel evaluation separates interesting recommendations from actionable ones | noticed→opened→first-action→submitted proxy distribution |

The cumulative V0–V7 ladder exercises many of these factors efficiently; isolated ablations are required before attributing gains to an individual factor. Screen V0–V7 once, repeat up to three provisional frontier variants to three total runs, then perform three-role blinded A/B checks in both orders. If time expires, publish the incomplete matrix without claiming convergence.

## Run controls

1. **Immutable inputs.** Hash the profile, baseline policy, direction, visible regression fixtures, rubric, variant text, schema bundle, and snapshot date. Save the hashes and exact prompt/input text with each run.
2. **Fixed research conditions.** Keep worker model, temperature/configuration, source-access environment, maximum source count, report budget, and per-stage timeout fixed for a matched comparison. Record any provider or retrieval failure.
3. **Independent artifacts.** Persist profile interpretation, triggers, discovery, verification, actionability, ranking, report, raw responses, parsed responses, status, timing, and usage metadata. Judges read saved artifacts only and never launch research.
4. **Seeded randomization.** Record seeds for discovery sampling, pairwise label assignment, and presentation order. Keep the actual A/B mapping outside the judge prompt.
5. **Matched snapshots.** Use one snapshot date for a comparison. A later live check is a new snapshot, not a silent update of the old run.
6. **No prompt mutation during a cell.** Known-case observations may be logged as diagnostics, but prompt text and ladder membership are frozen until the next explicitly declared experiment.
7. **Cost accounting.** Preserve provider-reported usage when available. If unavailable, keep token/cost fields null or clearly estimated; never present estimates as exact.

## Guardrails and failure handling

- Jobs, internships, recruiter programs, and generic career moves remain excluded unless an explicit future task requests them.
- `ACT_NOW` requires official evidence for status and deadline, a current/open or upcoming status, a profile bridge, and a concrete first action within seven days.
- Never infer citizenship, work authorization, visa eligibility, legal/tax status, medical status, or compensation from silence.
- Enforce no more than three ACT_NOW and four PREPARE_NEXT items, with no more than six estimated user-effort hours per week.
- Preserve source quotes, URLs, retrieval times, and unresolved eligibility/status uncertainty. Unsupported claims are failures, not opportunities for judge interpretation.
- A malformed JSON response, missing artifact, timeout, or failed schema validation is recorded as an invalid attempt. Raw stdout/stderr and partial files remain available for diagnosis.
- A judge cannot repair a missing source or add a factual opportunity. If an evidence judge finds an unsupported ACT_NOW claim, that hard failure overrides actionability or prose scores.
- At most one V7 item may be labeled serendipitous, and it must pass the same gates as every other item. Empty is the correct result when no qualified item exists.
- Visible regression fixtures are diagnostic only. They must not be hard-coded into a production prompt or treated as a hidden generalization test.

## Scoring and convergence

Use `evals/rubric.yaml`. Report dimension scores by owner, penalties, hard-gate outcomes, source-support rate, first-action feasibility, selected-set effort, diversity, elapsed time, and judge disagreement separately. Include individual repeats, median, range, and missing cells; do not reduce the evaluation to one unqualified mean.

A candidate variant can replace the incumbent only when all of the following hold:

1. it is eligible in at least two independent repeats;
2. its median rubric score improves by at least five points, or it removes a hard failure;
3. evidence correctness does not regress;
4. the relevant blinded pairwise result is order-stable;
5. it is not Pareto-dominated on hard failures, unsupported/stale claims, time, effort, disagreement, rubric score, source support, action feasibility, diversity, and visible-case outcome;
6. it does not regress the visible regression diagnostic from pass/acceptable alternative to fail.

Stop after two consecutive evaluated generations without a promotable, non-dominated variant, or at the three-hour wall-clock limit. A generation is a declared comparison batch, not an excuse to mutate prompts after seeing an individual judge response. Preserve the incumbent, rejected alternatives, and the exact reason for every promotion or stop decision.

## Honest holdout limitation

The holdout is sealed and is not read, copied into prompts, used for mutation, or exposed to workers or judges. No holdout labels or behavioral conversion outcomes are available to this evaluation. Therefore E1–E12 measure auditable proxy properties: evidence completeness, liveness discipline, bridge specificity, action feasibility, portfolio diversity, judge agreement, time, and visible regression behavior.

These results do **not** establish that a prompt increases applications, successful outcomes, user satisfaction, or generalization to unseen profiles. They are especially limited by one visible profile, changing live opportunity pages, model/provider variance, and sparse outcome labels. The final report must state this limitation and distinguish a best observed pipeline from a validated causal effect.
