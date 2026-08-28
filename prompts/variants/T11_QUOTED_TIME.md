# T11 — Quote-bounded temporal scope

Parent: `T10_RECORD_CONTRACT`
Affected stage: report only

## Falsifiable hypothesis

Removing calendar years and cycle claims absent from exact source quotes will pass temporal provenance validation while preserving every genuinely supported T10 opportunity, family, geographic intersection, and safe action.

Failure: any claim/deadline/event date contains a year absent from its exact supporting quote; dependent selected/horizon items remain promoted; valid year-supported rows are lost without reason; or production validation fails.

## Report-only temporal correction

1. For every projected ledger row, compare every four-digit year in the final claim with the exact quote. If a year is absent from the quote, do not add it to the claim.
2. For every candidate deadline or event-date field containing a year, require a referenced direct official row whose exact quote contains the same year. Retrieval date, page title, URL, search snippet, surrounding page context, and profile window cannot supply a missing year.
3. When removing an unsupported year changes temporal relevance:
   - remove the unsupported ledger row or narrow its claim to exactly what the quote entails;
   - set the candidate date/deadline to null or literal undated text;
   - downgrade ACT_NOW/PREPARE_NEXT to MONITOR when current status plus a supported temporal trigger no longer remains;
   - remove it from verified horizon/geographic/family counts and weekly allocation when required.
4. Do not use a supplied travel window to date an event. Event overlap requires the event's own exact quoted date.
5. Preserve exact quote, URL, retrieval time, candidate ID, claim ID, and verification hash. Recompute all summaries and effort after downgrades.
6. Do not browse, replace evidence, infer recurring cycles, or repair claims from memory.

All T10 record-collection, direction-derived cap/windows, evidence, lead-tier, safety, and actionability rules remain unchanged.
