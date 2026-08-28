# T8 — Evidence-preserving decision map

Parent: `T6_RECORD_PROJECTION`
Affected stage: report only

## Falsifiable hypothesis

Preserving all T5 verification candidates and anchor-critical evidence in the final decision map—without promoting closed, undated, generic-contact, or cycle-unknown items—will improve academic depth and funding clarity over T1 while retaining all evidence hard gates.

Failure: a verification candidate or anchor-evidence row is silently lost; an item is upgraded beyond verification; an unquoted year appears; selected action liveness is incomplete; or report validation fails.

## Report-only mutation

1. Preserve every `prior_artifacts.verification.candidates` item in final `candidates` using the same candidate ID, title, organization, classification, deadline, claim IDs, uncertainty, and rejection reason. You may add bounded action fields from actionability/ranking, but may not rename or renumber candidates.
2. Project exact official-primary `evidence_records` needed for:
   - selected actions;
   - verified horizon items;
   - `anchor_completeness` decisions;
   - funding, tuition, language-requirement, fit, eligibility, and named-person analysis;
   - explicit closed/ineligible precedents used to understand a future cycle.
   The last category remains REJECT/lead and earns no current-opportunity breadth.
3. Preserve `verification.anchor_completeness` and `verification.named_asset_results` rather than replacing evidenced fields with `unknown`. Attach ledger IDs where possible.
4. Apply liveness conservatively:
   - unknown target cycle or generic programme description → MONITOR, zero effort;
   - closed call → REJECT, zero effort;
   - generic public contact information → person-specific lead/monitor, zero effort unless a separately verified directed current participation route exists;
   - official user-controlled preparation resource with a current route may be PREPARE_NEXT when the bounded action does not assume exam booking or programme acceptance.
5. Do not select an item merely to preserve its evidence. Select only rows meeting the exact current-route and action gates.
6. Keep Cape Town outside-window or undated results as gaps/leads, not verified geography.
7. Render `anchor_decisions`, `anchor_completeness`, `named_asset_results`, and `route_portfolio` from preserved verification evidence. Distinguish verified current option, verified closed precedent, current lead, and unknown future cycle.

No browsing, new facts, evidence rewriting, or candidate replacement is allowed.
