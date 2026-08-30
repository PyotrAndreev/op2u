# P1 shared report-serialization addendum

Apply this addendum **only while rendering the final report JSON**. It is a common output serialization contract for the blinded P1 judge packet. It does not change discovery, source verification, ranking, candidate selection strategy, research breadth, or staged versus monolithic execution. Do not revisit earlier decisions to satisfy this addendum; serialize their supported final-report fields faithfully, leaving unsupported facts missing.

Return the normal final report JSON with `snapshot_date`, `candidates`, exact `selected_ids` buckets (`act_now`, `prepare_next`, `monitor`), `weekly_allocation`, and `evidence_ledger`. A candidate selected in a bucket must have the matching status: `ACT_NOW`, `PREPARE_NEXT`, or `MONITOR` respectively.

For every selected `ACT_NOW` or `PREPARE_NEXT` candidate, serialize ID, title, organization, `type`, profile bridge, first action, scheduled-week effort, blockers, uncertainties, and claim IDs. Also serialize exactly one or more material-claim objects for each of the three required kinds: `status`, `timing`, and `participation_route`. Each object has a unique `id` that is the matching direct ledger `claim_id` and a `kind`; do not reuse an ID for different kinds. A participation-route claim states the official way to apply, register, submit, or otherwise take part. Its `first_action` must include `action`, `deliverable`, `start_by_or_trigger`, date-only `start_date` (`YYYY-MM-DD`), `minutes_min`, and `minutes_max`. The start date must be from the saved snapshot date through snapshot +7 days; the action remains user-controlled and within the direction's minute bound.

For every material claim, serialize one or more linked direct `official_primary` evidence-ledger rows whose `claim_id` exactly equals that material claim's `id`. Each row needs candidate ID, claim ID, claim, `entailment: "direct"`, exact quote, HTTPS URL, retrieval time, and `supports`. `supports` must include `status` for a status claim, the matching temporal kind for a timing claim, or `participation_route` for a participation-route claim. Every evidence-ledger row must also serialize `current_status` and exactly this structured temporal shape (use `null` for unavailable values):

```json
{"temporal":{"kind":"deadline|event_date|rolling_window|null","date":"YYYY-MM-DD|null","start_date":"YYYY-MM-DD|null","end_date":"YYYY-MM-DD|null"}}
```

Every selected `ACT_NOW` and `PREPARE_NEXT` item must remain live: its mapped status and participation-route evidence must have `current_status` `open`, `current`, or `active`, and every mapped timing row must have that status plus a nonexpired deadline/event date or a rolling window containing the snapshot date. A closed, stale, expired, or unmapped selected item is invalid.

Serialize `weekly_allocation.cap_minutes`, `scheduled_min_minutes`, `scheduled_max_minutes`, and `residual_upper_minutes`.

Use the direction's job policy exactly. A selected job's `type` must exactly equal one of `jobs.allowed_types`, and excluded types are never selectable. A non-job opportunity's `type` must be one of `grant`, `fellowship`, `cfp`, `community`, `research_collaboration`, `residency`, `accelerator`, `travel_support`, or `other`; use `other` only for a genuine non-job opportunity. Never relabel a job with an arbitrary or non-job type to bypass this policy.
