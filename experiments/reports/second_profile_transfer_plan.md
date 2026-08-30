# Applying the pipeline to a second profile

## Why this is a real generalization test

The Sofya Balanina profile differs materially from the original profile:

- academic admission rather than an open-source project is the main trajectory;
- the relevant opportunity unit may be a supervisor, lab, program, scholarship, pre-doc, methods school, conference, or exam session;
- the activation horizon is approximately one year, not only the next seven days;
- language preparation and exam logistics form a parallel operational track;
- existing European research relationships may be stronger bridges than broad web search;
- Cape Town is a one-month academic/geographic window rather than a long-term relocation preference.

A pipeline that simply replaces “peermux” with “cognitive science” has not generalized.

## Required pipeline improvements before a fair full run

1. **Parameterize prompt inputs.** Remove hard-coded Hong Kong/Shanghai/South Africa dates and project-specific examples from production prompts. Read all windows, effort caps, routes, and exclusions from profile/direction snapshots.
2. **Route-aware discovery.** Represent direct PhD, research Master’s, pre-doc/RA, supervisor collaboration, methods training, conference, grant, and language track separately. Do not rank them as interchangeable links.
3. **Long-horizon action model.** Preserve the seven-day first action while also representing 3-, 6-, and 12-month readiness milestones and application-cycle dates.
4. **Supervisor/lab verification.** Program existence does not imply supervisor availability. Record lab fit, current projects, admission route, whether contact is invited, and uncertainty separately.
5. **Funding decomposition.** Separate tuition waiver, stipend, living costs, travel/application support, grant eligibility, and unresolved financial gap. Do not label “funded” from a partial scholarship.
6. **Network bridge privacy.** Treat named contacts as user-controlled assets. Never assume a warm introduction; propose a bounded conversation or feedback request only after relationship strength and permission are clarified.
7. **Language/exam sub-pipeline.** First determine accepted exams/scores from target programs; then verify official test centers and sessions; then rank preparation practices. Do not optimize an exam before knowing that programs accept it.
8. **Runner parameterization.** Replace hard-coded 360-minute validation and prompt limits with the direction snapshot's declared cap. Keep code-enforced evidence normalization generic.
9. **Profile-specific rubric.** Add dimensions for research fit, supervisor/lab fit, complete funding, application readiness, network leverage, language progress, and one-year option value.
10. **Cross-profile evaluation.** Use the original profile and this academic profile as separate cases. A mutation is general only when it improves one without introducing evidence or actionability regressions in the other.

## Suggested controlled experiments

- Flat CV versus CV plus active goals/current state.
- Program-first search versus supervisor/lab-first search.
- Prestige-first versus research-fit/funding-first ranking.
- Web-only discovery versus network-bridge hypotheses before web search.
- Direct PhD only versus route portfolio including Master’s and pre-doc.
- Generic English preparation versus target-program-accepted-exam-first planning.
- Broad Europe search versus connection- and methods-fit-directed Europe search.
- Cape Town event catalogue versus dated academic-bridge search during exact presence.

## Perturbation tests

Create synthetic copies without changing real facts:

- October Cape Town presence present versus absent;
- direct researcher connection available versus unavailable;
- PhD preferred versus Master’s preferred versus unresolved;
- full funding mandatory versus partial self-funding possible;
- current English B2 versus C1-ready versus unknown;
- target intake 2027 versus 2028;
- weekly application capacity 2 versus 7 hours.

Rankings should react to these causal fields and remain stable under irrelevant formatting changes.

## Files

- Profile source: `~/notes/data/discovery/profiles/sofiya_balanina.md`
- Immutable project snapshot: `usr/profiles/sofiya_balanina_2026-08-03.md`
- Direction: `evals/direction_sofiya.yaml`
