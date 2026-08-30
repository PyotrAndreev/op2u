# T9 — Stage-correct provenance and deep decision portfolio

Parent: `T8_DECISION_MAP`
Affected stages: verification, actionability, ranking, report

## Falsifiable hypothesis

Deferring verification-artifact hashing to the report stage while preserving exact verification records will prevent downstream false downgrades and yield a valid actionable portfolio plus an evidence-rich decision map.

Failure: verification invents its own artifact hash; actionability/ranking rejects exact records only because their future artifact hash is unavailable; report loses deep evidence; cross-artifact classifications diverge; or any hard gate fails.

## Stage-correct contract

- `verification`: return complete `candidates` and `evidence_records`. Do not emit, require, guess, or reason from a hash of the verification artifact being created. Exact quote, official URL, retrieval time, source type, claim ID, supports, and source ID are sufficient at this stage.
- `actionability` and `ranking`: use persisted verification records directly. They must not require a verification-artifact hash and must not downgrade otherwise valid evidence because such a hash is absent/null inside verification output. Preserve candidate IDs and classifications conservatively.
- `report`: only here, project exact records and attach the runner-supplied `prior_artifact_hashes.verification`. This is the sole authoritative verification hash. Ignore any null or model-supplied self-hash field inside verification.
- Preserve up to three deep anchor bundles and all anchor-critical evidence, including closed precedents as REJECT and unknown future cycles as MONITOR. Closed/monitor evidence improves the decision map but not current-opportunity breadth.
- Select only evidence-backed current user-controlled routes. A preparation resource may support a bounded measurable action. Generic public contact or programme description is not current external liveness. No unquoted year may be introduced.
- Keep all selected first actions <=60 minutes and total scheduled effort within the direction cap.

All cumulative T1 profile parameterization, T4 anchor focus, T5 temporal/resource completeness, T6 record projection, and T8 evidence-preserving decision-map rules remain in force where not corrected above.
