# Bugfix Requirements Document

## Introduction

During onboarding Step 0c, the agent attempts to read the power version from `senzing-bootcamp/VERSION` using `version.py` logic. In Kiro-sandboxed workspaces, only steering files and the MCP server are exposed to the agent — the `VERSION` file and Python scripts inside `senzing-bootcamp/` are not accessible. This causes the agent to fall back to the warning message "⚠️ Could not determine power version" and the bootcamper never sees which version of the Senzing Bootcamp Kiro Power is running.

Without a visible version, bootcampers cannot confirm which bootcamp version they are using, which blocks reproducibility, support conversations, and bug reporting.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent executes onboarding Step 0c in a Kiro-sandboxed workspace THEN the system fails to read `senzing-bootcamp/VERSION` because the file is not accessible in the agent's sandbox, and displays "⚠️ Could not determine power version" instead of the actual version string.

1.2 WHEN the agent attempts to read the version using `version.py` script logic THEN the system cannot execute or locate the script because `senzing-bootcamp/scripts/` is not mirrored into the agent's accessible file tree in Kiro Power sandboxed environments.

1.3 WHEN the version cannot be determined THEN the system proceeds through onboarding without ever displaying the power version to the bootcamper, leaving them with no way to identify which version of the bootcamp is running.

### Expected Behavior (Correct)

2.1 WHEN the agent executes onboarding Step 0c in any workspace (sandboxed or non-sandboxed) THEN the system SHALL successfully retrieve the power version and display it to the bootcamper in the format "Senzing Bootcamp Power vX.Y.Z" before proceeding with the rest of onboarding.

2.2 WHEN the agent retrieves the power version THEN the system SHALL obtain it from a source that is always accessible to the agent regardless of workspace sandboxing — specifically from content the agent receives during power activation (POWER.md overview, steering files, or MCP tool responses).

2.3 WHEN the version is successfully retrieved THEN the system SHALL display it as the first onboarding output line before the welcome banner, matching the format "Senzing Bootcamp Power v0.11.0" (using the actual current version).

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the VERSION file cannot be read AND the alternative version source also cannot be read THEN the system SHALL CONTINUE TO display the warning "⚠️ Could not determine power version" and proceed with onboarding without blocking.

3.2 WHEN the agent is in a non-sandboxed workspace where `senzing-bootcamp/VERSION` is directly accessible THEN the system SHALL CONTINUE TO display the correct version (the alternative retrieval method should produce the same version string as the file).

3.3 WHEN the version is displayed during Step 0c THEN the system SHALL CONTINUE TO require no user interaction — version display remains automatic and non-blocking.

3.4 WHEN scripts (CI validation, `validate_power.py`, `measure_steering.py`) read the VERSION file directly THEN those scripts SHALL CONTINUE TO function unchanged — the VERSION file remains the single source of truth for programmatic access.

3.5 WHEN the onboarding flow proceeds past Step 0c THEN all subsequent steps (MCP health check, directory setup, hook installation, language selection, prerequisite check, welcome banner, track selection) SHALL CONTINUE TO execute in their existing order and behavior.
