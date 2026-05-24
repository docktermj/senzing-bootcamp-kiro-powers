# Requirements Document

## Introduction

This feature enforces file placement rules at the hook level, preventing the agent from writing source code, documentation, data files, and non-config JSON files to the project root directory. The write-policy-gate hook gains a new CHECK 4 that blocks disallowed file types in the root and provides corrective routing instructions. Supporting steering files (agent-instructions.md and project-structure.md) are strengthened with explicit prohibition language to provide belt-and-suspenders enforcement.

## Glossary

- **Write_Policy_Gate**: The preToolUse hook (`write-policy-gate.kiro.hook`) that intercepts all write operations and enforces file path and content policies before the write proceeds.
- **Project_Root**: The top-level directory of the bootcamper's working project (e.g., `my-senzing-project/`), excluding subdirectories.
- **Root_Whitelist**: The set of files explicitly permitted in the Project_Root: `.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `.csproj`, `Cargo.toml`, `package.json`.
- **Blocked_Extensions**: File extensions that are never permitted in the Project_Root: `.py`, `.md`, `.jsonl`, `.csv`, and `.json` (when not a config/dependency file on the Root_Whitelist).
- **Corrective_Routing**: The guidance output by the Write_Policy_Gate that tells the agent which subdirectory a blocked file should be placed in.
- **Agent_Instructions**: The steering file `senzing-bootcamp/steering/agent-instructions.md` that defines core agent behavior rules.
- **Project_Structure_Steering**: The steering file `senzing-bootcamp/steering/project-structure.md` that defines directory layout and file placement rules.

## Requirements

### Requirement 1: Hook blocks disallowed file types in project root

**User Story:** As a bootcamp maintainer, I want the write-policy-gate hook to block writes of .py, .md, .jsonl, .csv, and non-config .json files to the project root, so that the project structure stays organized without relying solely on agent memory of steering rules.

#### Acceptance Criteria

1. WHEN a write targets a `.py` file in the Project_Root, THE Write_Policy_Gate SHALL reject the write and output corrective instructions.
2. WHEN a write targets a `.md` file in the Project_Root AND the filename is not `README.md`, THE Write_Policy_Gate SHALL reject the write and output corrective instructions.
3. WHEN a write targets a `.jsonl` file in the Project_Root, THE Write_Policy_Gate SHALL reject the write and output corrective instructions.
4. WHEN a write targets a `.csv` file in the Project_Root, THE Write_Policy_Gate SHALL reject the write and output corrective instructions.
5. WHEN a write targets a `.json` file in the Project_Root AND the filename is not on the Root_Whitelist, THE Write_Policy_Gate SHALL reject the write and output corrective instructions.
6. WHEN a write targets a file in the Project_Root AND the filename matches an entry on the Root_Whitelist, THE Write_Policy_Gate SHALL allow the write to proceed silently.

### Requirement 2: Corrective routing provides accurate redirection

**User Story:** As a bootcamp maintainer, I want the hook's corrective output to tell the agent exactly where each blocked file type should go, so that the agent can immediately rewrite the path without guessing.

#### Acceptance Criteria

1. WHEN the Write_Policy_Gate blocks a `.py` file that contains mapper or transformation logic, THE Corrective_Routing SHALL direct the agent to `src/transform/`.
2. WHEN the Write_Policy_Gate blocks a `.py` file that contains loader logic, THE Corrective_Routing SHALL direct the agent to `src/load/`.
3. WHEN the Write_Policy_Gate blocks a `.py` file that contains query logic, THE Corrective_Routing SHALL direct the agent to `src/query/`.
4. WHEN the Write_Policy_Gate blocks a `.py` file that does not match a specific src subdirectory, THE Corrective_Routing SHALL direct the agent to `scripts/`.
5. WHEN the Write_Policy_Gate blocks a `.md` file, THE Corrective_Routing SHALL direct the agent to `docs/`.
6. WHEN the Write_Policy_Gate blocks a `.jsonl` or `.csv` file, THE Corrective_Routing SHALL direct the agent to the appropriate `data/` subdirectory (`data/raw/`, `data/transformed/`, `data/samples/`, or `data/temp/`).
7. WHEN the Write_Policy_Gate blocks a non-config `.json` file, THE Corrective_Routing SHALL direct the agent to the appropriate subdirectory based on content type.

### Requirement 3: Root whitelist permits config and dependency files

**User Story:** As a bootcamp maintainer, I want config and dependency management files to remain writable in the project root, so that standard project tooling continues to work.

#### Acceptance Criteria

1. THE Write_Policy_Gate SHALL permit writes to `.gitignore` in the Project_Root.
2. THE Write_Policy_Gate SHALL permit writes to `.env` in the Project_Root.
3. THE Write_Policy_Gate SHALL permit writes to `.env.example` in the Project_Root.
4. THE Write_Policy_Gate SHALL permit writes to `README.md` in the Project_Root.
5. THE Write_Policy_Gate SHALL permit writes to `requirements.txt` in the Project_Root.
6. THE Write_Policy_Gate SHALL permit writes to `pom.xml` in the Project_Root.
7. THE Write_Policy_Gate SHALL permit writes to files ending in `.csproj` in the Project_Root.
8. THE Write_Policy_Gate SHALL permit writes to `Cargo.toml` in the Project_Root.
9. THE Write_Policy_Gate SHALL permit writes to `package.json` in the Project_Root.

### Requirement 4: Agent instructions enforce explicit root prohibition

**User Story:** As a bootcamp maintainer, I want the agent-instructions.md File Placement section to contain explicit "NEVER place in root" language for each blocked file type, so that the agent's primary steering prevents violations before the hook even fires.

#### Acceptance Criteria

1. THE Agent_Instructions File Placement section SHALL state that `.py` files are never permitted in the Project_Root.
2. THE Agent_Instructions File Placement section SHALL state that `.md` files other than `README.md` are never permitted in the Project_Root.
3. THE Agent_Instructions File Placement section SHALL state that `.jsonl` and `.csv` files are never permitted in the Project_Root.
4. THE Agent_Instructions File Placement section SHALL state that non-config `.json` files are never permitted in the Project_Root.
5. THE Agent_Instructions File Placement section SHALL list the Root_Whitelist as the only files permitted in the Project_Root.

### Requirement 5: Project structure steering enforces placement rules

**User Story:** As a bootcamp maintainer, I want the project-structure.md steering file to contain enforcement language that reinforces the hook's behavior, so that both steering and hook work together as defense-in-depth.

#### Acceptance Criteria

1. THE Project_Structure_Steering Rules section SHALL state that source code files (`.py`) are never permitted in the Project_Root.
2. THE Project_Structure_Steering Rules section SHALL state that documentation files (`.md`) other than `README.md` are never permitted in the Project_Root.
3. THE Project_Structure_Steering Rules section SHALL state that data files (`.jsonl`, `.csv`) are never permitted in the Project_Root.
4. THE Project_Structure_Steering Rules section SHALL state that non-config `.json` files are never permitted in the Project_Root.
5. THE Project_Structure_Steering Rules section SHALL list the corrective routing destinations for each blocked file type.
6. THE Project_Structure_Steering Rules section SHALL list the Root_Whitelist as the exhaustive set of root-permitted files.
