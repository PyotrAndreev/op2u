# Recommended breadth pipeline — BH7

1. Extract dynamic profile state, travel windows, reusable assets, constraints, side paths, and safe stretch preferences.
2. Fan search out independently by each geography/date window plus a separate global/online branch. Preserve empty branches.
3. Generate role-first hypotheses inside each branch: attendee, demonstrator, contributor, volunteer, teacher, maker, organizer, researcher, collaborator, speaker, or other profile-supported role.
4. Discover broadly, but distinguish opportunity candidates from organizational leads.
5. Verify both temporal relevance and a current participation route on official primary sources.
6. Split verification output into `verified_opportunities` and `exploration_leads`. Leads count toward no verified metric and consume no effort.
7. Build action packets and a separate awareness horizon. Select up to one real safe stretch action; monitoring is not stretch.
8. Apply multi-axis duplication across family, geography/window, participation mode, and intended outcome.
9. Apply weekly upper-bound allocation, maximum 360 minutes.
10. Generate report JSON, preserve raw model output, then run BH7 deterministic evidence normalization in code.
11. Fail closed on schema/provenance/effort violations; judge saved artifacts only.

## Critical runtime requirement

`prompts/find_opportunities_breadth_recommended.md` is not sufficient alone. Production must use the BH7 runner configuration with `normalize_ledger=True`. Prompt-only evidence copying failed repeatedly in BH5/BH6.

## Promotion criteria

Require at least two valid repeats, no evidence regression, no hard failures, non-domination, and order-stable pairwise support. Do not optimize horizon length; optimize evidence-backed family/role/geography coverage subject to actionability and cost.
