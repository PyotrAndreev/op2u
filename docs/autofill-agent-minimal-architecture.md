# Minimal Autofill Agent Architecture

## Goal

Define the smallest useful architecture for applying to events using reusable form automation.

The system is split into four services:

1. **Events-service** — event collection, identification, application URL metadata, and event type ownership.
2. **User-data-service** — user data storage, processing, contract fulfillment, preview, and scoped execution access.
3. **Application-process-service** — application job management, orchestration, policy evaluation, tracking, and notifications.
4. **Autofill-service** — automation bundle generation and Playwright execution.

V1 supports only regular events. Events that require CAPTCHA or authentication are classified and stopped until separate pipelines are designed.

## Core Principles

- Application-process-service orchestrates the workflow.
- Autofill-service owns automation bundles and execution queues.
- Events-service owns event type classification.
- User-data-service owns user data and returns data package references, not reusable raw profile access.
- Application-process-service stores references and decisions, not long-lived copies of resolved user data.
- Automation bundle versions are immutable.
- Production autofill execution is always fill-and-submit; user review happens before execution is queued.

## Event Types

Events-service owns event type:

- `regular`
- `with_captcha`
- `with_auth`
- `unknown`

V1 proceeds only for:

- `regular`
- `unknown`

If Autofill-service discovers CAPTCHA or auth during bundle generation, it reports the discovered type to Application-process-service. Application-process-service forwards the update to Events-service, marks the application job as `unsupported`, and notifies the user.

## Application Identity

Application identity is:

```text
user_id + event_id + application_type
```

`application_type` is a minimal enum:

- `speaker`
- `attendee`
- `sponsor`
- `volunteer`
- `other`

Application-process-service deduplicates active jobs by:

```text
user_id + event_id + application_type
```

## Automation Bundle

An automation bundle automates one application form for one event and application type.

Bundle identity:

```text
event_id + application_type + version
```

For v1, model each bundle version as one entity.

### Minimal Fields

```text
AutomationBundle:
- bundle_id
- event_id
- application_type
- version
- status
- playwright_script_ref
- user_data_contract
- metadata
- created_at
- updated_at
```

### Status

```text
AutomationBundle.status:
- generating
- ready
- unsupported
- failed
```

Absence of a bundle means no bundle exists.

Application-process-service behavior:

```text
not found    -> request async bundle generation
generating   -> wait/poll
ready        -> request user data
unsupported  -> mark application job unsupported
failed       -> fail job or escalate
```

### Bundle Immutability

Each bundle version is immutable. Its `user_data_contract` is also immutable.

If the form changes, Autofill-service creates a new bundle version with a new contract.

## User Data Contract

A user data contract describes the data required to fill the form.

```text
UserDataContract:
- contract_id or contract_hash
- fields[]
```

Each field contains:

```text
ContractField:
- field_id
- label
- semantic_type
- required
- value_type
- validation
- risk_level
- help_text, optional
- purpose, optional
```

Supported value types:

```text
string | number | boolean | enum | date | asset
```

Validation may include:

```text
- max_length
- format
- enum_options
- accepted_file_types
- max_file_size
```

Example:

```json
{
  "field_id": "speaker_bio",
  "label": "Speaker bio",
  "semantic_type": "professional_bio",
  "required": true,
  "value_type": "string",
  "validation": { "max_length": 500 },
  "risk_level": "normal"
}
```

## Application Job

Application job is owned by Application-process-service.

It is the user-facing application state machine and orchestration record.

### Minimal Fields

```text
ApplicationJob:
- application_job_id
- user_id
- event_id
- application_type
- status
- blocking_reason
- user_policy
- bundle_id
- bundle_version
- data_request_id
- data_package_id
- autofill_execution_id
- approval_status
- approved_at
- approved_by
- approved_data_package_id
- approved_contract_hash
- terminal_reason
- submitted_at
- evidence_ref
- created_at
- updated_at
```

### Status

```text
ApplicationJob.status:
- created
- preparing
- waiting
- executing
- succeeded
- failed
- unsupported
- cancelled
- expired
```

### Blocking Reason

`blocking_reason` is nullable.

```text
ApplicationJob.blocking_reason:
- bundle_generation
- user_data_resolution
- user_data
- approval
- autofill_execution
- unsupported_event_type
- operator
- none
```

Examples:

```text
status = preparing
blocking_reason = bundle_generation
```

```text
status = waiting
blocking_reason = approval
```

```text
status = unsupported
blocking_reason = unsupported_event_type
```

## User Application Policy

User policy is selected in Application-process-service.

```text
UserApplicationPolicy:
- review_all
- review_risky
- auto
```

Behavior:

### `review_all`

Application-process-service always requires user approval after user data is ready and before autofill execution is queued.

### `review_risky`

Application-process-service requires user approval only if the data package contains risky fields.

Risk indicators may include:

- LLM-extracted data
- low confidence
- sensitive data
- `requires_confirmation`
- required consent
- other high-risk metadata from User-data-service

### `auto`

Application-process-service queues autofill execution automatically if all required data is available, valid, and allowed to use.

System safety rules may still override `auto`.

## User Data Request

User-data-service owns data resolution and package creation.

Application-process-service creates an async data request using:

```text
- user_id
- application_job_id
- event_id
- application_type
- bundle_id
- bundle_version
- user_data_contract
```

### Status

```text
UserDataRequest.status:
- ready
- pending
- incomplete
- failed
```

Meaning:

```text
ready:
  data_package_id is available and contract is fulfilled

pending:
  user-data-service is still resolving/extracting data automatically

incomplete:
  user action is needed to update/provide data

failed:
  system error or contract cannot be processed
```

User-data-service response includes:

```text
- data_request_id
- status
- data_package_id, if ready
- missing_fields, if incomplete
- field_metadata, if ready
```

Application-process-service behavior:

```text
ready      -> evaluate application policy
pending    -> status=preparing, blocking_reason=user_data_resolution
incomplete -> status=waiting, blocking_reason=user_data, notify user
failed     -> status=failed
```

User-data-service does not notify the user directly. It returns structured missing-data/action information to Application-process-service. Application-process-service owns user notifications.

## Data Package References

Application-process-service should not persist raw resolved user data.

Preferred flow:

1. User-data-service creates a data package.
2. User-data-service returns `data_package_id` and metadata to Application-process-service.
3. Application-process-service evaluates policy using package metadata and preview APIs.
4. Application-process-service sends only a package reference and scoped access grant to Autofill-service.
5. Autofill-service fetches execution data directly from User-data-service.

## Review Preview

For `review_all` and `review_risky`, Application-process-service asks User-data-service for a review preview.

```text
GET /user-data/packages/{data_package_id}/preview
```

Preview contains display-safe data:

```text
DataPackagePreview:
- data_package_id
- contract_hash
- fields:
  - contract_field_id
  - label
  - display_value
  - source
  - confidence
  - risk_flags
  - sensitive_category
  - requires_confirmation
```

Application-process-service stores only the approval decision/reference:

```text
- approval_status
- approved_at
- approved_by
- approved_data_package_id
- approved_contract_hash
```

## Autofill Execution

Autofill-service owns execution queue and execution state.

Production execution is always fill-and-submit. If user review is required, it happens before execution is queued.

Application-process-service creates execution with:

```text
CreateExecutionRequest:
- application_job_id
- bundle_id
- bundle_version
- data_package_id
- data_access_grant
```

The `data_access_grant` should be:

- scoped to the application job
- scoped to the bundle id and version
- contract-scoped
- read-only
- short-lived

Autofill-service fetches execution data directly from User-data-service using the scoped grant.

### Execution Status

```text
AutofillExecution.status:
- queued
- running
- succeeded
- failed
```

Failure reasons:

```text
- site_unreachable
- form_changed
- validation_error
- submission_rejected
- timeout
- unknown
```

Application-process-service behavior:

```text
queued/running -> status=executing
succeeded      -> status=succeeded
failed         -> status=failed or retry/escalate
```

CAPTCHA/auth should be discovered and filtered before execution, during bundle generation.

## Execution Evidence

Autofill-service owns detailed browser evidence and artifacts.

Minimal execution result:

```text
AutofillExecutionResult:
- execution_id
- status
- failure_reason, nullable
- submitted_at, nullable
- final_url, nullable
- confirmation_text, nullable
- confirmation_id, nullable
- screenshot_ref, nullable
```

Application-process-service stores only summary references:

```text
- autofill_execution_id
- terminal_status
- terminal_reason
- submitted_at
- evidence_ref or screenshot_ref
```

## Minimal Workflow

### 1. Create Application Job

Input:

```text
- user_id
- event_id
- application_type
- user_policy
```

Application-process-service creates or returns an active deduplicated application job for:

```text
user_id + event_id + application_type
```

### 2. Load Event Metadata

Application-process-service fetches from Events-service:

```text
- event_id
- event_type
- application_url
- event metadata
```

If `event_type` is `with_captcha` or `with_auth`:

```text
ApplicationJob.status = unsupported
ApplicationJob.blocking_reason = unsupported_event_type
```

Then notify user and stop.

If `event_type` is `regular` or `unknown`, continue.

### 3. Get or Create Automation Bundle

Application-process-service asks Autofill-service for a ready bundle by:

```text
event_id + application_type
```

If no ready bundle exists, Application-process-service requests async bundle generation:

```text
CreateBundleRequest:
- event_id
- application_type
- application_url
- event_type
- optional metadata
```

Application-process-service polls bundle status.

Outcomes:

```text
ready:
  continue to user data request

generating:
  status=preparing, blocking_reason=bundle_generation

unsupported:
  forward discovered event type to Events-service
  status=unsupported, blocking_reason=unsupported_event_type

failed:
  status=failed
```

### 4. Request User Data

Application-process-service creates an async data request with User-data-service using the bundle's immutable `user_data_contract`.

Application-process-service polls data request status.

Outcomes:

```text
ready:
  store data_package_id reference and evaluate policy

pending:
  status=preparing, blocking_reason=user_data_resolution

incomplete:
  status=waiting, blocking_reason=user_data
  notify user using missing-data info from User-data-service

failed:
  status=failed
```

### 5. Evaluate Application Policy

Application-process-service evaluates the user's selected policy against package metadata.

If review is required:

1. Fetch review preview from User-data-service.
2. Notify user.
3. Set:

```text
ApplicationJob.status = waiting
ApplicationJob.blocking_reason = approval
```

After approval, store approval reference and continue.

If no review is required, continue automatically.

### 6. Queue Autofill Execution

Application-process-service creates an execution in Autofill-service:

```text
- application_job_id
- bundle_id
- bundle_version
- data_package_id
- scoped data access grant
```

Set:

```text
ApplicationJob.status = executing
ApplicationJob.blocking_reason = autofill_execution
```

### 7. Poll Execution and Notify

Application-process-service polls Autofill-service execution status.

Outcomes:

```text
queued/running:
  keep status=executing

succeeded:
  status=succeeded
  store evidence summary
  notify user

failed:
  status=failed
  store terminal reason/evidence summary
  notify user or escalate
```

## Service Ownership Summary

| Area | Owner |
| --- | --- |
| Event identity | Events-service |
| Event type | Events-service |
| Application URL metadata | Events-service |
| Application job | Application-process-service |
| User policy | Application-process-service |
| Notifications | Application-process-service |
| Bundle generation | Autofill-service |
| Bundle storage | Autofill-service |
| Playwright execution queue | Autofill-service |
| Execution artifacts/evidence | Autofill-service |
| User data storage | User-data-service |
| Data contract fulfillment | User-data-service |
| Missing data details | User-data-service |
| Review preview data | User-data-service |
| Scoped execution data access | User-data-service |

## V1 Non-Goals

- CAPTCHA application pipeline.
- Authenticated application pipeline.
- Browser-session resume after interruption.
- Post-fill browser preview before submit.
- Application-process-service storing long-lived resolved user data.
- Cross-job learning from executions.
- Multiple application forms without explicit `application_type`.
