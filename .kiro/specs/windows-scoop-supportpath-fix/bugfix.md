# Bugfix Requirements Document

## Introduction

During Module 2 (SDK Setup), Step 8 — Engine Configuration, the agent sets SUPPORTPATH to `$SENZING_DIR\data` when configuring the Senzing engine on Windows with a Scoop-installed SDK. However, the unofficial Scoop package uses a non-standard directory layout where `SENZING_DIR` points to the `er` subdirectory within the Scoop app folder, while the `data` directory (containing `g2SifterRules.ibm` and other support files) is located at the Scoop app version root — one level above `er`. This causes engine initialization to fail with SENZ2027 ("Plugin initialization error... GNR data files failed to load"), forcing the agent to spend multiple turns searching the filesystem to locate the correct path. This erodes bootcamper confidence during what should be a straightforward setup step.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent configures the Senzing engine on Windows with a Scoop-installed SDK THEN the system sets SUPPORTPATH to `$SENZING_DIR\data` (i.e., the `er\data` path), which does not exist in the Scoop package layout.

1.2 WHEN the engine initializes with the incorrect SUPPORTPATH THEN the system fails with SENZ2027 ("Plugin initialization error... GNR data files failed to load") because `g2SifterRules.ibm` and other support files are not found at the configured path.

1.3 WHEN the SENZ2027 error occurs THEN the agent spends multiple turns recursively searching the filesystem to locate the `data` directory, wasting time and eroding bootcamper confidence.

### Expected Behavior (Correct)

2.1 WHEN the agent configures the Senzing engine on Windows with a Scoop-installed SDK THEN the system SHALL verify whether `$SENZING_DIR\data` exists before using it as SUPPORTPATH, and if it does not exist, SHALL check one level up (`$SENZING_DIR\..\data`) for the `data` directory.

2.2 WHEN the `data` directory is found at `$SENZING_DIR\..\data` (the Scoop app version root) THEN the system SHALL set SUPPORTPATH to that path and the engine SHALL initialize successfully without SENZ2027 errors.

2.3 WHEN the agent resolves the correct SUPPORTPATH on the first attempt THEN the system SHALL proceed to engine initialization without additional filesystem searches or error recovery turns.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent configures the Senzing engine on Linux or macOS THEN the system SHALL CONTINUE TO use the SUPPORTPATH returned by `sdk_guide(topic='configure')` without modification.

3.2 WHEN the agent configures the Senzing engine on Windows with a non-Scoop installation where `$SENZING_DIR\data` exists THEN the system SHALL CONTINUE TO use `$SENZING_DIR\data` as SUPPORTPATH.

3.3 WHEN the `sdk_guide` MCP tool returns engine configuration JSON THEN the system SHALL CONTINUE TO use the MCP-returned paths as the starting point for configuration, applying the Scoop layout check only when the standard path does not exist on Windows.

3.4 WHEN the engine initializes successfully with the correct SUPPORTPATH THEN the system SHALL CONTINUE TO proceed to the database connection test (Step 9) without additional verification steps.
