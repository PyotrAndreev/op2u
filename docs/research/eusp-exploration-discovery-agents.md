# EUSP literature synthesis: exploration under an insufficient verified portfolio

**Status:** research record; no pipeline or product change.  
**Scope:** discovery research only. This record asks how to search more broadly when the strict verified-action portfolio is empty or underfilled. It does not relax the [Discovery MVP](../product/discovery-mvp.md) grounding, liveness, action, effort, job-policy, privacy, consent, or user-control requirements, and it makes no claim about conversion, applications, or user outcomes.

## Decision frame and terminology

`insufficient_verified_portfolio` is a report state, not a score target or a reason to fill slots. It can be recorded when the saved run has no eligible selected item, or is below a separately declared user/product review range. The trigger and range must be versioned in an experiment; an empty result remains valid.

The output classes below are deliberately non-substitutable:

| Class | What the evidence establishes | May it be selected or consume scheduled effort? | Presentation |
|---|---|---:|---|
| **Verified action portfolio** (`ACT_NOW` / `PREPARE_NEXT`) | Direct official-primary evidence, quote, URL, retrieval time, current/open status, route, and live timing; an explicit profile bridge and a bounded user-controlled first action. | Yes, only after every MVP/P1 gate passes. | The compact decision-ready portfolio. |
| **High-value path with gaps** | A potentially valuable, profile-grounded path and the precise evidence gap (for example, no current route, status, date, or unresolved eligibility). Partial evidence is retained; the missing claim is never implied. | **No.** It is not an opportunity-horizon item, action, or evidence/liveness/actionability credit. | A gap record: what was checked, exact missing claim, source/retrieval time if present, and why it could matter. |
| **Exploration lead** | A profile-relevant organization, topic, or path without a verified current participation route. It can be weaker than a high-value gap record. | **No.** | Clearly separated lead, uncertainty, or search gap; never a recommendation to apply/participate. |

This makes the existing MVP rule operational: an exploration lead is not an opportunity-horizon item. A high-value path with gaps is a more diagnostic *non-eligible* lead, not a third kind of recommendation. Neither can be upgraded by polished prose, a relevance score, or a model/judge opinion. Unknown eligibility remains unknown.

## What the literature supports—and its limits

### Findings relevant to a research treatment

1. **Exploration is iterative sense-making, not a single relevance query.** Marchionini characterizes exploratory search as moving from finding toward learning/understanding through iterative querying, browsing, comparison, and interpretation [1]. This supports testing independently declared search branches (opportunity family, participation role, geography/time window, or source type), including honest empty branches. It does **not** show that more branches produce better opportunity portfolios.
2. **Allocate scarce research attention by expected information value, not only topical similarity.** Information-foraging theory models people as following cues (“information scent”) while balancing expected value and cost [2]. A bounded verification queue can therefore be tested using observable cues—official-domain likelihood, an explicit route/status/date cue, profile bridge, and duplicate risk—while recording failures and stopping when marginal verified yield is low. This is a hypothesis about research allocation, not a license to infer missing facts.
3. **Diversity reduces redundancy but trades against relevance/accuracy.** Ziegler et al. introduced intra-list similarity and topic diversification; their study found diversification could improve satisfaction while reducing average accuracy in some settings [3]. The later survey by Kaminskas and Bridge treats diversity, novelty, serendipity, and coverage as distinct beyond-accuracy objectives rather than interchangeable rewards [4]. For op2u, diversity should be measured over *verified, materially distinct* routes/families—not raw links—and must be secondary to hard gates and readiness.
4. **Serendipity is not a settled target.** Kotkov, Wang, and Veijalainen find varying definitions and evaluation approaches for serendipity [5]. It is reasonable to preserve an unexpected but profile-bridged path as a clearly labelled lead; it is not justified to optimize an undefined “surprise” score or represent surprising content as a live opportunity.
5. **Bandit evidence motivates experimental allocation, not online optimization claims.** Li et al. formulate personalized news recommendation as a contextual-bandit problem and report results in the Yahoo! news setting [6]. The transferable idea is a logged exploration/exploitation comparison under a fixed budget. Click-through reward, online personalization, and its reported lift are not op2u metrics; opportunity research has delayed, sparse, safety-constrained feedback.
6. **Web-research agents can retrieve and cite, but reliability remains a gate.** WebGPT demonstrates browser-assisted, citation-bearing question answering [7]. Mind2Web and WebArena demonstrate that general web-agent action and generalization remain difficult [8, 9]. These works support retaining source traces and benchmarking retrieval/verification separately from prose. They do not support autonomous application, interaction with sites, or treating an agent’s completion as evidence.

### Transferable hypotheses, not established product facts

- A declared coverage plan may find additional *verified* routes in an underfilled case more efficiently than repeatedly reformulating one query.
- Evidence-gap-aware verification ordering may yield more live, directly supported routes per bounded research effort than relevance-only ordering.
- A diversity-aware choice among already eligible items may make the small portfolio less redundant without lowering readiness.
- Explicitly typed gap records may help an auditor distinguish a safe empty/underfilled portfolio from an unsupported recommendation. This requires a comprehension/audit evaluation, not a conversion claim.

### Inappropriate or unconfirmed ideas

- **Do not fill a portfolio to meet diversity, novelty, coverage, or serendipity quotas.** An empty branch, lead, horizon, or portfolio is preferable to an unsupported item.
- **Do not use clicks, dwell time, acceptance, application, or participation as an automatic reward.** They are not available as safe immediate feedback and would confound eligibility, opportunity supply, and user choice.
- **Do not use a bandit to explore people, protected traits, inferred eligibility, or private profiles.** Only explicit, consented, versioned inputs may be used; private profiles and full runs remain outside Git.
- **Do not delegate external action to a web agent.** No login, form completion, outreach, submission, payment, or eligibility/legal determination follows from these papers.
- **Do not let a secondary source, model citation, or an agent trace repair grounding/liveness.** A selected material claim still needs direct official-primary evidence with the required fields at the snapshot.

## Atomic evaluation hypotheses

All experiments below are proposals only. Run one treatment at a time against the same frozen explicit/synthetic input, snapshot, worker configuration, source-access environment, source/research budget, report budget, and deterministic preflight. Preserve partial/failed artifacts and report medians/ranges over matched repeats. A result is non-promotable on any grounding, liveness, classification, weekly-effort, job-policy, privacy, or packet/manifest failure.

| ID and single changed factor | Baseline | Primary metric | Failure condition | Safety constraints |
|---|---|---|---|---|
| **H1 — coverage-plan fan-out.** Replace one relevance-led query plan with independently logged, bounded branches over declared opportunity family × participation role × geography/time window. | The frozen incumbent search plan, with the same total source/research budget. | Median count of materially distinct **verified current participation routes** retained in the opportunity horizon or eligible portfolio per matched run; also report empty branches and source requests. | No increase over baseline across the declared repeats, a skipped declared branch, or any increase in invalid/stale/duplicate selections. | Empty branches are successively recorded search gaps, not filled. Only direct official-primary evidence can make an item verified; selection limits and effort cap do not change. |
| **H2 — evidence-gap-aware verification order.** Order a fixed discovered candidate set by predeclared evidence-scent features (official route/status/date cue, explicit bridge, duplicate risk) instead of relevance-only order. | Relevance-only verification order over exactly the same candidate set and request budget. | Median number of candidates passing all direct-evidence and liveness checks per official-source retrieval; report elapsed time and unresolved-gap precision. | No improvement, a lower live-pass rate, or more unsupported material claims than baseline. | Ordering never changes the acceptance predicate. A missing route/status/timing claim remains a gap; no extra browsing budget, external interaction, or inferred eligibility. |
| **H3 — diversity-aware selection among eligible items.** Apply a fixed material-distinctness penalty only after the existing eligibility/readiness ranking. | Existing relevance/readiness ranking of the same preflight-eligible set. | Median count of materially distinct verified families/routes in the selected set, subject to non-inferior `portfolio_readiness_to_act`; report pairwise stability. | Any readiness decrease, unstable paired outcome, no diversity gain, or a gate failure. | Diversity is a tie-breaker after gates, never a quota. Keep max three `ACT_NOW`, max four `PREPARE_NEXT`, the weekly upper-bound cap, and every first-action requirement. |
| **H4 — typed non-eligible disclosure.** Render evidence-backed gap records separately from generic exploration leads after the verified portfolio is finalized. | The same evidence ledger with an untyped exploration-lead/gap presentation. | In a blinded artifact audit, precision/recall of the three classes in the table above and reviewer accuracy in identifying which items are eligible for a scheduled action. | Any gap/lead labelled eligible, lower class accuracy than baseline, or reviewers reasonably interpret a non-eligible item as a current route. | No gap/lead gets an action label, action budget, horizon/breadth credit, or imperative to apply. Use synthetic/anonymized records or explicit consent; do not retain private profile data in Git. |

The metrics intentionally do not measure applications, conversion, participation, satisfaction, clicks, or presumed eligibility. If an experiment needs a human audit, consent, retention, and anonymization must be specified before collection.

## Product options for `insufficient_verified_portfolio`

1. **Verified-only with an explicit insufficiency state (default-safe).** Return the compact eligible portfolio exactly as supported—even empty—then show count, failed gate category, and search gaps. This changes neither what is selected nor what is claimed.
2. **Bounded research expansion.** Offer a separately logged, fixed-budget coverage-plan pass (H1) and evidence-gap-aware verification pass (H2). Its output can add only newly verified items; all other results remain gap records/leads. This is a research/policy option, not permission to weaken liveness or increase action budget.
3. **Gap map for user review.** Show high-value paths with the exact missing evidence and a non-committal question the user may choose to investigate. Keep them visually and semantically separate from the verified portfolio and opportunity horizon; op2u does not contact anyone or take action.
4. **Eligible-set diversification.** If multiple items already pass, optionally apply H3 as a post-gate tie-breaker to avoid near-duplicate routes. It must be disabled/no-op when fewer than two eligible, materially distinct candidates exist.

A product decision should choose one option only after its corresponding preregistered evaluation passes. None authorizes a pipeline implementation through this issue.

## References

1. **Primary paper:** Gary Marchionini, “Exploratory Search: From Finding to Understanding,” *Communications of the ACM* 49(4), 2006, pp. 41–46. https://doi.org/10.1145/1121949.1121979
2. **Primary theory paper:** Peter Pirolli and Stuart Card, “Information Foraging,” *Psychological Review* 106(4), 1999, pp. 643–675. https://doi.org/10.1037/0033-295X.106.4.643
3. **Primary paper:** Cai-Nicolas Ziegler, Sean M. McNee, Joseph A. Konstan, and Georg Lausen, “Improving Recommendation Lists Through Topic Diversification,” *WWW ’05*, 2005, pp. 22–32. https://doi.org/10.1145/1060745.1060754
4. **Survey:** Marius Kaminskas and Derek Bridge, “Diversity, Serendipity, Novelty, and Coverage: A Survey and Empirical Analysis of Beyond-Accuracy Objectives in Recommender Systems,” *ACM TIST* 7(1), 2017. https://doi.org/10.1145/2926720
5. **Survey:** Denis Kotkov, Shuaiqiang Wang, and Jari Veijalainen, “A Survey of Serendipity in Recommender Systems,” *Knowledge-Based Systems* 111, 2016, pp. 180–192. https://doi.org/10.1016/j.knosys.2016.08.014
6. **Primary paper:** Lihong Li, Wei Chu, John Langford, and Robert E. Schapire, “A Contextual-Bandit Approach to Personalized News Article Recommendation,” *WWW ’10*, 2010, pp. 661–670. https://doi.org/10.1145/1772690.1772758  
   Author-hosted paper: https://www.schapire.net/papers/www10.pdf
7. **Primary paper:** Reiichiro Nakano et al., “WebGPT: Browser-assisted Question-answering with Human Feedback,” 2021. https://arxiv.org/abs/2112.09332
8. **Benchmark paper:** Shijie Deng et al., “Mind2Web: Towards a Generalist Agent for the Web,” 2023. https://arxiv.org/abs/2306.06070
9. **Benchmark paper:** Shunyu Yao et al., “WebArena: A Realistic Web Environment for Building Autonomous Agents,” 2023. https://arxiv.org/abs/2307.13854

The DOI and paper links above are the canonical citation targets; access status may vary by publisher. Claims here are bounded to the cited settings and proposed evaluations, not evidence that an op2u treatment works.
