# Repository structure

The repository contains a discovery research and evaluation system, not yet a complete end-user application.

- `docs/product/` holds durable product intent, scope, requirements, and user boundaries.
- `docs/dev/` holds op2u-specific development conventions and maps repository artifacts.
- `docs/adr/` holds durable architecture and policy decisions.
- `prompts/` holds production and experimental prompt implementations.
- `evals/` holds rubrics, directions, schemas, and named fixtures.
- `tools/` holds runners, validators, scorers, report builders, and comparison tooling.
- `experiments/` holds reproducible experiment metadata, frontiers, selected reports, and retained comparison artifacts.
- `usr/` is deliberately empty in Git; local personal profiles are ignored.

A new directory needs an immediate, durable purpose. Do not reserve package, product, test, vendor, or platform directories in advance.

Experiment artifacts may remain only when they support reproduction, a maintained regression diagnostic, a frontier decision, or an explanation of an accepted result. Raw traces that contain profiles remain local and ignored. When retained artifacts become too numerous to navigate, keep a concise index and move nonessential raw output out of the main repository rather than treating history as a product document.
