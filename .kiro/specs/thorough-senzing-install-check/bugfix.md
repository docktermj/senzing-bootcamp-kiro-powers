# Bugfix Requirements Document

## Introduction

The Module 2 SDK Setup steering file instructs the agent to check for an existing Senzing installation before attempting to install. However, the check only uses a language-level import (e.g., `python3 -c "import senzing"`) and package manager queries (e.g., `dpkg -l senzing-*`). Both methods fail when environment variables like `PYTHONPATH` are not set or when the installed package names don't match the query pattern. This causes the agent to miss an existing installation at `/opt/senzing/er/` and proceed with unnecessary (and potentially conflicting) reinstallation steps, wasting the bootcamper's time.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the Senzing SDK is installed at `/opt/senzing/er/` but `PYTHONPATH` is not configured THEN the system fails the Python import check (`python3 -c "import senzing"`) and incorrectly concludes the SDK is not installed

1.2 WHEN the Senzing SDK is installed under package names that don't match the `senzing-*` glob pattern THEN the system fails the `dpkg -l senzing-*` check and incorrectly concludes the SDK is not installed

1.3 WHEN both the import check and package manager check fail despite a valid installation existing THEN the system proceeds with unnecessary installation steps that waste time and risk conflicts

### Expected Behavior (Correct)

2.1 WHEN the Senzing SDK is installed at `/opt/senzing/er/` but `PYTHONPATH` is not configured THEN the system SHALL detect the installation by checking for the native library file (`/opt/senzing/er/lib/libSz.so`) and the build version file (`/opt/senzing/er/szBuildVersion.json`)

2.2 WHEN the Senzing SDK is installed under non-standard package names THEN the system SHALL detect the installation by checking for the native library and build version files on the filesystem, independent of package manager metadata

2.3 WHEN the native library and build version files are found on the filesystem THEN the system SHALL report the SDK as already installed and skip installation steps, proceeding directly to verification and configuration

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the Senzing SDK is genuinely not installed (no native library or build version file exists on the filesystem) THEN the system SHALL CONTINUE TO proceed with the full installation workflow (Steps 2-3)

3.2 WHEN the Senzing SDK is installed and the language-level import check succeeds THEN the system SHALL CONTINUE TO detect the installation and skip reinstallation

3.3 WHEN the Senzing SDK is installed but the version is below V4.0 THEN the system SHALL CONTINUE TO recommend an upgrade rather than skipping installation
