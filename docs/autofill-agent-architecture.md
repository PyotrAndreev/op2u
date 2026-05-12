# Agent-Based Form Autofill Architecture

## Goal

Provide an async service that applies to conferences/events on a user's behalf. Current scope is the autofill pipeline: generate, validate, store, reuse, monitor, and execute deterministic form automation bundles.

## Service Boundary

> Autofill owns form automation, bundle lifecycle, execution, approval/submission policy, and submission evidence. User-data service owns user data access, resolution, collection, provenance, and data-level permission flags.

Autofill never receives raw unstructured user data. It receives only a resolved application data package for the current bundle contract.

## Core Principles

- Requests create async application jobs.
- Event/form automation is reusable across users.
- User data resolution is delegated to user-data service.
- User data returned to autofill is least-privilege and contract-scoped.
- LLM/agent is used during bundle generation, not deterministic execution.
- Scripts are internal service artifacts and are not visible to users.
- Database is source of truth; queues/workers execute pipeline stages.

## High-Level Workflow

1. Autofill service receives application request with normalized event/form data.
2. Create or deduplicate application job.
3. Identify application form.
4. Find active automation bundle for the form.
5. If no valid bundle exists, generate and validate a new bundle.
6. After bundle is active, send its required data contract plus policy context to user-data service.
7. Poll user-data service while data request is pending/incomplete.
8. When user-data returns a complete resolved data package, autofill validates it against the bundle contract.
9. Run deterministic bundle in sandbox with resolved data/assets only.
10. Stop for approval/action if policy requires.
11. Submit when allowed.
12. Persist evidence, audit events, artifacts, and final status.
13. Notify user on major milestones.

## Request Contract

Upstream event extraction is out of scope. Autofill expects:

- normalized event record
- organizer key
- event key
- edition key
- application form type
- application URL
- extraction confidence/provenance
- deadline, if known
- user/application policy

## Identity Model

Event identity and form identity are separate.

- `event_edition`
  - organizer
  - event
  - edition/year/season
- `application_form`
  - event edition parent
  - type: `speaker`, `attendee`, `sponsor`, `volunteer`, `other`
  - URL
  - form fingerprint
  - active automation bundle version

Reuse is keyed by application form, not just event.

## Automation Bundle

A bundle is a versioned reusable automation package for one application form of one event edition.

Contains:

- deterministic Playwright script or runtime-specific automation artifact
- form identity and source URL
- form fingerprint
- required data contract
- field mapping
- conditional branch model
- submit-boundary metadata
- smoke-validation policy
- risk/confidence score and factors
- validation lifecycle state
- generation metadata
- last execution metadata

The required data contract is part of the immutable bundle version. If the contract changes, a new bundle version is generated.

Lifecycle:

- `generated`
- `preflight_passed`
- `smoke_validated`
- `active`
- `deprecated`
- `failed`

Only active/sufficiently validated bundles may trigger user-data requests.

## Required Data Contract

Autofill sends user-data service a rich machine-readable contract, not the script or raw bundle.

Contract fields include:

- stable contract field id
- canonical semantic type
- original form label
- help/surrounding context
- options/enums
- required/optional flag
- constraints: type, length, format, file type, size
- field classification
- branch condition
- consent/legal exact text if applicable
- expected usage/purpose

Autofill includes required fields plus optional fields that policy says may be filled.

## User-Data Service Integration

Autofill creates a data request after bundle activation.

Request includes:

- `user_id`
- `application_job_id`
- `application_form_id`
- `bundle_id`
- `bundle_version`
- required data contract
- policy context
- deadline/risk context

Autofill uses service-to-service auth plus user-scoped authorization context. Scope is contract-level with per-field audit/enforcement inside user-data service.

User-data service owns:

- structured profile access
- raw/unstructured data access
- LLM extraction from user data
- missing-data collection
- sensitive-field opt-in checks
- data-level consent/permission flags
- asset library access
- data provenance/confidence

User-data service does not receive generated scripts.

## User-Data Response Model

Use hybrid synchronous/asynchronous resolution.

Package statuses:

- `complete` — resolved package is ready
- `pending` — user-data is resolving automatically
- `incomplete` — user action or policy change is needed; user-data owns notification
- `error` — system/infrastructure failure

Autofill behavior:

- `complete` → validate package and execute
- `pending` → keep polling with backoff/reconciler
- `incomplete` → internal `waiting_for_user_data`, external `action_required`
- `error` → retry/backoff or fail depending on deadline

Responses include both package-level and field-level statuses.

Resolved field response should include:

- contract field id
- value or asset reference
- field status
- source/provenance
- confidence
- `allowed_to_use`
- `requires_user_confirmation`
- sensitive category, if any
- consent status
- constraints satisfied flag
- expiry, if relevant

## Polling/Reconciliation

First implementation uses autofill-owned periodic reconciliation.

Autofill periodically polls only jobs in user-data-dependent internal states:

- `waiting_for_user_data`
- `waiting_for_user_data_refresh`
- `user_data_pending`

Autofill does not poll jobs that are executing, generating bundles, waiting for submit approval, or terminal.

User-data status may change independently, e.g. `incomplete` → `pending` → `complete`, after the user updates data or policy. Autofill discovers this via polling.

Every data request/response includes:

- `application_job_id`
- `bundle_id`
- `bundle_version`
- data request id

If bundle/contract changes, autofill generates a new bundle and explicitly cancels/supersedes old data requests.

## Data Package Storage

Autofill stores the resolved data package per job execution for reproducibility, audit, approval preview, retry consistency, and debugging.

Autofill does **not** store:

- full user profile
- raw unstructured documents
- unrelated user data
- long-lived reusable user-data cache

Autofill may store:

- resolved values required for this application
- resolved asset references
- provenance/confidence metadata
- data-level permission flags
- package id/version
- validation result against bundle contract

User-data service may cache internally. Autofill does not cache resolved packages across applications.

## Assets

User-data service owns the asset library.

Autofill requests assets by contract:

- asset type
- accepted formats
- max size
- purpose
- required/optional
- consent requirement

User-data returns asset metadata plus scoped access:

- signed temporary URL/token by default
- stable asset id if appropriate
- short-lived access for sensitive assets
- no inline file bytes in job payloads

Runner uses only scoped asset access during execution.

## Field Resolution and Validation

User-data service resolves fields. Autofill validates the returned package against the bundle contract before browser execution.

Autofill validates:

- required fields present
- value types
- max lengths/enums/formats
- asset references accessible
- required consent status present
- permission/review flags compatible with policy
- contract/bundle version matches current job

If browser execution reveals new validation constraints, autofill sends validation feedback to user-data as an amended data request. If the form contract itself changes, autofill regenerates the bundle.

Deterministic transforms should live in a shared normalization library/contract used by both services.

## Policy Ownership

For v1, autofill owns the final combined execution/submission policy decision.

User-data returns data-level permissions and review flags. Autofill combines them with:

- bundle risk
- form confidence
- user submission mode
- deadline
- legal/attestation requirements
- field classifications
- approval state

Submission modes:

- fully automatic submit
- submit after user approval

System safety rules may override user preference.

## User Approval and Notifications

Ownership split:

- user-data owns prompts for missing/invalid user data, low-confidence extracted data, sensitive-field opt-ins, and data policy changes
- autofill owns prompts for submit approval, legal/attestation gates, browser auth/CAPTCHA, bundle failures, and submission outcome
- notification service should deduplicate and render user-facing messages using event ownership metadata

Approval preview is assembled by autofill from:

- event/form context
- screenshot/final form state
- key answers
- user-data provenance/confidence
- LLM-inferred warnings
- legal/attestation fields

V1 caveat: approval is best-effort, not technically guaranteed. Generated scripts are expected to honor submit-boundary metadata. Hard submit blocking is a future hardening item.

## Validation

Validation levels:

- bundle preflight checks
- smoke validation with synthetic test data
- resolved data package validation
- production execution evidence

Bundle generation and smoke validation use schemas, samples, and controlled synthetic test identities/assets from a separate test-data service/vault, not real user-data service.

Smoke validation:

- fill until safe submit boundary if clear
- if submit boundary is ambiguous, downgrade to field-detection-only validation
- no uncontrolled external test-account creation

## Execution

Generated scripts are deterministic and execute inside isolated sandbox/container/VM.

Execution receives only resolved fields/assets required for the form, not the full user snapshot.

Generated code should use a constrained runner SDK/helper API rather than arbitrary runtime capabilities.

Security controls:

- isolated runtime
- no arbitrary script/runtime egress
- browser traffic allowed and domain-logged
- scoped secret/asset access only
- resource/time limits
- static/agentic code review
- unsafe code regeneration attempts capped, then operator escalation

## Job States

External states stay simple:

- `queued`
- `in_progress`
- `action_required`
- `succeeded`
- `failed`
- `already_submitted`
- `cancelled` / `expired` as needed

Internal states include:

- identifying form
- checking bundle cache
- generating bundle
- validating bundle
- requesting user data
- waiting_for_user_data
- waiting_for_user_data_refresh
- user_data_ready
- validating data package
- executing automation
- waiting for approval
- submitting
- recording evidence

`pending` from user-data maps externally to `in_progress`. `incomplete` maps externally to `action_required`.

## Action Required

Used for:

- user-data incomplete
- missing assets
- user approval
- legal/attestation consent
- low-confidence inferred values
- auth/OTP/CAPTCHA
- operator intervention
- ambiguous/broken automation

On autofill-owned `action_required` in v1:

- close browser session
- capture full interruption package
- later restart/refill from checkpoint
- do not preserve partial browser form state

## Failure Handling

Internal failure classes:

- `site_unreachable`
- `selector_not_found`
- `navigation_changed`
- `unexpected_branch`
- `validation_error`
- `missing_required_data`
- `upload_missing`
- `captcha_or_antibot`
- `auth_required`
- `user_data_pending`
- `user_data_incomplete`
- `user_data_unavailable`
- `timeout`
- `submission_rejected`
- `unknown`

Recovery:

- classify failure
- rerun preflight/fingerprint check if automation failed
- retry transient failures
- regenerate on stale/broken selectors/forms
- request/refresh user-data on validation/data failures
- escalate CAPTCHA/auth/risky cases
- action-required for missing user data or approvals

## Submission Evidence

Do not treat “clicked submit” as success.

Persist structured evidence:

- final URL
- success text/snippet
- screenshot
- timestamp
- submission/reference ID if present
- bundle version
- resolved data package id/version
- fingerprint at execution time

If site says already applied, mark internal terminal state `already_submitted` with evidence.

## Idempotency and Duplicate Prevention

Application requests deduplicate by `(user, application_form)` while non-terminal job exists.

Before final submit:

- acquire submission lock
- verify no successful submission already exists
- verify current job owns the attempt
- record submission attempt/evidence

## Queueing and Deadlines

Queue priority should consider:

- deadline
- whether valid bundle exists
- expected pipeline latency
- user-data pending/incomplete state
- user approval requirement
- retry/regeneration state

If deadline passes while queued/waiting/action-required, mark job expired and notify user.

## Privacy, Retention, and Deletion

Retention/deletion is shared:

- autofill enforces TTLs for stored resolved packages, artifacts, and evidence
- autofill reacts to user-data erasure events: user deleted, asset deleted, consent revoked, data package invalidated

If user revokes consent or deletes data after submission, policy determines outcome. Default:

- delete/anonymize resolved data package
- delete sensitive artifacts/screenshots if required
- keep minimal anonymized audit if required: job id, form id, timestamp, terminal status, bundle version

Reusable bundles remain if they contain no user data.

## Audit Log

Audit should include:

- job state transitions
- bundle lifecycle events
- data request ids/statuses
- resolved data package id/version
- field-level provenance and autofill usage context
- user approvals/consents
- operator actions
- submission evidence

Raw browser traces are artifacts, not the primary audit log.

## V1 Known Risks / Future Hardening

- Runtime language not yet chosen.
- Approval gate is best-effort, not technically enforced.
- Smoke validation avoids ambiguous submit boundaries but still depends on correct boundary detection.
- Platform ToS automation checks are not modeled in v1.
- No cross-job learning in v1.
- No reusable user credentials/sessions in v1.
- Network browser traffic is logged, not strictly allowlisted.
- Hard submit/request blocking should be added later.
- Polling user-data requests may be less efficient than event-driven integration; events can be added later.
