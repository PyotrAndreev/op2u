# EUSP social-graph connector admissibility spike

**Status:** completed spike; **decision:** reject a LinkedIn/social-graph connector from the Discovery MVP.
**Checked:** 2026-08-30 UTC. This is a feasibility and policy assessment, not legal advice or an implementation authorization.

The Discovery MVP accepts explicit user-profile facts and produces verified opportunity recommendations; it does not authenticate to third parties or take external actions ([MVP](../product/discovery-mvp.md)). Its profile boundary also keeps profiles/runs out of Git and requires a separate design before third-party sharing ([profile and consent](../product/user-profile-and-consent.md)). P1's grounding and liveness gates do not relax either boundary ([P1 charter](../dev/eusp-p1-experiment-charter.md)).

## Decision

**Do not acquire, infer, store, rank on, or display a LinkedIn connection/alumni graph in the MVP.** A public-profile URL supplied by a user is a pointer, not permission to collect profile or network data. It is not retained in this repository or treated as a profile fact.

The official program identified that expressly includes a `CONNECTIONS` portability domain is geographically limited and requires app-product access and member authorization. It can be reconsidered only as a separately specified, reviewed future integration—not as an MVP fallback or a promise of availability. Standard LinkedIn sign-in/OAuth supplies only lite identity/profile information unless a product/partner program grants additional scopes; it is not a general social-graph API.

## Comparison

| Route | Availability and provenance | Consent and restrictions | MVP result |
| --- | --- | --- | --- |
| **Public web / supplied profile URL** | Public visibility is neither a stable API nor provenance for a profile fact. A header-only, no-login check of the supplied candidate returned HTTP 999; no body was retrieved and no access was retried. That result is an access-control outcome, not evidence about the person. | LinkedIn's User Agreement forbids software/scripts/robots that scrape or copy profiles and prohibits bypassing access controls. Its crawling terms require express permission; even permitted crawling is limited to authorized paths/use. A user's URL cannot consent for LinkedIn or connected people. | **Rejected.** No browsing automation, scraping, enrichment, or graph inference. |
| **Member-requested export** | LinkedIn lets a member request a larger archive containing connections, delivered to their primary email. The export is a dated user-held snapshot, not current relationship truth. It covers only first-degree connections; emails appear only when connections allow them. | The file contains other people's data and can be incomplete/encoding-limited. It conflicts with the current profile boundary unless a future design defines a purpose limitation, minimization, local-only handling, deletion, revocation, and an appropriate basis for third-party data. | **Not an MVP input.** Do not upload, parse, retain, or derive a graph from it. |
| **Standard OAuth / API** | OAuth is an official, attributable route, but app scopes depend on products/partner programs. OIDC `openid profile email` returns only lite profile fields (and email may be absent), not a connection graph. API limits are endpoint/app/member specific and unpublished in docs. | The authorization-code flow is explicit member consent, but needs a registered app, HTTPS redirect URI, approved/provisioned scope, secure token handling, and least scope. LinkedIn API terms also prohibit accessing a member network without express permission and require deletion on user request/closure. | **Rejected for graph MVP.** OIDC could only be reconsidered for future optional identity linkage under a separate product/consent decision; it adds no graph basis. |
| **DMA Member Data Portability API** | Official docs list `CONNECTIONS` (name, position, company, connection date of first-degree connections) in Snapshot domains. It requires the Member Data Portability product and token; the Member help page says only members located in EU/EEA/Switzerland can use it. | Requires product access, a portability scope, member authorization, and handling of a broad personal-data export. Location eligibility, app/program changes, pagination/processing, API limits, deletion duties, and third-party connection data make it unsuitable as a default. | **Future-only conditional candidate; not MVP.** Validate the then-current terms, product access, exact scope/data domains, retention/deletion and privacy/legal review before any prototype. |
| **MCP server or “skill”** | MCP is a tool/authorization transport, not a LinkedIn data entitlement or provenance source. No provider-specific authorization can be inferred from a skill name or a user-provided URL. | MCP's authorization specification requires OAuth security, audience binding, secure storage, least privilege, and prohibits token passthrough. It cannot make scraping or unapproved API access permissible. | **Rejected as an acquisition workaround.** Consider only after a particular official/authorized upstream integration independently passes the future review. |

## Privacy and provenance rules

If this topic is reopened, keep the following non-negotiable gates before any data call or import:

1. **Separate, informed, revocable opt-in** that names the source, exact fields, purpose, recipient/processor, retention, deletion path, and the fact that connection data concerns other people. A profile URL or generic sign-in is insufficient.
2. **No credentials in op2u or prompts.** Perform provider-hosted authorization only; keep tokens out of Git, logs, prompts, reports, URLs, and MCP passthrough. Request the minimum approved scope.
3. **Field and purpose minimization.** Do not collect contact details, messages, private notes, inferred attributes, sensitive/identity domains, or a reusable relationship graph merely to rank opportunities. Do not turn a relationship into eligibility, endorsement, or permission to contact someone.
4. **Local, segregated, deletable data only.** Record source, retrieval time, declared scope, and consent state locally; support user deletion/revocation and provider-required deletion. Never commit exports, tokens, profile URLs, raw graph records, or production runs.
5. **Fail closed.** Missing access, a declined/expired grant, ineligible region, unknown scope, policy change, or uncertain provenance produces no social signal—not a retry, workaround, or inferred substitute.

## Graceful no-social-graph fallback

Run ordinary evidence-first discovery on only the user's explicit, non-graph profile facts and requested direction. Offer an optional, local prompt for **self-authored opportunity context** (for example: target field, places/organizations/programs already known, languages, travel window, reusable work, and constraints); allow “skip” and preserve unknowns. Do not ask for contacts, LinkedIn URLs, exports, messages, or alumni relationships.

The report remains useful without a graph: search and verify official opportunity sources, explain the explicit profile bridge, state uncertainties, and return an empty/underfilled verified portfolio plus clearly labelled research gaps when evidence is insufficient. This is the existing MVP/P1-safe fallback: no outreach, referral assertion, eligibility inference, social-distance score, or action based on personal-network data.

## Evidence and link check

Primary sources were retrieved on 2026-08-30 UTC. Links below were checked with an HTTPS request (`HEAD` where the host permits, otherwise `GET` without retaining content); the supplied personal URL was deliberately not recorded or linked.

- LinkedIn, [User Agreement §8.2](https://www.linkedin.com/legal/user-agreement): prohibits scraping/copying via software, robots, crawlers, browser plugins, etc., bypassing access controls, and unauthorized automated access.
- LinkedIn, [Crawling Terms](https://www.linkedin.com/legal/crawling-terms): automated crawling without express permission is strictly prohibited and permitted collection is constrained.
- LinkedIn, [API Terms of Use](https://www.linkedin.com/legal/l/api-terms-of-use): distinguishes self-serve/vetted/partner access; requires consent/privacy/security/deletion controls; prohibits accessing a member's network without express permission and non-API collection.
- LinkedIn Help, [Export connections](https://www.linkedin.com/help/linkedin/answer/a566336/export-connections-from-linkedin): archive route and first-degree/email limitations.
- LinkedIn Help, [Member portability APIs](https://www.linkedin.com/help/linkedin/answer/a6214075): member consent and EU/EEA/Switzerland availability restriction.
- LinkedIn Developer docs, [Sign In with LinkedIn using OIDC](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2) and [3-legged OAuth](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow): available OIDC fields, consent, provisioned scopes, token/redirect requirements.
- LinkedIn Developer docs, [Member Data Portability (Member)](https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/member-data-portability-member), [Snapshot API](https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/shared/member-snapshot-api), and [Snapshot domains](https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/shared/snapshot-domain): product/access flow, permission model, and documented `CONNECTIONS` domain.
- LinkedIn Developer docs, [API rate limits](https://learn.microsoft.com/en-us/linkedin/shared/api-guide/concepts/rate-limits): daily endpoint limits, 429 behavior, and Developer Portal visibility.
- Model Context Protocol, [Authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization): OAuth 2.1, least privilege, token audience validation, secure storage, and no token passthrough.
