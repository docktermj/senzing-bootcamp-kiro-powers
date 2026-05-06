# Design: Adaptive Pacing Based on Session Analytics

## Overview

The agent reads session analytics at module start and adjusts teaching pace based on the bootcamper's historical performance. Modules where the bootcamper struggled get deeper explanations; modules where they were comfortable get streamlined delivery.

## Pacing Classification Algorithm

```python
def classify_module(module_metrics, all_metrics):
    """Classify a completed module's difficulty for the bootcamper."""
    if not all_metrics:
        return "normal"
    
    median_time = median([m.total_seconds for m in all_metrics])
    
    # "struggled" if high correction density OR took much longer than average
    if module_metrics.correction_density > 0.3:
        return "struggled"
    if module_metrics.total_seconds > 2 * median_time:
        return "struggled"
    
    # "comfortable" if low corrections AND fast completion
    if module_metrics.correction_density < 0.1 and module_metrics.total_seconds < median_time:
        return "comfortable"
    
    return "normal"
```

### Metrics Used

- **correction_density**: corrections / turns (from `analyze_sessions.py`)
- **total_seconds**: cumulative time in module (from session log timestamps)
- **median_time**: median total_seconds across all completed modules

### Pacing Effects

| Classification | Explanation Depth | "Why" Framing | Proactive Offers |
|---|---|---|---|
| struggled | Full context before each step | Always included | Offer alternative explanations |
| normal | Standard (per verbosity setting) | When relevant | Standard offers |
| comfortable | Minimal lead-in | Skip unless asked | Reduce optional offers |

## Integration with Existing Systems

### Verbosity Control

Adaptive pacing adjusts the *baseline* but does not override explicit verbosity preferences:

- If bootcamper set verbosity to "detailed", pacing never reduces below "detailed"
- If bootcamper set verbosity to "concise", pacing can still add "why" framing for struggled prerequisites (it's additive context, not verbosity)

### Session Resume

`session-resume.md` Step 1 already reads state files. Adding session log reading here is natural — compute pacing classifications once at session start.

### Preferences Storage

```yaml
# config/bootcamp_preferences.yaml (additions)
pacing_overrides:
  3: "struggled"    # Bootcamper said "slow down" during Module 3
  6: "comfortable"  # Computed from analytics
```

Manual overrides ("slow down" / "speed up") take precedence over computed classifications.

## New Code Location

The classification function is added to `analyze_sessions.py` as `classify_pacing(entries) -> dict[int, str]`. This keeps analytics logic centralized and avoids a new script.

## Steering Changes

### agent-instructions.md additions (Module Steering section)

```markdown
### Adaptive Pacing

At module start, read `config/session_log.jsonl` and classify completed modules:
- **struggled** (density > 0.3 or time > 2× median): increase depth for this module
- **comfortable** (density < 0.1 and time < median): streamline delivery
- **normal**: use standard pacing per verbosity setting

Check `config/bootcamp_preferences.yaml` for `pacing_overrides` — manual overrides take precedence.

Pacing adjustments:
- struggled prerequisite → fuller "why" framing, proactive "would you like me to explain differently?"
- comfortable prerequisite → shorter lead-ins, skip optional context unless asked
```

### session-resume.md additions (Step 1)

Add: "Read `config/session_log.jsonl` if it exists. Compute pacing classifications for completed modules. Store in working memory for module-start decisions."

## Files Modified

- `senzing-bootcamp/scripts/analyze_sessions.py` — add `classify_pacing()` function
- `senzing-bootcamp/steering/agent-instructions.md` — add Adaptive Pacing subsection
- `senzing-bootcamp/steering/session-resume.md` — add session log reading to Step 1

## Testing

- Property test: classification is deterministic for same inputs
- Property test: manual overrides always take precedence over computed values
- Property test: empty session log → all modules classified as "normal"
- Unit test: known metrics produce expected classifications
- Unit test: "slow down" / "speed up" phrases update pacing_overrides correctly
