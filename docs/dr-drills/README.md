# DR drill evidence

Put completed restore drill records here as `YYYY-MM-DD-drill.md`.

CI (`scripts/ops/check_dr_docs.py`) requires:

- at least one drill markdown (not this README)
- fields: `drill_date`, `rpo_minutes`, `rto_minutes`, `result`
- newest `drill_date` within `DR_DRILL_MAX_AGE_DAYS` (default 120)

Use `DR_DRILL_ALLOW_STALE=1` only for forks / local when evidence is intentionally stale.
