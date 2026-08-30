# User profile, consent, and automation boundary

Opportunity discovery uses personal information. A profile may include biography, goals, projects, work or education history, location and travel windows, documents, preferences, and constraints.

## Profile handling

Only user-supplied facts may enter the profile. Unknown facts remain unknown. A profile should distinguish durable facts, current context, reusable assets, constraints, decisions, preferences, and unanswered questions so that a recommendation can identify its actual basis.

Personal profiles and complete production runs stay outside the Git repository. Repository fixtures and reports must be anonymized and must not contain private profile material.

## Consent boundary

Discovery and drafting are distinct from external action. Before a future system stores documents, contacts an organization, fills a form, submits an application, or shares profile information with a third party, it needs a separate explicit consent and review design.

The current discovery MVP performs none of those actions. It can recommend an atomic first action, but the user remains responsible for deciding and executing it.

## Open product decisions

Retention, deletion, encryption, third-party data sharing, approval modes for application drafting and submission, and notification handling need explicit specifications and, where durable, ADRs before implementation.
