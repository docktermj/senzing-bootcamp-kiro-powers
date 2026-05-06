# Design: Budget Threshold Consistency

## Overview

The `steering-index.yaml` budget section has both percentage fields (`warn_threshold_pct`, `critical_threshold_pct`) and the agent instructions reference absolute token values (120k, 160k). This creates a maintenance hazard — if `reference_window` changes, the absolute values become stale. The fix makes percentages authoritative and derives absolutes.

## Current State

```yaml
budget:
  total_tokens: 102625
  reference_window: 200000
  warn_threshold_pct: 60
  critical_threshold_pct: 80
  split_threshold_tokens: 5000
```

Agent instructions reference "120k" and "160k" directly.

## Design Decisions

### 1. Percentage fields are authoritative

The `warn_threshold_pct` and `critical_threshold_pct` fields define thresholds. Absolute values are computed as `reference_window × (pct / 100)`. No separate absolute fields are stored — they're redundant and create drift risk.

### 2. Script changes

`measure_steering.py --check` currently may use hardcoded values. It will be updated to:

1. Read `reference_window`, `warn_threshold_pct`, `critical_threshold_pct` from the budget section
2. Compute `warn_tokens = reference_window * warn_threshold_pct / 100`
3. Compute `critical_tokens = reference_window * critical_threshold_pct / 100`
4. Compare `total_tokens` against computed thresholds

### 3. Agent instruction updates

Replace absolute references like "warn at 120k, critical at 160k" with "warn at 60% of context budget, critical at 80%". This makes the instructions resilient to reference_window changes.

### 4. Documentation update

Update `docs/guides/STEERING_INDEX.md` Budget section to explain the derivation: "Absolute thresholds are computed as reference_window × percentage. For example, with reference_window: 200000 and warn_threshold_pct: 60, the warn threshold is 120,000 tokens."

## Files Modified

- `senzing-bootcamp/scripts/measure_steering.py` — use percentage-based computation
- `senzing-bootcamp/steering/agent-instructions.md` — replace absolute token references with percentage language
- `senzing-bootcamp/docs/guides/STEERING_INDEX.md` — document the derivation relationship

## Testing

- Existing `measure_steering.py --check` tests continue to pass (behavior unchanged, just derivation method changes)
- Unit test verifying threshold computation: `200000 * 60 / 100 == 120000`
