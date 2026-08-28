Implemented core tooling:

- `tools/run_experiment.py`
  - Immutable V0–V7 runs, input snapshots/hashes, manifests, flat call artifacts.
  - Monolithic V0–V3 and staged V4–V7 pipelines.
  - Explicit Luna/Terra `pi --mode json` calls, JSON/text/usage capture, per-call/global timeouts.
  - Partial-failure preservation, retry/resume attempts, dry-run mode.
  - Judge-only saved-artifact mode with three roles and registry appends.

- `tools/compare_variants.py`
  - Blinded saved-artifact A/B comparisons with randomized A/B mapping, role repeats, persisted mappings/results, and no research.

- `tools/build_report.py`
  - Static report generation from persisted runs, judges, comparisons, statuses, and cost artifacts; no model calls.

Validation run:
- `python -m py_compile tools/run_experiment.py tools/compare_variants.py tools/build_report.py`
- Dry-run smoke tests for staged research, resume/retry, judge-only mode, comparison, and report generation.
