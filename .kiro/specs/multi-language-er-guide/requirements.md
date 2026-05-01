# Requirements Document

## Introduction

Real-world entity resolution frequently involves data with mixed languages and scripts — customer names in English and Chinese, addresses in Arabic and Latin characters, organization names transliterated across multiple writing systems. The Senzing Bootcamp currently covers data quality and mapping in Module 5 but does not address the specific challenges of multi-language data: UTF-8 encoding requirements, how Senzing handles non-Latin characters natively, transliteration and name matching across scripts, or best practices for preparing multi-language data for entity resolution.

This feature adds a dedicated guide at `docs/guides/MULTI_LANGUAGE_DATA.md` covering multi-language entity resolution with Senzing. The guide explains Senzing's native globalization capabilities, UTF-8 encoding requirements, cross-script name matching (e.g., matching "John Smith" with "约翰·史密斯"), and best practices for multi-language data quality. The guide uses `search_docs` for authoritative Senzing globalization content. Module 5 references the guide when discussing data quality for international datasets, and the guides README indexes it for discoverability.

## Glossary

- **Multi_Language_Guide**: The Markdown document at `docs/guides/MULTI_LANGUAGE_DATA.md` that explains multi-language entity resolution patterns and best practices for Senzing.
- **Non_Latin_Character**: Any character outside the basic Latin alphabet (A-Z, a-z), including but not limited to Chinese (汉字), Japanese (漢字/かな/カナ), Korean (한글), Arabic (العربية), Cyrillic (Кириллица), Devanagari (देवनागरी), and Thai (ไทย) scripts.
- **Transliteration**: The process of converting text from one writing system to another based on phonetic correspondence (e.g., "Владимир" → "Vladimir", "محمد" → "Muhammad").
- **Cross_Script_Matching**: The ability of an entity resolution system to recognize that names written in different scripts refer to the same entity (e.g., "John Smith" and "约翰·史密斯").
- **UTF8_Encoding**: The Unicode Transformation Format 8-bit encoding standard that represents all Unicode characters and is required by Senzing for input data.
- **Module_5_Steering**: The steering file at `senzing-bootcamp/steering/module-05-data-quality-mapping.md` that defines the Module 5 workflow for data quality assessment and mapping.
- **Guide_Directory**: The directory at `senzing-bootcamp/docs/guides/` containing user-facing reference documentation for the bootcamp.
- **Guides_README**: The file at `senzing-bootcamp/docs/guides/README.md` that indexes all available guides with descriptions and links.
- **Senzing_Entity_Specification**: The JSON format (SGES) that Senzing uses for input records, requiring specific attribute names and UTF-8 encoded values.

## Requirements

### Requirement 1: Multi-Language Guide Creation

**User Story:** As a bootcamper working with international data, I want a dedicated guide on multi-language entity resolution, so that I understand how Senzing handles names and records across different languages and scripts.

#### Acceptance Criteria for Requirement 1

1. THE Multi_Language_Guide SHALL be located at `docs/guides/MULTI_LANGUAGE_DATA.md`
2. THE Multi_Language_Guide SHALL open with an introduction explaining why multi-language data presents unique challenges for entity resolution, including examples of real-world scenarios (e.g., customer databases spanning multiple countries, compliance screening across jurisdictions)
3. THE Multi_Language_Guide SHALL use a level-1 heading with the guide title, followed by an introductory paragraph, consistent with the heading and layout conventions in the Guide_Directory

### Requirement 2: Non-Latin Character Support

**User Story:** As a bootcamper, I want to understand how Senzing handles non-Latin characters natively, so that I know what to expect when loading data in Chinese, Arabic, Cyrillic, and other scripts.

#### Acceptance Criteria for Requirement 2

1. THE Multi_Language_Guide SHALL include a section explaining how Senzing processes Non_Latin_Characters natively without requiring pre-translation of input data
2. THE Multi_Language_Guide SHALL list the script families that Senzing supports for name matching, retrieved using `search_docs` from the Senzing MCP server rather than relying on training data
3. THE Multi_Language_Guide SHALL explain how Senzing stores and indexes names in their original script alongside any transliterated forms
4. THE Multi_Language_Guide SHALL include at least one example showing a Senzing_Entity_Specification record containing Non_Latin_Characters (e.g., a record with `NAME_FULL` in Chinese or Arabic)

### Requirement 3: UTF-8 Encoding Requirements

**User Story:** As a bootcamper preparing multi-language data files, I want to understand the UTF-8 encoding requirements for Senzing, so that my data loads correctly without character corruption or matching failures.

#### Acceptance Criteria for Requirement 3

1. THE Multi_Language_Guide SHALL include a section explaining that Senzing requires all input data to be encoded in UTF8_Encoding
2. THE Multi_Language_Guide SHALL describe common encoding problems that cause entity resolution failures: data files saved in legacy encodings (e.g., Latin-1, Shift-JIS, GB2312), byte-order marks (BOM) in UTF-8 files, and mojibake from double-encoding
3. THE Multi_Language_Guide SHALL provide a checklist of steps to verify and convert file encoding before loading into Senzing, including command-line examples for detecting and converting encodings
4. IF a data file contains characters that are not valid UTF8_Encoding, THEN THE Multi_Language_Guide SHALL explain the expected Senzing behavior (error on load or silent data corruption) as documented by `search_docs`

### Requirement 4: Transliteration and Cross-Script Name Matching

**User Story:** As a bootcamper, I want to understand how Senzing matches names across different scripts, so that I can trust that entities are resolved correctly even when the same person's name appears in English, Chinese, Arabic, or other writing systems.

#### Acceptance Criteria for Requirement 4

1. THE Multi_Language_Guide SHALL include a section explaining Senzing's Transliteration and Cross_Script_Matching capabilities
2. THE Multi_Language_Guide SHALL explain how Senzing's name matching algorithms handle phonetic equivalence across scripts, with the technical details retrieved using `search_docs`
3. THE Multi_Language_Guide SHALL include at least three practical examples of Cross_Script_Matching, each showing a pair of records in different scripts that Senzing resolves to the same entity (e.g., "John Smith" / "约翰·史密斯", a Cyrillic/Latin pair, and an Arabic/Latin pair)
4. THE Multi_Language_Guide SHALL explain the limitations of Cross_Script_Matching — scenarios where automatic matching may not succeed and manual review or additional data attributes are needed to confirm a match

### Requirement 5: Multi-Language Data Quality Best Practices

**User Story:** As a bootcamper, I want best practices for preparing multi-language data for entity resolution, so that I can maximize match quality when my data contains multiple languages and scripts.

#### Acceptance Criteria for Requirement 5

1. THE Multi_Language_Guide SHALL include a best practices section covering data preparation for multi-language entity resolution
2. THE Multi_Language_Guide SHALL recommend preserving original-script names in the data rather than pre-transliterating them, explaining that Senzing performs its own transliteration internally
3. THE Multi_Language_Guide SHALL describe how to use multiple name attributes (e.g., `NAME_FULL` in the original script and `NAME_FULL` in a transliterated form) when both versions are available in the source data
4. THE Multi_Language_Guide SHALL address data quality considerations specific to multi-language data: inconsistent romanization schemes, mixed-script fields (e.g., a single name field containing both Latin and Chinese characters), and honorifics or titles that vary by language
5. THE Multi_Language_Guide SHALL explain how the data quality scoring from Module 5 applies to multi-language data, including any additional quality dimensions that become relevant

### Requirement 6: MCP Tool Usage for Authoritative Content

**User Story:** As a bootcamper, I want the multi-language guide to use authoritative Senzing content, so that the information about globalization capabilities reflects current Senzing behavior rather than outdated or inaccurate information.

#### Acceptance Criteria for Requirement 6

1. WHEN explaining Senzing's globalization capabilities, Transliteration behavior, or Cross_Script_Matching algorithms, THE guide author SHALL use `search_docs` from the Senzing MCP server to retrieve current documentation rather than relying on training data
2. WHEN providing example records or attribute names, THE guide author SHALL use `search_docs` or `analyze_record` to verify that the attribute names and record structures are valid for the current Senzing_Entity_Specification
3. THE Multi_Language_Guide SHALL include a "Further Reading" section that directs bootcampers to use `search_docs` with relevant queries (e.g., "globalization", "transliteration", "multi-language") for the latest Senzing documentation on multi-language support

### Requirement 7: Module 5 Cross-Reference

**User Story:** As a bootcamper working through Module 5 data quality assessment, I want to be pointed toward the multi-language guide when my data contains non-Latin characters, so that I know where to find specialized guidance.

#### Acceptance Criteria for Requirement 7

1. THE Module_5_Steering SHALL include a reference to the Multi_Language_Guide as supplementary reading for bootcampers working with multi-language or multi-script data
2. WHEN referencing the Multi_Language_Guide from Module_5_Steering, THE reference SHALL describe the guide as covering UTF-8 encoding, non-Latin character support, cross-script name matching, and multi-language data quality best practices
3. THE reference in Module_5_Steering SHALL not add the Multi_Language_Guide as a required step — it SHALL be presented as optional supplementary reading relevant to data quality for international datasets

### Requirement 8: Guides README Integration

**User Story:** As a bootcamper, I want the multi-language guide listed in the guides README, so that I can discover it from the central documentation index.

#### Acceptance Criteria for Requirement 8

1. WHEN the Multi_Language_Guide is created, THE Guides_README SHALL include an entry for `MULTI_LANGUAGE_DATA.md` in the "Reference Documentation" section
2. WHEN listing the Multi_Language_Guide in the Guides_README, THE entry SHALL include the filename as a Markdown link, a bold title, and a two-to-three line description covering non-Latin character support, UTF-8 encoding, cross-script name matching, and multi-language data quality best practices
3. THE Guides_README SHALL list `MULTI_LANGUAGE_DATA.md` in the Documentation Structure tree under the `guides/` directory
