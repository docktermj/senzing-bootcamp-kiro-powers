# Requirements Document

## Introduction

The bootcamp currently tracks module completion via `config/bootcamp_progress.json`, recording which modules are done and the current step. However, it captures no session-level data — how long each module took, how many corrections the bootcamper made, or which steps caused confusion. This feature adds a lightweight append-only log at `config/session_log.jsonl` that the agent writes to on each turn, plus an analysis script that reads the log and produces a summary report. The goal is to give bootcamp maintainers data to identify which modules need the most improvement.

The scope covers three areas: (1) the logging mechanism that appends entries, (2) the JSONL log format and its schema, and (3) a Python analysis script that reads the log and produces a summary report.

## Glossary

- **Session_Logger**: The Python module (`scripts/session_logger.py`) that appends structured entries to the session log file.
- **Session_Log**: The append-only JSONL file at `config/session_log.jsonl` in the bootcamper's project directory, where each line is a self-contained JSON object representing one logged event.
- **Log_Entry**: A single JSON object written as one line in the Session_Log, containing fields that describe an agent turn or session event.
- **Turn**: A single agent interaction cycle — the agent receives input, processes it, and produces a response. Each turn that modifies session state generates one Log_Entry.
- **Correction**: An agent turn where the bootcamper's previous work is revised, a mistake is identified, or the agent re-explains a concept the bootcamper misunderstood.
- **Analysis_Script**: The Python script (`scripts/analyze_sessions.py`) that reads the Session_Log and produces a summary report.
- **Summary_Report**: The structured output produced by the Analysis_Script, containing per-module statistics such as total time, turn count, and correction count.
- **Agent**: The AI agent that guides the bootcamper through modules and invokes the Session_Logger.
- **Bootcamper**: The user completing the Senzing bootcamp.

## Requirements

### Requirement 1: Append Log Entries to the Session Log

**User Story:** As a bootcamp maintainer, I want the agent to append a structured log entry on each relevant turn, so that I have raw data about how bootcampers progress through modules.

#### Acceptance Criteria

1. WHEN the Agent completes a turn within a bootcamp module, THE Session_Logger SHALL append exactly one Log_Entry as a single line to the Session_Log file.
2. WHEN the Session_Log file does not exist, THE Session_Logger SHALL create the file and its parent directory before appending the first Log_Entry.
3. WHEN the Session_Log file already exists, THE Session_Logger SHALL append to the end of the file without modifying existing lines.
4. IF the Session_Logger encounters a file-system error while writing, THEN THE Session_Logger SHALL log a warning to stderr and continue without interrupting the bootcamp session.
5. THE Session_Logger SHALL write each Log_Entry as valid JSON followed by a newline character, conforming to the JSONL format.

### Requirement 2: Define the Log Entry Schema

**User Story:** As a bootcamp maintainer, I want each log entry to contain a consistent set of fields, so that the analysis script can reliably parse and aggregate the data.

#### Acceptance Criteria

1. THE Log_Entry SHALL contain a `timestamp` field with an ISO 8601 UTC datetime string.
2. THE Log_Entry SHALL contain a `session_id` field with a string identifier that remains constant across all entries within a single agent session and changes when a new session begins.
3. THE Log_Entry SHALL contain a `module` field with an integer from 1 to 11 representing the current bootcamp module number.
4. THE Log_Entry SHALL contain a `step` field with a string or integer identifying the current step within the module.
5. THE Log_Entry SHALL contain an `event` field with a string value from the set: `turn`, `correction`, `module_start`, `module_complete`.
6. THE Log_Entry SHALL contain a `duration_seconds` field with a non-negative numeric value representing the elapsed time in seconds since the previous Log_Entry in the same session, or zero for the first entry in a session.
7. THE Log_Entry SHALL contain a `message` field with a short free-text summary of what occurred during the turn.

### Requirement 3: Parse the Session Log (Round-Trip Safe)

**User Story:** As a bootcamp maintainer, I want the analysis script to parse every line of the session log back into structured objects, so that no data is lost between writing and reading.

#### Acceptance Criteria

1. WHEN the Analysis_Script reads the Session_Log, THE Analysis_Script SHALL parse each line as an independent JSON object.
2. IF a line in the Session_Log is not valid JSON, THEN THE Analysis_Script SHALL skip that line, increment a parse-error counter, and continue processing remaining lines.
3. THE Analysis_Script SHALL accept a file path argument specifying the Session_Log location, defaulting to `config/session_log.jsonl` when no argument is provided.
4. FOR ALL valid Log_Entry objects, writing a Log_Entry with the Session_Logger and then parsing the resulting line with the Analysis_Script SHALL produce a dictionary with identical field names and values (round-trip property).

### Requirement 4: Produce a Per-Module Summary Report

**User Story:** As a bootcamp maintainer, I want the analysis script to produce per-module statistics, so that I can identify which modules take the longest and cause the most corrections.

#### Acceptance Criteria

1. THE Summary_Report SHALL include, for each module present in the Session_Log, the total number of turns, the total number of corrections, and the total elapsed time in seconds.
2. THE Summary_Report SHALL list modules in ascending order by module number.
3. THE Summary_Report SHALL include a row or section for overall totals across all modules.
4. WHEN the Session_Log contains entries from multiple sessions, THE Summary_Report SHALL aggregate data across all sessions for each module.
5. WHEN the Session_Log is empty or contains no valid entries, THE Summary_Report SHALL indicate that no data is available rather than producing an error.

### Requirement 5: Produce a Confusion-Indicator Ranking

**User Story:** As a bootcamp maintainer, I want the analysis script to rank modules by a confusion indicator, so that I can prioritize which modules to improve first.

#### Acceptance Criteria

1. THE Summary_Report SHALL include a ranking of modules sorted by correction density, defined as the number of corrections divided by the number of turns for that module.
2. WHEN a module has zero turns, THE Analysis_Script SHALL exclude that module from the confusion ranking rather than dividing by zero.
3. THE Summary_Report SHALL display the correction density as a decimal value rounded to two decimal places for each ranked module.

### Requirement 6: Support Multiple Output Formats

**User Story:** As a bootcamp maintainer, I want the analysis script to output the summary as either plain text or JSON, so that I can read it directly or feed it into other tools.

#### Acceptance Criteria

1. WHEN the `--format text` option is provided, THE Analysis_Script SHALL write the Summary_Report to stdout as a human-readable plain-text table.
2. WHEN the `--format json` option is provided, THE Analysis_Script SHALL write the Summary_Report to stdout as a single valid JSON object.
3. WHEN no `--format` option is provided, THE Analysis_Script SHALL default to plain-text output.
4. THE Analysis_Script SHALL accept an optional `--output` argument specifying a file path, and write the Summary_Report to that file instead of stdout.

### Requirement 7: Pretty-Print Log Entries

**User Story:** As a bootcamp maintainer, I want a way to pretty-print individual log entries, so that I can inspect the raw log in a readable format during debugging.

#### Acceptance Criteria

1. WHEN the Analysis_Script is invoked with the `--pretty` flag, THE Analysis_Script SHALL read the Session_Log and print each valid Log_Entry as indented JSON (2-space indent) separated by a blank line.
2. WHEN the `--pretty` flag is combined with a `--module N` filter, THE Analysis_Script SHALL print only Log_Entries where the `module` field equals N.
3. FOR ALL valid Log_Entry objects, pretty-printing a Log_Entry and then stripping whitespace and re-parsing SHALL produce a dictionary identical to the original Log_Entry (round-trip property).
