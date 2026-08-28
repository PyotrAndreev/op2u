# BH5 — Participation-path verification before breadth credit

Parent: `BH4`
Affected stages: `verification`, `actionability`, `ranking`, and `report`

Apply BREADTH_V2, BH1 geography fan-out, BH2 role-first search, and BH4 tiered horizon unchanged.

## Falsifiable hypothesis

Enforcing the verified-opportunity versus lead split at verification, rather than only in final prose, removes unsupported-breadth hard failures while preserving every candidate with a real current or dated participation route.

Expected gain: consistent stage artifacts and honest breadth. Expected regression: fewer verified families/windows and more exploration leads. Falsification: verification still counts organization descriptions, undated monitors, or events without an access/registration/contribution route as verified breadth; or a supported route is lost without an explicit reason.

## Verification contract

For each candidate independently verify two things on official primary sources:

1. temporal relevance: current/open/rolling window or dated event overlapping a supplied presence window;
2. participation pathway: a current way to register, attend, apply, inquire through a directed official route, contribute, volunteer, teach, speak, make, organize, research, or collaborate.

A dated event with no current access/registration/participation evidence is an `exploration_lead`, not a verified opportunity. An organization mission/about page with no current route is also a lead. A generic contact page is not a directed participation route unless the source explicitly invites the relevant inquiry or contribution.

Persist separate arrays `verified_opportunities` and `exploration_leads`. Only verified opportunities may enter `opportunity_horizon`, verified family/role/geography counts, ACT_NOW, PREPARE_NEXT, adaptation credit, or stretch. Leads retain profile bridge, missing evidence, attempted official URLs, and future trigger, but consume zero effort and count toward no evaluation metric.

Every evidence row includes `source_type: official_primary|secondary`; selected and counted items use only direct `official_primary` rows. Copy exact quote, URL, retrieved_at, supports, and artifact hash.

## Downstream consistency

Actionability, ranking, and report must use the verification split without upgrading leads. Recompute all breadth summaries from verified opportunities only. Every MONITOR candidate must have zero scheduled effort and first-action text exactly beginning `No action this week;`.

For a PREPARE_NEXT candidate, unresolved final eligibility is allowed only when an official upcoming/open route is verified and the scheduled first action is a bounded eligibility-fit artifact or directed inquiry that does not assume acceptance.

Keep weekly effort <=360, at most 3 ACT_NOW/4 PREPARE_NEXT, multi-axis duplication, and real stretch gates unchanged. Empty or one-item verified horizon is acceptable.
