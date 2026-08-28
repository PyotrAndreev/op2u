# Execution plan

1. Validate and hash immutable inputs; create schemas, rubric, and experiment design.
2. Implement a simple subprocess-based runner with explicit Luna/Terra model selection, immutable run directories, manifests, complete artifacts, resumability, and saved-artifact evaluation.
3. Implement V0–V7 and controlled experiment metadata.
4. Smoke-test the runner without research, then run V0 baseline.
5. Run the cumulative ladder with three repeats where time permits; compare discovery, ranking, evidence, report, variance, and cost.
6. Use blinded external Luna/Terra judge calls; keep holdout out of all optimizer/mutation contexts.
7. Establish a Pareto frontier, analyze failures, and mutate until two externally judged generations fail to improve or the three-hour wall-clock budget is reached.
8. Write final comparison, recommended pipeline/prompt, and user-input gaps.

## Operational interpretation

There is no monetary/token ceiling. The hard operational ceiling is approximately three hours. Failed and partial runs are preserved. A real hidden holdout is unavailable, so no claim of holdout generalization is allowed.
