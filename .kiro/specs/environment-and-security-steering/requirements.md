# Requirements Document

## Introduction

The environment-and-security-steering feature provides two steering files that guide agent behavior during bootcamp project setup and code generation. `environment-setup.md` (manual inclusion) provides version control and language-specific environment setup instructions. `security-privacy.md` (auto inclusion) enforces data privacy rules, secure code generation practices, compliance triggers, and anonymization guidance.

## Glossary

- **Agent**: The AI assistant running the Senzing Bootcamp, which reads steering files to guide its behavior
- **Bootcamper**: A user completing the Senzing Bootcamp
- **Steering_File**: A markdown document in `steering/` with front-matter inclusion mode that the Agent loads to guide its actions
- **MCP_Server**: The Senzing MCP server that provides authoritative Senzing-specific information

## Requirements

### Requirement 1: Environment Setup Steering

**User Story:** As a bootcamper, I want the agent to guide me through version control setup and language-specific environment configuration, so that my project is correctly initialized with proper .gitignore, environment variables, and SDK bindings.

#### Acceptance Criteria

1. THE Steering_File `environment-setup.md` SHALL have `inclusion: manual` front-matter so the Agent loads it during onboarding or new project setup.
2. WHEN the Agent sets up version control, THE Steering_File SHALL provide git init, .gitignore (with bootcamp-specific entries for sensitive data, data files, database files, logs, backups, and OS files), and .env.example template instructions.
3. WHEN the Agent sets up a language environment, THE Steering_File SHALL reference the MCP_Server `sdk_guide` tool for current SDK binding installation commands for the chosen language.
4. THE Steering_File SHALL define that all source code goes in `src/` subdirectories and automation scripts go in `scripts/`.

### Requirement 2: Security and Privacy Steering

**User Story:** As a bootcamper, I want the agent to automatically enforce data privacy and secure coding practices, so that my bootcamp project never exposes credentials, PII, or raw data.

#### Acceptance Criteria

1. THE Steering_File `security-privacy.md` SHALL have `inclusion: auto` front-matter so the Agent loads it automatically for every interaction.
2. THE Steering_File SHALL define data handling rules: raw data gitignored, anonymized/synthetic data for testing, `.env` for credentials (gitignored), SQLite DB gitignored, and license files gitignored.
3. WHEN the Agent generates code, THE Steering_File SHALL enforce no hardcoded credentials, no PII in logs, and sanitized user input before passing to Senzing SDK.
4. WHEN the Bootcamper mentions GDPR, CCPA, HIPAA, or PCI-DSS, THE Agent SHALL load Module 10 for the full security hardening workflow and create `docs/security_compliance.md`.
5. WHEN the Agent creates sample data from real data, THE Steering_File SHALL require name replacement, identifier masking (keep last 4 digits), fake addresses/phones, and use of language-appropriate faker libraries (Python: Faker, Java: Faker, C#: Bogus, Rust: fake-rs, TypeScript: @faker-js/faker).
