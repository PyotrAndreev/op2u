# T13 — Funding label versus verified components

Parent: `T12_SEVEN_DAY_ACTION`
Affected stages: verification, ranking, report

## Falsifiable hypothesis

Separating an official “funded/fully funded” label from evidence for tuition, stipend, living support, duration, eligibility, deadline, and residual gap will remove funding-overclaim failures while preserving useful funded-route discovery.

Failure: a route is called full/nearly-full funded when only an undifferentiated label is supported; a partial scholarship is treated as full funding; exact official wording is hidden; or a valid route is discarded instead of preserving component uncertainty.

## Mutation

1. Preserve the exact official quote and may state: `the official source labels this funded/fully funded`.
2. Do not convert that label into the pipeline's conclusion that funding is complete or nearly complete unless direct official evidence separately establishes, as relevant:
   - tuition/fee coverage;
   - stipend or living support and amount;
   - funded duration;
   - research/travel support;
   - eligibility and deadline;
   - any uncovered or unknown financial gap.
3. Add a `funding_components` object for degree, studentship, grant, residency, or scholarship routes. Every component contains ledger IDs or `unknown`.
4. When components are missing, use phrasing such as `officially labelled fully funded; package completeness unverified`. Add the missing components to blockers and uncertainty. Do not rank it as proven nearly-full funding.
5. Partial awards, fee discounts, and tuition-only waivers remain partial unless living costs and the user's residual gap are separately supported.
6. Missing funding components do not by themselves erase an otherwise current route. Keep classification based on liveness and eligibility gates, and make a <=60-minute funding-gap table or eligibility matrix the first action when useful.
7. Preserve all T12 profile-derived windows/cap, exact record projection, quoted temporal scope, seven-day action, effort, and safety rules.
