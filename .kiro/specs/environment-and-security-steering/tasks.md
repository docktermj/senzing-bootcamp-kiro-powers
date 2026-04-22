# Tasks

## Requirement 1: Environment Setup Steering

- [x] 1.1 Create `steering/environment-setup.md` with `inclusion: manual` front-matter
- [x] 1.2 Add version control section with git init, bootcamp-specific .gitignore, and .env.example instructions
- [x] 1.3 Add environment variables section with project-local senzing-env scripts for Linux/macOS and Windows
- [x] 1.4 Add language setup section referencing MCP_Server `sdk_guide` tool for SDK binding installation
- [x] 1.5 Add source code location section defining `src/` subdirectories and `scripts/` for automation

## Requirement 2: Security and Privacy Steering

- [x] 2.1 Create `steering/security-privacy.md` with `inclusion: auto` front-matter
- [x] 2.2 Add data handling rules (raw data gitignored, anonymized/synthetic data, .env for credentials, SQLite DB gitignored, license files gitignored)
- [x] 2.3 Add code generation rules (no hardcoded credentials, no PII in logs, sanitize user input)
- [x] 2.4 Add compliance trigger to load Module 10 when GDPR/CCPA/HIPAA/PCI-DSS mentioned
- [x] 2.5 Add anonymization guidance with masking rules and language-specific faker library references
