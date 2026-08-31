# EUSP non-obvious participation-mode ranking evaluation

**Status:** synthetic ranking experiment and regression fixture; not a P1 amendment, product change, or behavioural study.

This record implements Radicle issue `361542d`. It tests exactly one treatment: after ordinary eligibility preflight, add a declared ranking bonus for a **non-obvious participation mode**. It does not add LinkedIn, social data, external accounts, profile enrichment, or any other ranking factor. A mode is only eligible to be surfaced when its current participation route and that exact mode are directly supported by primary official-source evidence. The ordinary grounding, liveness, `ACT_NOW`/`PREPARE_NEXT`, seven-day-action, capacity, and effort gates remain first; a mode bonus never repairs a failed gate.

The versioned surface is [`evals/schemas/eusp_participation_mode.schema.json`](../../evals/schemas/eusp_participation_mode.schema.json), with a fabricated fixture at [`evals/fixtures/eusp_participation_mode/v1/fixture.json`](../../evals/fixtures/eusp_participation_mode/v1/fixture.json). Reproduce it with:

```sh
python tools/eusp_participation_mode.py --public-fixture \
  evals/fixtures/eusp_participation_mode/v1/fixture.json
python -m unittest tests.test_eusp_participation_mode -v
```

## Frozen comparison and provenance

The fixture freezes the candidate set and snapshot with a SHA-256 ledger hash, plus the source/research budget, report budget, action capacity, and weekly-minute cap independently in both arms; the validator rejects a mismatch or hash that does not bind the recorded candidate ledger. Baseline ranks eligible candidates by the declared `baseline_priority`. The intervention uses the identical eligible candidates and controls, changing only the declared `non_obvious_mode_bonus`. The evaluator emits the selected IDs and preserves each selected candidate's original direct-official-primary evidence row, including claim, exact quote, HTTPS URL, retrieval time, current status, temporal basis, and route/mode support tags.

`non_obvious` is a hand-authored fixture label for a participation *mode*, not a statement about a person. It is not inferred from silence, history, accounts, social graphs, contacts, or behaviour. `relevance_proxy` and `readiness_score` are likewise fixed synthetic measurement inputs. The five readiness booleans mirror the P1 checks only mechanically. No proxy measures whether anyone notices, prefers, starts, completes, accepts, benefits from, or participates through a route.

## Predeclared metrics and failure condition

Before the fixture is evaluated, `failure_condition` fixes these measurements:

- **Mode-novelty proxy:** proportion of selected candidates whose fixture mode is labelled `non_obvious`; the intervention must increase it by at least `0.01`.
- **Relevance proxy:** mean fixed `relevance_proxy`; it must not decrease.
- **Grounding rate:** selected candidates with a current direct official-primary route (and, for a non-obvious mode, direct evidence for that exact mode); it must remain `1.0`.
- **Readiness-to-act proxy:** mean fixed readiness score, backed by all five declared local readiness checks; it must not decrease.

The run fails if the fixture/schema is invalid, controls differ, a selected candidate fails grounding/liveness/actionability or the effort cap, a non-obvious mode lacks direct official-primary route-and-mode evidence, novelty misses its predeclared gain, grounding is below its threshold, or relevance/readiness declines. An empty result remains valid but cannot satisfy a positive novelty-gain condition.

For the committed fabricated fixture, the mechanical baseline selects `pm-open-call` and `pm-standard-workshop`; the treatment replaces the latter with the primary-evidenced `pm-contribution-sprint`. The resulting fixture proxies are novelty `0.0 → 0.5`, relevance `89.0 → 89.0`, grounding `1.0 → 1.0`, and readiness `100.0 → 100.0`; the failure condition is not met. This confirms only deterministic ranking and gate preservation on fictional data, not that the intervention is useful, novel, relevant, grounded, ready, or effective for any user or live opportunity.
