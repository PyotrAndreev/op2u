# Generation 1 mutation plan

## M1

- **id:** `G1_M1`
- **parent:** `V4`
- **affected_stage:** `ranking`
- **change:** Allocate the shared weekly action budget explicitly and aggregate effort conservatively. Normalize each selected first action to a minute range, sum upper bounds across every action recommended for the current seven-day period, and allow a selected portfolio only when that upper-bound total is at most 360 minutes. Persist totals, allocations, residual budget, and downgrade reasons.
- **failure_addressed:** V2, V4, and V6 repeatedly presented selected ACT_NOW sets whose effort ranges could exceed the six-hour hard gate, while advising the user to choose a subset without actually selecting a compliant subset. This also produced effort ambiguity and unsupported fit-to-cap claims.
- **expected_metric_improvement:** Higher weekly-effort hard-gate rate; fewer `weekly_effort_limit`, `effort_cap_exceeded`, and `effort_ambiguity` failures; higher actionability-judge acceptance and first-week plan consistency.
- **expected_regressions:** Fewer selected recommendations, lower portfolio breadth or strategic-value coverage, and slightly higher ranking/report complexity or runtime from explicit range allocation.
- **falsification_condition:** Across valid repeats, the selected upper-bound total is still over 360 minutes or remains ambiguous in a material share of reports, with no improvement in weekly-effort hard-gate rate over V4; or any gain requires a material drop in evidence correctness or first-step executability.

## M2

- **id:** `G1_M2`
- **parent:** `V4`
- **affected_stage:** `report`
- **change:** Add a report-stage `claim_ledger` for every material factual claim. Copy `quote`, `url`, and `retrieved_at` exactly from the persisted verification artifact, link each row to its verification claim and artifact hash, and omit or label claims that lack exact support rather than repairing them in prose.
- **failure_addressed:** V4 and V6 judges found status, eligibility, and other material details asserted without matching quoted support, and exposed risk that evidence present in verification would be paraphrased or lost in the final report. The mutation also targets unsupported ACT_NOW claims and judge disagreement about source support.
- **expected_metric_improvement:** Higher evidence-correctness and source-support rates; fewer `unsupported_claim`, `unsupported_status_or_eligibility`, and official-evidence hard-gate failures; improved evidence-judge agreement and uncertainty hygiene.
- **expected_regressions:** More compact reports may become slightly longer or less fluent; reports may contain more explicit unknowns or fewer recommendations when verification is incomplete, with modest report-stage token/cost overhead.
- **falsification_condition:** Exact quote/URL/retrieved_at preservation fails for material claims, or source-support and evidence-correctness metrics do not improve over V4 across valid repeats, without a compensating reduction in unsupported-claim failures; any improvement is accompanied by a material liveness or actionability regression.

## M3

- **id:** `G1_M3`
- **parent:** `V4`
- **affected_stage:** `ranking`
- **change:** Permit `ACT_NOW` only when verification proves a currently live actionable state, ranking records a specific source-backed `why_now` reason, and actionability supplies an atomic tangible first action that is startable without unresolved eligibility assumptions and takes no more than 60 minutes. Otherwise downgrade or exclude using the existing classifications.
- **failure_addressed:** V4 and V6 judges identified unsupported current status, deadline-only evidence, and classifications that called for immediate action despite uncertain liveness or high-friction multi-hour first steps. The mutation prevents urgency language from outrunning verification and actionability.
- **expected_metric_improvement:** Higher liveness-and-eligibility and evidence-correctness scores for ACT_NOW items; fewer official-evidence, stale/unsupported ACT_NOW, vague-next-action, and first-action hard-gate failures; better actionability-judge confidence in immediate recommendations.
- **expected_regressions:** A smaller ACT_NOW set, lower shortlist recall and possibly lower strategic-value or portfolio-diversity scores; useful upcoming paths may be deferred to PREPARE_NEXT, and the 60-minute threshold may reduce first-action coverage.
- **falsification_condition:** Reports still contain ACT_NOW items without source-backed live status, specific why-now reasons, or low-friction actions, or liveness/first-step hard-gate rates do not improve over V4; alternatively, ACT_NOW coverage collapses without a measurable evidence or actionability gain.
