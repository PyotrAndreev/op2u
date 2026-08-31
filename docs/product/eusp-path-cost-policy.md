# EUSP path-cost policy

This v1 policy adds a cost view to the owned `path` in one [`eusp-opportunity/v1`](eusp-opportunity-contract.md) record. It is a decision aid, not financial advice, a price guarantee, a recommendation to spend money, or a booking workflow. It does not contact a provider, reserve travel or lodging, purchase anything, or assess affordability.

The machine-readable surface is `path.path_cost` in [`evals/schemas/eusp_opportunity.schema.json`](../../evals/schemas/eusp_opportunity.schema.json), checked by [`tools/eusp_opportunity.py`](../../tools/eusp_opportunity.py). The fabricated fixture demonstrates the shape only; it is not a price source.

## Three independent dimensions

`path_cost.money`, `path_cost.time`, and `path_cost.stress` are independent ledgers. Each has its own status, estimates, and gaps; none contains or derives an overall cost, score, rank, conversion, affordability result, or recommendation. Money entries retain a currency and monetary range. Time entries retain a minutes range. Stress entries retain only a stated `stress_1_to_5` range and its cited basis; it is not converted into money, time, value, or a route classification.

A high stress range never rejects, down-ranks, or removes an opportunity. In particular, `high_value_with_gaps` remains available for a path whose value hypotheses are evidence-backed even when its stress is high or uncertain. Consumers must show all three ledgers and their gaps together rather than hide a high-value/high-stress path behind a composite result.

## Evidence, date, location, and uncertainty

Every estimate records its range, location basis, retrieval timestamp, and source provenance (source type, HTTPS URL, and exact supporting quote). Money estimates additionally record a three-letter currency. `date_basis` names the single comparison date used by the assessment and retains the relevant official evidence ID.

When the opportunity has a date, `date_basis` must use that opportunity date. When it has no date, it must use the nearest user-available date and identify the explicit `user_supplied` availability field; it must not guess a date from silence. The deterministic validator enforces the representable branch and references, while the local profile remains the authority for whether that supplied date is nearest.

Unknowns stay visible: a dimension with no estimate is `unknown` with a non-empty gap; a partially researched dimension is `partial` with both an estimate and a gap. A gap records what is missing and searched sources. A range is only what its recorded source supports: do not invent fares, prices, exchange rates, taxes, fees, availability, reimbursement, or personal affordability.

## Long programmes

`programme_duration_days` records a sourced duration range when known. A programme of at least 14 days is long. For a long programme, research and display `cost_of_living` before `flights`: a cost-of-living estimate is `primary` and a flight estimate is `secondary`. If a cost-of-living estimate cannot be supported, an explicit `cost_of_living` gap is required instead. This is a research/display priority only; it makes no purchase, funding, or affordability decision.

## Validation

```sh
python tools/eusp_opportunity.py --public-fixture \
  evals/fixtures/eusp_opportunity/v1/opportunity.json
python -m unittest tests.test_eusp_opportunity -v
```

Validation is structural and deterministic. It cannot verify live prices, source truth, currency conversion, a user’s available funds, actual travel time, individual stress, eligibility, or a booking outcome. Those are intentionally outside this policy.
