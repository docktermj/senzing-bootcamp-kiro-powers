# Requirements Document

## Introduction

Display the Senzing Bootcamp Kiro Power version to the bootcamper at the very beginning of the bootcamp experience. The version follows Semantic Versioning (MAJOR.MINOR.PATCH) and is currently 0.1.0. This gives bootcampers immediate visibility into which version of the power they are running, aiding in troubleshooting and ensuring they have the expected version.

## Glossary

- **Onboarding_Flow**: The sequence of steps executed when a bootcamper starts the bootcamp, defined in `senzing-bootcamp/steering/onboarding-flow.md`.
- **Version_String**: A Semantic Versioning string in the format MAJOR.MINOR.PATCH (e.g., "0.1.0").
- **Welcome_Banner**: The visual banner displayed in Step 4 of the Onboarding_Flow that signals the bootcamp has officially started.
- **Bootcamper**: The user participating in the Senzing Bootcamp.
- **Version_Display**: The component responsible for presenting the Version_String to the Bootcamper during onboarding.
- **Version_Source**: The single authoritative location where the Version_String is stored and read from.

## Requirements

### Requirement 1: Store Version in a Single Authoritative Location

**User Story:** As a maintainer, I want the version stored in a single authoritative location, so that version updates require changing only one place.

#### Acceptance Criteria

1. THE Version_Source SHALL store the Version_String in a single file within the power's configuration or metadata, and no other file in the repository SHALL independently define or override the Version_String.
2. THE Version_Source SHALL use the Semantic Versioning format MAJOR.MINOR.PATCH where MAJOR, MINOR, and PATCH are non-negative integers.
3. WHEN the Version_Source file is read, THE Version_Display SHALL obtain the current Version_String without requiring any other file to be consulted.
4. IF the Version_Source file does not contain a parseable Version_String, THEN THE Version_Display SHALL report an error indicating the version is missing or malformed rather than returning a default or empty value.

### Requirement 2: Display Version at the Start of the Bootcamp

**User Story:** As a bootcamper, I want to see the power version at the very beginning of the bootcamp, so that I know which version I am running.

#### Acceptance Criteria

1. WHEN the bootcamp onboarding begins, THE Version_Display SHALL present the Version_String to the Bootcamper as the first line of onboarding output, before the Welcome_Banner in Step 4 of the Onboarding_Flow is displayed.
2. THE Version_Display SHALL render the Version_String in the format "Senzing Bootcamp Power v" followed by the MAJOR.MINOR.PATCH value (e.g., "Senzing Bootcamp Power v0.1.0").
3. THE Version_Display SHALL present the version automatically as part of the onboarding output without requiring any user interaction or command from the Bootcamper.
4. IF the Version_Source file cannot be read or is missing, THEN THE Version_Display SHALL present an error message indicating that the version could not be determined and SHALL continue the onboarding sequence without blocking.

### Requirement 3: Validate Version Format

**User Story:** As a maintainer, I want the version format validated, so that an invalid version string is caught before it reaches bootcampers.

#### Acceptance Criteria

1. WHEN the Version_String is read from the Version_Source, THE Version_Display SHALL validate that the string conforms to the Semantic Versioning format MAJOR.MINOR.PATCH where each component is a non-negative integer without leading zeros (e.g., "0.1.0" is valid; "01.1.0" is not).
2. IF the Version_String does not conform to Semantic Versioning format, THEN THE Version_Display SHALL report an error message that includes the invalid value verbatim.
3. THE Version_Display SHALL reject Version_Strings that contain pre-release identifiers, build metadata, or any characters beyond the MAJOR.MINOR.PATCH digits and dots.
4. FOR ALL valid Semantic Versioning strings within the range 0–99 for each component, THE Version_Display SHALL produce an identical string after parsing and re-formatting (round-trip property).

### Requirement 4: Version Accessible to Scripts

**User Story:** As a maintainer, I want scripts to be able to read the version programmatically, so that CI validation and other tooling can reference the current version.

#### Acceptance Criteria

1. THE Version_Source SHALL be parseable by Python 3.11+ using only standard library modules such that the Version_String can be extracted in a single file-open-and-parse operation.
2. WHEN a script reads the Version_Source, THE script SHALL obtain a Version_String that is byte-for-byte identical to the Version_String displayed to the Bootcamper.
3. THE Version_Source SHALL use a file format that does not require third-party parsing libraries (plain text, JSON, or YAML with PyYAML as the sole allowed exception per project conventions).
4. THE Version_Source SHALL reside at a fixed path relative to the power's root directory so that scripts can locate it without searching.
5. IF the Version_Source file is missing or cannot be parsed, THEN THE script SHALL exit with a non-zero exit code and print an error message indicating the file path and the nature of the failure.
