# T2 — Decision-route depth before list breadth

Parent: `T1_GENERAL`
Affected stages: profile, triggers, search_plan, discovery, verification, actionability, ranking, report

## Falsifiable hypothesis

Deriving a profile-specific route ontology and treating routes as different decisions will produce deeper, more decision-useful coverage than a flat opportunity-family list, without reducing exact evidence validity, actionability, or verified cross-route breadth.

Failure: routes are generic labels, unsupported by the supplied goal, or are collapsed into one ranking without stating what uncertainty each route resolves; or evidence/actionability regresses.

## Mutation

1. Derive 4–8 materially different routes from the supplied goal, profile, direction, and active horizon. A route is a causal strategy, not a topic label. Do not import routes from another profile.
2. For every route record: target outcome, user assets, key unknowns, evidence needed, first reversible test, time horizon, and what decision it informs.
3. Search each supported route independently before ranking. Empty routes remain explicit search gaps; do not fill quotas with weak links.
4. Do not treat unlike routes as interchangeable. A degree, funded position, grant, collaboration, event, examination, community, or public artifact may resolve different uncertainties even when all serve one long-term goal.
5. In verification, capture route-critical facts in addition to liveness. Examples include eligibility, requirements, complete resource/funding structure, duration, participation mode, application cycle, deliverables, and unresolved gap—but only when the current profile makes them decision-critical.
6. In ranking, prefer candidates that resolve a high-value uncertainty or unlock multiple later options. State why a route is selected, deferred, monitored, or rejected.
7. Add `route_portfolio` to the final JSON with route IDs, verified candidates, exploration leads, unresolved decision, and next evidence target. Recompute horizon breadth from verified opportunities only.

All T1 evidence, provenance, direction-cap, geography, uncertainty, effort, and safety gates remain unchanged.
