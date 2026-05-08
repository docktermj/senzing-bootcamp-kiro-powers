# Requirements Document

## Introduction

The `senzing-bootcamp/steering/entity-resolution-intro.md` steering file is the
bootcamper's first conceptual explanation of entity resolution (loaded from
`onboarding-flow.md` at Step 4a). The current version covers the essentials
(why matching is hard, principle-based matching, the three outputs) but does
not reflect the depth and currency of what Senzing itself publishes. This
feature refreshes that steering file using authoritative sources: the Senzing
MCP server (`search_docs` at `mcp.senzing.com`) and the public Senzing guide
at <https://senzing.com/what-is-entity-resolution/>. The refresh keeps the
file concise and scannable (suitable for a Step 4a interstitial, well under
the medium token budget), but upgrades the coverage to include modern ER
concepts the current file omits: entity resolution as accurate counting,
false-negative vs. false-positive tradeoffs (overmatching / undermatching),
relationship awareness (disclosed and discovered), ambiguous matches and
invisible false positives, and Senzing's specific differentiators (real-time,
sub-second cold start, no training or fine-tuning, full explainability and
attribution). The file remains manual-inclusion and continues to be loaded via
`#[[file:]]` from `onboarding-flow.md`. All Senzing-specific facts and
product claims are sourced from the MCP server at authoring time and cited
inline so they can be re-verified; the public Senzing page is the backup
source for general ER concepts.

## Glossary

- **Target_File**: The steering file at
  `senzing-bootcamp/steering/entity-resolution-intro.md` that this feature
  refreshes.
- **Onboarding_Flow**: The steering file at
  `senzing-bootcamp/steering/onboarding-flow.md` that loads the Target_File
  via `#[[file:]]` during Step 4a.
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml`
  file that records token counts and size categories for every steering
  file, including the Target_File.
- **Bootcamper**: A developer working through the senzing-bootcamp Kiro
  Power, encountering the Target_File at onboarding Step 4a.
- **Agent**: The Kiro agent presenting the bootcamp, which loads the
  Target_File, optionally calls the MCP_Server, and renders the content to
  the Bootcamper.
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com`, accessed via
  tools such as `search_docs`, that provides authoritative Senzing
  documentation.
- **Senzing_Public_Guide**: The public Senzing article at
  <https://senzing.com/what-is-entity-resolution/> that provides
  authoritative, in-depth coverage of entity resolution concepts.
- **Entity_Resolution**: The discipline of determining when different data
  records refer to the same real-world entity (person, organization, or
  other entity type), when they refer to different entities, and when they
  are related.
- **Principle_Based_Matching**: Senzing's approach to entity resolution,
  which uses generalized knowledge about attribute behaviors (frequency,
  exclusivity, stability) rather than hand-coded rules or trained ML
  models.
- **Relationship_Awareness**: The capability to track connections between
  resolved entities, including disclosed relationships (explicitly stated)
  and discovered relationships (detected through shared attributes).
- **Ambiguous_Match**: A record that could legitimately belong to more than
  one entity based on the attributes present; resolving it arbitrarily
  creates an invisible false positive.
- **CommonMark_Validator**: The repository validator `validate_commonmark.py`
  that checks markdown files for CommonMark compliance.
- **Power_Validator**: The repository validator `validate_power.py` that
  checks structural integrity of the senzing-bootcamp Kiro Power.
- **Steering_Measurer**: The script `measure_steering.py` (invoked with
  `--check` in CI) that verifies Steering_Index token counts match the
  actual content of each steering file.

## Requirements

### Requirement 1: Refresh Target_File Content While Preserving Integration Points

**User Story:** As a Bootcamper, I want the entity resolution introduction to
reflect authoritative and current Senzing material, so that my first mental
model of ER is accurate and matches what I will encounter in the rest of the
bootcamp and on docs.senzing.com.

#### Acceptance Criteria

1. THE Target_File SHALL exist at `senzing-bootcamp/steering/entity-resolution-intro.md` after the refresh.
2. THE Target_File SHALL retain a YAML frontmatter block with `inclusion: manual` as the only inclusion directive.
3. THE Target_File SHALL retain a top-level heading titled "What Is Entity Resolution?".
4. THE Target_File SHALL retain a note stating that the file is loaded via `#[[file:]]` from `onboarding-flow.md` during Step 4a.
5. THE Onboarding_Flow SHALL continue to load the Target_File via the existing `#[[file:senzing-bootcamp/steering/entity-resolution-intro.md]]` reference at Step 4a without path or filename changes.
6. WHEN the refresh is applied, THE Steering_Index SHALL be updated so that the `token_count` and `size_category` entries for `entity-resolution-intro.md` match the refreshed content as measured by the Steering_Measurer.

### Requirement 2: Define Entity Resolution Accurately and Concretely

**User Story:** As a Bootcamper, I want a clear definition of entity
resolution that emphasizes both matching and non-matching, so that I do not
mistake it for simple deduplication or fuzzy matching.

#### Acceptance Criteria

1. THE Target_File SHALL define Entity_Resolution as determining when different data records refer to the same real-world entity, when they refer to different entities, and when they are related.
2. THE Target_File SHALL state that entity resolution applies to multiple entity types (for example, people and organizations) rather than only one.
3. THE Target_File SHALL explain that entity resolution underlies accurate counting (for example, "is this one person or three?") and that downstream analytics depend on that count being correct.
4. THE Target_File SHALL distinguish entity resolution from simple fuzzy matching by stating that ER must also tell similar-looking records apart, not only find matches.

### Requirement 3: Explain Why Matching Records Is Hard, With False-Positive and False-Negative Framing

**User Story:** As a Bootcamper, I want to understand the two failure modes
of matching (missing true matches and overmatching), so that I appreciate
why ER accuracy is a tradeoff problem, not a tuning-up-one-dial problem.

#### Acceptance Criteria

1. THE Target_File SHALL describe at least four concrete data quality challenges that make matching hard: name variations, address changes over time, format inconsistencies (for example, phone or date formats), and data entry errors such as typos or abbreviations.
2. THE Target_File SHALL state that missing a true match is a false negative and describe its concrete consequence (for example, treating one person as two and losing a 360-degree view).
3. THE Target_File SHALL state that incorrectly merging distinct entities is a false positive (overmatching) and describe its concrete consequence using a relatable example such as a father and son who share a name and address.
4. THE Target_File SHALL state that simplistic or purely fuzzy matching cannot reliably distinguish these cases, motivating the need for a capable ER engine.

### Requirement 4: Explain How Entity Resolution Works at a High Level

**User Story:** As a Bootcamper, I want a brief, vendor-neutral view of how
ER works end-to-end, so that I can situate Senzing's approach against the
general process.

#### Acceptance Criteria

1. THE Target_File SHALL describe the general ER pipeline at a high level, covering at minimum: data ingestion and standardization, candidate selection (also known as blocking or indexing), comparison and scoring, classification (match / no match / possible match), and entity clustering.
2. THE Target_File SHALL describe the pipeline in conceptual terms only and SHALL NOT prescribe Senzing SDK calls, code, or implementation specifics (those belong in later bootcamp modules).
3. THE Target_File SHALL note that the most capable ER systems compare each inbound record against everything already known about an entity, not only pairwise against other records.

### Requirement 5: Explain Senzing's Principle-Based Matching Approach

**User Story:** As a Bootcamper, I want to understand what makes Senzing's
matching approach different, so that I can articulate why no rule-writing or
model training is required in later modules.

#### Acceptance Criteria

1. THE Target_File SHALL state that Senzing uses Principle_Based_Matching rather than hand-coded rules or ML models that require training data.
2. THE Target_File SHALL describe the three attribute behaviors that principles are built on: frequency (how common a value is), exclusivity (whether an entity typically has one or many values of that type), and stability (whether the value changes over an entity's lifetime).
3. THE Target_File SHALL give at least one concrete example for each of the three behaviors (frequency, exclusivity, stability) that a Bootcamper with no Senzing background can understand.
4. THE Target_File SHALL state that Senzing comes preconfigured for people and organizations, so the Bootcamper can load and resolve data without writing matching rules or training a model.

### Requirement 6: Cover Relationship Awareness, Disclosed and Discovered Relationships, and Ambiguous Matches

**User Story:** As a Bootcamper, I want to understand that modern ER tracks
relationships and surfaces ambiguous matches, so that I am not surprised
later in the bootcamp when I see "possible match" outputs or cross-source
relationships.

#### Acceptance Criteria

1. THE Target_File SHALL introduce Relationship_Awareness and explain that capable ER systems track connections between resolved entities, not only whether records match.
2. THE Target_File SHALL distinguish disclosed relationships (explicitly stated, for example "Person A is the CEO of Company B") from discovered relationships (detected through shared attributes such as a common address or phone number).
3. THE Target_File SHALL define Ambiguous_Match as a record that could legitimately belong to more than one entity and SHALL explain that arbitrarily resolving such a record creates an invisible false positive.
4. THE Target_File SHALL state that a well-designed ER engine flags ambiguous cases as "possible match" rather than forcing an arbitrary merge.

### Requirement 7: Describe the Outputs and Business Value of Entity Resolution

**User Story:** As a Bootcamper, I want to know what ER produces and why it
matters to a business, so that I can connect the bootcamp's code artifacts
to real business outcomes.

#### Acceptance Criteria

1. THE Target_File SHALL describe the three core outputs of entity resolution: matched entities (records recognized as the same real-world entity), cross-source relationships (connections discovered across data sources), and deduplication (identification and consolidation of duplicate records within and across sources).
2. THE Target_File SHALL frame each output in terms of concrete business value (for example, a 360-degree customer view, discovering that a vendor in procurement is the same company as a supplier in the ERP, or removing duplicate records that inflate customer counts).
3. THE Target_File SHALL state at least two representative use case areas that depend on ER (for example, fraud detection, compliance or KYC, customer 360, or investigations).
4. THE Target_File SHALL explicitly connect these outputs to the rest of the bootcamp by stating that producing, querying, and operationalizing them is what later modules teach.

### Requirement 8: Cover Senzing Differentiators Relevant to the Bootcamp

**User Story:** As a Bootcamper, I want to understand Senzing's concrete
differentiators at a conceptual level, so that I know what to look for in
later modules and can explain Senzing's value to stakeholders.

#### Acceptance Criteria

1. THE Target_File SHALL state that Senzing is designed for real-time, continuous resolution rather than batch-only processing.
2. THE Target_File SHALL state that Senzing requires no training, no fine-tuning, and no ER experts to onboard a new data source.
3. THE Target_File SHALL state that Senzing provides full attribution (every resolved record traces back to its source system and record ID) and full explainability ("why matched" and "why not matched") for every resolution decision.
4. THE Target_File SHALL state that Senzing scales from a laptop to billions of records without changing the engine.
5. THE Target_File SHALL avoid hardcoded marketing numerics (for example, specific customer counts or deployment sizes) that are likely to change over time, instead referring Bootcampers to docs.senzing.com or the MCP_Server for current figures.

### Requirement 9: Source and Cite Senzing-Specific Claims

**User Story:** As a maintainer, I want every Senzing-specific claim to be
traceable to an authoritative source, so that the file can be re-verified
and updated as Senzing evolves.

#### Acceptance Criteria

1. WHILE authoring or updating the Target_File, THE Agent SHALL source Senzing-specific factual claims (principle-based matching, differentiators, product behavior) from the MCP_Server via `search_docs` calls or from the Senzing_Public_Guide.
2. THE Target_File SHALL include a "Sources" section (or equivalent footer) that lists at minimum the Senzing_Public_Guide URL and a reference to the MCP_Server `search_docs` tool.
3. THE Target_File SHALL NOT introduce Senzing-specific facts sourced from the Agent's training data without confirmation from the MCP_Server or the Senzing_Public_Guide.
4. THE Target_File SHALL retain the existing agent-instruction HTML comment block telling the Agent to call `search_docs` before presenting the section, updated to list the specific queries relevant to the refreshed content (for example, principle-based matching, relationship awareness, Agentic Entity Resolution, Senzing differentiators).
5. IF the MCP_Server is unavailable when the Agent loads the Target_File, THEN THE Agent SHALL present the Target_File content as-is and note to the Bootcamper that live Senzing details can be re-verified later, per `mcp-offline-fallback.md`.

### Requirement 10: Preserve Scannability, Pacing, and Token Budget

**User Story:** As a Bootcamper and as a maintainer, I want the refreshed
section to remain fast to read and within its token budget, so that Step 4a
does not become a wall of text and the overall onboarding context stays
bounded.

#### Acceptance Criteria

1. THE Target_File SHALL use short paragraphs, bullet lists, or both, rather than long prose blocks, so that it can be scanned in under two minutes.
2. THE Target_File SHALL organize content under clearly labeled section headings that cover, at minimum: what entity resolution is, why matching is hard (with false-positive and false-negative framing), how ER works, Senzing's approach, relationship awareness and ambiguous matches, and what ER produces.
3. THE Target_File SHALL remain in the `medium` size category as recorded in the Steering_Index (token_count strictly less than the `large` threshold used elsewhere in the Steering_Index).
4. THE Target_File SHALL NOT introduce new mandatory gates, prompts, or questions that block the Bootcamper from advancing past Step 4a.
5. THE Target_File SHALL NOT duplicate content already covered in `onboarding-flow.md` Step 4 (module overview table, licensing, mock data availability).

### Requirement 11: Maintain Repository Validation and Consistency

**User Story:** As a maintainer, I want the refresh to pass all repository
validators, so that CI stays green and the steering file ecosystem stays
consistent.

#### Acceptance Criteria

1. WHEN the refresh is committed, THE CommonMark_Validator SHALL report the Target_File as valid.
2. WHEN the refresh is committed, THE Power_Validator SHALL report no structural errors for the senzing-bootcamp Kiro Power.
3. WHEN the refresh is committed, THE Steering_Measurer SHALL confirm (via `measure_steering.py --check`) that the Steering_Index `token_count` for `entity-resolution-intro.md` matches the measured token count of the refreshed content.
4. THE refreshed Target_File SHALL use terminology consistent with the rest of the senzing-bootcamp steering corpus (for example, continuing to refer to `DATA_SOURCE`, Senzing Entity Specification, and entity resolution using the same casing and phrasing as neighboring steering files).
5. IF any term newly introduced by the refresh is not already defined in `docs/guides/GLOSSARY.md`, THEN THE Target_File SHALL define that term inline on first use.

## Correctness Properties

The following properties describe behaviors that can be verified mechanically
about the refreshed artifact and its integration. They complement the
acceptance criteria above and are written to be checkable either by existing
repository tooling (`validate_commonmark.py`, `validate_power.py`,
`measure_steering.py`) or by a small content-structure test added alongside
this spec.

### Property 1: Integration Invariant (Onboarding Reference Preserved)

For any refresh of the Target_File, the reference
`#[[file:senzing-bootcamp/steering/entity-resolution-intro.md]]` in
`onboarding-flow.md` SHALL continue to resolve to an existing file with
`inclusion: manual` in its frontmatter.

Rationale: this is an invariant preserved across the refresh transformation;
breaking it would silently drop the Step 4a content.

### Property 2: Token Budget Invariant (Steering_Index Consistency)

For the refreshed Target_File, `measure_steering.py --check` SHALL report no
drift between the recorded `token_count` in `steering-index.yaml` and the
measured token count of `entity-resolution-intro.md`.

Rationale: this is the same invariant already enforced in CI for every
steering file; the refresh must not break it.

### Property 3: Source Attribution Invariant

For the refreshed Target_File, the rendered markdown SHALL contain at least
one reference to `senzing.com/what-is-entity-resolution` and at least one
reference to `search_docs` (the MCP_Server tool name), ensuring claims
remain traceable regardless of how the body is edited later.

Rationale: this is a structural invariant of the document, checkable by a
small grep-style assertion; if either reference disappears during a future
edit, the attribution invariant is violated.

### Property 4: Section Coverage Invariant

For the refreshed Target_File, the rendered markdown SHALL contain section
headings (at `##` level) whose concatenated text covers the six conceptual
areas from Requirement 10.2: a definition of entity resolution, the
hard-matching / false-positive / false-negative framing, how ER works at a
high level, Senzing's principle-based approach, relationship awareness and
ambiguous matches, and what ER produces.

Rationale: a future well-meaning edit that deletes one of these sections
should be caught; this is a structural coverage property, not a prose
property.

### Property 5: Idempotent Refresh

Re-running the refresh workflow against an already-refreshed Target_File
SHALL produce no content-meaningful changes (allowing for trivial
whitespace). In particular, the Steering_Index entry for
`entity-resolution-intro.md` SHALL be unchanged on a second run.

Rationale: this is an idempotence property (f(f(x)) = f(x)). It verifies
that the refresh is a stable transformation rather than one that keeps
drifting on each invocation.

### Property 6: No Regression of Existing Core Content

The refreshed Target_File SHALL still contain (in some form) each of the
three principle-based matching behaviors (frequency, exclusivity,
stability) and the three ER outputs (matched entities, cross-source
relationships, deduplication) that appeared in the pre-refresh version.

Rationale: this is a non-regression property on the existing useful content;
the refresh expands coverage and must not silently drop material that the
current version got right.
