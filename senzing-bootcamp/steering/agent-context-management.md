---
inclusion: auto
---

# Context & Pacing Management

Operational rules for managing context budget and adaptive pacing. These extend the core rules in `agent-instructions.md`.

## Adaptive Pacing

At module start, read `config/session_log.jsonl` and classify completed modules:

- **struggled** (correction density > 0.3 or time > 2× median): increase explanation depth for this module — fuller "why" framing before each step, proactive offer of alternative explanations
- **comfortable** (correction density < 0.1 and time < median): streamline delivery — shorter lead-ins, skip optional context unless asked
- **normal**: use standard pacing per verbosity setting

Check `config/bootcamp_preferences.yaml` for `pacing_overrides` — manual overrides ("slow down" → struggled, "speed up" → comfortable) take precedence over computed classifications.

Adaptive pacing adjusts the baseline but never reduces below explicit verbosity preferences. If the bootcamper set verbosity to "detailed", pacing never reduces below "detailed".

## Context Budget Management

Maintain a mental model of which steering files are currently loaded and their token costs (from `steering-index.yaml` `file_metadata`).

**Unload candidates** — a file is eligible for unloading when ALL of these are true:

1. It belongs to a completed module (not the current module)
2. It hasn't been referenced in the last 5 turns
3. It's not in the top 4 tiers of retention priority

**Retention priority (6 tiers):**

1. `agent-instructions.md` — never unload
2. Current module steering — never unload while in that module
3. Language file — never unload
4. `conversation-protocol.md` — never unload
5. `common-pitfalls.md` / troubleshooting — unload only at critical
6. Completed module steering — first to unload

**At warn threshold (60%):**

- Identify unload candidates and their token savings (from `file_metadata`)
- Present actionable message: "Context budget at X%. I can free ~N tokens by unloading [file] (completed). Want me to proceed, or keep it loaded?"
- Wait for bootcamper response before acting

**At critical threshold (80%):**

- Automatically unload all completed-module steering files
- Report what was freed: "Automatically unloaded [files] — freed ~N tokens. These can be reloaded on demand."
- No question asked — automatic action to prevent context overflow

**Phase-based fallback:** If all completed modules are unloaded and budget is still critical, load only the current phase of a split module (not the full file).

**Override:** If the bootcamper says "keep everything loaded", suppress automatic unloading for the current session (not persisted). Still show warnings but don't act.

**Reload on demand:** Unloaded files can be reloaded if the bootcamper revisits a completed module or asks about earlier content.
