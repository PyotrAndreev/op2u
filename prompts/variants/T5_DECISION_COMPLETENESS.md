# T5 — Temporal scope and decision completeness

Parent: `T4_FOCUSED_DEPTH`
Affected stages: verification, actionability, ranking, report

## Falsifiable hypothesis

Enforcing quote-level date scope and completing the highest-priority resource/requirement bundles will remove invented-cycle failures and deepen anchor decisions without reducing valid actions or named-asset personalization.

Failure: any year, cycle, deadline, open status, funding level, score, eligibility, or availability is broader than the exact official quote; or a high-priority resource/requirement question remains unsearched while lower-value catalogue items are verified.

## Mutation

1. Never attach a calendar year or cycle to a deadline unless that same year/cycle is directly present in the exact supporting official quote. A page retrieved in 2026 does not make an undated “May 1” deadline a 2027 deadline. Store the year as unknown, do not render an ISO year, and do not select the item as current/upcoming when cycle applicability is required.
2. `status` support must state an actual current/open/upcoming/rolling external route. A programme description, institutional directory, public email address, country listing, or generic portal does not by itself establish an open application or participation cycle. User-controlled drafting may be recommended only under a classification whose external liveness requirements are met; otherwise preserve it as an optional planning artifact outside verified opportunity counts.
3. For each degree/programme anchor when funding is high priority, verify official pages for tuition/fees, scholarship or waiver amount, stipend/living support, duration, eligibility, deadline, and uncovered gap before verifying another low-priority event. Missing components remain unknown; partial aid is never “funded” or “nearly fully funded.”
4. When a language exam serves admission, verify target-programme acceptance, test format, and minimum score from official programme/university pages before optimizing country or booking logistics. Keep measurable preparation as a separate user-controlled route.
5. Verify exact named people individually when they are anchor assets. A group page may support thematic fit but cannot establish an individual role or route.
6. Report an `anchor_completeness` matrix with one row per anchor and columns for every decision-critical component, each containing ledger IDs or `unknown`. Do not hide missing components in prose.

All cumulative T1 and T4 evidence normalization, direction cap, profile-derived geography, lead tiering, bounded actions, and relationship safety rules remain unchanged.
