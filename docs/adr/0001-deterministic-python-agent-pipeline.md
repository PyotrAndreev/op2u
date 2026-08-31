# ADR 0001: Deterministic Python agent pipeline

Status: Accepted
Issue: Radicle issue ae9a427

## Context

The Discovery MVP requires a small, current, evidence-backed action portfolio, with uncertainty preserved and no external submissions or other autonomous actions ([Discovery MVP specification](../product/discovery-mvp.md)). The evaluation design requires immutable inputs, persisted stage artifacts, and judges that read saved artifacts only ([evaluation experiment design](../../experiments/reports/experiment_design.md)).

The existing experiment runner already demonstrates the value of explicit stages and immutable attempt artifacts. However, E05 is explicitly only an architecture observation, not a controlled claim that staging improves outcomes ([E05](../../experiments/reports/E05.md)). A durable implementation decision is needed before replacing or extending the experimental runner.

## Decision

Use a deterministic Python pipeline as the durable orchestration boundary. "Deterministic" describes the stage graph, contracts, artifact selection, validation, and retry decisions; it does **not** claim that model responses, web search, or live pages are byte-for-byte deterministic.

### Fixed stages

A run executes this fixed ordered graph:

1. `profile` — interpret only supplied profile facts, constraints, and explicit unknowns;
2. `triggers` — derive clearly labelled search hypotheses from that profile state;
3. `search_plan` — produce bounded queries and intended primary-source targets;
4. `discovery` — collect candidate opportunities and discovery rationale;
5. `verification` — retrieve and record source evidence, liveness, dates, eligibility statements, and uncertainty;
6. `actionability` — produce profile bridges, blockers, bounded effort, and user-controlled first actions;
7. `ranking` — apply hard gates, classifications, diversity decisions, and allocation; and
8. `report` — render only supported selected claims and explicit unknowns.

Stages consume only their versioned input envelope and immutable upstream artifact references. `discovery` and `verification` are the only stages that may perform discovery or retrieval. The report is a projection of persisted artifacts, not hidden agent context. The stage sequence and its input/output JSON contracts are versioned together; adding, removing, or changing a stage requires a new contract version and, when consequential, a new ADR.

### State and LangChain boundary

The Python runner and its run store own workflow state: run identity, graph position, input and configuration hashes, completed artifacts, attempt history, and the decision to resume, retry, or stop. The source of truth is an immutable run manifest plus immutable artifact and append-only event records, stored locally now and addressable by content hash. No model, prompt, or agent owns workflow progress.

LangChain is the Python stage-local integration layer for model and tool invocation, structured-output parsing, and schema validation. It may assemble a single stage call from the declared input envelope and return that stage's JSON result. **LangChain is not durable workflow state:** it must not be the authority for checkpoints, resume state, retries, provenance, prior-stage context, or the final report. Its in-memory messages, chains, memory, and caches are disposable. A restarted runner reconstructs work only from the run store's versioned JSON artifacts.

### Versioned JSON, provenance, and immutable snapshots

Every stage has a versioned JSON input and output envelope: `schema_version: "op2u.stage-input/v1"` and `schema_version: "op2u.stage-output/v1"`, respectively. An input records at least the contract version, run ID, stage name, pipeline/configuration version, input snapshot references and SHA-256 hashes, model/tool configuration, and a work idempotency key. An output records its contract version, producing stage and attempt, input hash, artifact hash, timestamps, status, and the result or recorded failure. Schema validation occurs at the stage boundary; unsupported or malformed output fails closed rather than becoming implicit context for a later stage.

All artifacts are write-once. A run snapshots the profile, direction/policy, prompt and schema versions, source-access configuration, seed where applicable, repository revision, and snapshot date/timezone. It also preserves raw model/tool request and response data, parsed JSON, stdout/stderr, timing, and usage metadata where available.

Discovery and verification additionally create immutable search snapshots. Each snapshot records the query or fetch request, tool/provider and options, retrieval time, result/source URLs, returned result or retrieved source content (or the retained exact excerpt where full retention is not permitted), and content hashes. Evidence-ledger rows must point to the exact verification artifact and hash that supplied their quote, URL, and retrieval time. A later live lookup is a new snapshot, never an edit to an earlier run. This preserves provenance and permits saved-artifact evaluation without new research; it does not promise that a live URL can be replayed unchanged.

### Idempotency and retries

The idempotency boundary is one stage invocation. The runner derives a work idempotency key from the canonical versioned stage input, including immutable upstream references and execution-relevant configuration, but excluding invocation-only attempt numbering. For that key, a completed and valid output is reused; it is never overwritten or silently recomputed.

A failed, timed-out, malformed, or validation-failed invocation may be retried only as a new immutable `attempt-N` artifact with its own raw traces and status. Retrying a stage never changes a completed upstream artifact. If a retry produces a different output or a fresh search snapshot, all affected descendants use that new immutable reference in a derived execution branch; existing descendants remain historical. This makes retry effects inspectable even though model and web results can vary. There are no external write actions in this pipeline, so retries do not submit, contact, authenticate to, or otherwise act on third-party systems.

### Future Temporal compatibility

Temporal is not introduced by this decision. To lift the pipeline later without changing its durable contracts:

1. package each fixed Python stage as a function accepting a versioned input-artifact reference and returning a versioned output-artifact reference;
2. expose each function as one Temporal activity, passing the work idempotency key and immutable input references;
3. implement a thin deterministic Temporal workflow that orders those activities and carries only run and artifact references, never model messages, search results, or mutable LangChain state; and
4. configure Temporal activity retries to call the same idempotent stage boundary, while the Python run store remains the provenance and deduplication authority.

Activities may use LangChain internally under the same stage-local rule. This mapping permits Temporal heartbeats, queues, and worker recovery later while preserving the current JSON contracts, artifact hashes, retry semantics, and audit trail.

## Consequences

The pipeline gains an inspectable state owner, reproducible saved-artifact evaluation, source-to-report provenance, and independently resumable stages. It also makes the existing exact-quote, liveness, allocation, and uncertainty gates enforceable outside prompt text ([recommended pipeline](../../experiments/reports/recommended_pipeline.md)).

This choice requires schema maintenance, content-addressed artifact storage, retention controls for potentially sensitive source and profile snapshots, and explicit contract migration when contracts change. Personal profiles and complete production runs remain outside Git as required by the consent boundary ([user profile, consent, and automation boundary](../product/user-profile-and-consent.md)).

Out of scope are a Temporal migration, distributed scheduling, changing product requirements or evaluation claims, and autonomous external actions such as portal authentication, messaging, form completion, or application submission. The [future execution approval boundary](../product/future-execution-approval-boundary.md) now defines the product-policy prerequisites for any such future work; it does not authorize an implementation or make the pipeline an execution system.

## Evidence

The evaluation plan requires immutable input hashes, independent persisted artifacts, source quotes, retrieval times, raw partial failures, and saved-artifact-only judging ([evaluation experiment design](../../experiments/reports/experiment_design.md)). The retained comparison concludes that runner-enforced exact-quote provenance and staged artifacts are necessary, while limiting its quality claims to the evaluated profile ([final comparison](../../experiments/reports/final_comparison.md)).

The current [`tools/run_experiment.py`](../../tools/run_experiment.py) already uses fixed staged variants, write-once artifacts, versioned retry attempts, and deterministic validation. This ADR standardizes those boundaries for the future implementation; it does not claim that the experimental runner is already a Temporal or LangChain implementation.
