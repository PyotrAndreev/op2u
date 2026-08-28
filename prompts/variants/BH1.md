# BH1 — Geography-window fan-out

Parent: `BREADTH_V2`
Affected stages: `search_plan` and `discovery` only

## Mutation record

- **Parent:** `BREADTH_V2`
- **Stage:** `search_plan` → `discovery`
- **Falsifiable hypothesis:** Isolating every supplied geography-and-date window as an independent discovery branch will increase the number and share of materially relevant candidates from non-dominant windows, while preserving evidence correctness, current-status discipline, and weekly effort compliance.
- **Expected gains:** More balanced geographic coverage; fewer searches and candidates concentrated in the first convenient place; better preservation of distinct place/date experiments before ranking.
- **Expected regressions:** More search-plan and bookkeeping overhead; some branches will be empty or yield fewer verified candidates; the total number of selected actions may not increase.
- **Failure condition:** The run omits a supported window, uses another window's results to fill it without disclosure, or lets a single window consume the reserved discovery budget; or repeated evaluation shows no increase in non-dominant-window discovery/horizon coverage while evidence, liveness, or weekly-budget failures increase. An empty branch is not itself a failure when the search gap and attempted queries are persisted.

Apply the complete `BREADTH_V2` prompt and all of its evidence, liveness, profile-bridge, diversity, stretch, count, and weekly-effort gates unchanged. This is exactly one mutation; do not alter verification standards, actionability requirements, ranking scores, or report evidence rules.

## Geography-window fan-out

1. Read geographic windows only from the supplied profile and direction. Treat each distinct place/date interval as its own `geography_window_id`, even when two intervals have the same place. Keep an explicit `global_or_online` bucket for opportunities with no supported place intersection; it cannot substitute for a missing place window.
2. In `search_plan`, create one independent query bundle and research branch for every supported window, with the window's date interval, presence assumptions, relevant families, query rationale, and source budget recorded. Add a separate global/online bundle only when profile-supported. Do not infer presence in an unsupplied gap or convert an application deadline into an event-location overlap.
3. In `discovery`, execute every non-empty window branch before broad cross-window searching. Reserve a comparable discovery slice for each branch and an aggregate place-level slice so that one place cannot consume the budget reserved for other places. When multiple windows share a place, their combined allocation is bounded by that place's predeclared aggregate slice; log overflow separately rather than crowding out another place. Seek at least two materially relevant candidates per supported window before verification when available, but never manufacture weak candidates to satisfy a quota. Persist `search_gap` with attempted queries and the blocking reason when a branch has fewer candidates or none.
4. Tag every discovered candidate with exactly one primary `geography_window_id` (or `global_or_online`), `geographic_presence_basis`, event/participation dates if known, and whether the candidate is an intersection or merely a geographic lead. A candidate spanning windows may list secondary windows, but it must not be duplicated as separate candidates.
5. Pass all branch outputs, including empty branches and rejected/uncertain discoveries, into the normal selective verification funnel. Ranking may still select a compact portfolio, but it must not erase the branch coverage summary or describe an unverified lead as a fact.
6. Add a machine-readable discovery coverage summary with: supported windows, branches attempted, candidates discovered and retained per branch, families searched per branch, source-access gaps, and the share attributable to each branch. Use this summary in the final `breadth_summary` without weakening the existing 6–10 verified horizon target or any hard gate.

Do not hard-code event, organization, program, or opportunity names. Use only supplied windows, profile-supported families, and live retrieved sources. Preserve exact verification quotes, URLs, retrieval times, artifact hashes, official-source checks, the maximum three `ACT_NOW`/four `PREPARE_NEXT` limits, and the conservative upper-bound weekly scheduled-effort cap of 360 minutes.