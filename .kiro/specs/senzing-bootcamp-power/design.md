# Design Document

## Overview

The senzing-bootcamp Kiro Power is a guided 11-module curriculum for learning Senzing entity resolution. It is delivered as a Kiro Power installed into the IDE, connecting to the Senzing MCP server for dynamic code generation and authoritative documentation.

The power produces working code artifacts (transformation, loading, query programs) in the bootcamper's chosen language. No static code templates are shipped — the MCP server generates all SDK code dynamically, ensuring it always matches the current SDK version.

## Architecture

### File Layout

```text
senzing-bootcamp/                    # The distributed power root
├── POWER.md                         # Power manifest (name, description, keywords, docs)
├── mcp.json                         # MCP server configuration
├── CHANGELOG.md                     # Version history (Keep a Changelog format)
├── config/
│   ├── module-dependencies.yaml     # Module dependency graph and skip conditions
│   ├── module-artifacts.yaml        # Cross-module artifact dependency manifest
│   └── data_sources.yaml            # Data source registry (quality, mapping, load status)
├── docs/
│   ├── modules/                     # MODULE_N_*.md companion documentation
│   ├── guides/                      # 24 user guides (FAQ, glossary, quick start, etc.)
│   ├── feedback/                    # Feedback templates
│   ├── policies/                    # Agent policies (code quality, file storage, Senzing info)
│   └── diagrams/                    # Architecture and flow diagrams (Mermaid + ASCII)
├── hooks/                           # 23 .kiro.hook JSON files + hook-categories.yaml
├── scripts/                         # 30 Python CLI tools (stdlib only)
├── steering/                        # 75 steering files + steering-index.yaml
│   ├── agent-instructions.md        # Always-on core rules (89 lines)
│   ├── module-transitions.md        # Always-on transition protocol (71 lines)
│   ├── security-privacy.md          # Always-on PII policy (27 lines)
│   ├── agent-context-management.md  # Auto: context budget + adaptive pacing
│   ├── conversation-protocol.md     # Auto: turn-taking protocols
│   ├── design-patterns.md           # Auto: ER pattern gallery
│   ├── module-prerequisites.md      # Auto: prerequisite reference
│   ├── project-structure.md         # Auto: directory layout
│   ├── session-resume.md            # Auto: session resume workflow
│   ├── verbosity-control.md         # Auto: output level management
│   ├── lang-*.md                    # FileMatch: 5 language files
│   ├── module-*-*.md               # Manual: 11 root + phase files
│   ├── deployment-*.md              # Manual: 5 platform files
│   ├── inline-status.md             # Manual: "Where Am I?" response format
│   ├── whats-new.md                 # Manual: What's New notification format
│   └── ...                          # Manual: workflows, troubleshooting, etc.
├── templates/                       # User templates (checklists, lineage, UAT)
└── tests/                           # pytest + Hypothesis test suites (98 files)
```

### Steering Architecture

The steering system follows the "Steering Kiro: Best Practices" guidelines:

| Inclusion Mode | Files | Max Lines | Purpose |
|---|---|---|---|
| always | 3 | 89 each | Universal rules (file placement, MCP, communication) |
| auto | 7 | 284 max | Context loaded when relevant (budget management, conversation protocol, session resume) |
| fileMatch | 5 | 107 each | Language-specific SDK guidance + troubleshooting |
| manual | 61 | varies | Module workflows, deployment, troubleshooting, inline status |

**Context budget:** Total steering token budget tracked in `steering-index.yaml`. Warn at 60%, critical at 80% (percentage-based, derived from `reference_window`). Phase-splitting keeps individual loads small. Detailed unloading rules in `agent-context-management.md`.

### Module Phase Architecture

Large modules are split into a lightweight root file (router) and phase files (content):

```text
module-08-performance.md          # Root: banner, phases table, error handling (~30 lines)
├── module-08-phaseA-requirements.md   # Steps 1–3
├── module-08-phaseB-benchmarking.md   # Steps 4–7
└── module-08-phaseC-optimization.md   # Steps 8–13
```

The root file is loaded at module start. Phase files are loaded on-demand based on the bootcamper's current step (read from `config/bootcamp_progress.json`).

### Hook Architecture

23 hooks organized by lifecycle:

- **Critical (7):** Created during onboarding. Cover code quality, working directory enforcement, Senzing fact verification, conversation management (ask-bootcamper with silence-first default, review-bootcamper-input with feedback + status trigger detection), and feedback path enforcement.
- **Module-specific (14):** Created when the relevant module starts. Cover SDK verification, data validation, mapping enforcement, benchmark validation, security scanning, alert config validation, visualization offers, and deployment gating.
- **Any-time (2):** User-triggered (backup, git commit).

Hook registry sync is enforced by `sync_hook_registry.py --verify` in CI. Structural validation available via `test_hooks.py`.

### MCP Integration

The Senzing MCP server provides:
- `get_capabilities` — Discover available tools
- `mapping_workflow` — Interactive 8-step data mapping
- `generate_scaffold` — SDK code in any supported language
- `sdk_guide` — Platform-specific installation instructions
- `get_sdk_reference` — Method signatures and flags
- `explain_error_code` — 456 error code explanations
- `search_docs` — Indexed documentation search
- `find_examples` — Working code from 27 Senzing repos
- `analyze_record` — Data quality validation
- `get_sample_data` — Sample datasets (Las Vegas, London, Moscow)

The agent never fabricates Senzing information. If MCP is unavailable, `mcp-offline-fallback.md` defines what's blocked vs. continuable.

### State Management

```text
config/
├── bootcamp_progress.json       # Module state, step history, skipped steps
├── bootcamp_preferences.yaml    # Language, verbosity, cloud provider, hooks, pacing_overrides
├── mapping_state_*.json         # Per-source mapping workflow checkpoints
├── data_sources.yaml            # Data source registry
├── module-artifacts.yaml        # Artifact dependency manifest (what each module produces/requires)
├── .question_pending            # Transient: prevents self-answering
├── .mcp_status                  # Transient: MCP health check result (gitignored)
└── session_log.jsonl            # Session analytics (turns, corrections, time per module)
```

Progress is checkpointed after every step. `repair_progress.py` reconstructs state from artifacts if corrupted. Session analytics feed adaptive pacing (via `classify_pacing()` in `analyze_sessions.py`).

### Validation and CI

GitHub Actions pipeline (`validate-power.yml`):
1. `validate_power.py` — Cross-references, hooks, frontmatter, scripts, steering index
2. `measure_steering.py --check` — Token counts within budget
3. `validate_commonmark.py` — Markdown compliance
4. `sync_hook_registry.py --verify` — Hook registry in sync
5. `pytest` — 98 test files with property-based testing (Hypothesis)

### Team Mode

Optional `config/team.yaml` enables multi-user sessions:
- Co-located mode: shared repo, per-member progress files
- Distributed mode: separate repos, consolidated via `merge_feedback.py`
- Team dashboard: `team_dashboard.py`

## Constraints

- All files in `senzing-bootcamp/` are part of the distributed power — no dev-only files.
- Scripts use stdlib-only Python 3.11+ (exception: `validate_dependencies.py` uses PyYAML).
- No static code templates — all SDK code generated dynamically by MCP.
- Steering files follow the "Steering Kiro: Best Practices" article guidelines for inclusion modes and line budgets.
- Hook prompts must pass `test_hook_prompt_standards.py` (valid JSON, required fields, no inline closing questions, silent processing for pass-through hooks, registry sync).
- Hook files must pass `test_hooks.py` structural validation (event types, patterns, toolTypes, registry consistency).
- Always-on steering total: 3 files, ≤90 lines each, 187 lines combined.
- Context budget thresholds are percentage-based (60%/80% of `reference_window`) — never hardcoded absolute values.
