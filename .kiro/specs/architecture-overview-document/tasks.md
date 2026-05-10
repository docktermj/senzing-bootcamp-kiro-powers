# Tasks

## Task 1: Create the ARCHITECTURE.md document skeleton

- [x] 1.1 Create `senzing-bootcamp/docs/guides/ARCHITECTURE.md` with the document title, introductory paragraph (audience: contributors and advanced bootcampers), and a table of contents with anchor links to all seven major sections (Component Overview, Data Flow, Module Lifecycle, Hook Architecture, Configuration Relationships, MCP Integration, Context Budget Management)
- [x] 1.2 Add a metadata comment at the top of the document noting the source files it reflects (`module-dependencies.yaml`, `steering-index.yaml`, `hook-categories.yaml`) and the creation date

## Task 2: Write the Component Overview section

- [x] 2.1 Write the Component Overview section describing each major component (steering, hooks, scripts, config, MCP, modules, docs) with its directory location, file format, and primary responsibility
- [x] 2.2 Create an ASCII diagram showing the top-level directory layout of `senzing-bootcamp/` and how components relate to each other (steering drives agent behavior, hooks automate checks, config stores state, scripts provide tooling, MCP provides facts)

## Task 3: Write the Data Flow section

- [x] 3.1 Write the Data Flow section describing the end-to-end flow of a bootcamp session from session start through onboarding, module execution, and session resume
- [x] 3.2 Document the session-start decision logic: if `bootcamp_progress.json` exists → load `session-resume.md`, otherwise → load `onboarding-flow.md`
- [x] 3.3 Identify which configuration files are read or written at each stage (bootcamp_progress.json, bootcamp_preferences.yaml, data_sources.yaml, session_log.jsonl)
- [x] 3.4 Create an ASCII diagram showing the session lifecycle sequence (start → decision → onboarding/resume → module loop → completion)

## Task 4: Write the Module Lifecycle section

- [x] 4.1 Write the Module Lifecycle section describing the states a module passes through: prerequisite check, steering file load, step execution, checkpointing, gate evaluation, and completion
- [x] 4.2 Explain how split modules use phase-level loading from `steering-index.yaml` (modules 1, 5, 6, 8, 9, 10, 11 have phases with individual files and step ranges)
- [x] 4.3 Describe how `module-dependencies.yaml` gates control transitions between modules (gate conditions, prerequisite modules, skip conditions)
- [x] 4.4 Explain how step-level checkpointing updates `bootcamp_progress.json` after each numbered step (current_step field, step_history records)
- [x] 4.5 Create an ASCII diagram showing the module lifecycle state machine (prerequisite check → load steering → execute steps → checkpoint → gate check → next module)

## Task 5: Write the Hook Architecture section

- [x] 5.1 Write the Hook Architecture section describing how hooks function within the system (IDE event triggers, hook evaluation, agent action)
- [x] 5.2 Describe the two hook categories from `hook-categories.yaml`: critical hooks (7 hooks created during onboarding) and module hooks (created when the associated module starts)
- [x] 5.3 Explain the hook silence rule (zero output when a check passes) and how the `ask-bootcamper` hook owns all closing questions
- [x] 5.4 Create an ASCII diagram showing the hook trigger flow (IDE event → hook evaluation → condition check → pass silently / fail → agent action)

## Task 6: Write the Configuration Relationships section

- [x] 6.1 Write the Configuration Relationships section describing how `module-dependencies.yaml`, `steering-index.yaml`, `hook-categories.yaml`, and `bootcamp_progress.json` relate to each other
- [x] 6.2 Classify each configuration file as read-only power asset (shipped with the power, never modified by the agent) versus mutable user state (created/updated during bootcamp sessions)
- [x] 6.3 Describe how `bootcamp_preferences.yaml` stores user choices that influence agent behavior (language, track, verbosity, conversation style, hooks installed, pacing overrides)
- [x] 6.4 Create an ASCII diagram showing the data flow between configuration files (which files feed into which decisions)

## Task 7: Write the MCP Integration section

- [x] 7.1 Write the MCP Integration section describing how the Senzing MCP server at `mcp.senzing.com` provides facts, code generation, and tool assistance
- [x] 7.2 Document the rule that all Senzing facts come from MCP tools and never from training data
- [x] 7.3 List the primary MCP tool categories (discovery, mapping, code generation, reference, diagnostics) with brief descriptions
- [x] 7.4 Describe the MCP failure and offline fallback behavior (health check probe, `.mcp_status` file, offline mode capabilities)
- [x] 7.5 Create an ASCII diagram showing the boundary between local power assets and remote MCP capabilities

## Task 8: Write the Context Budget Management section

- [x] 8.1 Write the Context Budget Management section describing how the agent manages context window pressure using token counts from `steering-index.yaml`
- [x] 8.2 Describe the three budget states: normal (below 60%), warn (60-80%), and critical (above 80%) with the actions taken at each threshold
- [x] 8.3 Explain the retention priority order (6 tiers: agent-instructions > current module > language file > conversation-protocol > troubleshooting > completed modules)
- [x] 8.4 Describe how `steering-index.yaml` provides `token_count` and `size_category` metadata for each file, and how split modules reduce context pressure by loading only the current phase
- [x] 8.5 Create an ASCII diagram showing the budget state transitions (normal → warn → critical) with actions at each transition

## Task 9: Update documentation indexes

- [x] 9.1 Update `senzing-bootcamp/docs/guides/README.md` to add ARCHITECTURE.md in the Reference Documentation section with a description
- [x] 9.2 Update `senzing-bootcamp/docs/README.md` to add ARCHITECTURE.md in the `/guides/` file listing

## Task 10: Validate the document

- [x] 10.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` against the new ARCHITECTURE.md file and fix any CommonMark violations
- [x] 10.2 Verify all relative links in ARCHITECTURE.md point to existing files
- [x] 10.3 Verify no line in the document exceeds 120 characters
