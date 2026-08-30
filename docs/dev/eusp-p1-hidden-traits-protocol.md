# EUSP P1 synthetic-profile evaluation with evaluator-only hidden traits

## Purpose and boundary

This is a small, reproducible **synthetic** evaluation protocol for the EUSP P1 readiness metric. It asks whether a blinded evaluator can annotate whether a public portfolio corresponds to predefined, evaluator-only synthetic traits while still measuring `portfolio_readiness_to_act` by the charter's five equal checks. It is a calibration and regression protocol, not a product change or a promotion result.

The public fixture is fabricated. It is not a private profile, a transformed profile, a real opportunity, a raw model trace, or a record of a person's behaviour. `example.test` evidence is deliberately synthetic. Personal profiles and complete production runs remain outside Git under the [profile and consent boundary](../product/user-profile-and-consent.md).

## Fixture layout and roles

[`evals/fixtures/eusp_p1_hidden_traits/v1`](../../evals/fixtures/eusp_p1_hidden_traits/v1) has three deliberately separate surfaces:

- `pipeline_input/` is the only profile/direction material a pipeline may receive.
- `pipeline_outputs/` contains hand-authored, synthetic final-report fixtures used only to test packet construction and measurement mechanics. They are **not** model outputs or efficacy results.
- `evaluator_only/hidden_traits.json` is available only after pipeline output is frozen, to the evaluator packet builder and the blinded readiness judge. Its traits have opaque IDs and unique leakage markers.

No worker prompt, pipeline input, report, source trace, model call, or public P1 packet may receive the evaluator ledger. The evaluator-only packet strips the leakage markers because judges need trait questions, not the administrative canaries. An evaluator may see the traits; a pipeline may not.

## Deterministic generation and execution protocol

1. Create visible facts from an invented persona. Do not copy, summarize, translate, or derive them from a user, production profile, model trace, or prior run.
2. Independently define one or more synthetic evaluator traits, each with an opaque ID, a unique `leakage_marker`, and an evaluation question. Do not place any ID, marker, or evaluator-only JSON key in pipeline material.
3. Freeze and hash the public profile, direction, arm prompts, rubric, schemas, and worker configuration before either arm runs. Run the ordinary P1 arms on only `pipeline_input/`, using the charter's immutable-artifact and paired-order requirements.
4. After each final report is complete, project it to the ordinary treatment-neutral P1 packet. Then run `tools/eusp_hidden_traits.py` with the frozen report and evaluator-only ledger to build a separate evaluator packet. This builder performs the mechanical leakage checks before emitting a packet.
5. Give only the evaluator packets and saved rubric to the hidden-traits judge prompt. Use two paired repeats in forward and reverse order as required by the P1 charter. Persist the result and its packet hashes locally; do not commit raw calls, private mappings, or profiles.
6. Validate a judge response with `validate_hidden_traits_result`. It requires one annotation for every evaluator trait and reuses the ordinary P1 gate-first arithmetic. A trait annotation never repairs a deterministic gate failure.

The committed fixture is reproducible without a model call:

```sh
python tools/eusp_hidden_traits.py
python -m unittest discover -s tests -v
```

The first command validates the separated fixture and builds both evaluator packets in memory. Add `--write-packets DIR` only for a local evaluator handoff; generated packets are not committed.

## Mechanical leakage checks

`leakage_errors` rejects, in the public profile, direction, report, and projected P1 packet:

- every evaluator trait ID and unique leakage marker; and
- the reserved JSON keys `hidden_traits`, `evaluator_only`, and `leakage_marker`.

The builder also schema-validates the synthetic ledger and evaluator packet and hashes the exact public P1 packet placed inside it. These are intentionally lexical checks: they cannot prove that a model did not infer a semantically similar preference from visible facts. That limitation is retained rather than hidden.

## Judge packet and measurement

`eusp-p1-hidden-traits-judge-packet/v1` nests the pre-existing public `eusp-p1-judge-packet/v1` plus evaluator-only trait labels and questions. `hidden_traits_pair_prompt` explicitly tells the judge that traits were unavailable to workers, forbids browsing and outside facts, and requests:

- the ordinary grounding, liveness, limits, job-policy, and seven-day-action gates;
- one five-boolean readiness row for each selected candidate; and
- one secondary `hidden_trait_matches` annotation for each evaluator trait.

The primary metric remains the charter's `portfolio_readiness_to_act`: mean of five 20-point checks for each selected `ACT_NOW`/`PREPARE_NEXT` item, zero for an empty selection. Gate failure makes an arm ineligible. Trait alignment is secondary and neither changes readiness arithmetic nor grants eligibility. The same five-point margin, two repeats, order stability, and non-promotion rules in the [P1 charter](eusp-p1-experiment-charter.md) still apply.

## Limits

This protocol does **not** validate behaviour. It observes neither a real user's preferences nor a person starting, completing, accepting, benefiting from, or being satisfied with an action. It cannot establish eligibility, causal effects, preference inference accuracy, generalization, or that a readiness proxy predicts real-world action. The committed reports merely exercise contracts; they do not show that either pipeline, a model, or an intervention is better. Any later result is limited to its frozen synthetic fixture and its saved judge calls.
