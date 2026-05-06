# Requirements: Budget Threshold Consistency

## Overview

The `steering-index.yaml` budget section uses `reference_window: 200000` tokens but the warn/critical thresholds are absolute numbers (120000/160000) rather than percentages of the reference window. The `warn_threshold_pct` and `critical_threshold_pct` fields exist but their relationship to the absolute values is unclear. This feature makes the budget configuration internally consistent.

## Requirements

1. The `steering-index.yaml` budget section is updated so that `warn_threshold_pct` and `critical_threshold_pct` are the authoritative threshold definitions, and absolute token values are derived from them (reference_window × percentage)
2. The current values are preserved: warn at 60% of 200k = 120k tokens, critical at 80% of 200k = 160k tokens
3. The `measure_steering.py --check` script uses the percentage fields and reference_window to compute thresholds, rather than hardcoded absolute values
4. If both percentage and absolute fields exist, the script validates they are consistent and warns if they diverge
5. The budget section documentation in `docs/guides/STEERING_INDEX.md` is updated to clarify the relationship between reference_window, percentage thresholds, and computed absolute values
6. Agent instructions referencing budget thresholds use the percentage form ("60% of context budget") rather than absolute token counts, making them resilient to reference_window changes

## Non-Requirements

- This does not change the actual threshold values (60% warn, 80% critical remain)
- This does not change the reference_window size
- This does not affect how token counts are measured per-file
