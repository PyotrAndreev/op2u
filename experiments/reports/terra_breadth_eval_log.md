Created breadth evaluation assets:

- `evals/rubric_breadth.yaml`
- `tools/score_breadth.py`
- `experiments/reports/breadth_eval_design.md`

`score_breadth.py` has stdlib-only CLI and embedded self-test; it reads saved report/validation artifacts without model or web calls.

Validated with:
- `py_compile` (redirected temporary bytecode)
- `python3 tools/score_breadth.py --self-test` → PASS
- scorer run against the latest BREADTH_V2 saved run.
