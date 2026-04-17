# Changelog

All notable changes to the Senzing Bootcamp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For the complete version history (0.1.0 through 0.1.9), see the development repository at `senzing-bootcamp-power-development/CHANGELOG_FULL.md`.

## [0.7.0] - 2026-04-17

### Added in 0.7.0

- Glossary file copied to project during onboarding setup (was only in power distribution)
- Strict one-question-at-a-time rule at top of `onboarding-flow.md` — most common onboarding complaint
- `description` field required in generated steering file frontmatter (prevents Kiro warnings)
- License discovery in Module 0 — checks CONFIGPATH for existing system license before asking user
- `LICENSEFILE` in engine config when project-local license exists at `licenses/g2.lic` — overrides system CONFIGPATH
- Interactive visualization features — agent asks about how/why/search/find capabilities when user requests web page
- Module 1 demo uses 50-200 records (was 5-10) for richer entity clusters and meaningful search results
- Zero-matches handling in Module 8 — explains three possible causes when entity resolution finds no matches
- First-term explanation rule in `agent-instructions.md` — define Senzing terms inline on first use, reference glossary
- Guided troubleshooting diagnostic questions at top of `common-pitfalls.md`
- `validate_power.py` script for power self-validation
- System architecture diagram at `docs/diagrams/system-architecture.md`
- Stakeholder summary templates after Modules 2, 8, and 12
- Next-step options (proceed/iterate/explore/share) in `module-completion.md`
- Iterate vs. proceed decision gates in Modules 4, 5, and 8
- AFTER_BOOTCAMP.md updated with mapping checkpointing, quality gates, and Phase 1/2 deployment references

### Changed in 0.7.0

- `onboarding-flow.md` trimmed from 109 to 87 lines — replaced verbose YAML frontmatter block with one-line instruction
- `COLLABORATION_GUIDE.md` rewritten from 370 to 46 lines — language-agnostic, defers to CODE_QUALITY_STANDARDS.md
- `lessons-learned.md` rewritten from 208 to 46 lines — describes sections to include, agent generates at runtime
- `feedback-workflow.md` template path corrected to `senzing-bootcamp/docs/feedback/` (power distribution, not project)
- `common-pitfalls.md` Module 4 pitfall aligned with three-tier iterate-vs-proceed gate
- `data-flow.md` diagram replaced hardcoded Senzing attribute names with placeholders per SENZING_INFORMATION_POLICY
- Module 6 Step 1 fixed "Module 3" → "Module 5" for transformation program output
- `session-resume.md` now checks for `config/mapping_state_*.json` checkpoint files
- Module 12 Step 1 reads existing `cloud_provider` from preferences before re-asking
- `ONBOARDING_CHECKLIST.md` rewritten from 370 to 40 lines — reflects current automated onboarding flow
- Module 0 engine config rule: NEVER construct JSON manually, use exact output from `sdk_guide(topic='configure')`
- "data source" terminology in Module 1 bridging questions changed to "source systems or feeds" to avoid Senzing DATA_SOURCE collision

## [0.6.0] - 2026-04-16

### Added in 0.6.0

- Glossary reference in onboarding introduction — mentions `docs/guides/GLOSSARY.md` and invites questions about unfamiliar terms
- Iterate vs. proceed decision gates in Modules 4, 5, and 8 — three-tier guidance (strong/acceptable/needs work) with specific actions at each level
- `docs/diagrams/system-architecture.md` — runtime architecture diagram showing how SDK, database, programs, and optional layers fit together
- Next-step options in `module-completion.md` — after every module, presents four choices (proceed, iterate, explore, share) and waits for user
- Guided troubleshooting in `common-pitfalls.md` — diagnostic questions section at top; agent asks module/action/error before presenting pitfall tables
- Stakeholder summary templates after Modules 2, 8, and 12 — one-page formats for sharing results with team/management
- Explicit data visualization triggers in Modules 1, 5, 8, and 9 — agent offers HTML visualization at key data-presentation moments
- `scripts/validate_power.py` — self-validation script checking steering frontmatter, hook JSON, module docs, scripts, POWER.md cross-references, policies, and diagrams
- FAQ entries for guided discovery tone, glossary, license key safety, and data visualization feature
- Guided discovery framing in POWER.md and onboarding introduction — "take it slow, ask questions"
- Third-party MCP consultation rule in `agent-instructions.md` — always call `search_docs` before recommending Elasticsearch, PostgreSQL, Docker, etc.
- Data visualization offer in `agent-instructions.md` Communication section
- Module 12 restructured into Phase 1 (Packaging) and Phase 2 (Deployment, optional) — agent asks deployment target and method before deploying
- AWS CDK guidance in Module 12 Steps 2, 4, 5, 6, 9 with recommendation to install "Build AWS infrastructure with CDK and CloudFormation" Kiro Power
- "Where Senzing Fits in Your Architecture" section in `design-patterns.md` — correct layering for Senzing + search engines
- TypeScript SDK build-from-source warning in Module 0 Step 3
- `analyze_record` empty Feature Analysis table guidance in Module 5
- License key safety rule in Module 0 Step 5 — never paste BASE64 into chat, decode to `licenses/g2.lic` instead

### Changed in 0.6.0

- Language selection now MCP-driven — agent detects platform, queries MCP for supported languages, relays any warnings (no hardcoded assumptions)
- `lang-python.md` platform support line defers to MCP server
- `onboarding-flow.md` rewritten from 333 to 85 lines
- Module 0 SDK check strengthened — "MUST DO FIRST", explicit skip-entire-module logic for existing V4.0+ installations
- Module 12 deployment target question moved to Step 1 (before packaging) — target shapes what artifacts get built

## [0.5.0] - 2026-04-14

### Added in 0.5.0

- MCP offline guidance in `common-pitfalls.md` — tables showing what works without MCP and what's blocked, with fallback instructions
- Mapping state checkpointing in `module-05-data-mapping.md` — saves decisions to `config/mapping_state_[datasource].json` after each step for session resume
- `summarize-on-stop.kiro.hook` — agentStop hook ensuring agent summarizes accomplishments, changed files, and next step
- `verify-generated-code.kiro.hook` — fileCreated hook on `src/transform/`, `src/load/`, `src/query/` prompting agent to run and verify new code
- `module-completion.md` — manual steering file for journal entries, reflection questions, and path completion celebration (extracted from module-transitions.md to reduce auto-included context)
- Use-case bridging questions in `module-01-quick-demo.md` — targeted questions after demo to personalize transition to Module 2
- "Tell the user" blocks in `module-10-security.md` and `module-12-deployment.md` for security assessment, vulnerability scan, checklist, and deployment status
- Bootcamp journal reflection question — asks user for takeaway after each module
- Path completion celebration — distinct recognition when user finishes their chosen path
- Sample dataset details (Las Vegas, London, Moscow) surfaced in onboarding introduction and POWER.md

### Changed in 0.5.0

- Rewrote `agent-instructions.md` from 98 to 54 lines — compressed tables, merged redundant rules, within 80-line always-on guideline
- Rewrote `security-privacy.md` from 80 to 27 lines — removed generic advice the model already knows, kept only bootcamp-specific data handling rules
- Rewrote `project-structure.md` from 130 to 44 lines — removed descriptive "why" section, duplicate trigger points, verbose notes
- Split `module-transitions.md` (170 lines auto) into lean auto file (27 lines) + manual `module-completion.md` (49 lines) — auto context reduced 84%
- Rewrote `module-01-quick-demo.md` from 245 to 65 lines — removed verbose example output blocks, kept prescriptive instructions
- Rewrote `module-05-data-mapping.md` from 341 to 66 lines — removed verbose "tell the user" example text blocks, kept step structure and communication instructions
- All changes follow "Steering Kiro: Best Practices" guidelines: prescriptive not descriptive, deliberate inclusion modes, context budget management

### Fixed in 0.5.0

- `FILE_STORAGE_POLICY.md` referenced transformation programs as "Module 4" — corrected to Module 5
- `QUICK_START.md` Path B listed `0 → 5 → 6 → 8` and Path C listed `2 → 3 → 4 → 5 → 0 → 6 → 8` — corrected to match POWER.md (Module 0 is auto-inserted, not listed in path)
- `module-flow.md` diagram Path B showed `Module 0 → Module 6 → Done` — corrected to `Module 0 → Module 5 → Module 6 → Module 8 → Done`
- `hooks/README.md` missing entries for `summarize-on-stop` and `verify-generated-code` hooks — added

## [0.4.0] - 2026-04-09

### Changed in 0.4.0

- Streamlined onboarding: directory creation, hook installation, and steering generation now happen silently — user only sees two questions (language and path)
- Hooks install automatically at bootcamp start — no longer asks for permission
- Trimmed path descriptions in POWER.md and onboarding-flow.md to concise labels
- Rewrote QUICK_START.md from 230 lines to ~50 lines, aligned with current onboarding flow
- Condensed `common-pitfalls.md` from 514 to ~150 lines using prescriptive table format, changed from `auto` to `manual` inclusion
- Condensed `module-prerequisites.md` from 401 to ~54 lines using compact tables
- Condensed `complexity-estimator.md` from 352 to ~53 lines using compact tables
- Removed `#[[file:]]` references from always-loaded `agent-instructions.md` — reduced effective always-on context from ~700 to ~90 lines
- Changed `security-privacy.md` and `project-structure.md` from `manual` to `auto` inclusion
- Removed redundant directory setup narration from Module 2
- Updated HOOKS_INSTALLATION_GUIDE.md to reflect automatic installation
- Fixed broken markdown fence in module-03-data-collection.md
- Updated FAQ to note prerequisites are checked automatically

### Added in 0.4.0

- `session-resume.md` — structured workflow for resuming previous bootcamp sessions across context windows
- `enforce-working-directory.kiro.hook` — preToolUse hook that blocks writes to `/tmp` or paths outside the working directory
- Tool Usage Examples section in POWER.md with concrete MCP tool call examples
- Mapping workflow state loss recovery guidance in `common-pitfalls.md`
- Path B note for Module 0 requirement in onboarding flow
- PowerShell equivalents for all bash commands in modules 0-3
- AWS CDK guidance at the 8→9 gate and in Module 12
- Language steering file loaded immediately after language selection (not just on file match)
- Explicit `inclusion` frontmatter instructions for generated workspace steering files
- Kiro Refine button recommendation for generated steering files
- `preflight_check.py` and `validate_commonmark.py` added to POWER.md Useful Commands

### Fixed in 0.4.0

- `module-prerequisites.md` Module 5 skip note said "Go directly to Module 0" — corrected to Module 6
- `module-01-quick-demo.md` had Python-specific `os.makedirs` in language-agnostic instructions — made language-neutral
- `export_report` and `exportJSONEntityReport()` now explicitly banned across agent-instructions, module-08, and policies
- `/tmp` override instructions added to modules 6, 7, 8, 9 (previously only in 0, 1, 5)
- `generate_scaffold(workflow='redo')` in Module 9 Step 9 now has path override reminder

## [0.3.0] - 2026-04-08

### Changed in 0.3.0

- Split `agent-instructions.md` into a slim always-loaded core (principles, MCP rules, error handling) and a manual `onboarding-flow.md` (directory creation, language selection, prerequisites, path selection, validation gates) to reduce context usage on every turn
- Tightened `agent-instructions.md` from 156 lines to 90 lines — more prescriptive, less descriptive, uses `#[[file:]]` references instead of inline content
- Changed `security-privacy.md` from `inclusion: always` to `inclusion: manual` — loaded on demand during Module 10 or when handling PII
- Changed `common-pitfalls.md` from `inclusion: manual` to `inclusion: auto` — Kiro includes it when relevant to the conversation
- Extracted 8→9 gate cloud provider selection into dedicated `cloud-provider-setup.md` steering file
- Trimmed Modules 9-12 steering files from 1,100-1,500 lines each to 78-119 lines — removed verbose pseudocode, kept prescriptive step lists with MCP tool delegation
- Clarified script paths in POWER.md — scripts live in `senzing-bootcamp/scripts/` and should be referenced from the power directory
- Updated example project READMEs to explicitly note they are architectural blueprints, not runnable code
- Added diagram viewing guidance in POWER.md (Mermaid preview extension or mermaid.live)
- Trimmed CHANGELOG to current version only; full history moved to development repository
- Added foundational steering file generation (product.md, tech.md, structure.md) to onboarding flow
- Added `#[[file:]]` references in steering files to pull policy docs into context when needed

### Added in 0.3.0

- `lang-python.md` — conditional steering for Python files (`*.py`)
- `lang-java.md` — conditional steering for Java files (`*.java`)
- `lang-csharp.md` — conditional steering for C# files (`*.cs`)
- `lang-rust.md` — conditional steering for Rust files (`*.rs`)
- `lang-typescript.md` — conditional steering for TypeScript/JavaScript files (`*.ts`, `*.tsx`, `*.js`, `*.jsx`)

### Removed in 0.3.0

- `templates/` directory (templates have been dynamically generated by MCP since v0.1.5)
- `scripts/__pycache__/` build artifacts from power distribution

### Fixed in 0.3.0

- `module-prerequisites.md` Module 1 listed "No prerequisites" but Module 0 (SDK Setup) is required — corrected to match agent-instructions and QUICK_START

## [0.2.0] - 2026-04-06

### Changed in 0.2.0

- Standardized "boot camp" → "bootcamp" (one word) across all 55+ files
- Removed time estimates from all module listings — the complexity estimator provides personalized estimates instead
- Added MCP Failure Recovery, language switching, progress corruption recovery, AWS/cloud provider guidance, and many other improvements across steering files, docs, scripts, and examples
- See development repository for full 0.2.0 details
