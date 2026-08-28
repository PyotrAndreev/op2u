# T12 — Separate seven-day action from external trigger

Parent: `T11_QUOTED_TIME`
Affected stages: actionability, ranking, report

## Falsifiable hypothesis

Separating the user's immediate artifact-producing first step from the opportunity's later external opening/event/deadline will remove delayed-trigger actionability defects without inventing urgency, changing evidence, or increasing effort.

Failure: a selected action's `start_by_or_trigger` is outside seven days from the snapshot; an external date is represented as the user's start date; an unverified action is scheduled; effort exceeds the direction cap; or evidence/breadth regresses.

## Mutation

1. Every selected ACT_NOW or PREPARE_NEXT candidate must have a user-controlled first action that starts within seven calendar days of `snapshot_date` and is bounded to <=60 minutes.
2. Keep the external lifecycle date separate as `external_trigger` or in uncertainty. An application opening, event date, travel window, or deadline weeks later is not the first-action trigger.
3. Valid immediate PREPARE_NEXT artifacts include a fit matrix, requirements checklist, funding-gap table, abstract outline, inquiry draft, agenda/cost decision, or reusable asset inventory when causally useful and evidence-grounded.
4. Do not schedule “wait,” “monitor,” “check later,” or work whose only trigger is outside seven days. Such items become MONITOR with zero weekly effort.
5. The first-action deliverable must be tangible and must not assume eligibility, acceptance, registration, purchase, travel, access, or reply.
6. Recompute selected IDs and weekly allocation. Do not increase total scheduled upper minutes relative to the parent report merely to fill the portfolio.
7. Preserve T11 exact evidence, temporal scope, horizon, family/geography counts, and stretch unless a selected action must be downgraded under this gate.
