# Discovery MVP specification

## Purpose

Given an explicit user profile, a requested direction, a snapshot date, and a weekly effort budget, produce a decision-ready portfolio of opportunities. The result helps a user decide what to do next; it does not submit applications or assert that the user is eligible.

## Inputs

- an explicit profile: durable facts, current context, active trajectories, reusable assets, constraints, decisions, preferences, and unknowns;
- direction, opportunity-type exclusions, and any geographic or time windows;
- snapshot date and timezone;
- a weekly effort cap; and
- available source-access tools.

Silence is unknown. The system must not infer citizenship, residence, visa or work authorization, legal, tax, medical, compensation, or programme eligibility facts.

## Output

The output contains:

1. a compact action portfolio;
2. an evidence-backed opportunity horizon; and
3. explicitly separated exploration leads and uncertainties.

Each selected opportunity identifies its primary official source, direct quote, retrieval time, relevant status or date, profile bridge, bounded first action, deliverable, effort estimate, and blockers.

## Classifications

- **ACT_NOW**: an official source directly supports a current or upcoming route, and the user has a concrete first action that can begin within seven days without assuming unresolved eligibility.
- **PREPARE_NEXT**: an official source supports an upcoming or open route, while a bounded preparation or eligibility-fit action is useful before a final decision.
- **MONITOR**: relevant but not scheduled; it consumes no weekly action budget and begins with `No action this week;`.
- **REJECT**: stale, closed, unsupported, duplicate, excluded, infeasible, or otherwise unsuitable.
- **Exploration lead**: a profile-relevant organization or path without a verified current participation route. It is not an opportunity horizon item and cannot receive breadth, liveness, or actionability credit.

## Hard requirements

- `ACT_NOW` includes no job, internship, recruiter programme, or generic employment move unless the direction asks for it.
- Every material `ACT_NOW` claim has direct official-source evidence and a retrieval time.
- A closed, expired, stale, or status-unsupported item is never `ACT_NOW`.
- Select at most three `ACT_NOW` and four `PREPARE_NEXT` items.
- The sum of upper-bound scheduled effort is at most the direction-declared weekly cap.
- At least one selected path has a concrete deliverable that can begin within seven days.
- An opportunity recommendation must state a causal bridge from explicit profile signals or assets; generic skill labels alone are insufficient.

## Non-goals

This MVP does not authenticate to third-party application portals, submit applications, make legal or eligibility determinations, send messages, or track application outcomes. Those require separate specifications, consent boundaries, and evaluation.

## Verification

Schemas, deterministic validation, fixtures, scoring rubrics, and experiment runs test this specification. Their operation and limits are documented in [Evaluation](../dev/evaluation.md).
