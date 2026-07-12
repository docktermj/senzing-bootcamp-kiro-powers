# Requirements Document

## Introduction

This spec defines a Kiro-native **Session Handoff** capability tailored for the senzing-bootcamp Kiro Power. The capability produces a repeatable, fixed-structure end-of-session summary so a User can clear the conversation context and start a fresh Agent instance — or hand the bootcamp off to a teammate — without losing continuity. The Handoff_Summary is a context-handoff artifact addressed to a future Agent instance, not a stakeholder status report; a fresh Agent should be able to resume the bootcamp by reading the Handoff_Summary alongside the power's persisted state files.

The capability was adapted from a generic Claude Skill, but it is re-anchored to the bootcamp's concrete session model: an 11-module guided course whose durable state already persists across sessions in `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `config/mapping_state_*.json`, `config/session_log.jsonl`, `config/.question_pending`, and the recap/certificate artifacts under `docs/`. The bootcamp also has live runtime concerns — the Senzing MCP connection, a local visualization web service, and the SQLite or PostgreSQL database — that a fresh session must re-establish.

The Session_Handoff **coordinates with, and does not duplicate or override**, two existing mechanisms. `session-resume.md` already reconstructs persisted state at the start of the next session; the Session_Handoff surfaces that same state plus the in-session decisions and open questions that are not written to any file. `agent-context-management.md` already defines a context-reset message that instructs the learner to open a fresh chat and paste a Continuation_Phrase naming the current module (for example "continue the bootcamp from module 5"); the Session_Handoff reuses that phrase and module convention rather than inventing a new resume mechanism. The module-completion workflow (`module-completion-artifacts.md`) remains the sole writer of recap, certificate, and progress artifacts; the Session_Handoff references those files but never rewrites them.

Within this repo the capability is delivered as distributable power content (manual-invocation steering, optionally paired with a trigger hook) that conforms to the power's tech, structure, and security constraints.

## Glossary

- **Session_Handoff**: The capability that produces an end-of-session handoff summary for a future Agent instance of the bootcamp.
- **Handoff_Summary**: The structured, chat-only artifact produced by the Session_Handoff.
- **Agent**: The AI assistant (Kiro) operating within the senzing-bootcamp power.
- **User**: The person interacting with the Agent (a Bootcamper or a developer).
- **Current_Session**: The active conversation, from the start of the conversation to the moment the Session_Handoff is invoked.
- **Trigger_Phrase**: A recognized phrase or near-equivalent request that invokes the Session_Handoff (for example "session handoff", "wrap up session", "hand off", "handoff summary", "summarize before I clear").
- **Section**: One named part of the Handoff_Summary (for example "Running state").
- **Progress_File**: The primary state file `config/bootcamp_progress.json`, containing `current_module`, `modules_completed`, `current_step`, `step_history`, loaded data sources, database type, and `started_at`.
- **Preferences_File**: The state file `config/bootcamp_preferences.yaml`, containing `language`, `track`, `verbosity`/`conversation_style`, cloud provider, license info, `hooks_installed`, and `show_whats_new`.
- **Recap_File**: The consolidated per-module recap `docs/bootcamp_recap.md`, including its `### Journal` subsection.
- **Mapping_Checkpoint**: An in-progress data-mapping checkpoint file matching `config/mapping_state_*.json` (Module 5).
- **Session_Log**: The analytics file `config/session_log.jsonl` recording turns and corrections for adaptive pacing.
- **Pending_Question**: The marker file `config/.question_pending` holding a pending 👉 question awaiting the learner's answer.
- **Current_Module**: The module the Current_Session is working in, read from the `current_module` field of the Progress_File.
- **Current_Step**: The step or sub-step within the Current_Module, read from the `current_step` field of the Progress_File (an integer or a sub-step string such as `"5.3"` or `"7a"`).
- **Track**: The chosen bootcamp track recorded in the Preferences_File.
- **Language**: The chosen implementation language (python, java, csharp, rust, or typescript) recorded in the Preferences_File.
- **MCP_Session**: The connection to the Senzing MCP server at `mcp.senzing.com`, re-established at the start of every new session by calling `get_capabilities`.
- **Visualization_Service**: The local visualization web service (Modules 3 and 7) that runs on a local port as a background process.
- **Background_Process**: Any process started during the Current_Session that continues running after an Agent turn ends, including the Visualization_Service and any data-loading process, identified by a process identifier and, where applicable, a port.
- **Continuation_Phrase**: The resume phrase defined by the context-reset message in `agent-context-management.md`, naming the Current_Module (for example "continue the bootcamp from module 5").
- **Context_Reset_Message**: The context-reset communication defined in `agent-context-management.md` that tells the learner to open a fresh chat and paste the Continuation_Phrase.
- **Session_Resume_Workflow**: The behavior defined in `session-resume.md` that reconstructs persisted state at the start of the next session.
- **Driving_Artifact**: The plan, spec, or module document that primarily guided the work of the Current_Session, when one exists.
- **Steering_Index**: The registry file `senzing-bootcamp/steering/steering-index.yaml` that maps steering files and records token counts.

## Requirements

### Requirement 1: Handoff Invocation

**User Story:** As a User wrapping up a bootcamp session, I want a handoff summary produced when I ask for one or when I am about to clear context, so that I do not lose session continuity.

#### Acceptance Criteria

1. WHEN the User submits a message containing a Trigger_Phrase, THE Session_Handoff SHALL produce a Handoff_Summary.
2. WHEN the User states an intent to clear the Current_Session context before a Handoff_Summary has been produced, THE Session_Handoff SHALL offer to produce a Handoff_Summary before the context is cleared.
3. WHEN the Agent emits a Context_Reset_Message, THE Session_Handoff SHALL offer to produce a Handoff_Summary before the User opens a fresh chat.
4. WHERE the Current_Session contains no recorded work, decisions, or touched artifacts, THE Session_Handoff SHALL produce a Handoff_Summary containing every Section with "none" recorded for each Section that has no content.

### Requirement 2: Session-Scoped Synthesis

**User Story:** As a future Agent instance, I want the handoff to reflect only the current session, so that the summary is accurate and free of unrelated repository state.

#### Acceptance Criteria

1. THE Session_Handoff SHALL derive Handoff_Summary content exclusively from the Current_Session conversation and the artifacts the Agent created or modified during the Current_Session.
2. THE Session_Handoff SHALL construct the Handoff_Summary using in-session context only, excluding version-control history queries and repository-wide file searches.
3. THE Session_Handoff SHALL base the Handoff_Summary on the full Current_Session conversation rather than only the most recent turns.

### Requirement 3: Bootcamp State Sources

**User Story:** As a future Agent instance resuming the bootcamp, I want the handoff to capture all load-bearing session state, so that I can continue the course without re-discovering context.

#### Acceptance Criteria

1. THE Session_Handoff SHALL collect the Current_Module, the Current_Step, and the completed modules of the Current_Session.
2. THE Session_Handoff SHALL collect the active Track and the active Language of the Current_Session.
3. THE Session_Handoff SHALL collect the data sources loaded and the database type of the Current_Session.
4. THE Session_Handoff SHALL collect the generated code artifacts produced during the Current_Session.
5. THE Session_Handoff SHALL collect each active Mapping_Checkpoint of the Current_Session.
6. THE Session_Handoff SHALL collect the MCP_Session connection status of the Current_Session.
7. THE Session_Handoff SHALL collect each Visualization_Service and Background_Process started during the Current_Session together with the port of each Visualization_Service.
8. WHERE a Pending_Question exists, THE Session_Handoff SHALL collect the text of the Pending_Question.
9. THE Session_Handoff SHALL collect the in-session decisions and unresolved questions of the Current_Session that are not recorded in the Progress_File, the Preferences_File, a Mapping_Checkpoint, or the Recap_File.

### Requirement 4: Output Structure and Ordering

**User Story:** As a future Agent instance, I want every handoff to use the same section layout, so that I can locate information predictably regardless of session content.

#### Acceptance Criteria

1. THE Handoff_Summary SHALL contain the following Sections in exactly this order: (1) Title, (2) "Where it started", (3) "Decisions locked + what shipped", (4) "Key files for next session", (5) "Running state", (6) "Verification — how to confirm things still work", (7) "Deferred + open questions", (8) "Pick up here".
2. THE Title SHALL state the subject of the Current_Session in one line.
3. IF a Section has no content to report, THEN THE Session_Handoff SHALL include that Section and record "none" as the content of that Section.
4. THE "Pick up here" Section SHALL contain a single most-likely next action for a fresh Agent instance.

### Requirement 5: Content Precision Rules

**User Story:** As a future Agent instance that may run from a different working directory, I want file references and running state to be unambiguous, so that I can act on the handoff without guesswork.

#### Acceptance Criteria

1. THE Session_Handoff SHALL express every file reference in the Handoff_Summary as an absolute path.
2. WHERE a Driving_Artifact guided the Current_Session, THE Session_Handoff SHALL list the Driving_Artifact as the first entry in the "Key files for next session" Section.
3. WHEN one or more Visualization_Services or Background_Processes are reported in the "Running state" Section, THE Session_Handoff SHALL include, for each one, its port where applicable and the command that stops it.
4. THE "Running state" Section SHALL record the database as an absolute SQLite file path or as a PostgreSQL connection description.
5. THE "Running state" Section SHALL record the MCP_Session connection status.

### Requirement 6: Verification Guidance

**User Story:** As a future Agent instance, I want bootcamp-specific verification steps in the handoff, so that I can confirm the environment is healthy before continuing.

#### Acceptance Criteria

1. THE Session_Handoff SHALL populate the "Verification — how to confirm things still work" Section with commands paired with the expected outcome of each command.
2. THE "Verification — how to confirm things still work" Section SHALL include the instruction to re-establish the MCP_Session by calling `get_capabilities` together with the expected outcome of a reachable MCP server.
3. THE "Verification — how to confirm things still work" Section SHALL include the read-only command `python3 senzing-bootcamp/scripts/baseline_status.py` together with its expected data-source coverage report.
4. THE "Verification — how to confirm things still work" Section SHALL include a check that the Current_Module artifacts exist together with the expected outcome of that check.

### Requirement 7: Pick Up Here and Continuation Phrase

**User Story:** As a future Agent instance, I want the handoff to point me at the exact resume phrase, so that the User can restart the bootcamp in a fresh chat with no ambiguity.

#### Acceptance Criteria

1. THE "Pick up here" Section SHALL present the Continuation_Phrase naming the Current_Module read from the Progress_File.
2. THE "Pick up here" Section SHALL enclose the Continuation_Phrase in quotation marks.
3. THE "Pick up here" Section SHALL reuse the Continuation_Phrase convention defined by the Context_Reset_Message rather than introducing a new resume mechanism.
4. THE "Pick up here" Section SHALL exclude the temporal phrases "come back later", "come back tomorrow", "take a break", "try again in a while", "when you're ready", "try again later", "wait a moment", and "give it some time".

### Requirement 8: Coordination With Existing Mechanisms

**User Story:** As a power maintainer, I want the handoff to complement session-resume and the completion workflow, so that state is surfaced once without duplicating or corrupting persisted files.

#### Acceptance Criteria

1. THE Session_Handoff SHALL surface the persisted state that the Session_Resume_Workflow reconstructs together with the in-session decisions and open questions that are not stored in the Progress_File, the Preferences_File, a Mapping_Checkpoint, or the Recap_File.
2. THE Session_Handoff SHALL leave the Progress_File, the Preferences_File, and the Recap_File unmodified.
3. WHERE the module-completion workflow has written recap, certificate, or progress artifacts, THE Session_Handoff SHALL reference those artifacts by absolute path rather than rewriting them.
4. THE Session_Handoff SHALL reuse the Continuation_Phrase and Current_Module convention defined by the Context_Reset_Message.

### Requirement 9: Tone and Content Discipline

**User Story:** As a future Agent instance, I want a terse, factual handoff, so that I get actionable state without noise.

#### Acceptance Criteria

1. THE Session_Handoff SHALL write the Handoff_Summary in a terse, concrete engineering tone.
2. THE Session_Handoff SHALL exclude emojis, celebratory language, and retrospective commentary from the Handoff_Summary.
3. THE Session_Handoff SHALL limit forward-looking recommendations to the single action recorded in the "Pick up here" Section.
4. THE Session_Handoff SHALL record only state observed during the Current_Session, recording "none" for a Section rather than inferred or assumed content.

### Requirement 10: Output Destination

**User Story:** As a User, I want the handoff delivered in chat by default and never written to a file without my say-so, so that no artifact is created behind my back.

#### Acceptance Criteria

1. THE Session_Handoff SHALL deliver the Handoff_Summary as chat output in the Current_Session.
2. IF the User has not explicitly requested that the Handoff_Summary be saved to a file, THEN THE Session_Handoff SHALL write no Handoff_Summary file and SHALL leave the Progress_File, the Preferences_File, the Recap_File, and all steering files unmodified.
3. WHERE the User explicitly requests that the Handoff_Summary be saved, THE Session_Handoff SHALL write the Handoff_Summary to the User-specified absolute path and report the written path.

### Requirement 11: Kiro Power Packaging Conformance

**User Story:** As a power maintainer, I want the handoff capability delivered as conformant power content, so that the capability ships cleanly and passes CI validation.

#### Acceptance Criteria

1. THE Session_Handoff SHALL be delivered as manual-invocation steering content located in `senzing-bootcamp/steering/` with a kebab-case filename and YAML frontmatter containing an `inclusion` key set to `manual` and a `description` key.
2. WHEN the Session_Handoff steering content is added, THE Session_Handoff steering content SHALL be registered in the Steering_Index with a recorded token count.
3. THE Session_Handoff content SHALL exclude personally identifiable information, credentials, and internal-only URLs.
4. THE Session_Handoff content SHALL reference `mcp.senzing.com` as the only external endpoint.
5. WHERE the Session_Handoff includes an executable script, THE script SHALL use only the Python standard library.
6. WHERE the Session_Handoff is triggered by a Kiro hook, THE hook SHALL conform to the `v1` JSON schema with `name`, `trigger`, and `action` fields and SHALL remain synchronized with the hook registry.
