# Evaluation

Evaluation checks whether a discovery run conforms to the Discovery MVP specification, not whether a response merely sounds useful.

`evals/` contains directions, rubrics, schemas, and visible fixtures. `tools/` runs staged discovery, validates structured output, scores it, and compares variants. `experiments/` records variant metadata, run inventories, comparisons, and selected conclusions. The fixed EUSP priority-1 protocol is defined in the [EUSP priority-1 experiment charter](eusp-p1-experiment-charter.md).

A deterministic check should validate properties such as schema validity, unique identifiers, required evidence fields, referenced artifacts, classification limits, and weekly effort arithmetic. Semantic judgment remains separate: judges assess evidence quality, liveness, profile bridge, actionability, strategic value, and portfolio diversity.

Visible fixtures are regression diagnostics, not a hidden holdout. Conclusions drawn from them are profile-scoped and must not claim generalization. A prompt or implementation change is promotable only under the rubric's recorded evidence and comparison criteria; a polished report does not repair missing source evidence.

Every experiment should state its hypothesis, changed factor, method, measurements, result, and limits. Keep an experiment when it continues to support a maintained decision or regression check; otherwise retain the conclusion in an issue or ADR and remove transient material from the integration branch.
