# Requirements Document

## Introduction

The Entry Point Assessment script determines where a bootcamper should begin (or resume) the Senzing Bootcamp. It reads the `module-artifacts.yaml` manifest, scans the bootcamper's filesystem for produced artifacts, checks Senzing SDK importability via subprocess, and outputs a per-module checklist with a final recommendation of the first incomplete module. The script lives at `senzing-bootcamp/scripts/assess_entry_point.py`, uses Python 3.11+ stdlib only, provides an argparse CLI, and includes a custom YAML parser for the manifest.

## Glossary

- **Assessment_Script**: The Python CLI tool at `senzing-bootcamp/scripts/assess_entry_point.py` that performs entry point assessment
- **Module_Manifest**: The `module-artifacts.yaml` configuration file describing per-module artifact expectations
- **Artifact**: A file or directory that a bootcamp module produces as output
- **SDK_Check**: A subprocess-based import test that determines whether the Senzing Python SDK is importable
- **Module_Status**: The computed completeness state of a single bootcamp module (complete or incomplete)
- **Recommendation**: The suggested module number where the bootcamper should start or resume work
- **Project_Directory**: The bootcamper's working directory against which artifact paths are resolved

## Requirements

### Requirement 1: Manifest Parsing

**User Story:** As a bootcamper, I want the script to read the module-artifacts manifest so that it knows which artifacts each module should produce.

#### Acceptance Criteria

1. WHEN the Assessment_Script is invoked, THE Assessment_Script SHALL parse the Module_Manifest file using a custom YAML parser that requires no third-party dependencies.
2. WHEN the Module_Manifest file does not exist at the expected path, THE Assessment_Script SHALL exit with code 1 and print an error message identifying the missing file path.
3. WHEN the Module_Manifest contains a module entry, THE Assessment_Script SHALL extract the module number, the list of produced artifact paths, each artifact's type (file or directory), and each artifact's required flag.
4. WHEN the Module_Manifest contains `requires_from` entries for a module, THE Assessment_Script SHALL extract the dependency mapping of source module numbers to their required artifact paths.

### Requirement 2: Artifact Scanning

**User Story:** As a bootcamper, I want the script to check which artifacts already exist in my project so that it can determine my progress.

#### Acceptance Criteria

1. WHEN the Assessment_Script evaluates a module, THE Assessment_Script SHALL check each artifact path from the Module_Manifest against the Project_Directory filesystem.
2. WHEN an artifact has type "directory", THE Assessment_Script SHALL consider the artifact present only if the directory exists and contains at least one entry.
3. WHEN an artifact has type "file", THE Assessment_Script SHALL consider the artifact present only if the file exists and has a size greater than zero bytes.
4. WHEN an artifact has `required: true`, THE Assessment_Script SHALL include the artifact in the module completeness determination.
5. WHEN an artifact has `required: false`, THE Assessment_Script SHALL report the artifact status but exclude the artifact from the module completeness determination.

### Requirement 3: SDK Importability Check

**User Story:** As a bootcamper, I want the script to verify whether the Senzing SDK is installed so that the recommendation accounts for SDK availability.

#### Acceptance Criteria

1. WHEN the Assessment_Script runs, THE Assessment_Script SHALL execute a subprocess that attempts to import the `senzing` Python package.
2. WHEN the subprocess import succeeds, THE Assessment_Script SHALL record the SDK status as available and capture the SDK version string.
3. WHEN the subprocess import fails with a non-zero exit code, THE Assessment_Script SHALL record the SDK status as unavailable.
4. IF the subprocess times out after 15 seconds, THEN THE Assessment_Script SHALL record the SDK status as unavailable and include a timeout note in the output.
5. WHEN no Python interpreter is found on the system PATH, THE Assessment_Script SHALL record the SDK status as unknown and include a diagnostic message.

### Requirement 4: Module Completeness Determination

**User Story:** As a bootcamper, I want the script to determine which modules are complete so that it can identify my current position.

#### Acceptance Criteria

1. WHEN all required artifacts for a module are present on disk, THE Assessment_Script SHALL mark that module's Module_Status as complete.
2. WHEN any required artifact for a module is missing from disk, THE Assessment_Script SHALL mark that module's Module_Status as incomplete.
3. THE Assessment_Script SHALL evaluate modules in ascending numeric order starting from module 4 through module 11.

### Requirement 5: Entry Point Recommendation

**User Story:** As a bootcamper, I want a clear recommendation of which module to start so that I do not repeat completed work or skip prerequisites.

#### Acceptance Criteria

1. WHEN all evaluated modules have a complete Module_Status, THE Assessment_Script SHALL recommend proceeding beyond the last module (graduation).
2. WHEN at least one module has an incomplete Module_Status, THE Assessment_Script SHALL recommend the first incomplete module in ascending numeric order as the entry point.
3. WHILE the SDK status is unavailable, THE Assessment_Script SHALL recommend module 2 (SDK Setup) regardless of artifact presence, unless module 2 artifacts are already complete.
4. WHEN the SDK status is unavailable and module 2 artifacts are incomplete, THE Assessment_Script SHALL recommend module 2 as the entry point.

### Requirement 6: Output Report

**User Story:** As a bootcamper, I want a detailed per-module checklist and recommendation so that I can see my progress at a glance.

#### Acceptance Criteria

1. THE Assessment_Script SHALL output a per-module section showing each artifact's path, expected type, required flag, and presence status (present or missing).
2. THE Assessment_Script SHALL output the SDK check result including availability status and version string when available.
3. THE Assessment_Script SHALL output a summary line stating the recommended entry point module number and module name.
4. WHEN invoked with no arguments, THE Assessment_Script SHALL default to scanning the current working directory as the Project_Directory.
5. WHEN invoked with a `--project-dir` argument, THE Assessment_Script SHALL use the specified path as the Project_Directory.

### Requirement 7: CLI Interface

**User Story:** As a developer, I want a standard argparse CLI so that the script integrates with existing bootcamp tooling conventions.

#### Acceptance Criteria

1. THE Assessment_Script SHALL provide a `main(argv=None)` entry point that accepts an optional argument list.
2. THE Assessment_Script SHALL accept a `--project-dir` option specifying the path to the bootcamper's project directory.
3. THE Assessment_Script SHALL accept a `--manifest` option specifying an alternate path to the Module_Manifest file, defaulting to `config/module-artifacts.yaml` relative to the power's script directory.
4. THE Assessment_Script SHALL exit with code 0 when the assessment completes successfully.
5. IF the Assessment_Script encounters an unrecoverable error (missing manifest, unreadable file), THEN THE Assessment_Script SHALL exit with code 1 and print a diagnostic message to stderr.

### Requirement 8: Cross-Platform Compatibility

**User Story:** As a bootcamper on any OS, I want the script to work on Linux, macOS, and Windows so that my platform choice does not affect assessment accuracy.

#### Acceptance Criteria

1. THE Assessment_Script SHALL use `pathlib.Path` or `os.path` for all filesystem operations to ensure cross-platform path handling.
2. THE Assessment_Script SHALL use `shutil.which` to locate the Python interpreter for SDK checks.
3. THE Assessment_Script SHALL handle both forward-slash and backslash path separators when comparing artifact paths.
