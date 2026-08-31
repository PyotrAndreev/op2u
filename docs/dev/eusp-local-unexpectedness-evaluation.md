# EUSP local-unexpectedness ranking evaluation

**Status:** synthetic, fixture-scoped ranking experiment and regression check; not an MVP change, P1 promotion, behavioural study, or production ranking decision.

This record implements Radicle issue `471c5a2`. It tests exactly one post-verification ranking signal: an **explicit local-unexpectedness proxy**. No other ranking factor, source-discovery behaviour, account, social connector, external write, or profile ingress changes. In particular, it does not use LinkedIn, social data, contact data, browsing history, calendar data, external accounts, IP-derived location, or inferred dates/locations.

## Reproduce

The schema is [`evals/schemas/eusp_local_unexpectedness.schema.json`](../../evals/schemas/eusp_local_unexpectedness.schema.json); the fabricated fixture is [`evals/fixtures/eusp_local_unexpectedness/v1/fixture.json`](../../evals/fixtures/eusp_local_unexpectedness/v1/fixture.json).

```sh
python tools/eusp_local_unexpectedness.py --public-fixture \
  evals/fixtures/eusp_local_unexpectedness/v1/fixture.json
python -m unittest tests.test_eusp_local_unexpectedness -v
```

The fixture stores SHA-256 hashes of the complete candidate set and the whole common input/budget bundle. Each evidence row retains its direct official-primary quote, URL, retrieval time, liveness data, synthetic verification-artifact identifier, and a hash of that provenance row. The evaluator rejects any altered row, input/budget bundle, or candidate-set hash and projects those exact rows into each arm's selected output.

## Frozen control and treatment

The common fixture contains one explicit, fictional `Cedar Bay` window (`2026-10-01` through `2026-10-31`) with `user_supplied` provenance, one snapshot, one candidate set, one source-retrieval budget, one report budget, and one selection capacity. The baseline and treatment read that same frozen bundle; there is no per-arm research, report, or capacity allowance.

| Arm | Ranking rule | Changed factor |
| --- | --- | --- |
| `LU_V0_FROZEN` | frozen descending `base_rank` | none |
| `LU_LOCAL_UNEXPECTEDNESS` | the same `base_rank` plus a fixed bonus | local-unexpectedness proxy only |

A candidate gets that bonus only when all of these literal facts are present:

1. its local-awareness state is `unknown` with an exactly empty evidence list (not a claim that the person is surprised);
2. its directly evidenced place exactly equals an explicitly supplied place string; and
3. its directly evidenced start and end dates both lie inside that same explicitly supplied inclusive date window.

There is no geocoding, proximity lookup, place aliasing, date completion, nearest-date rule, or fallback for omission. A different place, a partial/outside window, known/forgotten awareness, absent evidence, or a failed gate produces no bonus. `unknown` means no awareness fact is available, following the [known-versus-forgotten contract](eusp-known-forgotten-evaluation.md); it is never converted into a fact of novelty, surprise, preference, or usefulness.

## Gates and preregistered failure condition

Before ranking, every candidate must have direct official-primary, exact-quote evidence for status, participation route, liveness, place, and date. Its liveness date must be current at the frozen snapshot. Every selected action remains `ACT_NOW` or `PREPARE_NEXT`, local and user-controlled, has a bounded 1–60 minute first action, disclosed blocker, and starts within seven days. Failed grounding, liveness, provenance, or action safeguards reject the fixture rather than creating a selection.

The fixture declares this failure condition **before** calculating its result. The treatment fails if any of the following holds:

- its local-unexpectedness novelty count rises by less than one over the frozen baseline;
- its mean declared relevance proxy is lower than baseline;
- either arm has incomplete grounding; or
- either arm loses a readiness-to-act safeguard, evidence/liveness gate, or `ACT_NOW` safeguard.

The reported metrics are: selected local-unexpectedness proxy count/rate (**novelty**), mean fixture-declared relevance proxy (**relevance**), direct-evidence pass rate (**grounding**), and complete bounded-action rate (**readiness-to-act proxy**). The committed deterministic fixture produces 0 to 2 proxy-novel selections, relevance 87.5 to 90.5, and complete grounding/readiness in both arms; therefore its preregistered failure condition is not met. This is only a check that the frozen mechanics behave as declared—not evidence that the signal improves a real portfolio.

## Limits

The relevance labels, awareness statements, opportunities, organizations, sources, places, dates, and outcomes are fictional/anonymized fixture data. The local-unexpectedness metric is a structural proxy, not observed novelty or a user benefit. This fixture does not measure preference, relevance for a person, memory, surprise, eligibility, action completion, participation, conversion, satisfaction, safety in real geography, or generalization. It cannot validate the truth or present liveness of a real source, even though it ensures evidence/liveness fields are retained and fail closed in the fixture.

Consequently this result cannot promote P1, change the Discovery MVP, or justify a production score. Any future experiment must freeze its own explicit consented inputs, supplied geography/date windows, source environment, and identical budgets; preserve the same evidence/liveness and local-action gates; declare its failure condition before results; and keep profiles and raw source traces outside Git.
