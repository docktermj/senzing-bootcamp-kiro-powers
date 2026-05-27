# Requirements Document

## Introduction

The completion-summary feature transforms the bootcamp completion experience into a comprehensive, automatically-generated narrative PDF that records the entire bootcamp journey. Rather than producing a static project summary, the system maintains a progressive session log throughout the bootcamp and, at every natural stopping point, offers to render it as a ready-to-use PDF document. The PDF reads as a chronological liturgy — a structured record of questions asked, answers given, actions taken, and artifacts produced — organized by module.

## Glossary

- **Session_Logger**: The component that progressively accumulates bootcamp interaction events (questions, answers, actions, artifacts) into a structured log file during the session
- **Completion_Detector**: The component that identifies natural stopping points (end of core bootcamp, end of advanced track, or explicit bootcamper request to stop)
- **Summary_Offer_Presenter**: The component that presents the non-optional offer to generate a completion summary PDF at every detected stopping point
- **Narrative_Formatter**: The component that transforms the accumulated session log into a chronological, module-structured narrative markdown document
- **PDF_Generator**: The component that converts the formatted narrative markdown into a PDF file without requiring manual bootcamper intervention
- **Session_Log**: The structured JSONL file (`config/session_log.jsonl`) that stores progressive interaction events
- **Completion_Summary**: The final PDF document containing the narrative record of the bootcamp journey
- **Stopping_Point**: A moment where the bootcamper has reached a natural pause — end of core bootcamp (Module 7), end of advanced track (Module 11), or an explicit "stop here" request
- **Narrative_Section**: A per-module block in the completion summary containing questions asked, answers given, actions taken, and artifacts created
- **Bootcamper**: The user progressing through the Senzing bootcamp

## Requirements

### Requirement 1: Progressive Session Logging

**User Story:** As a bootcamper, I want my bootcamp interactions to be recorded progressively throughout the session, so that the completion summary reflects what actually happened rather than a reconstruction from memory.

#### Acceptance Criteria

1. WHEN the agent poses a question to the Bootcamper that requests information needed to proceed with the current module, THE Session_Logger SHALL append a question event to the Session_Log containing the question text (maximum 2000 characters), module number (1–11), and ISO 8601 UTC timestamp
2. WHEN the Bootcamper provides a response to an agent question, THE Session_Logger SHALL append an answer event to the Session_Log containing the response text (maximum 5000 characters), the originating question event's timestamp as the question reference, module number (1–11), and ISO 8601 UTC timestamp
3. WHEN the agent creates, modifies, or deletes a file, THE Session_Logger SHALL append an action event to the Session_Log containing the action type (one of "create", "modify", or "delete"), file path, description (maximum 500 characters), module number (1–11), and ISO 8601 UTC timestamp
4. WHEN the agent executes a command or invokes an MCP tool, THE Session_Logger SHALL append an action event to the Session_Log containing the command or tool name, description (maximum 500 characters), module number (1–11), and ISO 8601 UTC timestamp
5. WHEN an artifact is produced during a module (script, configuration file, data file, or report), THE Session_Logger SHALL append an artifact event to the Session_Log containing the file path, artifact type (one of "script", "configuration", "data", or "report"), description (maximum 500 characters), module number (1–11), and ISO 8601 UTC timestamp
6. THE Session_Logger SHALL write events to `config/session_log.jsonl` in append-only JSONL format with one JSON object per line
7. IF the Session_Log file does not exist when an event occurs, THEN THE Session_Logger SHALL create the file and any missing parent directories before writing the first event
8. IF a write to the Session_Log fails due to a file system error, THEN THE Session_Logger SHALL emit a warning to stderr indicating the failure reason and continue the bootcamp flow without blocking execution
9. IF the question text, response text, or description exceeds its maximum character limit, THEN THE Session_Logger SHALL truncate the value to the maximum length before writing the event

### Requirement 2: Stopping Point Detection

**User Story:** As a bootcamper, I want the system to recognize when I've reached a natural stopping point, so that I am always offered a completion summary without having to ask for it.

#### Acceptance Criteria

1. WHEN the Bootcamper completes Module 7 (end of core bootcamp track), as indicated by Module 7 appearing in the `modules_completed` array of the Progress_File, THE Completion_Detector SHALL identify a Stopping_Point within the same agent turn that the module completion is recorded
2. WHEN the Bootcamper completes Module 11 (end of advanced track), as indicated by Module 11 appearing in the `modules_completed` array of the Progress_File, THE Completion_Detector SHALL identify a Stopping_Point within the same agent turn that the module completion is recorded
3. WHEN the Bootcamper explicitly requests to stop by sending a message whose primary intent is to end the session (matching phrases such as "stop here", "I'm done", "that's enough", "wrap up", "let's stop", "I want to stop", or semantically equivalent statements), THE Completion_Detector SHALL identify a Stopping_Point
4. WHEN the Bootcamper switches tracks at a track boundary (Module 7 for core-to-advanced, or any module endpoint defined by the track_switcher script), THE Completion_Detector SHALL identify a Stopping_Point for the completed track before the track switch is applied
5. IF the Progress_File (`config/bootcamp_progress.json`) is unreadable or missing when the Completion_Detector checks for module completion, THEN THE Completion_Detector SHALL not identify a Stopping_Point and SHALL log a warning without interrupting the bootcamp flow
6. IF the Bootcamper's message contains a stop phrase embedded within a longer substantive request (e.g., "I'm done with this module, let's move to the next one"), THEN THE Completion_Detector SHALL not identify a Stopping_Point from the stop phrase alone

### Requirement 3: Mandatory Summary Offer

**User Story:** As a bootcamper, I want to always be offered a completion summary at every stopping point, so that I never miss the opportunity to capture my bootcamp journey.

#### Acceptance Criteria

1. WHEN a Stopping_Point is detected, THE Summary_Offer_Presenter SHALL present the offer to generate a Completion_Summary PDF before any other post-completion options
2. THE Summary_Offer_Presenter SHALL present the offer as a single message that names the deliverable ("Completion Summary PDF") and lists the four content categories it contains (questions asked, answers given, actions taken, and artifacts created, organized by module)
3. THE Summary_Offer_Presenter SHALL present the offer at every Stopping_Point regardless of whether a previous summary was generated earlier in the session
4. THE Summary_Offer_Presenter SHALL present the offer as a binary yes/no prompt that requires the Bootcamper to explicitly accept or decline before the post-completion flow continues
5. IF the Bootcamper declines the summary offer, THEN THE Summary_Offer_Presenter SHALL proceed to the next post-completion step without generating any summary file and without re-prompting for the same Stopping_Point
6. IF the Bootcamper accepts the summary offer, THEN THE Summary_Offer_Presenter SHALL invoke the Narrative_Formatter followed by the PDF_Generator

### Requirement 4: Narrative Formatting

**User Story:** As a bootcamper, I want my completion summary to read as a chronological narrative of my bootcamp experience, so that it serves as a meaningful record of what I learned and decided.

#### Acceptance Criteria

1. WHEN the Narrative_Formatter is invoked, THE Narrative_Formatter SHALL read the Session_Log at `config/session_log.jsonl` and organize events chronologically by module number in ascending order
2. THE Narrative_Formatter SHALL produce a Narrative_Section for each completed module that contains four subsections: Questions Asked, Answers Given, Actions Taken, and Artifacts Created, derived from the `message` field of session log entries categorized by `event` type
3. THE Narrative_Formatter SHALL maintain one-to-one correspondence between questions and answers within each module section, and IF a question has no corresponding answer in the session log, THEN THE Narrative_Formatter SHALL display the question with a placeholder indicating no answer was recorded
4. THE Narrative_Formatter SHALL include a cover section containing the bootcamper name, bootcamp start date, completion date, total duration displayed as days and hours, and track completed
5. THE Narrative_Formatter SHALL include a summary statistics section containing total modules completed, total artifacts produced, and entity resolution results (entity count, dedup rate, cross-source matches) when those fields are present in session log entries for modules that performed entity resolution
6. WHEN the output path `docs/completion_summary.md` already exists, THE Narrative_Formatter SHALL overwrite the existing file with the newly generated narrative
7. IF the Session_Log contains no events for a module that was completed, THEN THE Narrative_Formatter SHALL include that module with a note indicating the session log was unavailable for that module
8. THE Narrative_Formatter SHALL exclude secrets, credentials, environment variable values, and connection strings from the narrative content by omitting any session log message content that matches key=value patterns where the key contains "secret", "password", "token", "key", "credential", or "connection_string"
9. IF the Session_Log file does not exist or cannot be parsed, THEN THE Narrative_Formatter SHALL produce an error message indicating the session log is unavailable and SHALL NOT write a partial narrative to the output path
10. THE Narrative_Formatter SHALL produce a narrative document not exceeding 500 kilobytes in total size, truncating individual module sections from the earliest entries if the limit would be exceeded

### Requirement 5: Automatic PDF Generation

**User Story:** As a bootcamper, I want the completion summary delivered as a ready-to-use PDF without running any commands myself, so that I can immediately share it with my team.

#### Acceptance Criteria

1. WHEN the Narrative_Formatter completes successfully, THE PDF_Generator SHALL convert `docs/completion_summary.md` into `docs/completion_summary.pdf` without requiring bootcamper intervention
2. THE PDF_Generator SHALL render the PDF with a cover page where the bootcamper name, dates, duration, and track information are each on separate lines with the title rendered in a larger font size than the body fields
3. THE PDF_Generator SHALL render each module Narrative_Section on its own page with headings rendered in a larger font size than body text, numbered lists for questions and answers, and bulleted lists for actions and artifacts
4. THE PDF_Generator SHALL handle inline code references (backtick content) using a monospace font in the PDF output
5. IF the fpdf2 library is not installed, THEN THE PDF_Generator SHALL attempt to install it using `pip install fpdf2` with a timeout of 30 seconds before rendering
6. IF the fpdf2 library cannot be installed within the timeout and no system-level PDF command-line tool (such as pandoc or wkhtmltopdf) is available on PATH, THEN THE PDF_Generator SHALL inform the Bootcamper that the markdown file is available at `docs/completion_summary.md` and provide the single command needed to install fpdf2
7. WHEN the PDF is generated successfully, THE PDF_Generator SHALL display the output path to the Bootcamper with a confirmation message
8. IF PDF generation fails for any reason after installation attempts, THEN THE PDF_Generator SHALL inform the Bootcamper of the failure, provide the markdown file path as a fallback, and continue the post-completion flow without blocking
9. IF `docs/completion_summary.md` exists but contains no Narrative_Section content, THEN THE PDF_Generator SHALL inform the Bootcamper that the session log contained insufficient data to generate a PDF and provide the markdown file path as a fallback

### Requirement 6: Session Log Schema

**User Story:** As a developer, I want the session log to follow a consistent schema, so that the narrative formatter can reliably parse and organize events.

#### Acceptance Criteria

1. THE Session_Logger SHALL write each event as a JSON object containing the fields: `event_type`, `module`, `timestamp` (ISO 8601 format in UTC), and `data`
2. THE Session_Logger SHALL use one of the following values for `event_type`: `question`, `answer`, `action`, `artifact`
3. WHEN the event_type is `question`, THE Session_Logger SHALL include in the `data` field: `text` (the question posed) and `question_id` (a string unique within the session log file, used to correlate answers to their originating question)
4. WHEN the event_type is `answer`, THE Session_Logger SHALL include in the `data` field: `text` (the bootcamper response) and `question_id` (matching the `question_id` of the corresponding question event in the same session log)
5. WHEN the event_type is `action`, THE Session_Logger SHALL include in the `data` field: `action_type` (one of: file_create, file_modify, file_delete, command_run, mcp_tool_call), `description`, and `file_path` (required when action_type is file_create, file_modify, or file_delete; omitted otherwise)
6. WHEN the event_type is `artifact`, THE Session_Logger SHALL include in the `data` field: `file_path`, `artifact_type` (one of: script, config, data, report, visualization), and `description`
7. THE Session_Logger SHALL write the `module` field as an integer in the range 0–11, where 0 represents events occurring outside a module context (such as onboarding) and 1–11 correspond to the bootcamp module numbers
8. IF an event JSON object is missing any of the required fields (`event_type`, `module`, `timestamp`, `data`), THEN THE Session_Logger SHALL reject the entry and not write it to the session log

### Requirement 7: Integration with Existing Completion Workflow

**User Story:** As a bootcamper, I want the completion summary offer to integrate smoothly with the existing module completion and graduation workflows, so that the experience feels cohesive rather than disjointed.

#### Acceptance Criteria

1. WHEN a track completion Stopping_Point is detected, THE Summary_Offer_Presenter SHALL present the summary offer after the track completion celebration message and before the export results offer; IF the export results offer is not available, THEN THE Summary_Offer_Presenter SHALL present the summary offer as the next step after the celebration message
2. WHEN a mid-session Stopping_Point is detected (bootcamper says "stop here"), THE Summary_Offer_Presenter SHALL present the summary offer as the next agent message after acknowledging the stop request, with no intervening prompts or offers between the acknowledgment and the summary offer
3. THE Summary_Offer_Presenter SHALL source all completion summary content exclusively from the Session_Log (`config/session_log.jsonl`) and SHALL NOT read from or reference `docs/bootcamp_recap.md` when constructing the summary narrative
4. IF the graduation workflow has already generated `docs/bootcamp_recap.pdf`, THEN THE PDF_Generator SHALL generate the completion summary as a separate file (`docs/completion_summary.pdf`) without overwriting the recap PDF
5. IF both a track completion Stopping_Point and a mid-session Stopping_Point are detected for the same event (bootcamper says "stop here" at a track boundary), THEN THE Summary_Offer_Presenter SHALL follow the track completion sequence (celebration message first, then summary offer) rather than the mid-session sequence
