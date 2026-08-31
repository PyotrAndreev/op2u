# EUSP path components and research gaps

This v1 extension makes practical path research explicit inside the owning `path` of one [`eusp-opportunity/v1`](eusp-opportunity-contract.md) record. It is a deterministic record boundary, not discovery, scraping, legal advice, eligibility assessment, booking, funding administration, contact lookup, or outreach.

## Required component ledger

Every path records exactly one component for `travel`, `lodging`, `visa`, `funding`, and `outreach_route`. Each component carries its applicability, status, HTTPS source links, component retrieval time, and one or more explicit assumptions. This fixed ledger makes an omitted practical concern visible rather than silently treating it as available or irrelevant.

`status` has three meanings:

- `verified` is permitted only for an applicable component with direct official-primary evidence explicitly mapped to that component.
- `gap` records unavailable or unresolved information. An applicable or unknown component must use it unless it is verified. A gap has a non-empty reason and non-empty `searched_sources`, both cited from its source links, and has no evidence IDs. It is therefore not a factual claim.
- `not_applicable` is permitted only where the component is explicitly marked not applicable and directly evidenced. It is not a default for silence.

Assumptions bound interpretation; they do not fill a gap. For example, a quoted travel stipend does not establish an amount, a booking procedure, lodging, visa status, legal eligibility, or that it meets a person's needs. A visa component may record a source-backed organizer fact, but an individual's legal outcome remains an unknown/gap; the contract never concludes whether someone may travel or participate.

## Route distinction

`path.route_status` preserves three different record states:

- `verified_actions` has a supported user-controlled action and no unresolved component gap.
- `high_value_with_gaps` may have verified actions, but it visibly retains one or more component gaps. It is not silently upgraded to a fully verified route.
- `exploration_lead` has no verified action and must retain a component gap. It cannot be `ACT_NOW` or `PREPARE_NEXT`; it receives no selected-opportunity action credit.

`outreach_route` is only a researched route component. This contract neither proposes an external message nor authorizes contacting anyone; it records a verified public route or an explicit gap without converting either into outreach.

## Validation and fixture

The component ledger is part of [`evals/schemas/eusp_opportunity.schema.json`](../../evals/schemas/eusp_opportunity.schema.json) and is validated by the existing opportunity validator:

```sh
python tools/eusp_opportunity.py --public-fixture \
  evals/fixtures/eusp_opportunity/v1/opportunity.json
```

The committed fixture is fabricated. Its unknown lodging, visa, and outreach-route components are cited gaps, not claims that those facts do or do not exist. Real source artifacts, profiles, and research runs remain outside Git.
