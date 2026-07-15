# Decision Record: target standard inclusion mode for each `auto` file

_Feature: steering-inclusion-auto-audit — satisfies Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

## Audit branch that produced this assignment

The `Audit_Finding` (`audit-finding.md`) established
`Runtime_Behavior = loads-manual-only` — i.e. `Runtime_Behavior != loads-always`.

Under the design's **audit contingency rule** (design.md → "Decision model (Req 2)"),
because the verified behavior is not `loads-always`, no `Auto_File` was
unconditionally present in every session before the change, so Req 6.3 imposes no
"must stay always" constraint arising from these files. Therefore the **provisional
3×`always` / 1×`fileMatch` / 7×`manual` split stands** and is the final assignment
recorded below. This also matches what the current budget accounting already assumes
(the pre-existing always-loaded baseline of the three `inclusion: always` files,
≈6,668 tokens).

> **Branch taken:** `Runtime_Behavior != loads-always` → provisional split is final.
> The alternative branch (`loads-always` → map all eleven to `always`, projected
> baseline ≈24,830 tokens) was **not** taken.

All per-file `token_count` values below were re-verified on 2026-07-08 against the
current `senzing-bootcamp/steering/steering-index.yaml` `file_metadata` block and
match exactly.

## Decision entries (Decision_Record data model — one per Auto_File)

### 1. agent-behavior-rules.md

```yaml
filename:            agent-behavior-rules.md
target_mode:         always                 # Req 2.1
intended_condition:  every-session          # Req 2.2
token_count:         822                    # Req 2.5 — counted in projected baseline
rationale: >                                # Req 2.3
  Four foundational behavior rules that must govern every turn of the guided
  workflow. The file is not keyword-routed in the Steering_Index and has no natural
  file-edit or reference trigger, so the only condition that guarantees it governs
  every turn is unconditional presence. Assigning `always` produces the
  every-session condition.
```

### 2. conversation-protocol.md

```yaml
filename:            conversation-protocol.md
target_mode:         always                 # Req 2.1
intended_condition:  every-session          # Req 2.2
token_count:         4600                    # Req 2.5 — counted in projected baseline
rationale: >                                # Req 2.3
  Defines turn-taking, question-handling, and module-transition protocol that the
  guided bootcamp workflow relies on being present throughout an active session.
  It is not keyword-routed and its behavior must fire on every turn, so `always`
  is the mode that yields the required every-session presence.
```

### 3. qa-transcript.md

```yaml
filename:            qa-transcript.md
target_mode:         always                 # Req 2.1
intended_condition:  every-session          # Req 2.2
token_count:         1284                    # Req 2.5 — counted in projected baseline
rationale: >                                # Req 2.3
  Emits Q&A completion events whenever the agent asks a leading question. That
  behavior must be able to fire at any point across the bootcamp, which requires
  the file to be loaded in every session. It is not keyword-routed, so `always`
  is the mode that produces the every-session condition.
```

### 4. file-placement.md

```yaml
filename:            file-placement.md
target_mode:         fileMatch              # Req 2.1
intended_condition:  on-file-match          # Req 2.2
file_match_pattern:  "**/*"                 # Req 2.4 — single non-empty glob
rationale: >                                # Req 2.3
  Its stated intended trigger is "load when creating or writing any project file,"
  which is a classic file-edit match rather than a session-wide or reference-only
  condition. Assigning `fileMatch` with the glob `**/*` loads the guidance exactly
  when any project file is being created or written, matching the intended
  on-file-match condition.
```

### 5. agent-context-management.md

```yaml
filename:            agent-context-management.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed in the Steering_Index (context budget / pacing / unload). It is
  situational guidance pulled in only when those concerns arise or the file is
  referenced, not needed on every turn. `manual` produces the intended
  on-explicit-ref condition while the preserved keyword routing entries continue
  to surface it on demand.
```

### 6. design-patterns.md

```yaml
filename:            design-patterns.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed (pattern). A reference gallery consulted only when discussing
  design patterns or when explicitly referenced, so it needs presence only on
  explicit reference. `manual` yields that on-explicit-ref condition; its keyword
  routing entry is retained unchanged.
```

### 7. mcp-response-caching.md

```yaml
filename:            mcp-response-caching.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed (cache / mcp cache). Situational guidance relevant only when
  caching is being discussed or the file is referenced. `manual` produces the
  intended on-explicit-ref condition; the keyword routing entry is preserved.
```

### 8. module-prerequisites.md

```yaml
filename:            module-prerequisites.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed (prerequisite). Consulted only when checking module readiness or
  when explicitly referenced, not on every turn. `manual` produces the intended
  on-explicit-ref condition while the retained routing entry pulls it in on demand.
```

### 9. project-structure.md

```yaml
filename:            project-structure.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed (project-structure). Reference material consulted only on demand
  or explicit reference. `manual` produces the intended on-explicit-ref condition.
  Note: this file has NO `description` frontmatter value and must remain without
  one after re-classification (Req 3.2).
```

### 10. session-resume.md

```yaml
filename:            session-resume.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed (resume) and the `session-resume:` root in the Steering_Index.
  Loaded at resume time or on explicit reference, not on every turn. `manual`
  produces the intended on-explicit-ref condition; both the keyword entry and the
  session-resume root are retained unchanged.
```

### 11. verbosity-control.md

```yaml
filename:            verbosity-control.md
target_mode:         manual                 # Req 2.1
intended_condition:  on-explicit-ref        # Req 2.2
rationale: >                                # Req 2.3
  Keyword-routed (output level / verbose / verbosity / content rules). Loaded when
  adjusting output verbosity or when explicitly referenced. `manual` produces the
  intended on-explicit-ref condition; its keyword routing entries are preserved.
```

## Assignment summary

| # | Auto_File | Target mode | Intended condition | Glob / token_count |
|---|---|---|---|---|
| 1 | agent-behavior-rules.md | `always` | every-session | 822 tokens |
| 2 | conversation-protocol.md | `always` | every-session | 4600 tokens |
| 3 | qa-transcript.md | `always` | every-session | 1284 tokens |
| 4 | file-placement.md | `fileMatch` | on-file-match | `**/*` |
| 5 | agent-context-management.md | `manual` | on-explicit-ref | — |
| 6 | design-patterns.md | `manual` | on-explicit-ref | — |
| 7 | mcp-response-caching.md | `manual` | on-explicit-ref | — |
| 8 | module-prerequisites.md | `manual` | on-explicit-ref | — |
| 9 | project-structure.md | `manual` | on-explicit-ref | — |
| 10 | session-resume.md | `manual` | on-explicit-ref | — |
| 11 | verbosity-control.md | `manual` | on-explicit-ref | — |

**Split:** 3× `always` / 1× `fileMatch` / 7× `manual` (11 files total).

## Projected Baseline_Footprint (Req 2.5)

The projected always-loaded footprint sums the measured `token_count` of the
`always` entries in this record **together with the pre-existing always-loaded
files** (the three files that already declare `inclusion: always`):

| File | Source | token_count |
|---|---|---|
| agent-instructions.md | pre-existing `always` | 4482 |
| module-transitions.md | pre-existing `always` | 1908 |
| security-privacy.md | pre-existing `always` | 278 |
| agent-behavior-rules.md | reclassified → `always` (this record) | 822 |
| conversation-protocol.md | reclassified → `always` (this record) | 4600 |
| qa-transcript.md | reclassified → `always` (this record) | 1284 |
| **projected_baseline_footprint** | | **13,374** |

```yaml
projected_baseline_footprint: 13374        # Req 2.5 (tokens)
```

Arithmetic: `4482 + 1908 + 278 + 822 + 4600 + 1284 = 13374` tokens.

Budget headroom: the ceiling read from `steering-index.yaml` `budget:` is
`always_loaded_ceiling_pct` (25) % of the warn threshold, where the warn threshold
is `warn_threshold_pct` (60) % of `reference_window` (200000):
`0.60 * 200000 = 120000` warn threshold → `0.25 * 120000 = 30000` ceiling.
The projected baseline **13,374 < 30,000**, so the finalized `always` set is well
within budget. (No token value is hardcoded in tooling; these are stated here only
as the projected total for Req 2.5. `measure_steering.py` reads the thresholds from
the index at check time.)

## Notes

- **Audit branch recorded (Req 2 ↔ Req 6.3):** provisional split is final because
  `Runtime_Behavior = loads-manual-only` (`!= loads-always`).
- **`fileMatch` glob (Req 2.4):** the single non-empty glob for the one `fileMatch`
  file (file-placement.md) is `**/*`.
- **`always` token counts (Req 2.5):** each `always` entry includes its measured
  `token_count`, all re-verified against the current Steering_Index `file_metadata`.
- **`manual` condition (Req 2.6):** each of the seven `manual` files records the
  on-explicit-ref (explicit-reference) condition.
- **Downstream (Req 3):** these assignments drive the frontmatter rewrites; keyword
  routing entries in `steering-index.yaml` are retained unchanged (Req 3.4), and
  project-structure.md keeps no `description` (Req 3.2).
