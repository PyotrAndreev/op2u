# EUSP funding and competitiveness packet

This v1 path extension records a grounded funding decision surface inside the owning `path` of one [`eusp-opportunity/v1`](eusp-opportunity-contract.md) record. It is a record and validation boundary only: it does not discover sources, assess a user's eligibility, predict a user's chances, provide financial or legal advice, submit an application, or handle private data.

The packet is `path.funding_packet` in [`evals/schemas/eusp_opportunity.schema.json`](../../evals/schemas/eusp_opportunity.schema.json). It is validated by the ordinary opportunity validator:

```sh
python tools/eusp_opportunity.py --public-fixture \
  evals/fixtures/eusp_opportunity/v1/opportunity.json
```

## Required coverage and evidence boundary

The packet covers `programme`, `deadline`, `requirements`, and `documents`, plus the available competitiveness indicators `pool_size`, `acceptance_rate`, and `prior_recipients`. Every subject is one of:

- an `official_facts` row, grounded by direct `official_primary` evidence already in the opportunity ledger; or
- a `gaps` row with one or more searched sources.

An official fact only points to the existing evidence IDs. That ledger retains the exact quote, HTTPS URL, source type, retrieval time, verification-artifact path, hash, and direct-entailment boundary. A fact cannot be a free-standing paraphrase.

A gap is not evidence and does not assert that a fact does or does not exist. Each gap names its subject and question and cites every searched source with its URL, source provenance, retrieval time, verification artifact, and hash. A missing field therefore remains visible rather than becoming an unstated assumption.

## Competitiveness indicators

`indirect_indicators` is intentionally separate from `official_facts`. It can record only a published pool size, acceptance rate, or prior-recipient observation. Each indicator stores its exact quote and its own source URL, provenance, retrieval time, verification artifact, hash, and explicit uncertainty. Its source may be official-primary, official-secondary, or independent-secondary, but that provenance does not turn the indicator into an official programme fact.

An indicator is contextual evidence, not a conclusion about an individual. Historical pool size, rate, or recipient information does not establish the current pool, criteria, eligibility, ranking, funding completeness, or any person's outcome. The schema has no eligibility, chance, probability, or recommendation field, and the validator rejects packet claims that make a conclusion or prediction about the user.

## Fixture and limits

The committed fixture is fabricated and anonymized. It demonstrates official programme, deadline, requirements, and document facts; two separately sourced historical indicators; and a cited acceptance-rate gap. It contains no real person, profile, source snapshot, financial advice, legal advice, or private data. Real source artifacts and records remain outside Git under the existing profile and consent boundary.
