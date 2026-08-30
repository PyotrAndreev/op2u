# ADR 0000: Record architecture decisions

Status: Accepted
Issue: Not applicable — repository documentation foundation

## Context

op2u combines product requirements, prompts, evaluation machinery, and research experiments. Durable choices must remain distinguishable from temporary experiments and ordinary implementation details.

## Decision

Use ADRs for durable architecture and product-policy decisions. Each ADR uses this format:

```text
# ADR NNNN: Title

Status: Proposed | Accepted | Rejected | Superseded
Issue: <GitHub issue URL or `Not applicable`>

## Context
## Decision
## Consequences
## Evidence
```

An ADR may link reproducible experiments, source material, and checks. It must state uncertainty where evidence is incomplete.

## Consequences

Project requirements belong in product specifications, experimental methods and results belong with evaluation artifacts, and task progress belongs in GitHub issues. ADRs provide the durable connection when a decision is made.

## Evidence

This structure follows the project practice described in the Devesis handbook: specifications, decisions, experiments, implementations, and tests answer different questions and should remain traceable.
