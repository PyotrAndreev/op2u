# EUSP artifact action contract

This v1 contract defines a small local action portfolio for the Discovery MVP. It makes the P1 actionability checks durable: a selected action is an artifact the user can begin within seven days, not a request for the system to act externally.

The machine-readable contract is [`evals/schemas/eusp_action.schema.json`](../../evals/schemas/eusp_action.schema.json). Its only committed example is the fabricated fixture at [`evals/fixtures/eusp_action/v1/actions.json`](../../evals/fixtures/eusp_action/v1/actions.json). Validate it with:

```sh
python tools/eusp_action.py --public-fixture \
  evals/fixtures/eusp_action/v1/actions.json
```

## Action boundary

An `eusp-action/v1` record contains local actions only. Every action has all of the following:

- an `ACT_NOW` or `PREPARE_NEXT` classification;
- a bounded local deliverable, a start date no later than seven days after the saved snapshot, and a closed `1..60` minute range;
- at least one disclosed blocker; and
- direct official-primary evidence that explicitly supports that action.

`ACT_NOW` and `PREPARE_NEXT` retain their meanings in the [Discovery MVP](discovery-mvp.md): the former is a current route with a concrete first step, and the latter is a useful bounded preparation action for a supported route. The record does not make a liveness or eligibility decision, and it cannot promote `MONITOR` or `REJECT` into scheduled work.

The validator checks identifiers, references, timestamps, effort ordering, the seven-day window, evidence-to-action support, and the local-only action vocabulary. It cannot establish that an official quote remains true or that an artifact will resolve a blocker.

## Cold-outreach drafts

The only outreach-shaped action is `kind: "cold_outreach_draft"`. Its deliverable is a **local, unsent draft** for the user's review. It requires both an explicit `user_supplied` profile-field reference and direct official-primary evidence whose purpose is `verified_shared_context`. This is a narrow proof that a shared context was actually supplied and verified; silence, topical similarity, or a guessed acquaintance is not enough.

The contract intentionally has no recipient, destination, contact detail, contact-route, relationship, introduction, permission, credential, or dispatch field. The validator rejects those unrepresentable additions and rejects draft text that asserts a relationship, introduction, permission, or contact route. It also rejects action/deliverable text that describes sending, messaging, submitting, booking, uploading, registering, or contacting.

A draft does not authorize a later external act. It does not select a person or route, imply that anyone may be contacted, or promise a reply. The user independently decides whether any external act is appropriate and remains the sole controller of it.

## Execution boundary and fixture hygiene

This contract creates no connector and performs no sending, messaging, submission, booking, upload, registration, authentication, credential access, notification, or status tracking. It remains in the Discovery/drafting plane described by [ADR 0002](../adr/0002-explicit-approval-for-future-external-writes.md) and the [future execution approval boundary](future-execution-approval-boundary.md). Any future external write requires the separate reviewed, action-specific approval specified there; this record is never such approval.

Committed fixtures must set `synthetic: true` and use the exact fabricated-data notice checked by `--public-fixture`. They must contain only anonymous fictional organizations and `example.test` URLs. Do not commit profiles, contacts, contact routes, messages, personal data, credentials, or production action records.
