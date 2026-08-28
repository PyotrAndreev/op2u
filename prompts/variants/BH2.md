# BH2 — Geography fan-out plus identity/role-first generation

Parent: `BH1`
Affected stages: `search_plan` and `discovery` only

## Mutation record

- **Parent:** `BH1`
- **Stage:** `search_plan` → `discovery`
- **Falsifiable hypothesis:** After geography-window fan-out, generating from explicit participation roles before opportunity categories will increase materially distinct role pathways and profile-grounded bridges in the horizon, without increasing unsupported claims, stale candidates, duplicate collapse, or weekly-effort violations.
- **Expected gains:** More ways to participate beyond applying for the obvious category; better visibility of attendee, contributor, volunteer, teacher, maker, organizer, researcher, collaborator, speaker, and related role pathways; stronger awareness value and participation-mode diversity.
- **Expected regressions:** Additional query and verification cost; some role hypotheses will have no current route; role labels may become decorative or generic if not tied to an official participation mechanism; the compact selected set may remain unchanged or become smaller.
- **Failure condition:** A role is assigned without an explicit profile basis or source-supported participation route, role-first branches do not execute across the BH1 windows, or repeated evaluation finds no increase in distinct supported participation modes while unsupported/stale/duplicate candidates, evidence failures, or weekly-budget failures increase. Empty role branches are valid only when their attempted search and reason are preserved.

Apply the complete `BREADTH_V2` prompt and cumulative `BH1` mutation unchanged. This is exactly one additional mutation; do not replace geography fan-out, relax evidence gates, or change ranking, selection counts, stretch limits, or weekly effort rules.

## Identity/role-first opportunity generation

1. Treat a participation role as a testable mode of engagement, not as an inferred personal identity, demographic attribute, entitlement, or eligibility fact. Derive roles from explicit profile assets, interests, current context, and the supplied direction. Do not infer citizenship, residence, authorization, or membership.
2. Before category-first queries, build a role matrix for each supported `geography_window_id` from BH1. Use profile-supported roles such as `attendee`, `contributor`, `volunteer`, `teacher`, `maker`, `organizer`, `researcher`, `collaborator`, `speaker`, or other explicitly justified roles. The list is a search vocabulary, not a requirement to find every role.
3. For each supported window and role with a credible profile basis, create role-first queries using participation verbs and the relevant family/context (for example, attend, contribute, volunteer, teach, make, organize, research, collaborate, or speak). Record the role hypothesis, its profile basis, target window, family, query, and what evidence would falsify it. Run these branches before generic opportunity-name/category searches; global/online role branches remain separate from place branches.
4. Discovery candidates must include `participation_role`, `role_profile_basis`, `intended_outcome`, `geography_window_id`, and `role_route_hypothesis`. A candidate may have more than one plausible role only when the source and participation modes are materially distinct; do not multiply one opportunity into aliases.
5. Seek at least two materially distinct role pathways per supported window before verification when available, while retaining BH1's no-filler rule. Prefer role diversity across the horizon, but preserve a search gap when the official ecosystem exposes only one role or no route.
6. Verification must independently confirm the current status and the claimed participation route. A page describing an organization's mission, audience, or topic does not prove that the user can currently attend, contribute, volunteer, teach, make, organize, research, collaborate, or speak. If the route is not directly supported, keep the role as an explicitly unverified hypothesis and do not select it as `ACT_NOW`.
7. Carry role coverage into `breadth_summary` and `opportunity_horizon`: report distinct verified `participation_mode` values, role search gaps, and the new identity/role possibility each retained item reveals. Keep the existing multi-axis duplicate test (`family × geography/window × participation mode × intended outcome`) and do not treat role diversity as permission to retain weak or near-duplicate items.

Do not hard-code event, organization, program, or opportunity names. Preserve exact evidence-ledger copying, official-source and artifact-hash validation, unknowns, job exclusion, maximum shortlist counts, at-most-one stretch slot, and the 360-minute conservative weekly scheduled-effort gate.