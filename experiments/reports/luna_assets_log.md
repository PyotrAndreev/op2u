Implemented evaluation assets and prompt variants only.

Changes:
- Added/updated `evals/rubric.yaml`.
- Added six JSON schemas under `evals/schemas/`, including report and judge schemas.
- Rewrote cumulative prompt ladder `prompts/variants/V1.md`–`V7.md`.
- Added `experiments/reports/experiment_design.md` with E1–E12, budgets, controls, guardrails, convergence, and holdout limitations.
- Validated all JSON schemas syntactically and confirmed rubric YAML parsing.
- Did not read or modify `evals/holdout.yaml` or prohibited files.
