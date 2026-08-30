# T3 — Anchor-decision verification and named-asset leverage

Parent: `T2_DECISION_DEPTH`
Affected stages: search_plan, discovery, verification, actionability, ranking, report

## Falsifiable hypothesis

Allocating verification depth to a small set of anchor decisions and testing user-supplied named relationships/entities directly will increase decision completeness and personalization without inventing access, reducing route diversity below the supported minimum, or weakening evidence liveness.

Failure: the run returns a longer shallow catalogue; substitutes a generic organization page for a named person/entity; assumes a relationship is warm, available, endorsing, or responsive; or leaves anchor-critical facts unsearched while spending budget on low-value leads.

## Mutation

1. After route discovery, identify at most three `anchor_decisions`: choices whose resolution would materially change the user's next 3–12 months. Persist the competing options and the facts needed to decide.
2. Reserve at least half of verification effort for these anchors before expanding the catalogue. For each anchor seek an evidence bundle, as profile-relevant: current cycle/status, fit mechanism, eligibility/requirements, full cost/funding/resource structure, deadlines, duration/location, and one executable next step.
3. Do not count an anchor as decision-ready when only its title, mission, or general existence is verified. Missing bundle components remain explicit and generate a bounded next-evidence action when useful.
4. Treat user-supplied named people, programmes, projects, communities, or organizations as `named_assets`. Search the exact entity and its current official publications, events, calls, application routes, or directed contact mechanisms before substituting a broad institution or lab catalogue.
5. A named relationship remains user-controlled context. Never infer warmth, permission, availability, endorsement, reply, supervision, funding, introduction, or eligibility. When no public participation route exists, propose at most one bounded draft or decision about contact, clearly conditional on user permission; do not call it a verified external opportunity.
6. Allocate remaining verification across other supported routes to preserve option awareness. A route gap is preferable to an unsupported item.
7. Add `anchor_decisions` and `named_asset_results` to the final JSON. Every factual field uses exact projected evidence or is marked unknown.

All cumulative T1/T2 evidence, provenance, cap, geography, actionability, tiering, and safety gates remain unchanged.
