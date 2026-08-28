## Implementable 3-hour evaluation design

### 1. Immutable evaluation packet

For every run, hash and save:

- `usr/profile.md`
- `prompts/find_opportunities_baseline.md`
- `evals/direction.yaml`
- the visible regression fixture in `evals/known_cases.yaml`
- variant ID, model, temperature, timestamps, budget, and source retrieval timestamps

Do not expose hidden test material to prompt authors, variant mutation, or judges.

Use a fixed `snapshot_date` per evaluation. An opportunity is “live” only if its official source explicitly supports an open/upcoming status relative to that date; otherwise it must be marked `VERIFY_STATUS`, not `ACT_NOW`.

---

## 2. Artifact schemas

Store JSON artifacts per run. Strict validation should reject malformed or unverifiable recommendations.

### `opportunity.schema.json` (one item)

```json
{
  "id": "string",
  "title": "string",
  "organization": "string",
  "type": "grant|fellowship|cfp|community|research_collaboration|residency|accelerator|travel_support|other",
  "status": "ACT_NOW|PREPARE_NEXT|WATCH|REJECT",
  "official_url": "https://...",
  "source_checked_at": "ISO-8601",
  "deadline": "YYYY-MM-DD|null",
  "status_evidence": {
    "quote": "verbatim official-source excerpt",
    "url": "https://...",
    "retrieved_at": "ISO-8601"
  },
  "eligibility_evidence": {
    "quote": "verbatim excerpt or null",
    "url": "https://...|null",
    "retrieved_at": "ISO-8601|null"
  },
  "profile_bridge": [
    {
      "profile_fact": "explicit fact from profile",
      "why_it_matters": "causal connection to this opportunity"
    }
  ],
  "reusable_asset": "existing talk/project/code/network asset, or null",
  "value_hypothesis": "specific plausible outcome",
  "uncertainties": ["explicit unresolved facts"],
  "first_action": {
    "action": "atomic verb-led action",
    "deadline_or_trigger": "date or immediate trigger",
    "estimated_minutes": 30,
    "deliverable": "draft / email / proposal outline / issue"
  },
  "estimated_total_effort_hours": 2.0,
  "risk_notes": ["..."],
  "disqualifiers_checked": {
    "is_job": false,
    "stale_or_closed": false,
    "requires_unverified_legal_assumption": false
  }
}
```

### `report.schema.json`

```json
{
  "run_id": "string",
  "variant_id": "V0",
  "snapshot_date": "YYYY-MM-DD",
  "act_now": ["opportunity-id"],
  "prepare_next": ["opportunity-id"],
  "rejected_candidates": [
    {"title": "string", "reason": "closed|job|weak_fit|unsupported|duplicate"}
  ],
  "portfolio_rationale": "why the selected set has distinct paths",
  "weekly_effort_hours": 0,
  "opportunities": ["opportunity objects"],
  "known_case_result": {
    "case_id": "pycon_za_2026",
    "outcome": "pass|acceptable_alternative|fail|not_run",
    "reason": "string"
  }
}
```

### `judge_result.schema.json`

```json
{
  "judge_id": "evidence|action|portfolio",
  "model": "string",
  "blind_candidate_id": "A",
  "hard_failures": [
    "unsupported_status|unsupported_deadline|job|stale|missing_first_action|effort_limit"
  ],
  "dimension_scores": {
    "evidence": 0,
    "liveness": 0,
    "profile_bridge": 0,
    "actionability": 0,
    "strategic_value": 0,
    "portfolio_diversity": 0,
    "uncertainty_hygiene": 0,
    "conciseness": 0
  },
  "penalties": {
    "generic_recommendation": 0,
    "unsupported_claim": 0,
    "stale_opportunity": 0,
    "vague_next_action": 0,
    "ignored_known_constraint": 0,
    "excessive_report_length": 0
  },
  "score": 0,
  "verdict": "accept|conditional|reject",
  "rationale": ["claim tied to packet evidence"]
}
```

Keep raw model responses plus parsed JSON; parsing failure is itself a failed judge call, never silently repaired.

---

## 3. Auditable rubric

Score each report on a 100-point pre-penalty scale.

| Dimension | Points | Operational test |
|---|---:|---|
| Official evidence and provenance | 25 | Every `ACT_NOW` item has official URL, quote, retrieval time, and support for key status/deadline claim. |
| Liveness and eligibility discipline | 15 | Open/upcoming status is supported; no inferred citizenship, visa, legal, or work authorization. |
| Profile-specific causal bridge | 15 | Connects at least two explicit profile facts/current context/reusable assets to the opportunity. |
| Seven-day actionability | 15 | Atomic first action, tangible deliverable, feasible time estimate, and urgency where relevant. |
| Expected strategic value | 12 | Plausible route to prototype validation, collaborators, funding, users, or public visibility. |
| Portfolio diversity | 8 | Top three do not duplicate organization/program/type and represent genuinely distinct paths where possible. |
| Uncertainty and constraint handling | 5 | States material unknowns; excludes jobs; honors six-hour weekly limit. |
| Decision quality / concision | 5 | Selective, ranked, non-generic, and decision-oriented. |

Apply the configured penalties exactly:

- generic recommendation: −2 each
- unsupported claim: −5 each
- stale opportunity: −5 each
- vague next action: −2 each
- ignored known constraint: −4 each
- excessive report length: −0.5 per defined excess unit

### Hard gates

A report is ineligible for selection if any is true:

1. Any `ACT_NOW` item is a job or internship.
2. Any `ACT_NOW` status/deadline claim lacks official evidence.
3. More than three `ACT_NOW`, more than four `PREPARE_NEXT`, or estimated weekly effort exceeds six hours.
4. An `ACT_NOW` item is known closed/stale at the snapshot date.
5. No selected item has a concrete first action within seven days.

Hard-gated reports remain in artifacts and comparison tables, but cannot win on a high average score.

---

## 4. Controlled V0–V7 ladder

All variants use the same profile, snapshot date, model settings, maximum research time, source-access environment, output schema, and final report budget. Change one cumulative capability at a time.

| Variant | Increment over prior variant | Purpose |
|---|---|---|
| V0 | Existing baseline prompt only | Establish unstructured baseline. |
| V1 | Require structured candidate records and official-source citation fields | Measure provenance improvement. |
| V2 | Add liveness/deadline/eligibility verification gate before ranking | Reduce stale and unsupported recommendations. |
| V3 | Add explicit profile-bridge extraction: current trajectory, reusable assets, constraints, uncertainty | Test profile specificity without changing discovery scope. |
| V4 | Add first-action planner with seven-day deliverable and effort accounting | Test practical actionability. |
| V5 | Add constrained ranker: objective weights, jobs exclusion, max counts, six-hour cap | Test disciplined selection. |
| V6 | Add portfolio/diversity selector and near-duplicate suppression | Test top-three breadth rather than three variants of one path. |
| V7 | Add critique-and-repair pass using the evidence/action judge failures; no new facts without source records | Test whether self-revision improves quality without hallucination. |

Implementation controls:

- Freeze prompt text for each tagged variant.
- Fix model, temperature, search budget, and source cap across variants.
- Preserve candidate pools before ranking, so V3–V7 can distinguish discovery changes from selection changes.
- V7 repair may delete/downgrade claims but may not add factual claims unless accompanied by a captured source record.
- Log elapsed time by stage: profile interpretation, discovery, verification, ranking, reporting, judging.

### Feasible run allocation

Three repeats for all 24 variant/repeat cells is unlikely to fit three hours if live research is involved. Use a sequential design:

1. **Smoke test** schemas/runner: 10 minutes.
2. **Screen V0–V7 once** with equal per-run research caps: about 80 minutes.
3. Select up to three eligible provisional frontier variants.
4. Run those variants until each has three total repeats: up to 60–75 minutes.
5. Blind judging, order checks, aggregation, and report: 30–40 minutes.

If time expires, publish the incomplete repeat matrix and do not claim repeat-level conclusions for unreplicated variants.

---

## 5. Three logically distinct blind judge prompts

Provide judges only: immutable profile summary, snapshot date, anonymous report/candidate packet, source excerpts, and rubric. Do not reveal variant, model, or prior scores.

### A. Evidence and compliance judge

> You are an evidence auditor, not an opportunity strategist. Evaluate only whether each material claim is supported by the supplied source records and whether the report obeys explicit constraints. Do not credit plausible facts absent from the packet and do not browse. Check official-source provenance, open/upcoming status relative to `snapshot_date`, deadline support, job exclusion, unsupported eligibility assumptions, count caps, and effort cap. Return `judge_result.schema.json`. Cite item IDs and quote IDs for every failure. Score only Evidence, Liveness, and Uncertainty/constraint handling; set other dimensions to null.

### B. Action and strategic-value judge

> You are a decision analyst for a technically sophisticated builder. Treat supplied evidence as true only to the extent indicated, but do not re-audit citation formatting. Judge whether each selected opportunity has a causal bridge to explicit profile facts, a meaningful plausible upside, and a feasible first action within seven days. Penalize generic fit, speculative upside, actions that are not atomic, and effort that is implausible under six hours/week. Do not reward employment opportunities. Return `judge_result.schema.json`, scoring Profile bridge, Actionability, Strategic value, and Decision quality only. State uncertainties rather than inventing missing facts.

### C. Portfolio and ranking judge

> You are a portfolio-selection reviewer. Ignore prose polish and independently assess whether the ordered shortlist is the best constrained portfolio represented by the supplied candidates. Check ranking rationale, duplication by organization/program/opportunity type, coverage of distinct paths, urgency tradeoffs, and whether a lower-ranked item dominates a higher-ranked one on evidence, value, and effort. Return `judge_result.schema.json`, scoring Portfolio diversity and Decision quality plus a ranked list of selected IDs. Identify dominated selections and omitted higher-value candidates using only the packet.

Dimension ownership prevents three near-duplicate “overall quality” judges. Aggregate only dimensions owned by a judge.

---

## 6. Pairwise and order-bias checks

Use pairwise comparisons for provisional frontier reports, not every pair of all variants.

For every pair `(X, Y)`:

1. Render identical blinded packets, randomizing names to `A/B`.
2. Ask a pairwise judge: “Which report is better under the hard gates and rubric? Return `A`, `B`, or `TIE`, with criterion-specific reasons.”
3. Re-run the identical packet with order reversed (`B/A`).
4. Use both Luna and Terra where available.

A pairwise result is **order-stable** only if:

- the mapped winner is identical under both presentation orders, or both are ties;
- otherwise mark it `ORDER_SENSITIVE`, award no pairwise win, and retain both reports for review.

Add a calibration check once per judge/model: compare the same report against itself under swapped labels. Any non-tie is a judge reliability failure. Also record left-position win rate; flag if it exceeds 60% across enough comparisons. With a small sample, report this descriptively rather than as a statistical claim.

---

## 7. Known-case and sparse-label handling

`pycon_za_2026` is a visible directional regression fixture, not a generalization metric.

Its pass condition is:

- finds verified PyCon ZA with supported CFP status/deadline and recommends adapting the existing talk; **or**
- finds an equally strong verified South African Python/developer-tools CFP with the specified bridge.

Failure modes are explicitly logged: no relevant search path, incorrect status, no reuse of existing talk, or generic conference suggestion. Never hard-code case names or facts into production prompts.

With no behavioral outcome labels, optimize measured decision quality rather than pretend to measure conversion. Preserve these proxies separately:

- evidence completeness;
- action feasibility;
- bridge specificity;
- portfolio diversity;
- independently judged strategic value;
- known-case regression outcome.

Do not collapse these into a claim of user success.

---

## 8. Convergence and Pareto rules

### Per-run eligibility and aggregate score

For each eligible run:

```text
weighted_score =
evidence + liveness + bridge + actionability +
strategic_value + diversity + uncertainty + concision - penalties
```

For a variant, report median, range, individual repeats, hard-gate rate, source-support rate, time, and judge disagreement. Do not rely on a mean of three runs alone.

### Pareto objectives

Minimize:

- hard-gate rate
- unsupported/stale claims
- total elapsed time
- estimated user effort
- judge disagreement

Maximize:

- rubric score
- source-support rate
- `ACT_NOW` first-action feasibility
- portfolio diversity
- known-case result

A variant is Pareto-dominated only when another variant is no worse on all objectives and materially better on at least one, while both are eligible.

### Promotion / winner rule

A variant may replace the incumbent only when:

1. it is hard-gate eligible in at least two of three repeats;
2. its median rubric score improves by at least **5 points**, or it removes a hard failure;
3. both presentation orders support the pairwise result, with no order-sensitive result;
4. it is not Pareto-dominated;
5. it does not regress the visible known-case fixture from pass/acceptable alternative to fail.

If the evidence judge finds an unsupported `ACT_NOW` claim, evidence/compliance overrides other judge scores.

### Stop rule

Stop mutation when either:

- two consecutive evaluated generations produce no promotable, non-dominated variant; or
- the three-hour deadline is reached.

A “generation” is the three variants allowed in `direction.yaml`; compare them against the incumbent under the above rule. Preserve partial work and state exactly which variants lack repeats or order checks.

This yields an auditable recommendation of the best observed pipeline, not a claim that V7 or any chosen variant generalizes beyond the visible profile and regression fixture.
