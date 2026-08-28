# Cross-profile prompt experiments

## Objective

Extract a single opportunity-discovery framework from the BH7 prompt, use the Sofya academic profile as a visible transfer case, deepen the academic result, and rerun the resulting framework on the original breadth profile without evidence or actionability regression.

## Baseline

BH7 on Sofya (`2026-08-03T162417+0000-156f9e84d514`) passed production schema but failed all academic judge verdicts because it retained the original 360-minute cap instead of the supplied 240-minute cap. It also inherited the original profile's broad South Africa window and selected a November event outside Sofya's October Cape Town presence. Funding, target-program TOEFL requirements, and person-specific routes remained shallow.

## Hypothesis outcomes

- **T1 — profile/direction parameterization:** removed geography leakage and used the 240-minute cap. One run was useful, but controlled repeats had zero recall or cross-artifact evidence failure.
- **T2/T3 — route ontology and anchors:** generated useful structure, but stage outputs collapsed into status acknowledgments or empty verification artifacts.
- **T4 — focused anchors:** greatly improved named-person personalization and safe stretch, but invented a 2027 deadline from an undated May 1 quote.
- **T5/T6/T8/T9 — decision completeness and provenance:** exposed the mismatch between verification `evidence_records` and report-time `evidence_ledger`; some variants preserved deep funding evidence but lost actions or stage consistency.
- **T10 — actual verification-record contract:** fixed the cross-profile evidence-loss mechanism and recovered actionable output on both profiles.
- **T11 — quote-bounded time:** prevented years/cycles absent from exact quotes. Prompt-only retries remained unreliable, so equivalent year filtering was enforced deterministically in the runner.
- **T12 — seven-day action separation:** separated immediate user artifacts from later external openings/events and raised original-profile actionability to 16/16.
- **T13 — funding components:** separated an official “fully funded” label from verified tuition, stipend, living support, duration, and residual gap.
- **T14 — quote-bounded geography:** required exact official evidence for both place and date before geographic-window credit.

## T14 cross-profile result

### Original profile, strong run

Run: `2026-08-04T043420+0000-45439953034f`

- Production validation PASS.
- Evidence 24/24; actionability 16/16; stretch 5/5.
- Five verified families: place event, community, funding, adaptation, visibility.
- Four deterministic geographic hits covering Hong Kong, first Shanghai window, and South Africa/Cape Town.
- 205 scheduled upper minutes.
- Remaining gaps: later Shanghai window, recurring South Africa adaptation, teaching, creative, outdoors.

### Original profile, conservative repeat

Run: `2026-08-04T043017+0000-49a87bbbddc6`

- Production validation and all external hard gates PASS.
- Evidence 24/24 and actionability 16/16.
- Recall fell to one verified family and no quote-supported geographic window.

This demonstrates safety stability but not recall stability.

### Sofya profile

Run: `2026-08-04T043904+0000-22d8821ba413`, using independent research prefix `2026-08-04T031327+0000-e1201c9ff784`.

- Production validation PASS; four judge roles without hard failure.
- Evidence 20/20; actionability 15/15.
- Selected PREPARE_NEXT route: University of Barcelona Brainlab VariSoA 3+1 cognitive-neuroscience PhD eligibility-and-fit matrix, 40–60 minutes.
- The source states Spring 2027 and an expected November–December 2026 FPI call.
- Material blockers are explicit: EU citizenship and at least 300 ECTS including a Master's degree are unresolved.
- The source's “fully funded” wording is retained only as an official label; tuition, stipend/living support, and residual gap remain unknown.
- Funding completeness 4/12; graduate-route depth 8/15; person-specific path 5/10.
- No verified October Cape Town route or complete TOEFL target-score plan.

## Pairwise evidence

- T14 vs BH7 on original profile: `compare-2026-08-04T044322+0000-24ba5aabe6`, 8/8 mapped votes for T14, all four role outcomes order-stable.
- T13 parent vs BH7 on original profile: `compare-2026-08-04T034904+0000-d9d023138c`, 16/16 votes for T13.
- T13 parent vs Sofya BH7 baseline: `compare-2026-08-04T035601+0000-3095ac07eb`, 16/16 votes for T13.

## Framework extracted

The portable core is not an academic prompt or a project prompt. It consists of:

1. profile/direction-derived routes, windows, exclusions, and effort cap;
2. independent geography and role branches only when profile-supported;
3. separate verified opportunities and exploration leads;
4. verification via direct official-primary records;
5. report projection from the verification collection actually produced;
6. deterministic quote/time/hash checks;
7. quote-bounded temporal and geographic claims;
8. seven-day user action separated from future external trigger;
9. funding labels separated from funding components;
10. profile-specific rubric overlays on a shared evidence/actionability core.

## Promotion decision

T14 is the provisional cross-profile frontier. It generalizes evidence safety, actionability, cap handling, and profile isolation across two visible profiles and wins blinded comparisons. It is not a final stable production release because recall varies materially across repeated discovery calls and no hidden holdout exists.
