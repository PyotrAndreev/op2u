# Future execution approval boundary

**Status:** durable future-design specification; no implementation authorization.
**Issue:** Radicle issue b417ba7

## Purpose and scope

This specification defines the safety boundary for a *future* workflow that might send a message, create or change a booking, upload/store a document with a third party, save a third-party form, submit a form or application, grant/revoke third-party access, or make another external state-changing request (an **external write action**).

It does not add a connector, credential, authentication flow, notification channel, execution worker, booking, sending, submission, or automation. It does not change the Discovery MVP, EUSP experiments, prompts, schemas, or current pipeline behaviour. In particular, this document does not authorize the exploratory `Auto` control shown in the [future product concept](future-product-concept.md).

The boundary applies to every destination, including an organization, portal, calendar, email service, storage provider, and notification provider. A read, retrieval, or locally generated draft is not an external write action, but is still subject to its own source-access and privacy policy.

## Invariants

1. **Action-specific explicit approval is required.** No component may make an external write action unless the user has just explicitly approved that exact action. Generic consent, a profile, a preference, a prior approval, a scheduled rule, an “auto” mode, a draft review, or possession of a credential is never approval to write.
2. **Discovery and drafting cannot execute.** They may read their declared inputs and produce local, immutable recommendation or draft artifacts, but have no execution capability, credential access, dispatch endpoint, or authority to change an external system.
3. **Review precedes approval.** A user must be able to inspect the complete, rendered action and its consequences before approving it. Approval is a distinct, affirmative confirmation; viewing or editing a draft is not approval.
4. **Approval is exact, short-lived, and single-use.** It is bound to one immutable action bundle and one dispatch attempt. It expires after ten minutes and is invalidated by any change to its payload, recipient/destination, action type, selected credential/scope, execution configuration, or by cancellation. It cannot be replayed or delegated to another action.
5. **Fail closed.** Missing, expired, revoked, malformed, mismatched, or already consumed approval; missing/revoked credentials; unavailable evidence; or an uncertain dispatch state prevents a write. No component may silently substitute a recipient, credential, source, document, or action.
6. **No unattended recovery writes.** A retry, resume, scheduler, worker restart, timeout recovery, or notification failure may record state and ask the user for a new review and approval, but may not send, book, submit, upload, save, or otherwise write externally.
7. **Data stays local and segregated unless separately authorized.** Personal profiles, drafts, execution records, credentials, and production traces remain outside Git. Unknown profile facts remain unknown; no execution step may turn an inferred fact into eligibility or permission.

## Separation of responsibilities

A future architecture has two capability-separated planes:

| Plane | May do | Must not do |
| --- | --- | --- |
| Discovery and drafting | Interpret explicit profile facts; retrieve permitted opportunity evidence; create local recommendations, checklists, and drafts; expose uncertainty and blockers. | Authenticate to a destination; obtain/use a credential; send or upload material; save/fill/submit a third-party form; create/change a booking; contact anyone; schedule an external write. |
| Execution | Validate a reviewed immutable action bundle, a valid action-specific approval, and the necessary explicit consent and credential grant; perform at most the bound external write once; record its outcome. | Discover recipients or routes; alter a draft; infer missing data; select a different credential; broaden scope; reuse approval; retry automatically; use model/prompt memory as authority. |

The deterministic discovery pipeline remains in the first plane. Its run store and immutable artifacts are useful provenance, but neither an artifact nor an EUSP classification confers execution authority. A future orchestration system (including a Temporal worker) must keep execution as a separately versioned contract and capability; it must not turn pipeline retry/resume semantics into write retries.

## Consent, credentials, and drafts

### Consent

Before preparing an action that would disclose profile or document data to a third party, the user must receive and affirm a separate, informed, revocable consent record. It names the destination/provider, purpose, data categories and documents, recipient, retention/deletion policy, and any processor or transfer. Consent is limited to that purpose and destination; it is not authorization to dispatch any action.

Creating, renewing, or revoking a provider grant is itself an external state-changing operation. It requires its own reviewed, action-specific approval as well as the applicable consent. A generic “connect account” control is insufficient.

### Credentials

A future credential integration must use provider-hosted authorization where applicable and request the least available scope. A credential record must be locally protected, scoped to one provider/account/purpose, time-bounded where the provider supports it, revocable, and selectable by the user before action approval. Raw secrets, tokens, authorization codes, cookies, passwords, and credential-bearing URLs must never appear in Git, profile fields, prompts, model context, drafts, reports, analytics, notifications, or audit events.

Discovery and drafting receive no credential material. The execution plane receives only a protected credential handle after it has validated the approval binding; it must not expose the secret to a model or downstream artifact. Missing, expired, excess-scope, ambiguous, or revoked access fails closed and asks the user to review a new credential-grant action. It does not trigger a workaround, scraping, or credential substitution.

### Draft review

A draft is a local, non-executing artifact. Before approval, the review surface must show the complete rendered payload (including attachments and form fields), destination and recipient, action type, data to be disclosed, source/draft versions, credential identity and scope, any cost/commitment, and known blockers or uncertainty. The user can edit, reject, or discard it. Editing creates a new immutable draft/action bundle and invalidates any prior review or approval.

A draft may not claim a relationship, introduction, contact path, eligibility, or fact that its evidence does not support. Drafting must preserve unknowns rather than invent them. A reviewed draft remains a draft until the separate approval step completes.

## Action bundle, approval, and dispatch

Before showing approval, execution constructs an immutable **action bundle** with a canonical digest. At minimum it contains:

- action ID and action type; destination/provider and recipient or target resource;
- complete rendered payload, attachment/form-field digests, and the exact draft/evidence references used;
- the data categories to be disclosed, user-visible consequences/cost, and intended credential account/scope;
- contract/configuration versions, creation time, and an execution idempotency key; and
- a `not_before` time and a ten-minute approval expiry.

The approval record binds the user, action-bundle digest, intended credential handle/scope, one dispatch-attempt ID, confirmation time, and expiry. It is created only by an explicit affirmative user interaction after the review above; it is single-use and cannot be minted by a model, agent, scheduler, API retry, or imported state. It deliberately carries no secret or raw credential.

Immediately before dispatch, the execution boundary recomputes and verifies every binding, checks consent and credential state, atomically consumes the approval, and applies the provider's idempotency facility when available. Only then may it invoke the one bound external request. A destination that lacks idempotency support is not a license to retry: its outcome must be treated conservatively.

## Failure, retry, and cancellation

Execution records one of `draft`, `ready_for_review`, `ready_for_approval`, `approved`, `dispatching`, `succeeded`, `failed_no_dispatch`, `outcome_unknown`, or `cancelled`. State transitions and attempts are append-only while retained.

- A local validation, consent, credential, or approval failure is `failed_no_dispatch`; no request is sent.
- A transport failure before a request is started is `failed_no_dispatch`. The user may make a fresh action bundle/approval; the system does not retry it.
- A timeout, process crash, or lost response after dispatch begins is `outcome_unknown`, not `failed`. The system must preserve the request correlation/idempotency key, notify the user, and offer only a non-writing reconciliation view. It must not resend until the user has reviewed the known state and explicitly approved a new attempt.
- A provider-declared failure is retained with a minimized error category. It may lead to a repaired draft and a fresh approval, never an automatic retry.
- Cancellation before dispatch atomically invalidates approval and transitions to `cancelled`; the dispatcher must check that state immediately before its request. Cancellation during or after dispatch cannot promise remote undo: it prevents further writes, marks the result `outcome_unknown` or the provider-confirmed terminal state, and tells the user what is known.

## Notifications and audit

The future product must surface local, user-visible status for approval needed/expired, dispatch started, success, failure, unknown outcome, cancellation, credential expiry/revocation, and impending retention deletion. A notification is informational and cannot approve, renew, or retry an action. It must minimize personal content and never disclose credentials, complete drafts, sensitive profile facts, or a recipient unnecessarily.

An external notification delivery (for example, email, push provider, or SMS) is itself an external write action. It requires a separately reviewed, action-specific notification approval; a notification preference cannot authorize delivery. No such channel is introduced by this specification.

Maintain a local, access-controlled, append-only audit trail for each retained action: action and bundle digests, consent/approval/credential-handle references, actor, state transitions, attempt ID, timestamps, destination identifier, minimized outcome/error category, cancellation, notification events, and retention/deletion events. The audit trail must not contain credential secrets or more payload/profile content than needed to prove the binding. Audit access is limited to the user and authorized local support process, if one is separately designed.

## Retention and deletion

Before any future execution feature is enabled, the user chooses a documented retention period for drafts, action bundles, raw provider responses, and audit metadata, with a safe no-retention/default-minimum option. Retain only what is necessary for the stated purpose, reconciliation, and audit; do not use execution data to enrich a profile or train a model without a separately specified consent and policy.

The user can cancel pending work, revoke consent/credentials, and request deletion. Revocation immediately blocks future dispatch. Deletion securely removes retained payloads, credentials, drafts, and raw responses within the chosen policy window; it records a minimized deletion/tombstone event without retaining the deleted content. Where a legal, security, or provider obligation prevents immediate deletion, disclose the category, basis, and deadline before consent, isolate the data, and delete it when the obligation ends. Nothing from these records may be committed to this repository.

## Threat and failure handling

| Threat or failure | Required control | Safe result |
| --- | --- | --- |
| A model, stale job, or generic setting tries to dispatch | Only the execution boundary can dispatch and it requires a valid single-use approval bound to the bundle. | Reject before any provider call. |
| Draft/payload, recipient, attachment, scope, or configuration changes after review | Canonical digest binding; invalidate approval on every material change; recompute immediately before dispatch. | Return to review/approval; no write. |
| Approval replay, duplicate worker, or crash recovery | Atomic approval consumption, attempt IDs, durable state, and provider idempotency where available. | At most one authorized request; otherwise `outcome_unknown`, never automatic resend. |
| Credential leak, scope escalation, expiry, or revocation | Protected least-scope handles; secrets excluded from artifacts/logs/model context; status validation at dispatch. | Block dispatch and require a new explicit grant/approval. |
| Cancellation races with dispatch | Atomic cancellation/consumption checks and conservative post-dispatch state. | No future write; remote outcome reported as known or unknown. |
| Provider/network ambiguity or changed remote form | Minimized failure record; bind the reviewed payload/configuration; no interpretation of silence as success. | Notify user, reconcile without writing, require new review/approval to try again. |
| Unauthorized notification or retention overreach | Treat outbound notification as a write; local minimization, expiry/deletion jobs, and audit tombstones. | No unapproved delivery; retained data is deleted on schedule. |

## Testable acceptance rules for a future implementation

A future implementation satisfies this specification only if automated tests and an adversarial integration test demonstrate all of the following:

1. Calling any external-write adapter without a valid, unexpired, unconsumed approval produces no adapter/network invocation.
2. The approval screen exposes every action-bundle field listed above, and a positive confirmation creates a record bound to that exact canonical digest and one attempt ID.
3. Changing a byte of payload/attachment/form field, destination, recipient, action type, credential handle/scope, or execution configuration invalidates approval and prevents dispatch.
4. A reviewed draft, profile consent, generic automation setting, prior approval, scheduler event, restored workflow, or credential alone cannot dispatch an action.
5. Dispatch consumes approval atomically; a replay, concurrent worker, or resumed job cannot produce a second request. A retry path always returns to review and requires a fresh approval.
6. A timeout/crash after dispatch starts becomes `outcome_unknown`; recovery makes no write and presents reconciliation plus a new-approval path.
7. Cancellation before dispatch prevents the request; cancellation during/after dispatch prevents any later attempt and reports the remote outcome conservatively.
8. Discovery/drafting integration tests run with no execution capability or credential handle, while execution tests cannot alter drafts, discover a recipient, or choose a replacement credential.
9. Secret-scanning and fixture tests prove that tokens, passwords, authorization codes, cookies, and credential URLs are absent from repository files, logs, prompts, model inputs, reports, notifications, and audit records.
10. Audit tests prove ordered state/attempt records, approval and bundle bindings, minimized errors, access control, retention expiry, revocation blocking, and deletion/tombstone behaviour; tests also prove no deleted payload or secret remains recoverable from retained records.
11. Notification tests prove that status notifications contain only the permitted minimum and that no external notification adapter is called without its own action-specific approval.
12. Regression checks prove the current Discovery MVP and EUSP pipeline still perform no authentication, external write, execution retry, status tracking, booking, sending, submission, or notification delivery.

Any failed rule is a release blocker for the relevant future execution feature. It does not justify weakening the Discovery MVP boundary.

## Related records

- [Discovery MVP specification](discovery-mvp.md)
- [User profile, consent, and automation boundary](user-profile-and-consent.md)
- [Future product concept](future-product-concept.md)
- [ADR 0001: Deterministic Python agent pipeline](../adr/0001-deterministic-python-agent-pipeline.md)
- [ADR 0002: Explicit approval for future external writes](../adr/0002-explicit-approval-for-future-external-writes.md)
- [EUSP P1 experiment charter](../dev/eusp-p1-experiment-charter.md)
