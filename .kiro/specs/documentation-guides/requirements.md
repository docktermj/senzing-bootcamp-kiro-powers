# Requirements Document

## Introduction

This spec retroactively documents five documentation and guidance artifacts that help Bootcampers avoid common mistakes, find help efficiently, reflect on completed projects, understand module dependencies, and troubleshoot issues systematically. All artifacts are already implemented and distributed as part of the senzing-bootcamp power.

## Glossary

- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Common_Mistakes_Guide**: The file `docs/guides/COMMON_MISTAKES.md` cataloguing frequent bootcamp mistakes with real examples and fixes.
- **Getting_Help_Guide**: The file `docs/guides/GETTING_HELP.md` defining the support hierarchy and when to use each resource.
- **Lessons_Learned_Template**: The file `templates/lessons_learned.md` providing a post-project retrospective structure.
- **Module_Prerequisites_Diagram**: The file `docs/diagrams/module-prerequisites.md` containing a Mermaid diagram of module dependencies and skip paths.
- **Troubleshooting_Decision_Tree**: The steering file `steering/troubleshooting-decision-tree.md` providing a visual diagnostic flowchart for guided troubleshooting.

## Requirements

### Requirement 1: Mistake Prevention and Help Resources

**User Story:** As a Bootcamper, I want guides covering common mistakes and where to get help, so that I can resolve issues quickly without getting stuck.

#### Acceptance Criteria

1. THE Common_Mistakes_Guide SHALL organize mistakes into categories: data preparation, SDK configuration, loading, query, and production — each with a real example and fix.
2. THE Getting_Help_Guide SHALL present a support hierarchy (agent → FAQ → MCP tools → guides → docs.senzing.com → support) with a quick-reference table showing when to use each resource.
3. WHEN a Bootcamper encounters an issue covered by the Common_Mistakes_Guide, THE Agent SHALL reference the relevant section to accelerate resolution.

### Requirement 2: Retrospective and Learning Path Artifacts

**User Story:** As a Bootcamper, I want a retrospective template and a module dependency diagram, so that I can reflect on completed projects and plan my learning path.

#### Acceptance Criteria

1. THE Lessons_Learned_Template SHALL include sections for project summary, what went well, what could be improved, key decisions with rationale, data insights, and recommendations.
2. THE Module_Prerequisites_Diagram SHALL render a Mermaid diagram showing module dependencies, learning paths, and skip points.
3. THE Troubleshooting_Decision_Tree SHALL provide a visual Mermaid flowchart that guides the Agent through systematic issue diagnosis when loaded as a manual steering file.
