# Breadth optimization hypotheses

## Scope

This is a prompt-design plan for three cumulative variants over `BREADTH_V2`. It uses the expanded profile, the breadth direction, the production discovery prompt, and the persisted BREADTH/BREADTH_V2 artifacts. It does not change existing prompts, tools, schemas, or runs.

The observed baseline pattern is useful but limited: breadth reports preserved several families in the horizon, yet discovery and ranking concentrated practical attention on one dated place/event path while South Africa leads often had organizational-purpose evidence but no current participation route. One earlier report used a placeholder verification hash and failed validation; a later revalidation accepted the explicit official-source marker and passed. The variants therefore treat evidence correctness and weekly effort as non-regressable gates, not as breadth targets to trade away.

## Cumulative ladder

| Variant | Parent | Mutation stage(s) | Added capability |
|---|---|---|---|
| `BH1` | `BREADTH_V2` | `search_plan`, `discovery` | Independent fan-out for every supplied geography/date window, with explicit empty search gaps |
| `BH2` | `BH1` | `search_plan`, `discovery` | Role-first generation inside each geography branch, using participation modes as a discovery axis |
| `BH3` | `BH2` | `discovery`, `verification`, `actionability`, `ranking`/`report` stretch handling | Multiple stretch hypotheses followed by a verified current-pathway and reversible-`<=60m` funnel, selecting at most one |

No variant hard-codes event, organization, program, or opportunity names. All use the supplied windows, profile-supported families, and live primary sources.

## Mutation records

### BH1

- **Parent:** `BREADTH_V2`
- **Stage:** `search_plan` → `discovery`
- **Falsifiable hypothesis:** Independent branches for each supplied geography/date window increase non-dominant-window discovery and horizon coverage without worsening evidence, liveness, or weekly-budget outcomes.
- **Expected gains:** Less first-place bias; separate experiments for distinct date intervals at the same place; aggregate place-level protection so one place cannot crowd out other places; more useful geographic search-gap reporting.
- **Expected regressions:** More query and bookkeeping cost; empty branches; overflow logging; no guaranteed increase in selected actions.
- **Failure condition:** A supported window is skipped or filled by another window's results, or repeated evaluation shows no coverage gain while evidence, stale-status, or effort failures increase. Empty with a persisted search gap is valid.

### BH2

- **Parent:** `BH1`
- **Stage:** `search_plan` → `discovery`
- **Falsifiable hypothesis:** Role-first searches increase distinct, source-supported participation modes and profile-grounded bridges beyond category-first search, without increasing unsupported, stale, duplicate, or budget-unsafe candidates.
- **Expected gains:** Attendee, contributor, volunteer, teacher, maker, organizer, researcher, collaborator, speaker, and other profile-supported modes become visible as different ways to participate rather than only as opportunity categories.
- **Expected regressions:** Role labels can become decorative; more role branches require verification; many roles may correctly remain empty or unverified.
- **Failure condition:** A role has no profile basis or official route, role branches are not run across BH1 windows, or role coverage fails to improve while evidence/duplicate/effort failures increase. Empty role branches must retain their attempted search and reason.

### BH3

- **Parent:** `BH2`
- **Stage:** `discovery` → `verification` → `actionability` → `ranking`/`report` stretch handling
- **Falsifiable hypothesis:** A multi-hypothesis stretch funnel raises qualified useful novelty and safe actionability while eliminating monitor-only or unsupported stretch recommendations.
- **Expected gains:** At most one genuinely supported, emotionally challenging but safe action; transparent rejection of interesting but non-actionable stretch leads.
- **Expected regressions:** Higher verification cost and more empty stretch slots; fewer stretch selections; selected stretch work still consumes the ordinary weekly budget.
- **Failure condition:** More than one stretch item is selected, or the selected item lacks current-pathway evidence, an exact source-backed claim, or a real reversible action with upper effort `<=60` minutes; any ordinary evidence, safety, count, or weekly-effort gate is bypassed.

## Invariants across all variants

- Jobs, internships, recruiter programs, and generic career moves remain excluded unless explicitly requested.
- Primary-source evidence is required for status, dates, deadlines, eligibility, requirements, and participation pathways. Exact quote, URL, retrieval time, claim reference, artifact reference, and SHA-256 hash must be copied from persisted verification records; placeholders are invalid.
- Unknown eligibility, budget, access, presence, legal, immigration, medical, tax, banking, military, or authorization facts stay unknown and cannot be silently inferred.
- Keep the two products separate: a compact action portfolio and a broader evidence-supported horizon. Do not use discovery quotas to force weak candidates into either product.
- Keep the maximum three `ACT_NOW` and four `PREPARE_NEXT` items, the ordinary liveness and profile-bridge gates, the multi-axis duplicate test, and the 360-minute conservative upper-bound scheduled-effort gate.
- Preserve failed and partial stages, empty search gaps, rejected candidates, uncertainty, evidence ledgers, validation artifacts, and `known_case_result` discipline. No judge or report writer may repair missing evidence.
- Stretch is optional. Its maximum is one, and BH3's `<=60`-minute action and current participation pathway are additional gates, not replacements for the baseline gates.

## Evaluation plan

Run each cumulative variant against the same snapshot, worker configuration, source-access budget, and persisted input bundle. Use independent repeats before promotion; do not treat one live run as causal proof.

### Primary readouts

1. **Geography coverage:** supported windows attempted; non-empty branches; unique retained candidates per window; share of pre-verification candidates and verified horizon items by window; number of honest search gaps.
2. **Role breadth:** distinct verified participation modes; role/window/family coverage; number of candidates with an explicit role route and at least two profile signals; role-specific search gaps.
3. **Stretch validity:** generated hypotheses; verified current-pathway hypotheses; candidates with a real reversible action; selected count (`0` or `1`); action upper minutes; source-support rate; unsafe or monitor-only stretch failures.
4. **Evidence and liveness:** official-source support rate; exact quote/url/retrieval-time equality; artifact-hash validity; unsupported status/deadline/eligibility/participation claims; stale or closed `ACT_NOW` items; production-validation result.
5. **Actionability and cost:** atomic deliverable rate; first-action upper minutes; total selected scheduled upper minutes; cap violations; `ACT_NOW`/`PREPARE_NEXT` counts; research calls/time/cost.
6. **Portfolio quality:** materially distinct families, geography/window, participation mode, and intended outcome; bridge quality; useful novelty; ranking stability; selected-set diversity; horizon compactness.

### Promotion and failure interpretation

A breadth variant is promising only if it improves its targeted coverage or qualified-stretch readout in repeated matched runs without evidence correctness or weekly-effort regression. A larger horizon alone is not a gain if it consists of generic, stale, unsupported, inaccessible, or duplicate leads. A smaller or empty selected set is acceptable when the new gates correctly expose missing evidence or participation pathways.

Record every repeat, incomplete run, validation error, cost/time variance, and failure condition. Compare medians and ranges rather than a single result. Do not claim increased real-world applications, participation, satisfaction, or life outcomes from these proxy artifacts; the hypotheses concern auditable discovery breadth, evidence discipline, safe actionability, and budget-aware selection.
