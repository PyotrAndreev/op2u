# ADR 0002: Explicit approval for future external writes

Status: Accepted
Issue: Radicle issue b417ba7

## Context

The Discovery MVP deliberately stops at evidence-backed, user-controlled next actions. ADR 0001 also excludes portal authentication, messaging, form completion, and submission from the deterministic discovery pipeline. The future product sketch mentions application and autonomy concepts, but a generic mode, credential, draft, or resumed workflow must not become authority to act for a user.

A durable boundary is needed before any future send, book, upload, save, submit, credential-grant, or other third-party state-changing workflow can be designed or implemented.

## Decision

Every external write action requires an action-specific, explicit user approval after review of an immutable action bundle. Approval is bound to the exact payload, destination/recipient, action type, credential scope, configuration, and one dispatch attempt; it is short-lived, single-use, and invalidated by a material change or cancellation. No generic consent, profile, draft review, credential, automation mode, scheduler, retry, or restored workflow can authorize a write.

Discovery and drafting remain capability-separated from execution. They cannot access credentials or dispatch external actions. A future execution boundary must fail closed, consume approval atomically, never retry an external write unattended, preserve ambiguous post-dispatch outcomes as unknown, and retain only minimized local audit data under the user's retention/deletion controls.

The normative requirements, state handling, threat controls, and testable acceptance rules are in the [future execution approval boundary](../product/future-execution-approval-boundary.md).

## Consequences

Any future integration needs separate provider-specific implementation and security design, user consent, credential handling, and tests against the normative specification. A Temporal migration or pipeline retry mechanism cannot be reused as an execution authorization or retry mechanism.

This decision does not implement or authorize authentication, credentials, connectors, notifications, sending, booking, saving, uploading, form completion, submission, status tracking, or automation. It does not change current Discovery MVP or EUSP behaviour.

## Evidence

The [Discovery MVP specification](../product/discovery-mvp.md) and [user profile, consent, and automation boundary](../product/user-profile-and-consent.md) prohibit the relevant current actions and require separate consent/review design. ADR 0001 establishes deterministic artifact and retry semantics for discovery only; the [EUSP P1 charter](../dev/eusp-p1-experiment-charter.md) explicitly excludes future execution capability from its evaluation scope.
