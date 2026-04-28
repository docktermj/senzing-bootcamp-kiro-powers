# Requirements Document

## Introduction

The senzing-bootcamp power currently ships two overlapping environment-check scripts — `check_prerequisites.py` (tool/directory/config checks with colored output) and `preflight_check.py` (runtime/disk/memory/permissions checks with emoji output). Neither is wired into the onboarding flow as a mandatory gate; the agent runs ad-hoc checks in Step 3 of `onboarding-flow.md` using inline `shutil.which()` calls. This feature consolidates both scripts into a single `preflight.py` that runs every check (language runtime, disk space, network connectivity to `mcp.senzing.com`, Senzing SDK availability with version detection, write permissions, required tools), produces a structured pass/warn/fail report with actionable fix instructions, supports `--json` output for programmatic consumption and `--fix` for auto-remediation of simple issues, and is integrated into the onboarding flow as a mandatory pre-track-selection gate.

## Glossary

- **Preflight_Script**: The consolidated Python script at `senzing-bootcamp/scripts/preflight.py` that performs all environment verification checks.
- **Check_Result**: A single verification outcome containing a check name, status (pass, warn, or fail), a human-readable message, and an optional fix instruction.
- **Preflight_Report**: The ordered collection of all Check_Results produced by a single invocation of the Preflight_Script, including a summary with total pass, warn, and fail counts and an overall verdict.
- **Overall_Verdict**: A single value — PASS, WARN, or FAIL — derived from the worst individual Check_Result status in the Preflight_Report.
- **Fix_Instruction**: A human-readable string attached to a Check_Result that tells the user exactly how to resolve the issue (install command, configuration step, or manual action).
- **Auto_Fix**: An automated remediation action the Preflight_Script performs when invoked with the `--fix` flag, limited to safe, idempotent operations such as creating missing directories.
- **Onboarding_Gate**: The mandatory step in `onboarding-flow.md` where the Preflight_Script runs and must produce a non-FAIL Overall_Verdict before the bootcamper proceeds to track selection.
- **MCP_Endpoint**: The Senzing MCP server at `mcp.senzing.com:443` that the bootcamp connects to for tools and workflows.
- **Senzing_SDK**: The Senzing entity resolution SDK whose importability and version the Preflight_Script verifies.

## Requirements

### Requirement 1: Consolidated Preflight Script

**User Story:** As a bootcamp maintainer, I want a single preflight script that replaces both `check_prerequisites.py` and `preflight_check.py`, so that environment verification logic lives in one place and is easier to maintain.

#### Acceptance Criteria

1. THE Preflight_Script SHALL reside at `senzing-bootcamp/scripts/preflight.py`.
2. THE Preflight_Script SHALL perform all checks previously performed by `check_prerequisites.py` and `preflight_check.py` without requiring either script to be present.
3. THE Preflight_Script SHALL depend only on the Python standard library (no third-party packages).
4. THE Preflight_Script SHALL be cross-platform, supporting Linux, macOS, and Windows.

### Requirement 2: Language Runtime Check

**User Story:** As a bootcamper, I want the preflight to detect which language runtimes are installed, so that I know whether I can proceed with my chosen language.

#### Acceptance Criteria

1. THE Preflight_Script SHALL check for the presence of Python (python3 or python), Java, .NET SDK (dotnet), Rust (rustc), and Node.js (node) using `shutil.which`.
2. WHEN at least one supported language runtime is found, THE Preflight_Script SHALL produce a pass Check_Result listing each detected runtime and its version string.
3. WHEN no supported language runtime is found, THE Preflight_Script SHALL produce a fail Check_Result with a Fix_Instruction listing installation URLs for each supported runtime.
4. WHEN a Python runtime is found, THE Preflight_Script SHALL additionally check for pip (pip3 or pip) and produce a warn Check_Result if pip is absent.

### Requirement 3: Disk Space Check

**User Story:** As a bootcamper, I want the preflight to verify I have enough disk space, so that I do not run out of space mid-bootcamp.

#### Acceptance Criteria

1. THE Preflight_Script SHALL check available disk space in the current working directory using `shutil.disk_usage`.
2. WHEN available disk space is 10 GB or more, THE Preflight_Script SHALL produce a pass Check_Result reporting the available space.
3. WHEN available disk space is less than 10 GB, THE Preflight_Script SHALL produce a warn Check_Result reporting the available space and recommending 10 GB or more.
4. IF `shutil.disk_usage` raises an exception, THEN THE Preflight_Script SHALL produce a warn Check_Result stating that disk space could not be determined.

### Requirement 4: Network Connectivity Check

**User Story:** As a bootcamper, I want the preflight to verify I can reach the Senzing MCP server, so that I know MCP tools will work during the bootcamp.

#### Acceptance Criteria

1. THE Preflight_Script SHALL attempt an HTTPS connection to the MCP_Endpoint on port 443 with a timeout of 5 seconds.
2. WHEN the connection succeeds, THE Preflight_Script SHALL produce a pass Check_Result confirming connectivity to the MCP_Endpoint.
3. WHEN the connection fails or times out, THE Preflight_Script SHALL produce a warn Check_Result with a Fix_Instruction advising the user to check internet connectivity and firewall rules for `mcp.senzing.com:443`, and referencing `docs/guides/OFFLINE_MODE.md`.
4. THE Preflight_Script SHALL use only Python standard library modules (`ssl`, `socket`, or `urllib`) for the connectivity check.

### Requirement 5: Senzing SDK Availability Check

**User Story:** As a bootcamper, I want the preflight to detect whether the Senzing SDK is already installed and report its version, so that Module 2 can be skipped if the SDK is ready.

#### Acceptance Criteria

1. WHEN a Python runtime is available, THE Preflight_Script SHALL attempt to import the `senzing` package in a subprocess and capture the version string.
2. WHEN the Senzing SDK is importable and reports version 4.0 or higher, THE Preflight_Script SHALL produce a pass Check_Result including the detected version.
3. WHEN the Senzing SDK is importable but reports a version below 4.0, THE Preflight_Script SHALL produce a warn Check_Result advising the user to upgrade to version 4.0 or higher.
4. WHEN the Senzing SDK is not importable, THE Preflight_Script SHALL produce a warn Check_Result stating the SDK is not installed and noting that Module 2 will cover installation.
5. WHEN no Python runtime is available, THE Preflight_Script SHALL skip the Senzing SDK check and produce a warn Check_Result noting that SDK detection requires Python.

### Requirement 6: Write Permissions Check

**User Story:** As a bootcamper, I want the preflight to verify I can write files in the project directory, so that the bootcamp can create directories and files without permission errors.

#### Acceptance Criteria

1. THE Preflight_Script SHALL attempt to create and remove a temporary directory inside the current working directory.
2. WHEN the create-and-remove operation succeeds, THE Preflight_Script SHALL produce a pass Check_Result confirming write permissions.
3. WHEN the create-and-remove operation fails, THE Preflight_Script SHALL produce a fail Check_Result with a Fix_Instruction advising the user to check directory ownership and permissions.

### Requirement 7: Required Tools Check

**User Story:** As a bootcamper, I want the preflight to verify that required command-line tools (git, curl) are installed, so that bootcamp scripts and operations work correctly.

#### Acceptance Criteria

1. THE Preflight_Script SHALL check for the presence of `git` and `curl` using `shutil.which`.
2. WHEN a required tool is found, THE Preflight_Script SHALL produce a pass Check_Result reporting the tool name and version.
3. WHEN a required tool is missing, THE Preflight_Script SHALL produce a fail Check_Result with a Fix_Instruction containing the installation URL for the missing tool.
4. WHEN the platform is not Windows, THE Preflight_Script SHALL additionally check for `zip` and `unzip` and produce a fail Check_Result with installation instructions if either is missing.

### Requirement 8: Structured Report Output

**User Story:** As a bootcamper, I want a clear, readable report after the preflight runs, so that I can quickly see what passed, what needs attention, and how to fix problems.

#### Acceptance Criteria

1. THE Preflight_Script SHALL print a header banner identifying the report as "Senzing Bootcamp — Environment Verification".
2. THE Preflight_Script SHALL group Check_Results by category (Core Tools, Language Runtimes, Disk Space, Network, Senzing SDK, Permissions) with a category heading for each group.
3. THE Preflight_Script SHALL display each Check_Result with a status indicator (pass, warn, or fail), the check name, and the message.
4. WHEN a Check_Result has status warn or fail, THE Preflight_Script SHALL display the Fix_Instruction indented below the check line.
5. THE Preflight_Script SHALL print a summary section showing total pass, warn, and fail counts and the Overall_Verdict.
6. WHEN the Overall_Verdict is FAIL, THE Preflight_Script SHALL exit with a non-zero exit code.
7. WHEN the Overall_Verdict is PASS or WARN, THE Preflight_Script SHALL exit with exit code 0.

### Requirement 9: JSON Output Mode

**User Story:** As a developer or CI system, I want to get the preflight report as structured JSON, so that I can parse and act on results programmatically.

#### Acceptance Criteria

1. WHEN the `--json` flag is provided, THE Preflight_Script SHALL output the Preflight_Report as a single JSON object to stdout instead of the human-readable format.
2. THE JSON output SHALL contain a `checks` array where each element has `name`, `category`, `status`, `message`, and `fix` fields.
3. THE JSON output SHALL contain a `summary` object with `pass_count`, `warn_count`, `fail_count`, and `verdict` fields.
4. WHEN the `--json` flag is provided, THE Preflight_Script SHALL suppress all non-JSON output (banners, colors, progress messages).
5. FOR ALL valid environments, parsing the JSON output with `json.loads` SHALL produce a valid Python dictionary without raising an exception (round-trip property).

### Requirement 10: Auto-Fix Mode

**User Story:** As a bootcamper, I want the preflight to automatically fix simple issues like missing directories, so that I can resolve common problems without manual intervention.

#### Acceptance Criteria

1. WHEN the `--fix` flag is provided, THE Preflight_Script SHALL attempt Auto_Fix actions for each fixable Check_Result before reporting.
2. THE Preflight_Script SHALL support Auto_Fix for creating missing project directories (`data/raw`, `data/transformed`, `database`, `src`, `scripts`, `docs`, `backups`, `licenses`).
3. WHEN an Auto_Fix action succeeds, THE Preflight_Script SHALL re-run the associated check and update the Check_Result to reflect the new status.
4. WHEN an Auto_Fix action fails, THE Preflight_Script SHALL retain the original fail or warn status and append the Auto_Fix failure reason to the Fix_Instruction.
5. THE Preflight_Script SHALL limit Auto_Fix to safe, idempotent operations that do not modify existing files or install software.
6. WHEN the `--fix` flag is combined with `--json`, THE Preflight_Script SHALL include a `fixed` boolean field in each Check_Result indicating whether an Auto_Fix was applied.

### Requirement 11: Onboarding Flow Integration

**User Story:** As a bootcamper, I want the environment verification to run automatically during onboarding before I choose a track, so that problems are surfaced early and I do not hit failures mid-module.

#### Acceptance Criteria

1. THE Onboarding_Gate SHALL be documented in `onboarding-flow.md` as a mandatory step between directory setup (Step 1) and language selection (Step 2).
2. THE Onboarding_Gate SHALL instruct the agent to run the Preflight_Script and present the Preflight_Report to the bootcamper.
3. WHEN the Overall_Verdict is FAIL, THE Onboarding_Gate SHALL instruct the agent to present the Fix_Instructions and ask the bootcamper to resolve the issues before proceeding.
4. WHEN the Overall_Verdict is WARN, THE Onboarding_Gate SHALL instruct the agent to present the warnings and allow the bootcamper to proceed.
5. WHEN the Overall_Verdict is PASS, THE Onboarding_Gate SHALL instruct the agent to proceed to language selection without additional prompts.
6. THE Onboarding_Gate SHALL replace the current inline `shutil.which()` checks in Step 3 of `onboarding-flow.md` with a reference to the Preflight_Script.

### Requirement 12: Deprecation of Legacy Scripts

**User Story:** As a bootcamp maintainer, I want the old check scripts to be clearly deprecated, so that contributors know to use the consolidated preflight script.

#### Acceptance Criteria

1. THE Preflight_Script SHALL include a deprecation notice at the top of both `check_prerequisites.py` and `preflight_check.py` directing users to `preflight.py`.
2. WHEN `check_prerequisites.py` is executed directly, THE Script SHALL print a deprecation warning to stderr and delegate to the Preflight_Script.
3. WHEN `preflight_check.py` is executed directly, THE Script SHALL print a deprecation warning to stderr and delegate to the Preflight_Script.
4. THE `POWER.md` Useful Commands section SHALL list `preflight.py` as the primary environment verification command and mark the legacy scripts as deprecated.
