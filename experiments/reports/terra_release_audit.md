## CONDITIONAL

**Passed**
- Required structure, registry, frontier, runs, schemas, and exact `E01.md`–`E12.md` exist under `experiments/`.
- All 1,386 JSON and 192 JSONL files parse.
- Python compile and `--help` pass: `tools/run_experiment.py`, `tools/compare_variants.py`, `tools/build_report.py`.
- All 21 non-dry run input snapshots match their recorded hashes; registry IDs match run directories.
- Frontier prompt hash matches current production prompt: `experiments/frontier.json` ↔ `prompts/find_opportunities_recommended.md`.
- Saved-artifact judges and comparisons are supported by `tools/run_experiment.py judge` and `tools/compare_variants.py`.
- Did not read `evals/holdout.yaml`.

**Material blockers / contradictions**
1. **Production ledger enforcement is not implemented.**  
   `prompts/find_opportunities_recommended.md` and `experiments/reports/recommended_pipeline.md` require runner validation of ledger IDs, quote equality, artifact hashes, official-source support, counts, and effort. `tools/run_experiment.py` only requests JSON and persists it; it performs no JSON Schema or evidence-ledger validation. Existing schemas also do not define the production prompt’s required ledger format: `evals/schemas/report.schema.json`. This makes the claimed fail-closed production safety contract unavailable.

2. **The promoted production prompt was not the tested G2_M1 prompt.**  
   Frontier records `prompts/find_opportunities_recommended.md` hash `186da…`, but all three cited controlled runs snapshot `prompts/variants/G2_M1.md` hash `960eed…`:  
   - `runs/2026-08-02T155136+0000-96133818abdf/inputs/hashes.json`  
   - `runs/2026-08-02T155302+0000-2bc8b8a5c893/inputs/hashes.json`  
   - `runs/2026-08-02T155420+0000-91d4a29ccb62/inputs/hashes.json`  
   No saved run contains the production-prompt hash. The frontier therefore overstates direct evidence for the exact deployable prompt.

3. **Final accounting is unsupported and internally inconsistent.**  
   `experiments/reports/final_comparison.md` claims provider-reported cost **$2.388421**, while all persisted cost records have unknown cost and `experiments/reports/run_inventory.md` reports total cost as unknown. The same final report says controlled weekly upper budgets ranged “105–165”; `experiments/frontier.json` and `experiments/reports/generation_2_results.md` record **150, 150, 165**.

4. **Immutable hash is not recorded in the final comparison.**  
   `experiments/reports/final_comparison.md` contains no hash, despite `experiments/frontier.json` recording the production-prompt SHA-256. Add the exact prompt and relevant input/artifact hashes to the final comparison.

**Rerun limitation**
- Exact saved-artifact judging/comparison is supported. `tools/run_experiment.py` can resume missing stages or reuse a saved prefix, but cannot rerun a completed research run from its saved snapshot as a new immutable replay; fresh research uses repository-current inputs and live retrieval.
