# Requirements Document

## Introduction

The Senzing Bootcamp Power includes five language steering files (`lang-python.md`, `lang-java.md`, `lang-csharp.md`, `lang-rust.md`, `lang-typescript.md`) that provide code style guidance to the AI agent when generating language-specific code. Currently each file is only 10-20 lines covering basic naming conventions and linting tools. This feature expands each file to 50-100 lines with language-specific Senzing SDK best practices, common pitfalls, performance considerations, and platform-specific notes — while preserving all existing content.

## Glossary

- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` loaded by the AI agent at runtime to guide its behavior when generating code or instructions
- **Language_Steering_File**: A steering file with `inclusion: conditional` and a `fileMatchPattern` that activates when the agent works with files of a specific programming language
- **Senzing_SDK**: The Senzing Software Development Kit providing entity resolution APIs in multiple languages
- **MCP_Server**: The Senzing Model Context Protocol server that provides SDK reference, code generation, and documentation tools
- **Bootcamper**: A developer using the Senzing Bootcamp Power to learn entity resolution

## Requirements

### Requirement 1: Preserve Existing Content

**User Story:** As a power maintainer, I want all existing content in each language steering file preserved exactly, so that no current guidance is lost during expansion.

#### Acceptance Criteria

1. THE Expansion_Process SHALL retain all existing frontmatter (inclusion, fileMatchPattern) in each Language_Steering_File without modification
2. THE Expansion_Process SHALL retain all existing heading text, bullet points, and formatting in each Language_Steering_File without modification
3. WHEN new sections are added, THE Expansion_Process SHALL append new sections after the existing content

### Requirement 2: Senzing SDK Best Practices Section

**User Story:** As a bootcamper, I want language-specific Senzing SDK best practices in the steering file, so that generated code follows idiomatic patterns for my chosen language.

#### Acceptance Criteria

1. THE Language_Steering_File SHALL include a "Senzing SDK Best Practices" section with at least 5 best-practice items specific to that language
2. WHEN generating Senzing SDK code, THE Language_Steering_File SHALL instruct the agent to use language-idiomatic patterns for engine initialization, configuration loading, record operations, and resource cleanup
3. THE Language_Steering_File SHALL instruct the agent to always obtain SDK method signatures from the MCP_Server rather than guessing

### Requirement 3: Common Pitfalls Section

**User Story:** As a bootcamper, I want language-specific pitfall warnings in the steering file, so that the agent avoids generating code with known issues for my language.

#### Acceptance Criteria

1. THE Language_Steering_File SHALL include a "Common Pitfalls" section with at least 4 language-specific pitfalls relevant to Senzing SDK usage
2. WHEN a pitfall is listed, THE Language_Steering_File SHALL describe both the problem and the correct approach
3. THE Language_Steering_File SHALL cover pitfalls related to resource management, error handling, and data encoding specific to that language

### Requirement 4: Performance Considerations Section

**User Story:** As a bootcamper, I want language-specific performance guidance in the steering file, so that generated code handles threading, memory, and async patterns correctly for entity resolution workloads.

#### Acceptance Criteria

1. THE Language_Steering_File SHALL include a "Performance Considerations" section with at least 4 items covering threading, memory management, and concurrency patterns specific to that language
2. WHEN the language supports async or concurrent patterns, THE Language_Steering_File SHALL describe the recommended concurrency model for Senzing record loading and querying
3. THE Language_Steering_File SHALL include guidance on batch size recommendations and memory-efficient processing of large record sets

### Requirement 5: Code Style Conventions for Generated Code

**User Story:** As a bootcamper, I want expanded code style conventions in the steering file, so that all generated Senzing code is consistent and idiomatic for my language.

#### Acceptance Criteria

1. THE Language_Steering_File SHALL include a "Code Style for Generated Code" section with at least 4 conventions specific to Senzing bootcamp code generation
2. THE Language_Steering_File SHALL specify conventions for project structure, file organization, and module/package naming relevant to Senzing projects
3. THE Language_Steering_File SHALL specify conventions for error handling patterns, logging, and configuration management in generated code

### Requirement 6: Platform-Specific Notes

**User Story:** As a bootcamper, I want platform-specific notes in the steering file, so that the agent accounts for OS and environment differences when generating code for my language.

#### Acceptance Criteria

1. THE Language_Steering_File SHALL include a "Platform Notes" section with at least 2 items covering OS-specific or environment-specific considerations for that language with Senzing
2. WHEN the language has platform-specific installation or runtime differences for Senzing, THE Language_Steering_File SHALL document those differences
3. IF a language has limited Senzing platform support, THEN THE Language_Steering_File SHALL instruct the agent to relay MCP_Server warnings about platform compatibility

### Requirement 7: Target File Size

**User Story:** As a power maintainer, I want each expanded steering file to be between 50 and 100 lines, so that files are comprehensive without being excessively long for agent context windows.

#### Acceptance Criteria

1. THE Expansion_Process SHALL produce Language_Steering_Files that are between 50 and 100 lines each (including frontmatter)
2. THE Expansion_Process SHALL prioritize the most impactful guidance items when approaching the 100-line limit
