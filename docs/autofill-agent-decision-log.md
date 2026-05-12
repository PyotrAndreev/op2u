# Autofill Agent Decision Log

Concise decision record for the agent-based form autofill pipeline.

## Scope

- Build async autofill pipeline for applying to events/conferences.
- URL-only event extraction is out of scope.
- Pipeline receives normalized event/form data from upstream.
- Direct interaction with user profile/raw user data is delegated to user-data service.

## User-Data Service Split

1. **Service boundary**: autofill owns automation, bundle lifecycle, execution, final execution/submission policy, and submission evidence; user-data owns data access, resolution, collection, provenance, and data-level permission flags.
2. **Raw user data**: autofill never receives raw unstructured user data.
3. **When to request data**: autofill requests data only after an active/sufficiently validated bundle exists.
4. **Request shape**: autofill sends required data contract plus policy/deadline/risk context.
5. **User-data knowledge of bundle**: user-data receives bundle/job/form ids and versions for traceability, not generated scripts.
6. **Data contract location**: data contract is embedded in immutable bundle version; if contract changes, generate a new bundle.
7. **Data contract richness**: contract must include semantic field type, original label, help text/context, options, constraints, required/optional flag, classification, branch condition, consent/legal text, and purpose.
8. **Optional fields**: autofill requests required fields plus optional fields that policy says may be filled.
9. **LLM extraction from user data**: owned by user-data service.
10. **Missing data interaction**: split ownership. User-data collects data/policy updates; autofill handles submit approval, legal gates, auth/CAPTCHA, bundle failures, and submission status.
11. **User-data statuses**: `complete`, `pending`, `incomplete`, `error`.
12. **External status mapping**: user-data `pending` maps to external `in_progress`; `incomplete` maps to external `action_required`.
13. **Polling model**: v1 autofill periodically polls only jobs in user-data-dependent internal states.
14. **Mutable data request status**: user-data may move requests from `incomplete` to `pending` to `complete`; autofill discovers via polling.
15. **Version matching**: data responses include job id, bundle id, bundle version, and data request id; autofill ignores stale responses.
16. **Superseded requests**: if bundle/contract changes, autofill cancels/supersedes old data requests.
17. **Response granularity**: user-data returns both package-level and field-level statuses.
18. **Resolved package storage**: autofill snapshots resolved package per job execution, not the full profile/raw documents.
19. **No autofill data cache**: user-data may cache internally; autofill does not cache resolved packages across applications.
20. **Provenance ownership**: user-data returns source/confidence; autofill adds form-usage context.
21. **Policy flags**: user-data returns machine-readable flags: allowed-to-use, requires confirmation, sensitive category, consent status, confidence, source, expiry, constraints-satisfied.
22. **Final combined policy**: v1 autofill owns final execution/submission policy by combining bundle risk with user-data flags.
23. **Policy refusal**: autofill respects user-data refusals; optional fields are skipped, required refusals become action-required or terminal failure.
24. **Additional context requests**: user-data does not request more context; autofill must send complete contract initially.
25. **Validation feedback**: autofill may send validation error context back to user-data via amended data request.
26. **Deterministic transforms**: shared normalization library/contract used by both services.
27. **Assets**: user-data owns asset library and grants scoped temporary access; no inline file bytes.
28. **AuthZ**: service-to-service auth plus user-scoped authorization context.
29. **Scopes**: contract-level request with per-field scope/audit inside user-data.
30. **Deletion/retention**: shared. Autofill enforces TTLs and reacts to user-data erasure/package invalidation events.
31. **Post-submission deletion**: policy-dependent, default is anonymize/delete user-specific data while keeping minimal audit.
32. **Notification ownership**: notification service should deduplicate user-data and autofill events; if absent, user-data owns data prompts and autofill owns application status prompts.
33. **User-data unavailable**: retry/backoff in autofill; not user action.
34. **Smoke validation data**: use separate test-data service/vault, not real user-data service.
35. **Approval preview**: autofill assembles preview from form context plus user-data provenance/confidence.

## Existing Architecture Decisions

36. **Event identity**: use organizer + event + edition + form fingerprint, not raw URL only.
37. **Form identity**: event edition is parent; each application form is a child identity.
38. **Application types**: use explicit enum: speaker, attendee, sponsor, volunteer, other.
39. **Reuse unit**: reuse one versioned automation bundle per application form/event edition.
40. **Script reuse**: v1 uses one event/form-specific script, not platform-level templates.
41. **Bundle contents**: bundle includes script, fingerprint, mapping, data contract, submit boundary, validation/risk metadata, generation metadata, and execution metadata.
42. **Bundle lifecycle**: generated → preflight_passed → smoke_validated → active → deprecated/failed.
43. **Bundle promotion**: orchestrator promotes automatically; operator can override.
44. **Runtime language**: undecided; decide before final bundle execution format.
45. **Execution model**: LLM at generation time only; execution is deterministic.
46. **Generation inputs**: v1 generation uses current live page/form only.
47. **No cross-job learning**: v1 does not learn from other executions.
48. **Generated code API**: generated scripts should use constrained runner/helper API.
49. **Generated code dependencies**: no arbitrary imports or external libraries by default.
50. **Sandboxing**: generated code runs in isolated container/VM.
51. **Network policy**: block script/runtime egress; allow browser traffic and log domains.
52. **Code review**: unsafe generated scripts are regenerated with feedback, capped attempts, then operator escalation.
53. **Job model**: every application request creates an async application job.
54. **Job state source of truth**: database, not queue or in-memory worker.
55. **External job states**: keep simple; internal states are detailed.
56. **Deduplication**: dedupe non-terminal jobs by user + application form.
57. **Retries**: support stage-level retries internally and whole-job retry/resume externally.
58. **Checkpoints**: major stages plus interruption/resume points.
59. **Action required**: first-class state for missing data, approval, auth, CAPTCHA, ambiguity, or operator needs.
60. **Action-required fallback actor**: user or operator depending on reason.
61. **On action_required**: close browser and resume later from checkpoint.
62. **Partial form state**: do not preserve in v1; restart/refill.
63. **Interruption package**: capture reason, URL, screenshot, field context, missing data, bundle version, provenance, and resume recommendation.
64. **Field mapping**: agent produces explicit mapping artifact, not only script code.
65. **Execution inputs**: script receives only resolved fields/assets required by the form.
66. **Meaning-changing transforms**: action_required with suggested edit; no silent rewrite/truncation.
67. **Field policy taxonomy**: use rich classification: identity, contact, professional, creative, legal, sensitive, asset.
68. **Sensitive/demographic fields**: fill only with explicit user opt-in per category.
69. **Optional-field policy**: central policy engine combining user prefs, field class, and risk.
70. **Reusable answer preferences**: later, not v1.
71. **Legal/attestation fields**: require explicit user consent unless deterministic policy says already covered.
72. **Consent representation**: special consent-required fields with exact text/provenance.
73. **Consent coverage**: deterministic policy engine decides, not generation agent.
74. **Submission policy**: users choose fully automatic or submit-after-approval.
75. **Safety override**: system policy can require approval despite user preference.
76. **Approval timing**: depends on risk tier; default is after fill, before final submit.
77. **Approval preview**: show screenshot, key answers, LLM-inferred warnings, legal/consent fields.
78. **Approval enforcement**: v1 approval is best-effort, not hard technically enforced.
79. **Approval violations**: log approval state at submission time and flag violations.
80. **Submit boundary**: bundle stores explicit submit-boundary metadata.
81. **Submit blocking**: not in v1; future hardening item.
82. **Smoke validation**: run only when safe stopping point is clear; otherwise field-detection-only.
83. **Smoke data**: use synthetic test identities/assets, not real user data.
84. **External test accounts**: only with operator-approved platform policy.
85. **Preflight checks**: freshness/fingerprint, artifact integrity, bundle readiness.
86. **Staleness trigger**: regenerate when execution fails materially or fingerprint changes.
87. **Failure recovery**: classify failure, rerun preflight/fingerprint, then retry/regenerate/escalate.
88. **Failure taxonomy**: rich internal codes, simplified external messages.
89. **User-facing failures**: deterministic templates mapped from internal reason codes.
90. **Regeneration trigger**: auto for safe known failures; operator for risky cases.
91. **Success detection**: use success signals and persisted evidence, not final click alone.
92. **Submission evidence**: final URL, text, screenshot, timestamp, reference ID, bundle version, fingerprint, resolved package version.
93. **Already submitted**: separate terminal internal state with evidence.
94. **Duplicate prevention**: submission lock + final pre-submit check + evidence.
95. **Conditional branches**: represent explicitly in data contract/mapping.
96. **Branch evaluation**: bundle contract predicts branch; script verifies actual UI path.
97. **Queue priority**: deadline + expected latency + action-required risk + bundle/data state.
98. **Deadline source**: upstream provides deadline.
99. **Deadline passed**: mark expired/failed and notify user.
100. **Cancellation**: best-effort until submission; impossible after confirmed submit.
101. **Notifications**: major milestones, action required, terminal outcomes.
102. **Metrics**: track full funnel, including generation, validation, reuse, user-data waits, failures, action_required, approval, regeneration.
103. **Privacy policy**: design retention/redaction controls now, even if lightly implemented.
104. **Audit log**: job events, bundle events, data request/package ids, field provenance/use context, approvals, operator actions, submission evidence.
105. **Artifacts**: raw traces/screenshots are artifacts, not primary audit log.
106. **Platform ToS**: v1 records user authorization; platform-specific ToS checks not modeled.
107. **Anti-bot/CAPTCHA**: first-class handling with reason code and escalation.
108. **Save/resume links**: use only for real jobs, job-scoped; not reusable bundle validation.
109. **Human/operator actions**: modeled as first-class workflow events.

## Explicit V1 Risks

- Runtime language not chosen yet.
- Approval before submit is best-effort, not technically guaranteed.
- Smoke validation depends on safe submit-boundary detection.
- No platform-specific ToS automation policy in v1.
- No cross-job learning in v1.
- No reusable credentials/sessions in v1.
- Browser traffic is logged but not strictly allowlisted.
- Hard submit/request blocking deferred.
- User-data integration starts with polling; event-driven callbacks can be added later.
