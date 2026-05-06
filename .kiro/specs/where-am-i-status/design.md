# Design: "Where Am I?" Quick Status Command

## Overview

Keyword-triggered inline status lets the bootcamper ask "where am I?" and get a compact progress summary without leaving the conversation. The agent reads progress state and responds with a formatted block.

## Trigger Detection

The `review-bootcamper-input` hook already detects trigger phrases (e.g., "bootcamp feedback"). Status triggers are added to the same mechanism:

**Trigger phrases**: "where am I", "status", "what step am I on", "show progress", "how far along am I"

Detection is case-insensitive and matches partial phrases within longer messages.

## Response Format

```console
📍 **Module 6: Loading Data** — Step 3 of 8

Track: Fast Track (B) — 60% complete
Data sources: 3 registered (CUSTOMERS, ORDERS, PRODUCTS)
Next milestone: Complete loading → unlock Module 7 (Multi-Source Queries)

👉 Ready to continue with Step 3 (configure load parameters)?
```

### Format Rules

- Maximum 8 lines
- Starts with 📍 emoji and current position
- Includes track name and completion percentage
- Shows data sources if registry exists
- Ends with a single 👉 question to resume flow

## Track Completion Calculation

```python
def track_completion_pct(progress, track_modules):
    """Calculate track completion with partial credit."""
    total_steps = 0
    completed_steps = 0
    
    for module_num in track_modules:
        module_total = get_module_step_count(module_num)
        total_steps += module_total
        
        if module_num in progress["modules_completed"]:
            completed_steps += module_total
        elif module_num == progress["current_module"]:
            completed_steps += progress.get("current_step", 0)
    
    return round(completed_steps / total_steps * 100) if total_steps > 0 else 0
```

Track module lists (from module-dependencies.yaml):

- Quick Demo (A): [1, 2, 3]
- Fast Track (B): [5, 6, 7]
- Complete Beginner (C): [1, 4, 5, 6, 7]
- Full Production (D): [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

## Steering File: inline-status.md

```markdown
---
inclusion: manual
---

# Inline Status Response

When the bootcamper asks for status (trigger phrases: "where am I", "status", 
"what step am I on", "show progress", "how far along am I"):

1. Read `config/bootcamp_progress.json`
2. Read `config/data_sources.yaml` (if exists)
3. Read `config/bootcamp_preferences.yaml` for track selection
4. Compute track completion percentage
5. Format response using the template below

## Response Template

📍 **Module [N]: [Title]** — Step [S] of [Total]

Track: [Track Name] ([Letter]) — [X]% complete
Data sources: [count] registered ([names])
Next milestone: [what completing current step unlocks]

👉 [Contextual resume question]

## Edge Cases

- No progress file: "You haven't started yet — would you like to begin onboarding?"
- Between modules: Show last completed module and next available
- Track not selected: Omit track line, show module progress only
```

## Integration with review-bootcamper-input Hook

The hook's prompt is updated to include status trigger detection alongside existing feedback triggers:

```console
If the message contains a status trigger phrase ("where am I", "status", 
"what step am I on", "show progress", "how far along am I"):
- Output: "STATUS_TRIGGER_DETECTED"
- The agent should respond with the inline status format from inline-status.md
```

## Files Created/Modified

- `senzing-bootcamp/steering/inline-status.md` — new steering file (manual inclusion)
- `senzing-bootcamp/steering/steering-index.yaml` — add keywords and file_metadata entry
- `senzing-bootcamp/hooks/review-bootcamper-input.kiro.hook` — add status trigger detection
- `senzing-bootcamp/steering/hook-registry.md` — update review-bootcamper-input entry

## Testing

- Unit test: inline-status.md exists and has correct frontmatter
- Unit test: steering-index.yaml has keyword entries for all trigger phrases
- Unit test: review-bootcamper-input hook prompt mentions status triggers
- Property test: track completion percentage is always 0-100
- Property test: response format is always ≤ 8 lines
