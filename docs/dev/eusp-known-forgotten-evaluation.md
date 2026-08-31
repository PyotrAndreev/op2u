# EUSP known-versus-forgotten local ranking evaluation

**Status:** synthetic ranking experiment and regression fixture; not an MVP change, behavioural study, or P1 promotion result.

This record implements Radicle issue `0b28a35`. It tests one narrow treatment: make explicit local awareness state visible without turning silence, a discovery trace, or a third-party record into a claim that a person knows or has forgotten an opportunity. It preserves the Discovery MVP's evidence/liveness/action gates and the `ACT_NOW` / `PREPARE_NEXT` meanings. It does not amend the P1 comparison arms or readiness metric.

## Boundary and local evidence model

The machine-readable surface is [`evals/schemas/eusp_known_forgotten.schema.json`](../../evals/schemas/eusp_known_forgotten.schema.json); its committed fixture is fabricated at [`evals/fixtures/eusp_known_forgotten/v1/fixture.json`](../../evals/fixtures/eusp_known_forgotten/v1/fixture.json). Validate and reproduce its deterministic result with:

```sh
python tools/eusp_known_forgotten.py --public-fixture \
  evals/fixtures/eusp_known_forgotten/v1/fixture.json
python -m unittest tests.test_eusp_known_forgotten -v
```

This is a **minimal local input**, not a memory system. An awareness record contains only an opaque candidate ID, a current explicit statement, and its local user-supplied provenance. It has no account identifier, URL, external source, browsing/saved history, contact, relationship, calendar, credential, profile enrichment, collection process, timestamped event log, or inferred trait. The fixture has no real data. A future local UI would require the same explicit, per-item input; it must not synthesize records from omitted facts or accumulate behavioural history.

| State | Representable evidence | Meaning and restriction |
| --- | --- | --- |
| `known` | One or more `explicit_current_recognition` statements with `user_supplied_local` provenance. | The user currently says they recognize this exact candidate. It is a label, not a value, eligibility, or novelty conclusion. |
| `forgotten` | One or more `explicit_reminder_request` statements with `user_supplied_local` provenance. | The user explicitly requests a local reminder for this exact candidate. It does **not** diagnose memory or assert that the system observed forgetting. |
| `unknown` | Exactly an empty evidence list. | No awareness fact is available. Silence remains unknown and is retained; no state can be guessed from similarity, a prior run, absence of a record, an account, history, contacts, calendar, or behaviour. |

The validator rejects state/evidence mismatches, duplicate IDs/priorities, an oracle reference to an unknown candidate, and a usefulness label for a gate-failed reminder. Awareness evidence can never prove opportunity grounding, liveness, user eligibility, profile facts, value, cost, or permission to act.

## Ranking treatment

The treatment is intentionally a projection, **not** a scalar awareness bonus or penalty.

1. Apply the ordinary grounding, liveness, and actionability preflight first. Only a candidate that passes all three may enter any lane. Its classification remains `ACT_NOW` or `PREPARE_NEXT`; a failed or stale candidate is neither selected nor reminded.
2. Freeze the ordinary action ordering by the already-declared `action_priority` and capacity. The baseline and treatment action-selected IDs must be identical. Thus a known high-value candidate cannot be silently removed, demoted, or displaced by a novelty/reminder label.
3. After that fixed selection, project three visibly separate, non-competing lanes: `known_label` for eligible explicitly known candidates, `novelty_lane` for eligible `unknown` candidates only, and `reminder_lane` for eligible `forgotten` candidates only. A reminder is a local display label; it consumes no scheduled effort and does not itself make an action live, eligible, or selected. A candidate independently selected for an action may also carry a reminder label.

`known` and `forgotten` are therefore excluded from the novelty lane, but not from the action decision lane. This separates repeat/recognition handling from novelty rather than letting it silently suppress a high-value action. No awareness state changes an evidence row, source requirement, liveness result, profile bridge, weekly cap, action start date, or `ACT_NOW`/`PREPARE_NEXT` classification.

## Reproducible synthetic evaluation

The fixture fixes identical candidates, gate statuses, action priorities, capacity, and budget proxy for both arms. The only changed factor is the post-selection awareness projection:

- **Baseline:** ordinary eligibility-gated action selection, with no awareness lanes.
- **Known/reminder treatment:** the identical action selection plus the three awareness lanes above.

It records two deterministic measures:

1. **False suppression rate:** high-value (`action_priority >= 80`) candidates selected by baseline but absent from treatment action selection, divided by baseline-selected high-value candidates. The fixture result is `0.0` (zero candidates). Any non-zero rate, a changed action-selected ordering, or a gate/classification violation is a treatment failure.
2. **Reminder usefulness proxy:** precision and recall of emitted live reminder IDs against the fixture's separately declared `reminder_useful_ids`. The fixture emits two live reminders, one labelled useful by the synthetic oracle, giving precision `0.5` and recall `1.0`. The stale forgotten candidate is excluded. This deliberately exposes an unnecessary reminder instead of calling every reminder useful. For a future preregistered synthetic comparison, require recall `1.0` and precision at least `0.5`; report counts as well as rates.

The oracle is a hand-authored fixture label, not user feedback. It tests that the ranking logic preserves a declared reminder target and exposes false positives; it does **not** observe a real person noticing, valuing, starting, completing, accepting, or benefiting from a reminder. It cannot validate memory, preference, relevance, eligibility, action outcome, conversion, satisfaction, or generalization. It makes no behavioural-validation claim.

The experiment is non-promotable on an invalid schema/fixture, any failed grounding/liveness/actionability gate in an emitted action or reminder, changed action selection, non-zero false suppression, reminder recall below `1.0`, reminder precision below `0.5`, or any privacy/scope violation. A result remains fixture-scoped even if it clears these mechanical conditions.
