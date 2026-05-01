# Requirements Document

## Introduction

The bootcamp currently jumps into entity resolution workflows without first explaining why the problem is hard or what makes Senzing's approach different. Bootcampers arrive at track selection (onboarding Step 5) without a mental model of what entity resolution is, why naive matching fails, or what outcomes to expect. This feature adds a concise conceptual section to the onboarding introduction (Step 4) that builds that mental model before the bootcamper chooses a track. The section covers three pillars: why matching records across systems is hard, how Senzing handles it automatically, and what entity resolution produces. All Senzing-specific claims must come from the Senzing MCP server (`search_docs`) rather than training data.

## Glossary

- **Onboarding_Flow**: The `senzing-bootcamp/steering/onboarding-flow.md` steering file that guides the agent through directory creation, language selection, prerequisites, introduction, and track selection
- **Introduction_Step**: Step 4 of the Onboarding_Flow, where the agent presents the welcome banner, bootcamp overview, module table, and contextual information before track selection
- **Conceptual_Section**: A new sub-step within the Introduction_Step that explains entity resolution challenges, Senzing's approach, and expected outcomes
- **Bootcamper**: A developer working through the Senzing bootcamp
- **Entity_Resolution**: The process of determining when different data records refer to the same real-world entity (person, organization, or other entity type) and when they do not
- **Principle_Based_Matching**: Senzing's approach to entity resolution that uses generalized knowledge about attribute behaviors (frequency, exclusivity, stability) rather than hand-coded rules or trained models
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides authoritative Senzing documentation and tools via `search_docs`
- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that guides the agent through a bootcamp module or workflow
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file that maps steering files to their metadata including token counts and step ranges

## Requirements

### Requirement 1: Add a Conceptual Entity Resolution Section to the Onboarding Introduction

**User Story:** As a bootcamper, I want to understand what entity resolution is and why it matters before I choose a track, so that I have a mental model for the work ahead.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL include a Conceptual_Section as a new sub-step within the Introduction_Step (Step 4), positioned after the module overview table and before the verbosity preference (Step 4b)
2. THE Conceptual_Section SHALL be presented to every bootcamper regardless of which track they later select
3. THE Conceptual_Section SHALL be concise enough to read in under two minutes, serving as a mental model builder rather than a comprehensive reference
4. THE Conceptual_Section SHALL use a clear heading that signals its purpose (e.g., "Why Entity Resolution Is Hard — and How Senzing Solves It")

### Requirement 2: Explain Why Matching Records Across Systems Is Hard

**User Story:** As a bootcamper, I want to understand the core challenges of matching records across systems, so that I appreciate why entity resolution requires specialized technology.

#### Acceptance Criteria

1. THE Conceptual_Section SHALL explain that the same real-world person or organization can appear differently across data sources due to data quality variance
2. THE Conceptual_Section SHALL cover at least four specific challenge categories: name variations, address changes over time, format inconsistencies across systems, and data entry errors such as typos and abbreviations
3. THE Conceptual_Section SHALL include at least one concrete example the bootcamper can relate to, such as the same person appearing as "John Smith" in one system, "J. Smith" in another, and "Jonathan Smith" in a third
4. THE Conceptual_Section SHALL explain that similar-looking records can refer to different entities (e.g., a father and son with the same name at the same address), making the problem harder than simple fuzzy matching
5. THE Conceptual_Section SHALL avoid vague generalizations and instead use specific, relatable scenarios to illustrate each challenge

### Requirement 3: Explain How Senzing Handles Entity Resolution Automatically

**User Story:** As a bootcamper, I want to understand how Senzing solves entity resolution without manual rules or model training, so that I know what makes the technology different from other approaches.

#### Acceptance Criteria

1. THE Conceptual_Section SHALL explain that Senzing uses Principle_Based_Matching rather than hand-coded rules or machine learning models that require training data
2. THE Conceptual_Section SHALL explain the three attribute behaviors that Senzing's principles are built on: frequency (how many entities share a value), exclusivity (whether an entity typically has one or many values of that type), and stability (whether the value changes over an entity's lifetime)
3. THE Conceptual_Section SHALL give at least one concrete example of how principles work (e.g., a social security number is typically exclusive to one person, while a date of birth is shared by many)
4. THE Conceptual_Section SHALL state that Senzing comes preconfigured for people and organizations, so the bootcamper can load and resolve data without writing matching rules or training a model
5. WHEN presenting Senzing-specific claims, THE Agent SHALL retrieve content from the MCP_Server using `search_docs` rather than relying on training data

### Requirement 4: Explain What Entity Resolution Produces

**User Story:** As a bootcamper, I want to understand the outputs of entity resolution, so that I know what to expect from the bootcamp and can connect the outputs to my business goals.

#### Acceptance Criteria

1. THE Conceptual_Section SHALL explain that entity resolution produces matched entities — records from different sources recognized as the same real-world person or organization
2. THE Conceptual_Section SHALL explain that entity resolution produces cross-source relationships — connections discovered between entities across data sources
3. THE Conceptual_Section SHALL explain that entity resolution produces deduplication — identification and consolidation of duplicate records within and across sources
4. THE Conceptual_Section SHALL frame these outputs in terms of business value (e.g., "a single view of each customer" or "discovering that a vendor in one system is the same company as a supplier in another")

### Requirement 5: Source All Senzing-Specific Content from the MCP Server

**User Story:** As a maintainer, I want all Senzing-specific claims in the conceptual section sourced from the MCP server, so that the content stays accurate as Senzing evolves.

#### Acceptance Criteria

1. THE Steering_File SHALL include an instruction for the agent to call `search_docs` from the MCP_Server to retrieve authoritative content about Senzing's principle-based approach before presenting the Conceptual_Section
2. THE Steering_File SHALL include an instruction for the agent to call `search_docs` from the MCP_Server to retrieve authoritative content about entity resolution outputs and capabilities
3. IF the MCP_Server is unavailable, THEN THE Agent SHALL present the Conceptual_Section using the static content embedded in the steering file and note to the bootcamper that it will verify details when the server is available
4. THE Steering_File SHALL NOT hardcode Senzing marketing claims, version-specific features, or product comparisons — these must come from the MCP_Server at runtime

### Requirement 6: Preserve Onboarding Flow Structure and Pacing

**User Story:** As a maintainer, I want the conceptual section integrated without disrupting the existing onboarding flow, so that the bootcamper experience remains smooth and the steering file stays structurally sound.

#### Acceptance Criteria

1. THE Conceptual_Section SHALL be positioned within Step 4 of the Onboarding_Flow, after the module overview table and before Step 4b (Verbosity Preference)
2. THE Conceptual_Section SHALL NOT introduce a new mandatory gate — the bootcamper can absorb the content and move on without being required to answer a question
3. THE Conceptual_Section SHALL NOT duplicate content already present in Step 4's existing overview (module table, licensing, mock data availability)
4. WHEN the Conceptual_Section is added, THE Steering_Index SHALL be updated to reflect any change in token count for `onboarding-flow.md`
5. THE modified Onboarding_Flow SHALL pass `validate_commonmark.py` and `validate_power.py` without errors

### Requirement 7: Keep the Section Concise and Scannable

**User Story:** As a bootcamper, I want the conceptual section to be brief and easy to scan, so that it builds my understanding without slowing down my onboarding.

#### Acceptance Criteria

1. THE Conceptual_Section SHALL use short paragraphs or bullet points rather than long prose blocks
2. THE Conceptual_Section SHALL organize content into three clearly labeled parts: challenges, Senzing's approach, and outputs
3. THE Conceptual_Section SHALL avoid jargon that has not been defined in the bootcamp glossary at `docs/guides/GLOSSARY.md` or explained inline
4. THE Conceptual_Section SHALL avoid deep technical detail about Senzing internals — the goal is conceptual understanding, not implementation knowledge
5. THE Conceptual_Section SHALL respect the bootcamper's verbosity preference from Step 4b if it has already been set, or use the standard verbosity level as default
