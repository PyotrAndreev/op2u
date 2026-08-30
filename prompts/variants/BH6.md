# BH6 — Lossless evidence projection

Parent: `BH5`
Affected stage: `report` only

Apply all BH5 discovery, verification, participation-path, actionability, ranking, tiering, effort, and breadth decisions unchanged. Do not browse, verify again, add candidates, upgrade leads, or change classifications.

## Falsifiable hypothesis

Constructing the final evidence ledger only by selecting persisted verification rows removes quote/URL/time/hash mismatch failures without changing the candidate set, verified breadth, geographic coverage, scheduled effort, or stretch result.

Falsification: any quote, URL, retrieved_at, supports, source type, claim ID, or candidate ID differs from its verification row; any unused/mismatched evidence remains; or any opportunity/ranking fact changes.

## Lossless projection rule

Build `evidence_ledger` by selecting rows directly from `prior_artifacts.verification.evidence_ledger`. Copy these fields byte-for-byte: `ledger_id`, `claim_id`, `candidate_id`, `claim`, `quote`, `url`, `retrieved_at`, `source_type`, `entailment`, `supports`, and `verification_artifact`. Do not reconstruct, normalize, shorten, translate, fix, or substitute any field.

The only allowed augmentation is `verification_artifact_hash`, which must equal the exact `prior_artifact_hashes.verification` supplied by the runner. If a selected verification row omits `source_type`, include it only when a matching `verification_record` with the same candidate, exact quote, exact URL, and retrieval time marks it `official_primary`; otherwise omit the row and downgrade/remove the dependent claim.

Include only direct official-primary rows actually referenced by candidates in the final action portfolio or verified opportunity horizon. Exploration leads, rejected candidates, unused requirements, secondary sources, uncertain entailment, empty supports, and rows whose exact verification match cannot be proven must not appear in the final ledger.

Every retained candidate's `claim_ids` must reference only included ledger rows. If removing an invalid row leaves an ACT_NOW item without status plus deadline/event_date/rolling_window support, downgrade it. Recompute summaries after that downgrade, but do not replace evidence or search again.
