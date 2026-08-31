# EUSP opportunity contract

This is the v1 contract for one evidence-backed opportunity record. It realizes the Discovery MVP's requirement for an explicit profile bridge, primary-source evidence, liveness, bounded action, and preserved uncertainty. It is a record and validation boundary only: it does not discover opportunities, infer profile facts, determine eligibility, contact an organization, or submit anything.

The machine-readable contract is [`evals/schemas/eusp_opportunity.schema.json`](../../evals/schemas/eusp_opportunity.schema.json). Its public fabricated fixture is [`evals/fixtures/eusp_opportunity/v1/opportunity.json`](../../evals/fixtures/eusp_opportunity/v1/opportunity.json). Validate a record deterministically:

```sh
python tools/eusp_opportunity.py --public-fixture \
  evals/fixtures/eusp_opportunity/v1/opportunity.json
```

## Entity boundary

An `eusp-opportunity/v1` document is exactly one opportunity (`id`) and has exactly one owned `path` object. A path is not an entity to join against opportunities: there is no `paths` collection, no opportunity reference in `path`, and no opportunity × path expansion. A different possible route is a different revision or a separately considered opportunity record, not an additional selected copy of this record.

`path.verified_actions` contains only concrete user-controlled next actions supported by direct official-primary evidence. `path.gaps` contains unanswered questions or missing material. A gap is never an action, does not have evidence references, and does not become verified because it is useful or plausible. This distinction keeps a verified action separate from preparation work caused by a gap. The path also owns the fixed [practical-component research ledger](eusp-path-components.md), [funding and competitiveness packet](eusp-funding-competitiveness-packet.md), and [separate path-cost policy](eusp-path-cost-policy.md): they separate verified actions, high-value paths with cited gaps, and exploration leads without making an unresolved travel, lodging, visa, funding, outreach-route, money, time, or stress fact into a claim. The funding packet preserves official programme facts separately from contextual competitiveness indicators and never makes an eligibility or chances conclusion.

## Value hypotheses

`value_hypotheses` is a non-empty list of independent, falsifiable explanations of possible value from the same opportunity. Every hypothesis has:

- `causal_bridge`: why the named explicit profile signals could lead to the stated value;
- `profile_basis`: explicit `field_id` references with `user_supplied` provenance, never inferred traits;
- `evidence_ids`: its own direct official-primary evidence rows;
- `uncertainty_ids`: explicit unknowns that limit the hypothesis; and
- `confidence`: `low`, `medium`, or `high`, never a certainty claim.

The validator requires one distinct direct evidence row per hypothesis whose `supports` contains that hypothesis ID. It also requires every referenced uncertainty and profile field ID to be non-empty. It does not turn a profile reference or a confidence label into proof.

## Evidence, liveness, and eligibility boundary

Every evidence row records claim text, an exact quote, HTTPS source URL, retrieval time, source type, direct entailment, liveness status/temporal data, and the immutable verification artifact and SHA-256 hash that produced it. For `ACT_NOW` and `PREPARE_NEXT`, deterministic gates require direct official-primary evidence for a current participation route and current liveness at the saved snapshot; a passed gate does not make the user eligible.

The contract intentionally has no user-eligibility conclusion. `eligibility_assessment` is always `not_assessed`; any organizer requirement belongs in quoted source evidence or an explicit gap. Missing personal facts remain in `uncertainties` or `path.gaps`. The validator rejects a user eligibility field and does not infer a result from source text.

`synthetic` and `fixture_notice` exist only to mark a committed public fixture. Real profiles, production records, raw source snapshots, and private data remain outside Git under the [profile and consent boundary](user-profile-and-consent.md).

## Limits

Validation is structural and deterministic. It checks references, provenance shape, independent hypothesis grounding, action/gap separation, liveness/grounding gates, and bounded seven-day verified actions. It cannot establish that a quote is true, that a URL remains live, that a causal bridge will produce value, or that a user satisfies an organizer's requirements. Those unknowns remain explicit.
