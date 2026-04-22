# Requirements Document

## Introduction

The policies feature provides four policy documents in `senzing-bootcamp/docs/policies/` that govern agent behavior and code generation during bootcamp execution. These policies cover code quality standards, file storage rules, Senzing information sourcing, and dependency management. They are referenced by steering files and enforced by hooks (e.g., `verify-senzing-facts`, `enforce-working-directory`).

## Glossary

- **Policy**: A markdown document in `docs/policies/` that defines rules the agent must follow during bootcamp execution
- **Agent**: The AI assistant running the Senzing Bootcamp, which reads and enforces policies
- **MCP_Server**: The Senzing MCP server that provides authoritative Senzing-specific information via tools
- **Bootcamper**: A user completing the Senzing Bootcamp

## Requirements

### Requirement 1: Agent Governance Policies

**User Story:** As a bootcamp user, I want the agent to follow documented policies for code quality, file organization, and Senzing information accuracy, so that all generated code and guidance is consistent, correct, and well-organized.

#### Acceptance Criteria

1. THE Policy `CODE_QUALITY_STANDARDS.md` SHALL define language-appropriate coding standards (style guide, naming, documentation, indentation, validation tools) for Python, Java, C#, Rust, and TypeScript.
2. THE Policy `FILE_STORAGE_POLICY.md` SHALL define storage rules for all project file types (source code, data, database, scripts, docs, config, licenses, backups, temporary files) using project-relative directories only.
3. THE Policy `SENZING_INFORMATION_POLICY.md` SHALL require that all Senzing-specific facts (attribute names, SDK methods, configuration values, error explanations) come exclusively from MCP_Server tools, never from training data.
4. THE Policy `DEPENDENCY_MANAGEMENT_POLICY.md` SHALL define dependency file conventions (file name, tool, location) for each supported language (Python, Java, C#, Rust, TypeScript).
5. IF the MCP_Server does not return a definitive answer for a Senzing-specific question, THEN THE Agent SHALL inform the Bootcamper that no authoritative answer was found and suggest checking official Senzing documentation.

### Requirement 2: Policy Index and Cross-References

**User Story:** As a bootcamp user or contributor, I want a policies index page that summarizes all policies and their scope, so that I can quickly find the relevant policy for any situation.

#### Acceptance Criteria

1. THE Policy index `README.md` SHALL list all policy documents with their purpose, key rules, and applicability scope.
2. THE Policy index SHALL include a file organization overview showing the standard project directory structure.
3. WHEN a new policy is added to the `docs/policies/` directory, THE Policy index SHALL be updated to include the new policy.
