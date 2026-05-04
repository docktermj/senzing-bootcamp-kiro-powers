# Tasks

## Task 1: Insert the Conceptual Entity Resolution Section into onboarding-flow.md

- [x] 1.1 Add the `### 4a. What Is Entity Resolution?` heading and agent instruction block after the existing Step 4 overview content (after the glossary bullet point) and before `### 4b. Verbosity Preference`
- [x] 1.2 Write the "Why matching records is hard" subsection with short paragraphs or bullets covering: data quality variance, name variations (with the "John Smith" / "J. Smith" / "Jonathan Smith" example), address changes over time, format inconsistencies across systems, data entry errors (typos, abbreviations), and the false-positive problem (father/son same name same address)
- [x] 1.3 Write the "How Senzing handles it" subsection covering: principle-based matching (not rules or ML), the three attribute behaviors (frequency, exclusivity, stability) with the SSN-exclusive vs DOB-shared example, and preconfigured for people and organizations
- [x] 1.4 Write the "What entity resolution produces" subsection covering: matched entities, cross-source relationships, and deduplication, each framed in business value terms
- [x] 1.5 Add the MCP `search_docs` agent instruction block directing the agent to retrieve Senzing-specific content before presenting, with a static fallback path if MCP is unavailable
- [x] 1.6 Ensure the section does not introduce a mandatory gate, does not duplicate existing Step 4 content (module table, licensing, mock data), and uses only glossary-defined terms or provides inline explanations

## Task 2: Update steering-index.yaml with New Token Count

- [x] 2.1 Run `python3 senzing-bootcamp/scripts/measure_steering.py` to calculate the new token count for `onboarding-flow.md`
- [x] 2.2 Update the `file_metadata.onboarding-flow.md.token_count` value in `senzing-bootcamp/steering/steering-index.yaml` with the calculated count
- [x] 2.3 Recalculate and update the `budget.total_tokens` value (old total minus old onboarding-flow count plus new count)

## Task 3: Validate the Changes

- [x] 3.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` and confirm `onboarding-flow.md` passes with no errors
- [x] 3.2 Run `python3 senzing-bootcamp/scripts/validate_power.py` and confirm all checks pass
- [x] 3.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and confirm token counts match
