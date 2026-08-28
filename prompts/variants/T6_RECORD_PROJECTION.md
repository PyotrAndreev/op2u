# T6 — Verification-record projection

Parent: `T5_DECISION_COMPLETENESS`
Affected stage: report only

## Falsifiable hypothesis

Projecting the final ledger from the verification stage's actual `evidence_records` array, rather than requiring a nonexistent verification-stage `evidence_ledger`, will preserve T5's verified decision depth without quote/URL/time/hash mismatches or candidate-ID drift.

Failure: the report emits an empty ledger despite valid direct official-primary evidence records; changes verification candidate IDs; includes unsupported rows; rewrites exact evidence; or causes production-validation failure.

## Report-only contract correction

1. Read `prior_artifacts.verification.evidence_records`. If that array is absent, use `prior_artifacts.verification.evidence_ledger`; never require both.
2. Preserve candidate IDs and claim IDs exactly from verification. Do not create replacement candidates for the same entity and do not renumber claims.
3. For every retained direct official-primary record, map fields without paraphrase:
   - `exact_quote` or `quote` → final `quote` byte-for-byte;
   - `official_url` or `url` → final `url` byte-for-byte;
   - `retrieved_at` → final `retrieved_at` byte-for-byte;
   - preserve `claim_id`, `candidate_id`, `source_type`, and supports;
   - use the source/evidence record ID as `verification_artifact`;
   - set `verification_artifact_hash` to the exact supplied `prior_artifact_hashes.verification`.
4. Include only rows needed by retained action candidates or verified horizon items. The runner will fail closed and remove anything without an exact verification triple.
5. Use verification candidates as the factual/classification basis and actionability/ranking artifacts for bounded actions. Do not upgrade rejected/closed candidates or organizational leads.
6. Preserve T5 `anchor_completeness` and `named_asset_results` in the report, with ledger IDs or explicit unknowns. Recompute selected IDs, horizon, breadth, and effort from the retained candidates.

No browsing, discovery, re-verification, date repair, or evidence invention is allowed in this report-only mutation.
