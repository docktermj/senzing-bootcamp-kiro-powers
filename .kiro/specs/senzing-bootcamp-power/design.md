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
├── VERSION                          # Semver version (must match POWER.md frontmatter)
├── CHANGELOG.md                     # Version history (Keep a Changelog format)
├── config/
│   ├── module-dependencies.yaml     # Module dependency graph, tracks, gates, skip conditions
│   ├── module-artifacts.yaml        # Cross-module artifact dependency manifest
│   ├── bootcamp_progress.json.example    # Template for user progress state
│   ├── bootcamp_preferences.yaml.example # Template for user preferences
│   └── er_baseline_vendors.json.example  # Template for ER baseline stats
├── docs/
│   ├── modules/                     # MODULE_N_*.md companion documentation (11 files)
│   ├── guides/                      # 19 user guides (FAQ, quick start, architecture, etc.)
│   ├── feedback/                    # Feedback templates
│   ├── policies/                    # Agent policies (code quality, file storage, Senzing info, dependency management)
│   └── diagrams/                    # Architecture and flow diagrams (Mermaid + ASCII)
├── hooks/                           # 28 .kiro.hook JSON files + hook-categories.yaml + README.md
├── scripts/                         # 40 Python CLI tools (stdlib only)
├── steering/                        # 79 steering files + steering-index.yaml
│   ├── agent-instructions.md        # Always-on core rules (140 lines)
│   ├── module-transitions.md        # Always-on transition protocol (84 lines)
│   ├── security-privacy.md          # Always-on PII policy (27 lines)
│   ├── agent-context-management.md  # Auto: context budget + adaptive pacing
│   ├── conversation-protocol.md     # Auto: turn-taking protocols (231 lines)
│   ├── design-patterns.md           # Auto: ER pattern gallery
│   ├── module-prerequisites.md      # Auto: prerequisite reference
│   ├── project-structure.md         # Auto: directory layout
│   ├── session-resume.md            # Auto: session resume workflow
│   ├── verbosity-control.md         # Auto: output level management
│   ├── lang-*.md                    # FileMatch: 5 language files (~105 lines each)
│   ├── module-*-*.md               # Manual: 11 root + phase files
│   ├── deployment-*.md              # Manual: 5 platform files
│   ├── visualization-guide.md       # Manual: consolidated visualization protocol + guide
│   ├── visualization-web-service.md # Manual: web service delivery mode
│   ├── mcp-usage-reference.md       # Manual: detailed MCP patterns
│   ├── conversation-examples.md     # Manual: violation examples reference
│   └── ...                          # Manual: workflows, troubleshooting, etc.
├── templates/                       # User templates (checklists, lineage, UAT, lessons learned)
└── tests/                           # pytest + Hypothesis test suites (151 files)
tests/                               # Repo-level tests (26 files, hook validation)
```

### Steering Architecture

The steering system follows the "Steering Kiro: Best Practices" guidelines:

| Inclusion Mode | Files | Purpose |
|---|---|---|
| always | 3 | Universal rules (file placement, MCP, communication, gates) |
| auto | 7 | Context loaded when relevant (budget management, conversation protocol, session resume) |
| fileMatch | 5 | Language-specific SDK guidance + troubleshooting |
| manual | 65 | Module workflows, deployment, troubleshooting, visualization, references |

**Context budget:** Total steering ~136k tokens tracked in `steering-index.yaml`. Warn at 60%, critical at 80% (percentage-based, derived from `reference_window` of 200k). Phase-splitting keeps individual loads small. Detailed unloading rules in `agent-context-management.md`.

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

28 hooks organized by lifecycle:

- **Critical (7):** Created during onboarding. Cover: conversation management (ask-bootcamper with silence-first default, review-bootcamper-input with feedback + status trigger detection), code quality (code-style-check, commonmark-validation), security (block-direct-sql, enforce-file-path-policies), and UX enforcement (enforce-single-question).
- **Module-specific (17):** Created when the relevant module starts. Cover: business problem validation (Module 1), SDK verification (Module 2), mandatory gate enforcement + visualization gating + demo verification (Module 3), data file validation (Module 4), mapping enforcement + quality checks (Module 5), backup + testing + code verification (Module 6), visualization offers (Modules 3/5/7/8), benchmark validation (Module 8), security scanning (Module 9), alert config validation (Module 10), deployment phase gate (Module 11).
- **Any-module (4):** backup-project-on-request (userTriggered), error-recovery-context (postToolUse), git-commit-reminder (userTriggered), module-completion-celebration (postTaskExecution).

Hook registry sync is enforced by `sync_hook_registry.py --verify` in CI. Structural validation in `tests/test_hook_structural_validation.py`.

### MCP Integration

The Senzing MCP server (required — hard gate at onboarding) provides:
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
- `reporting_guide` — Reporting and visualization guidance
- `download_resource` — Workflow resources (entity spec, analyzer script)

The agent never fabricates Senzing information. If MCP is unavailable after one retry, the bootcamp blocks until connectivity is restored.

### State Management

```text
config/                              # In the bootcamper's working directory (runtime)
├── bootcamp_progress.json           # Module state, step history, skipped steps
├── bootcamp_preferences.yaml        # Language, verbosity, track, cloud provider, hooks, pacing
├── mapping_state_*.json             # Per-source mapping workflow checkpoints
├── data_sources.yaml                # Data source registry (created during Module 4)
├── visualization_tracker.json       # Visualization offer state per checkpoint
├── .question_pending                # Transient: prevents self-answering (gitignored)
└── .mcp_status                      # Transient: MCP health check result (gitignored)
```

Progress is checkpointed after every step. `repair_progress.py` reconstructs state from artifacts if corrupted. User-state files are not tracked in git — `.example` templates are provided in the power's `config/` directory.

### Validation and CI

GitHub Actions pipeline (`validate-power.yml`):
1. `validate_power.py` — Cross-references, hooks, frontmatter, scripts, steering index, version sync
2. `measure_steering.py --check` — Token counts within 10% tolerance
3. `validate_commonmark.py` — Markdown compliance
4. `validate_dependencies.py` — Module dependency graph consistency
5. `sync_hook_registry.py --verify` — Hook registry in sync with hook files
6. `validate_prerequisites.py` — Module prerequisite consistency
7. `validate_progress_ci.py` — Progress schema validation
8. `validate_mandatory_gates.py` — Mandatory gate enforcement
9. `pytest senzing-bootcamp/tests/ tests/` — 177 test files with property-based testing (Hypothesis)

### Team Mode

Optional `config/team.yaml` enables multi-user sessions:
- Co-located mode: shared repo, per-member progress files
- Distributed mode: separate repos, consolidated via `merge_feedback.py`
- Team dashboard: `team_dashboard.py`

## Constraints

- All files in `senzing-bootcamp/` are part of the distributed power — no dev-only files.
- Scripts use stdlib-only Python 3.11+ (exception: `validate_dependencies.py` uses PyYAML).
- No static code templates — all SDK code generated dynamically by MCP.
- Steering files follow the "Steering Kiro: Best Practices" article guidelines for inclusion modes.
- Hook prompts must pass structural validation (valid JSON, required fields, no inline closing questions, silent processing for pass-through hooks, registry sync).
- Context budget thresholds are percentage-based (60%/80% of `reference_window`) — never hardcoded absolute values.
- User-state config files are not tracked in git — `.example` templates provided.
- The MCP server is required (no offline fallback) — hard gate at onboarding Step 0b.
