# User profile, consent, and automation boundary

Opportunity discovery uses personal information. A profile may include biography, goals, projects, work or education history, location and travel windows, documents, preferences, and constraints.

## Profile handling

Only user-supplied facts may enter the profile. Unknown facts remain unknown. A profile should distinguish durable facts, current context, reusable assets, constraints, decisions, preferences, and unanswered questions so that a recommendation can identify its actual basis. The [local EUSP user-profile model](eusp-local-user-profile.md) defines the v1 Markdown ingress, including per-field provenance and explicit geography periods.

Personal profiles and complete production runs stay outside the Git repository. `usr/profile.md` is ignored local storage; repository fixtures and reports must be anonymized and must not contain private profile material.

## Consent boundary

Discovery and drafting are distinct from external action. The [future execution approval boundary](future-execution-approval-boundary.md) defines the required future consent, review, action-specific approval, credential, retry, notification, audit, cancellation, and retention rules. It is a design boundary, not authorization to implement an integration or to change the current MVP.

The current discovery MVP performs none of those actions. It can recommend an atomic first action, but the user remains responsible for deciding and executing it.

## Open product decisions

Provider-specific retention/deletion obligations, encryption/key-management implementation, third-party data-sharing arrangements, supported execution action types, and notification delivery channels require separate implementation designs and, where durable, ADRs. They must conform to the future execution approval boundary and are not authorized by it.
