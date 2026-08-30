Read the requested files; `evals/holdout.yaml` was not read. No files were modified.

## Minimal architecture

Implement one Python entry point:

```text
tools/run_experiment.py
```

with small internal modules or classes:

```text
Config
RunStore
PiProcess
StageRunner
JudgeRunner
CostTracker
Manifest
```

### 1. Immutable run layout

Each experiment receives a UUID-like run ID:

```text
runs/<run-id>/
  manifest.json
  inputs/
    profile.md
    policy.md
    direction.yaml
    known_cases.yaml
    prompt.md
    hashes.json
  stages/
    01_profile/
      prompt.txt
      input.json
      stdout.txt
      stderr.txt
      result.json
      status.json
    02_triggers/
    03_discovery/
    04_verification/
    05_actionability/
    06_ranking/
    07_report/
  judges/
    <judge-run-id>/
      prompt.txt
      input.json
      stdout.txt
      stderr.txt
      result.json
      status.json
  costs.jsonl
  events.jsonl
```

Every subprocess invocation writes artifacts before the runner proceeds. Failed and partial invocations remain preserved.

`manifest.json` should include:

- run ID and timestamps
- git/repository revision if available
- immutable input hashes
- pipeline variant and generation
- worker/judge model names
- random seed
- parent run IDs
- stage graph and status
- timeout configuration

Never overwrite a run. Resumption creates missing artifacts only, or produces a new derived run.

## Research pipeline

Use explicit JSON stage contracts rather than passing free-form text between stages.

```text
profile + policy
    ↓
profile interpretation
    ↓
trigger/context hypotheses
    ↓
candidate discovery
    ↓
primary-source verification
    ↓
actionability and bridge analysis
    ↓
diversity-aware ranking
    ↓
final report
```

Each stage invocation should receive:

```json
{
  "run_id": "...",
  "stage": "verification",
  "variant": "V0",
  "profile": "...",
  "prior_artifacts": ["..."],
  "output_schema": "...",
  "constraints": {...}
}
```

The subprocess adapter should invoke `pi` with:

- selected model
- noninteractive mode
- prompt from a saved file
- captured stdout and stderr
- timeout
- optional environment/configuration
- machine-readable output where supported

Do not rely solely on the final response. Save the exact prompt, exact input artifact references, raw stdout, raw stderr, parsed JSON, exit code, duration, and usage metadata.

Research stages should be independently rerunnable, but the minimal experiment can initially run the full chain in one subprocess per stage.

## Artifact contracts

At minimum:

- `profile`: interpreted constraints, priorities, exclusions, uncertainty
- `triggers`: current context and search hypotheses
- `discovery`: candidates with URLs and discovery rationale
- `verification`: source URL, access date, open/closed status, deadline, eligibility, quoted evidence, uncertainty
- `actionability`: bridge from profile to opportunity, first seven-day action, effort estimate
- `ranking`: score components, penalties, diversity decisions, ACT_NOW/PREPARE_NEXT classification
- `report`: final user-facing output with citations and explicit unknowns

The final report must be derived from saved stage artifacts, not hidden subprocess state.

## Judge reruns without research

Create a separate command path:

```bash
python tools/run_experiment.py judge \
  --run runs/<run-id> \
  --judge-model openai-codex/gpt-5.6-luna
```

Judging reads only persisted artifacts. It must not invoke research stages.

Judge records should contain:

- exact evaluation prompt
- artifact snapshot or hashes
- rubric version
- judge model
- raw and parsed response
- cost and timing
- judge seed/configuration

Support judging:

1. whole reports;
2. individual stages;
3. paired A/B comparisons;
4. repeated judge calls.

This enables rerunning judges with different models, rubrics, or repeats at negligible research cost.

## Blind A/B comparisons

Before sending candidates to a judge:

1. Load two saved reports or artifact bundles.
2. Randomly assign them labels `A` and `B`.
3. Remove variant names, run IDs, model names, generation numbers, and path names from the judge prompt.
4. Randomize presentation order using a recorded seed.
5. Ask the judge for structured output:

```json
{
  "winner": "A|B|tie",
  "scores": {
    "actionability": 0,
    "evidence": 0,
    "profile_fit": 0,
    "freshness": 0,
    "ranking_quality": 0
  },
  "reasons": [],
  "failure_tags": []
}
```

Store the mapping from blinded labels to actual variants outside the judge prompt, in the runner’s metadata. Aggregate repeated comparisons using win rate, tie rate, and confidence intervals or at least repeat counts.

Do not expose `known_cases.yaml` to the optimizer as if it were a holdout. It may be used for visible smoke/evaluation checks; the unavailable holdout remains excluded.

## Cost and time tracking

`CostTracker` should append one record per subprocess to `costs.jsonl`:

```json
{
  "run_id": "...",
  "stage": "discovery",
  "role": "worker",
  "model": "...",
  "started_at": "...",
  "duration_seconds": 123,
  "input_tokens": null,
  "output_tokens": null,
  "total_tokens": null,
  "estimated_cost": null,
  "usage_source": "provider_metadata|estimated|unknown",
  "exit_code": 0
}
```

Prefer usage reported by `pi`. If unavailable, preserve `null` and optionally estimate tokens from captured text; never present estimates as exact costs.

Use a global three-hour deadline:

- reserve a small finalization margin;
- reject new work after the deadline;
- terminate timed-out subprocesses;
- preserve partial artifacts;
- report completed, failed, and skipped jobs.

A minimal scheduler can run sequentially. Parallelism is useful only for independent repeats and A/B judges, and risks rate limits and budget overruns.

Suggested first-pass schedule:

- one baseline run;
- one or two variants;
- three repeats only for the most promising comparison;
- judges after research artifacts are complete;
- stop when the deadline or two non-improving generations is reached.

## Failure modes and mitigations

| Failure | Mitigation |
|---|---|
| Pi hangs or exceeds the wall clock | Per-process timeout plus global deadline; preserve stderr/status |
| Malformed model JSON | Save raw output; retry once with a repair prompt; mark invalid if still failing |
| Lost provenance | Require URLs, source quotes, access dates, and source IDs in stage schemas |
| Stale opportunities | Verification stage must explicitly determine current status and deadline |
| Stages silently invent prior results | Pass only declared artifact files and include their hashes |
| Research repeated during judging | Separate `research` and `judge` commands; judges reject missing persisted inputs |
| A/B judge detects variant identity | Sanitize labels, paths, model names, and metadata before prompt construction |
| Ordering bias | Randomized A/B order and recorded seed |
| Prompt/model confounding | Keep model, rubric, and input snapshot explicit in manifests |
| Duplicate opportunities dominate top three | Ranking stage enforces organization/type diversity |
| Jobs leak into recommendations | Carry `exclude_jobs_by_default` as a hard constraint into every relevant stage |
| Partial run appears complete | Per-stage status plus final manifest validation |
| Cost data is missing | Capture raw provider metadata and retain unknown/null values |
| Retry changes results invisibly | Each retry gets its own attempt artifact and seed |
| Optimizer overfits known cases | Treat known cases as visible diagnostics only; do not mutate prompts using hidden data |
| Excessive report length | Enforce report schema and explicit length budget |
| Research quality varies across models | Record worker model per stage and compare with blinded judges |

## Build order for a three-hour experiment

1. **Run store and manifest**
   - Create immutable run directories.
   - Hash all permitted inputs.
   - Implement atomic artifact writes.

2. **Pi subprocess adapter**
   - Configurable model and timeout.
   - Capture prompt, stdout, stderr, exit code, duration, and usage.
   - Add a fake/mock adapter for smoke tests.

3. **Single baseline pipeline**
   - Implement the seven stages with JSON validation.
   - Run V0 end-to-end.
   - Do not implement evolutionary mutation yet.

4. **Resume and judge-only mode**
   - Validate existing artifacts.
   - Rerun only missing stages.
   - Add judge command operating exclusively on saved runs.

5. **Blind A/B evaluator**
   - Sanitization, randomized order, repeat aggregation, persisted mappings.

6. **Budget controller**
   - Global deadline, subprocess timeouts, retry limits, cost/event logs.

7. **Experiment orchestration**
   - Represent V0–V7 as configuration:
     - prompt variant
     - stage graph
     - worker model
     - judge model
     - generation/repeat metadata
   - Run a small cumulative ladder rather than building a general optimizer.

8. **Validation**
   - Mock smoke test with no research.
   - Baseline run.
   - Known-case diagnostic, especially PyCon ZA-style bridge, freshness, and deadline verification.
   - One blinded A/B comparison.
   - Final cost/failure report.

The key scope decision is to build an auditable sequential runner and saved-artifact judge first. Evolutionary search, parallel scheduling, and sophisticated statistical analysis should remain configuration-level additions until the baseline and comparison loop work reliably.
