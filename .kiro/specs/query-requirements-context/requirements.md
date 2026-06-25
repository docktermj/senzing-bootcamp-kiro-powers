# Requirements Document

## Introduction

In Module 7 Step 1 (Define Query Requirements), the agent currently asks the bootcamper "What questions do you need to answer with your data?" without consulting the business problem document created in Module 1. The bootcamper has already defined their business problem, success criteria, and desired outputs in `docs/business_problem.md` — the agent should read that artifact first, derive query requirements from it, and present them for confirmation rather than asking the bootcamper to repeat themselves.

This feature ensures the agent uses its own previously-created artifacts to maintain continuity across modules. The business problem document exists precisely so that later modules can reference it. If the agent ignores its own artifacts, the bootcamper loses trust in the bootcamp's coherence.

## Glossary

- **Agent**: The Kiro-powered assistant guiding the bootcamper through the Senzing bootcamp modules
- **Business_Problem_Document**: The file at `docs/business_problem.md` created during Module 1, containing the bootcamper's business problem statement, success criteria, and desired outputs
- **Query_Requirements**: The set of queries the bootcamper needs to answer their business questions, derived from success criteria and desired outputs in the Business_Problem_Document
- **Module_07_Steering**: The steering file `module-07-query-visualize-discover.md` that governs agent behavior during Module 7
- **Bootcamper**: The user progressing through the Senzing bootcamp

## Requirements

### Requirement 1: Read Business Problem Before Defining Query Requirements

**User Story:** As a bootcamper, I want the agent to remember what I said in Module 1 about my business problem, so that I do not have to repeat myself when defining queries in Module 7.

#### Acceptance Criteria

1. WHEN Module 7 Step 1 begins, THE Agent SHALL read `docs/business_problem.md` before presenting any query-related question to the Bootcamper
2. IF the Business_Problem_Document contains success criteria or desired outputs, THEN THE Agent SHALL derive between 1 and 10 Query_Requirements from those criteria, present them to the Bootcamper as a proposed list, and indicate which success criterion or desired output each query requirement addresses
3. WHEN presenting derived Query_Requirements, THE Agent SHALL ask the Bootcamper if there is anything to add or change, rather than asking the Bootcamper to restate their query needs from scratch
4. WHEN presenting derived Query_Requirements, THE Agent SHALL reference the source material in a single attribution sentence (e.g., "Based on your business problem from Module 1...") so the Bootcamper understands where the requirements came from
5. IF the Bootcamper rejects all derived Query_Requirements, THEN THE Agent SHALL ask the Bootcamper what queries they need without referencing the rejected derivations further

### Requirement 2: Graceful Fallback When Business Problem Is Unavailable

**User Story:** As a bootcamper who may not have completed Module 1's business problem step, I want the agent to still help me define query requirements, so that I can proceed with Module 7 regardless.

#### Acceptance Criteria

1. IF `docs/business_problem.md` does not exist, THEN THE Agent SHALL fall back to asking the Bootcamper directly what questions they need to answer with their data
2. IF `docs/business_problem.md` exists but contains neither success criteria nor desired outputs (both sections are missing or empty), THEN THE Agent SHALL fall back to asking the Bootcamper directly what questions they need to answer with their data
3. IF `docs/business_problem.md` exists and contains at least one success criterion or at least one desired output, THEN THE Agent SHALL derive Query_Requirements from the available content and follow the Requirement 1 flow
4. IF the Agent falls back to asking directly, THEN THE Agent SHALL not reference Module 1, prior steps, or missing documents, and SHALL phrase the question as a forward-looking prompt (e.g., "What questions do you need to answer with your data?")

### Requirement 3: Update Module 7 Steering File

**User Story:** As a power author, I want the Module 7 steering file to specify the business-problem-first flow, so that every future bootcamper benefits from context-aware query requirement gathering.

#### Acceptance Criteria

1. THE Module_07_Steering Step 1 SHALL instruct the Agent to read `docs/business_problem.md` as the first action before any bootcamper interaction
2. THE Module_07_Steering Step 1 SHALL instruct the Agent to derive query requirements from the success criteria and desired outputs found in the Business_Problem_Document
3. THE Module_07_Steering Step 1 SHALL instruct the Agent to present derived requirements and ask for additions or changes, rather than asking an open-ended question about query needs
4. IF the Business_Problem_Document is missing or contains no success criteria and no desired outputs, THEN THE Module_07_Steering Step 1 SHALL instruct the Agent to fall back to the existing open-ended question about query needs
5. THE Module_07_Steering Step 1 SHALL replace the current open-ended question ("What questions do you need to answer with your data?") with the business-problem-first flow as the primary path, retaining the open-ended question only as the fallback path
