# Requirements: Mapping Regression Testing

## Overview

Provide a lightweight mechanism to compare entity resolution results before and after mapping changes, helping bootcampers understand the impact of their iterations in Module 5.

## Requirements

1. Create a `scripts/compare_results.py` script that compares two sets of entity resolution statistics (entity count, record count, match count, possible match count, relationship count)
2. The script must accept `--baseline <file>` and `--current <file>` arguments pointing to JSON files containing ER statistics
3. Output a human-readable diff showing: entities gained/lost, matches gained/lost, possible matches gained/lost, net quality change assessment
4. Add a step to Module 5 Phase 3 (test-load) steering that captures baseline statistics after the first successful test load
5. Add a step that captures current statistics after any subsequent test load and runs the comparison automatically
6. Statistics capture must use the Senzing SDK (via `generate_scaffold` or `find_examples`) to query entity/record/match counts
7. Store baseline statistics in `config/er_baseline_[datasource].json`
8. The comparison must work incrementally — each new test load becomes the new baseline if the bootcamper accepts the results
9. Add the script to POWER.md "Useful Commands" section
10. Write tests for the comparison script covering: identical baselines, improved results, degraded results, missing baseline file
