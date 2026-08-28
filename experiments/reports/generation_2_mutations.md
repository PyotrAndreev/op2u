# Generation 2 mutation

mutation:
  id: G2_M1
  parent: G1_M3
  affected_stage: ranking
  change: Combine the strict source-backed ACT_NOW gate with conservative upper-bound allocation of every action actually scheduled in the next seven days; separate first action, scheduled-week effort, and total completion effort.
  failure_addressed: G1_M3 passed liveness and actionability checks but all judges interpreted retained candidate total-effort ranges as a 6–11 hour selected week, contradicting the report's 2h15 first-action sum.
  expected_metric_improvement: Remove weekly_effort_limit and effort_accounting_ambiguous hard failures while preserving G1_M3 evidence and personalization scores.
  expected_regressions: Smaller shortlist, more deferred actions, and reduced portfolio breadth.
  falsification_condition: At least two of three repeats still fail effort accounting, or evidence/liveness materially regresses relative to G1_M3.

Three repeats are required before promotion. All use the same worker and external judge models as the screen.
