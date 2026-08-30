Updated `tools/compare_variants.py` only.

- Runs both forward and reversed blinded presentations for every repeat/role.
- Stores per-orientation private mappings.
- Maps votes to stable `left`/`right` identities in aggregate outputs.
- Reports `order_stable`, `ORDER_SENSITIVE`, or incomplete outcomes per repeat-role.
- Counts stable pairwise wins only when mapped outcomes agree.
- Preserves blinded prompts and dry-run behavior.

Verified with:

```bash
python -m py_compile tools/compare_variants.py
```
