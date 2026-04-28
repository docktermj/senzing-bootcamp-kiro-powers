# Requirements Document

## Introduction

Reorder the Senzing Bootcamp's 12 modules from a 0-based numbering scheme (Modules 0–11) to a 1-based numbering scheme (Modules 1–12), and move the Business Problem module to the front of the sequence. This is a documentation and configuration change that affects module files, steering files, diagrams, guides, scripts, hooks, and all cross-references throughout the senzing-bootcamp power.

The new module order is:

| New Number | Module Name                  | Old Number |
|------------|------------------------------|------------|
| 1          | Business Problem             | 2          |
| 2          | SDK Setup                    | 0          |
| 3          | Quick Demo                   | 1          |
| 4          | Data Collection              | 3          |
| 5          | Data Quality and Mapping     | 4          |
| 6          | Single Source Loading         | 5          |
| 7          | Multi-Source Orchestration    | 6          |
| 8          | Query Validation             | 7          |
| 9          | Performance Testing          | 8          |
| 10         | Security Hardening           | 9          |
| 11         | Monitoring & Observability   | 10         |
| 12         | Deployment & Packaging       | 11         |

## Glossary

- **Module_File**: A markdown file in `senzing-bootcamp/docs/modules/` that documents a single bootcamp module (e.g., `MODULE_1_BUSINESS_PROBLEM.md`).
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides agent workflow instructions for a single module (e.g., `module-01-business-problem.md`).
- **Cross_Reference**: Any textual reference to a module by number, name, or file path that appears in a file other than the module's own Module_File or Steering_File.
- **Module_Number**: The integer identifier assigned to a module (old scheme: 0–11, new scheme: 1–12).
- **Renumbering_System**: The process of changing all Module_Numbers from the old scheme to the new scheme across the entire senzing-bootcamp power.
- **POWER.md**: The top-level power configuration and documentation file at `senzing-bootcamp/POWER.md`.
- **Diagram_File**: A markdown file in `senzing-bootcamp/docs/diagrams/` containing visual representations of module relationships.
- **Guide_File**: A markdown file in `senzing-bootcamp/docs/guides/` providing user-facing guidance.
- **Hook_File**: A `.kiro.hook` file in `senzing-bootcamp/hooks/` that automates agent actions.
- **Script_File**: A Python file in `senzing-bootcamp/scripts/` that provides utility functions for the bootcamp.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps steering files to modules.

## Requirements

### Requirement 1: Rename Module Documentation Files

**User Story:** As a bootcamp maintainer, I want the module documentation filenames to reflect the new numbering scheme, so that file names are consistent with the new module order.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE Module_File for Business Problem SHALL be renamed from `MODULE_2_BUSINESS_PROBLEM.md` to `MODULE_1_BUSINESS_PROBLEM.md`.
2. WHEN the Renumbering_System is applied, THE Module_File for SDK Setup SHALL be renamed from `MODULE_0_SDK_SETUP.md` to `MODULE_2_SDK_SETUP.md`.
3. WHEN the Renumbering_System is applied, THE Module_File for Quick Demo SHALL be renamed from `MODULE_1_QUICK_DEMO.md` to `MODULE_3_QUICK_DEMO.md`.
4. WHEN the Renumbering_System is applied, THE Module_File for Data Collection SHALL be renamed from `MODULE_3_DATA_COLLECTION.md` to `MODULE_4_DATA_COLLECTION.md`.
5. WHEN the Renumbering_System is applied, THE Module_File for Data Quality and Mapping SHALL be renamed from `MODULE_4_DATA_QUALITY_AND_MAPPING.md` to `MODULE_5_DATA_QUALITY_AND_MAPPING.md`.
6. WHEN the Renumbering_System is applied, THE Module_File for Single Source Loading SHALL be renamed from `MODULE_5_SINGLE_SOURCE_LOADING.md` to `MODULE_6_SINGLE_SOURCE_LOADING.md`.
7. WHEN the Renumbering_System is applied, THE Module_File for Multi-Source Orchestration SHALL be renamed from `MODULE_6_MULTI_SOURCE_ORCHESTRATION.md` to `MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`.
8. WHEN the Renumbering_System is applied, THE Module_File for Query Validation SHALL be renamed from `MODULE_7_QUERY_VALIDATION.md` to `MODULE_8_QUERY_VALIDATION.md`.
9. WHEN the Renumbering_System is applied, THE Module_File for Performance Testing SHALL be renamed from `MODULE_8_PERFORMANCE_TESTING.md` to `MODULE_9_PERFORMANCE_TESTING.md`.
10. WHEN the Renumbering_System is applied, THE Module_File for Security Hardening SHALL be renamed from `MODULE_9_SECURITY_HARDENING.md` to `MODULE_10_SECURITY_HARDENING.md`.
11. WHEN the Renumbering_System is applied, THE Module_File for Monitoring & Observability SHALL be renamed from `MODULE_10_MONITORING_OBSERVABILITY.md` to `MODULE_11_MONITORING_OBSERVABILITY.md`.
12. WHEN the Renumbering_System is applied, THE Module_File for Deployment & Packaging SHALL be renamed from `MODULE_11_DEPLOYMENT_PACKAGING.md` to `MODULE_12_DEPLOYMENT_PACKAGING.md`.
13. WHEN the Renumbering_System is complete, THE `senzing-bootcamp/docs/modules/` directory SHALL contain exactly 12 Module_Files numbered 1 through 12 and zero Module_Files numbered 0.

### Requirement 2: Rename Steering Files

**User Story:** As a bootcamp maintainer, I want the steering filenames to reflect the new numbering scheme, so that agents load the correct steering file for each module.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE Steering_File for Business Problem SHALL be renamed from `module-02-business-problem.md` to `module-01-business-problem.md`.
2. WHEN the Renumbering_System is applied, THE Steering_File for SDK Setup SHALL be renamed from `module-00-sdk-setup.md` to `module-02-sdk-setup.md`.
3. WHEN the Renumbering_System is applied, THE Steering_File for Quick Demo SHALL be renamed from `module-01-quick-demo.md` to `module-03-quick-demo.md`.
4. WHEN the Renumbering_System is applied, THE Steering_File for Data Collection SHALL be renamed from `module-03-data-collection.md` to `module-04-data-collection.md`.
5. WHEN the Renumbering_System is applied, THE Steering_File for Data Quality and Mapping SHALL be renamed from `module-04-data-quality-mapping.md` to `module-05-data-quality-mapping.md`.
6. WHEN the Renumbering_System is applied, THE Steering_File for Single Source Loading SHALL be renamed from `module-05-single-source.md` to `module-06-single-source.md`.
7. WHEN the Renumbering_System is applied, THE Steering_File for Multi-Source Orchestration SHALL be renamed from `module-06-multi-source.md` to `module-07-multi-source.md`.
8. WHEN the Renumbering_System is applied, THE Steering_File for Query Validation SHALL be renamed from `module-07-query-validation.md` to `module-08-query-validation.md`.
9. WHEN the Renumbering_System is applied, THE Steering_File for Performance Testing SHALL be renamed from `module-08-performance.md` to `module-09-performance.md`.
10. WHEN the Renumbering_System is applied, THE Steering_File for Security Hardening SHALL be renamed from `module-09-security.md` to `module-10-security.md`.
11. WHEN the Renumbering_System is applied, THE Steering_File for Monitoring & Observability SHALL be renamed from `module-10-monitoring.md` to `module-11-monitoring.md`.
12. WHEN the Renumbering_System is applied, THE Steering_File for Deployment & Packaging SHALL be renamed from `module-11-deployment.md` to `module-12-deployment.md`.
13. WHEN the Renumbering_System is applied, THE Steering_File `module-06-reference.md` SHALL be renamed to `module-07-reference.md`.
14. WHEN the Renumbering_System is complete, THE `senzing-bootcamp/steering/` directory SHALL contain module steering files numbered 01 through 12 and zero module steering files numbered 00.

### Requirement 3: Update Internal Content of Module Files

**User Story:** As a bootcamp user, I want the content inside each module file to display the correct new module number and reference the correct neighboring modules, so that navigation and context are accurate.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE heading and title inside each Module_File SHALL display the new Module_Number for that module.
2. WHEN the Renumbering_System is applied, THE prerequisite references inside each Module_File SHALL reference the correct new Module_Numbers of prerequisite modules.
3. WHEN the Renumbering_System is applied, THE "next module" and "previous module" navigation links inside each Module_File SHALL reference the correct new Module_Numbers and filenames.
4. WHEN the Renumbering_System is applied, THE Cross_References to other modules within each Module_File SHALL use the correct new Module_Numbers.

### Requirement 4: Update Internal Content of Steering Files

**User Story:** As an AI agent, I want the steering file content to reference the correct new module numbers, so that agent workflows navigate between modules correctly.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE heading and title inside each Steering_File SHALL display the new Module_Number for that module.
2. WHEN the Renumbering_System is applied, THE Cross_References to other modules within each Steering_File SHALL use the correct new Module_Numbers and filenames.
3. WHEN the Renumbering_System is applied, THE references to Module_Files within each Steering_File SHALL use the correct new filenames.
4. WHEN the Renumbering_System is applied, THE module transition logic inside each Steering_File SHALL reference the correct new Module_Numbers for predecessor and successor modules.

### Requirement 5: Update POWER.md

**User Story:** As a bootcamp user or agent, I want POWER.md to reflect the new module numbering and order, so that the top-level documentation is accurate.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE module table in POWER.md SHALL list modules numbered 1 through 12 in the new order with Business Problem as Module 1.
2. WHEN the Renumbering_System is applied, THE "Available Steering Files" section in POWER.md SHALL reference the new steering filenames (e.g., `module-01-business-problem.md` for Module 1).
3. WHEN the Renumbering_System is applied, THE learning track descriptions in POWER.md SHALL reference the correct new Module_Numbers (e.g., Track A references Modules 2 and 3 instead of Modules 0 and 1).
4. WHEN the Renumbering_System is applied, THE skip-ahead guidance in POWER.md SHALL reference the correct new Module_Numbers.
5. WHEN the Renumbering_System is applied, THE overview description in POWER.md SHALL state the module range as "Modules 1-12" instead of "Modules 0-11".
6. WHEN the Renumbering_System is applied, THE troubleshooting section in POWER.md SHALL reference the correct new module numbers and filenames.

### Requirement 6: Update Diagram Files

**User Story:** As a bootcamp user, I want the module flow and prerequisite diagrams to reflect the new numbering and order, so that visual aids are accurate.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE module-flow.md diagram SHALL display modules numbered 1 through 12 in the new order with Business Problem as Module 1.
2. WHEN the Renumbering_System is applied, THE module-prerequisites.md Mermaid diagram SHALL display modules numbered 1 through 12 with correct dependency arrows reflecting the new order.
3. WHEN the Renumbering_System is applied, THE learning path descriptions in module-flow.md SHALL reference the correct new Module_Numbers.
4. WHEN the Renumbering_System is applied, THE module dependency list in module-flow.md SHALL reference the correct new Module_Numbers.
5. WHEN the Renumbering_System is applied, THE skip conditions in module-flow.md SHALL reference the correct new Module_Numbers.
6. WHEN the Renumbering_System is applied, THE module outputs list in module-flow.md SHALL reference the correct new Module_Numbers.

### Requirement 7: Update Module README Index

**User Story:** As a bootcamp user, I want the modules README index to list modules in the new order with correct numbers and file links, so that the index is accurate.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE `senzing-bootcamp/docs/modules/README.md` SHALL list modules in order from Module 1 through Module 12.
2. WHEN the Renumbering_System is applied, THE file links in the modules README SHALL point to the correct new Module_File filenames.
3. WHEN the Renumbering_System is applied, THE module dependency diagram in the modules README SHALL reference the correct new Module_Numbers.
4. WHEN the Renumbering_System is applied, THE quick reference table in the modules README SHALL reference the correct new Module_Numbers.

### Requirement 8: Update Guide Files

**User Story:** As a bootcamp user, I want all guide files to reference the correct new module numbers, so that user-facing guidance is accurate.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE Cross_References to modules in all Guide_Files SHALL use the correct new Module_Numbers.
2. WHEN the Renumbering_System is applied, THE file path references to Module_Files in all Guide_Files SHALL use the correct new filenames.
3. WHEN the Renumbering_System is applied, THE file path references to Steering_Files in all Guide_Files SHALL use the correct new filenames.

### Requirement 9: Update Steering Index and Cross-Cutting Steering Files

**User Story:** As an AI agent, I want the steering index and cross-cutting steering files (module-transitions, module-prerequisites, module-completion, onboarding-flow, session-resume) to reference the correct new module numbers, so that agent navigation logic is correct.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE Steering_Index SHALL map the correct new steering filenames to the correct new Module_Numbers.
2. WHEN the Renumbering_System is applied, THE module-transitions.md steering file SHALL reference the correct new Module_Numbers for all transition logic.
3. WHEN the Renumbering_System is applied, THE module-prerequisites.md steering file SHALL reference the correct new Module_Numbers for all prerequisite logic.
4. WHEN the Renumbering_System is applied, THE onboarding-flow.md steering file SHALL reference the correct new Module_Numbers for track definitions and module sequences.
5. WHEN the Renumbering_System is applied, THE session-resume.md steering file SHALL reference the correct new Module_Numbers.
6. WHEN the Renumbering_System is applied, THE module-completion.md steering file SHALL reference the correct new Module_Numbers.

### Requirement 10: Update Hook Files

**User Story:** As a bootcamp maintainer, I want hook files that reference specific module numbers to use the correct new numbers, so that automated checks trigger at the right modules.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE `module11-phase-gate.kiro.hook` Hook_File SHALL be renamed to `module12-phase-gate.kiro.hook` to reflect the new Module_Number for Deployment & Packaging.
2. WHEN the Renumbering_System is applied, THE content of the renamed phase-gate Hook_File SHALL reference Module 12 instead of Module 11.
3. WHEN the Renumbering_System is applied, THE Cross_References to module numbers in all other Hook_Files SHALL use the correct new Module_Numbers.

### Requirement 11: Update Script Files

**User Story:** As a bootcamp maintainer, I want scripts that reference module numbers to use the correct new numbers, so that validation and status scripts work correctly.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE `validate_module.py` Script_File SHALL recognize modules numbered 1 through 12 and reject module number 0.
2. WHEN the Renumbering_System is applied, THE `status.py` Script_File SHALL display modules numbered 1 through 12 in the new order.
3. WHEN the Renumbering_System is applied, THE `repair_progress.py` Script_File SHALL reference modules numbered 1 through 12.
4. WHEN the Renumbering_System is applied, THE Cross_References to module numbers in all other Script_Files SHALL use the correct new Module_Numbers.

### Requirement 12: Update Learning Path Definitions

**User Story:** As a bootcamp user, I want the learning path definitions to reference the correct new module numbers, so that track navigation is accurate across all files.

#### Acceptance Criteria

1. WHEN the Renumbering_System is applied, THE Track A (Quick Demo) path SHALL reference Modules 2 and 3 (SDK Setup → Quick Demo) instead of Modules 0 and 1.
2. WHEN the Renumbering_System is applied, THE Track B (Fast Track) path SHALL reference Modules 5 → 6 → 8 (Data Quality → Single Source → Query Validation) instead of Modules 4 → 5 → 7.
3. WHEN the Renumbering_System is applied, THE Track C (Complete Beginner) path SHALL reference Modules 1 → 4 → 5 → 6 → 8 (Business Problem → Data Collection → Data Quality → Single Source → Query Validation) instead of Modules 2 → 3 → 4 → 5 → 7.
4. WHEN the Renumbering_System is applied, THE Track D (Full Production) path SHALL reference Modules 1 through 12 instead of Modules 0 through 11.
5. WHEN the Renumbering_System is applied, THE auto-insertion rule for SDK Setup SHALL state that Module 2 is auto-inserted instead of Module 0.

### Requirement 13: Preserve Module Dependency Semantics

**User Story:** As a bootcamp maintainer, I want the logical dependency relationships between modules to remain unchanged after renumbering, so that prerequisite logic is correct.

#### Acceptance Criteria

1. THE Renumbering_System SHALL preserve the dependency that Data Collection (Module 4) requires Business Problem (Module 1).
2. THE Renumbering_System SHALL preserve the dependency that Data Quality and Mapping (Module 5) requires Data Collection (Module 4).
3. THE Renumbering_System SHALL preserve the dependency that Single Source Loading (Module 6) requires SDK Setup (Module 2) and Data Quality and Mapping (Module 5).
4. THE Renumbering_System SHALL preserve the dependency that Multi-Source Orchestration (Module 7) requires Single Source Loading (Module 6).
5. THE Renumbering_System SHALL preserve the dependency that Query Validation (Module 8) requires Single Source Loading (Module 6) or Multi-Source Orchestration (Module 7).
6. THE Renumbering_System SHALL preserve the dependency that each production module (Modules 9–12) requires the preceding module.
7. THE Renumbering_System SHALL preserve the dependency that Quick Demo (Module 3) has no strict prerequisites beyond SDK Setup (Module 2).

### Requirement 14: Consistency Validation

**User Story:** As a bootcamp maintainer, I want to verify that no stale references to the old numbering scheme remain after the change, so that the renumbering is complete and correct.

#### Acceptance Criteria

1. WHEN the Renumbering_System is complete, THE senzing-bootcamp power SHALL contain zero references to "Module 0" as a valid module identifier.
2. WHEN the Renumbering_System is complete, THE senzing-bootcamp power SHALL contain zero references to steering filenames using the old numbering scheme (e.g., `module-00-sdk-setup.md`).
3. WHEN the Renumbering_System is complete, THE senzing-bootcamp power SHALL contain zero references to Module_File filenames using the old numbering scheme (e.g., `MODULE_0_SDK_SETUP.md`).
4. WHEN the Renumbering_System is complete, THE `validate_power.py` Script_File SHALL pass validation with zero errors related to module numbering or cross-references.
