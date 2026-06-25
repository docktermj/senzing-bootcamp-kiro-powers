# Requirements Document

## Introduction

This feature ensures bootcamper preferences persist reliably across sessions and that context-limit communication is clear and actionable. The bootcamp spans 11 modules and typically requires multiple sessions to complete. Bootcampers must never be forced to re-answer preference questions, and when a context reset is needed, the agent must communicate the reason transparently without implying a time delay.

## Glossary

- **Preferences_File**: The YAML file at `config/bootcamp_preferences.yaml` that stores all bootcamper choices (language, track, verbosity, conversation style, etc.)
- **Session_Resume_Steering**: The steering file that governs agent behavior when a returning bootcamper starts a new chat session
- **Preference_Writer**: The component responsible for writing preference values to the Preferences_File immediately upon selection
- **Context_Reset_Advisor**: The agent behavior that communicates context window limitations and guides the bootcamper to start a fresh session
- **Bootcamper**: The user progressing through the Senzing bootcamp modules
- **Progress_File**: The JSON file at `config/bootcamp_progress.json` that tracks module completion and current step
- **Context_Window**: The conversation memory available to the agent within a single chat session

## Requirements

### Requirement 1: Immediate Preference Persistence

**User Story:** As a bootcamper, I want my preference selections saved immediately when I make them, so that returning to the bootcamp in a new session does not require re-answering the same questions.

#### Acceptance Criteria

1. WHEN the Bootcamper selects a programming language, THE Preference_Writer SHALL write the `language` field to the Preferences_File before the next agent response
2. WHEN the Bootcamper selects a verbosity level, THE Preference_Writer SHALL write the `verbosity` field to the Preferences_File before the next agent response
3. WHEN the Bootcamper selects a track, THE Preference_Writer SHALL write the `track` field to the Preferences_File before the next agent response
4. WHEN the Bootcamper selects a conversation style, THE Preference_Writer SHALL write the `conversation_style` field to the Preferences_File before the next agent response
5. WHEN the Bootcamper makes any preference decision during the bootcamp, THE Preference_Writer SHALL persist that decision to the corresponding field in the Preferences_File within the same agent turn
6. WHEN the Bootcamper changes a previously set preference, THE Preference_Writer SHALL update the Preferences_File with the new value and preserve all other existing preference fields unchanged
7. IF the Preferences_File does not yet exist when a preference is selected, THEN THE Preference_Writer SHALL create the file with the selected preference field before the next agent response
8. IF the Preference_Writer cannot write to the Preferences_File due to a file system error, THEN THE Preference_Writer SHALL inform the Bootcamper that the preference was not saved and suggest verifying file permissions on the `config/` directory

### Requirement 2: Session Resume Preference Loading

**User Story:** As a returning bootcamper, I want my saved preferences automatically loaded and applied when I start a new session, so that I can continue seamlessly without re-configuration.

#### Acceptance Criteria

1. WHEN a new session starts and the Preferences_File exists and contains valid YAML, THE Session_Resume_Steering SHALL read and apply all present preference fields before any interaction with the Bootcamper
2. WHEN preferences are successfully loaded, THE Session_Resume_Steering SHALL display a confirmation of no more than two sentences summarizing the active language, track, and verbosity values (e.g., "Resuming with Python, standard verbosity, Core track")
3. WHEN preferences are successfully loaded, THE Session_Resume_Steering SHALL apply the loaded language, track, verbosity, and conversation style to all subsequent agent behavior without re-asking
4. WHEN preferences are successfully loaded and the `language` field is present, THE Session_Resume_Steering SHALL load the corresponding language steering file based on the persisted `language` preference
5. IF the persisted `language` value does not map to a supported language steering file, THEN THE Session_Resume_Steering SHALL inform the Bootcamper that the saved language is unrecognized and prompt for a new language selection while preserving all other loaded preferences

### Requirement 3: Graceful Preference Recovery

**User Story:** As a returning bootcamper, I want the agent to handle missing or corrupted preference files gracefully, so that I am re-asked only the necessary questions rather than encountering errors or silent defaults.

#### Acceptance Criteria

1. IF the Preferences_File is missing or unreadable, THEN THE Session_Resume_Steering SHALL prompt the Bootcamper for each required preference (language, track, verbosity) one at a time in that order
2. IF the Preferences_File contains invalid YAML syntax or contains values that cannot be parsed into recognized preference fields, THEN THE Session_Resume_Steering SHALL inform the Bootcamper that preferences could not be loaded and prompt for re-selection of all required preferences (language, track, verbosity)
3. IF one or more preference fields are null or missing from an otherwise valid Preferences_File, THEN THE Session_Resume_Steering SHALL prompt the Bootcamper only for each missing preference individually while preserving all other loaded values
4. IF the Preferences_File is missing or corrupted, THEN THE Session_Resume_Steering SHALL NOT assume default values silently without informing the Bootcamper
5. WHEN the Bootcamper provides a preference value during recovery prompting, THE Session_Resume_Steering SHALL persist that value to the Preferences_File before the next agent response

### Requirement 4: Context Reset Communication

**User Story:** As a bootcamper, I want clear and honest communication when the agent needs a context reset, so that I understand the technical reason and know I can immediately continue without waiting.

#### Acceptance Criteria

1. WHEN the agent's context window reaches 80% capacity or the agent detects degraded response quality due to context length, THE Context_Reset_Advisor SHALL explain the technical reason using language such as "My conversation memory is getting full from our work so far"
2. WHEN the agent suggests a fresh session, THE Context_Reset_Advisor SHALL explain that starting a new chat can be done immediately with no waiting period
3. WHEN the agent suggests a fresh session, THE Context_Reset_Advisor SHALL state that all progress is saved in project files and will be available in the new session
4. WHEN the agent suggests a fresh session, THE Context_Reset_Advisor SHALL provide a continuation phrase enclosed in quotation marks that the Bootcamper can copy and paste into the new chat (e.g., "Say 'continue the bootcamp' in the new chat")
5. WHEN the agent suggests a fresh session, THE Context_Reset_Advisor SHALL include the current module number so the Bootcamper knows where they will resume
6. THE Context_Reset_Advisor SHALL NOT use temporal language that implies the Bootcamper must wait before continuing, including but not limited to phrases such as "come back later", "come back tomorrow", "take a break", "try again in a while", or "when you're ready"
7. WHEN the agent suggests a fresh session, THE Context_Reset_Advisor SHALL present the technical reason, continuation instructions, and module number together in a single message

### Requirement 5: Context Reset Message Format

**User Story:** As a bootcamper, I want the context reset suggestion delivered as a single cohesive message, so that I have all the information I need in one place.

#### Acceptance Criteria

1. WHEN the agent communicates a context reset, THE Context_Reset_Advisor SHALL include all four elements in a single uninterrupted agent response with no intervening user prompts: technical reason, immediacy clarification, progress reassurance, and continuation instructions
2. WHEN the agent communicates a context reset, THE Context_Reset_Advisor SHALL format the message in no more than 4 sentences, where the final sentence contains a specific next-step instruction the Bootcamper can execute immediately
3. WHEN the agent communicates a context reset, THE Context_Reset_Advisor SHALL reference the current module number and step identifier as recorded in the Progress_File so the Bootcamper knows exactly where they will resume
4. WHEN the agent communicates a context reset, THE Context_Reset_Advisor SHALL NOT request additional input from the Bootcamper or split the context reset information across multiple responses

### Requirement 6: Preference File Schema Completeness

**User Story:** As a bootcamper, I want all my preference decisions captured in the preferences file, so that no choice is lost between sessions.

#### Acceptance Criteria

1. THE Preferences_File schema SHALL support the following fields with their respective types: language (string), track (string), verbosity (string), conversation_style (string), deployment_target (string), cloud_provider (string), database_type (string), mapping_verbosity (string), hooks_installed (boolean), and pacing_overrides (mapping of string keys to string or boolean values)
2. THE Preferences_File SHALL treat all preference fields as optional; a field that has not yet been set by the Bootcamper SHALL be absent from the file rather than stored with a null or empty value
3. WHEN the Preference_Writer persists a preference value, THE Preference_Writer SHALL read the existing Preferences_File, merge the new field value, and write the complete updated file so that all previously stored fields are preserved
4. THE Preference_Writer SHALL write the Preferences_File in valid YAML format parseable by PyYAML, with a maximum file size of 10 KB
5. THE Preference_Writer SHALL produce files where reading the written file back and comparing each field value yields identical type and content to what was written (round-trip equivalence)
6. IF the Preference_Writer fails to write the Preferences_File due to a filesystem error, THEN THE Preference_Writer SHALL preserve the previous file contents unchanged and report the failure to the agent
