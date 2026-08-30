# Final comparison

## Scope and accounting

This is an artifact-scoped report from the persisted experiment set. It covers 21 research runs, four blinded comparisons, 180 persisted subprocess calls, 7,067.8 subprocess seconds, and provider-reported cost of **$2.388421**. It does not read or use `evals/holdout.yaml`; no genuine holdout result exists.

The matrix in `experiment_design.md` is an E1–E12 master plan, not a claim that every cell was run. The per-experiment reports mark cumulative-ladder observations and parent/child checks as partial where the factor was not isolated.

## Frontier evidence

| Evidence | Result | Interpretation |
|---|---|---|
| V0 `bbadccc02a87` | Rejected for a closed NLnet `ACT_NOW` recommendation and missing supporting quotes | The unstructured baseline can let urgency outrun liveness and provenance. |
| V4 `79402a4b4754` | Role scores 87 / 71 / 88; rejected on the effort hard gate | Staging and bridges helped, but a report-level claim that the portfolio fit six hours was not enough. |
| G1_M3 `343039cb5e80` | Role scores 87 / 84 / 93; rejected on effort accounting | A strict live-status/first-action gate did not solve the distinction between first-action effort and all selected weekly effort. |
| G2_M1 controlled replays `96133818abdf`, `2bc8b8a5c893`, `91d4a29ccb62` | No hard failures in 3/3; conservative scheduled **upper bounds were 150, 150, and 165 minutes** | The strongest repeat evidence supports explicit upper-bound allocation of scheduled actions. These are controlled downstream replays with a reused prefix. |
| G2 parent/child comparison `ae274aef40` | Child received 4 votes and 2 ties, no losses; only one role produced a stable child win, while actionability/evidence were order-sensitive | Directionally favorable but not an order-stable across-role promotion result. |
| G3_M3 comparison `0535929b15` | G2 retained unanimously, 6/6 votes, order-stable in all three roles | Supports retaining G2 behavior against this G3_M3 report, not a general claim that G3 is worse in all settings. |

The uncontrolled G2 repeats are evidence of search variance, not evidence of a ranking effect. The controlled replays reused the identical prefix through actionability, so their cleaner comparison is about downstream allocation/report behavior rather than new discovery.

## Why role-score medians are unsafe

The role scores are not a common, consistently populated measurement scale. The rubric assigns ownership by dimension: evidence owns evidence correctness, liveness, and uncertainty; actionability owns bridge and first-step execution; personalization owns strategic value, context intersection, and portfolio diversity. Persisted judge records sometimes report only owned dimensions (with other dimensions null), while other records expose a role total or a different score presentation. Thus values such as V4's 87/71/88, G1_M3's 87/84/93, and G2 role outputs cannot be treated as three exchangeable observations and naively medianed into one quality number. A high personalization score also cannot override an evidence or effort hard gate.

The defensible aggregation is therefore hierarchical:

1. apply hard gates first;
2. report each owned dimension and its missingness;
3. use repeat-level ranges and disagreement descriptively;
4. use order-stable pairwise results for relative selection; and
5. use the role scores only with their role, dimension coverage, and verdict attached.

## Recommendation

The best observed pipeline profile is: explicit dynamic-state extraction; trigger/context hypotheses; primary-source verification; a persisted staged chain; a strict source-backed live `ACT_NOW` gate; atomic seven-day deliverables; conservative upper-bound allocation of every action actually scheduled this week; explicit separation of first-action, scheduled-week, and total-completion effort; bounded portfolio counts; and evidence-backed ranking/report artifacts. Keep `MONITOR` out of the weekly action budget and require a verified upcoming-window reason before scheduling `PREPARE_NEXT` work.

The exact-quote evidence ledger must be a **runner-enforced output/schema requirement**, not merely a prompt instruction. Prompt-only ledger requests in M2/G3_M1 failed to emit the ledger. The runner should reject or downgrade material claims that do not map to exact verification quotes, URLs, retrieval times, and artifact/claim IDs.

This is a best-observed production profile, not a validated causal effect. No genuine holdout exists, behavioral conversion labels are absent, the profile and live opportunity pages are sparse, and the current evidence does not establish convergence beyond this profile.

## Reproducibility hashes and deployment caveat

- Immutable profile SHA-256: `d4e4e43779822e9edbf7b2e821fdcb1055b81ca8915ebb4363cfc7601d49401d`
- Immutable baseline prompt SHA-256: `45b66f9f029c539302d25e1b249faee781ac74a0a10dcfc59ac913b3f7ab3951`
- Standalone recommended prompt SHA-256: `186da80eaa4682298871453cd2597d164174c593013ad24ff868c93c498a2165`
- Tested G2_M1 variant prompt SHA-256 in the controlled run snapshots: `960eed75df03e44bdedd873e4770e96d90e78a095088af0a2cbb6fc2d0991ec3`

The standalone `prompts/find_opportunities_recommended.md` is a production derivation of the tested G2_M1 behavior, not the exact prompt used in the cited runs. It has **not** received a live evaluation run and must not inherit G2's empirical scores. The runner now exposes it as variant `PROD` and fail-closes its report with cross-artifact evidence-ledger, count, status/deadline-reference, and weekly-allocation validation. A dry/smoke validation is not evidence of research quality.
