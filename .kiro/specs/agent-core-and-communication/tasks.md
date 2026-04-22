# Tasks

## Task 1: Agent Instructions Split and Core Rules

- [x] 1.1 Split monolithic `agent-instructions.md` into compact always-loaded core rules (`inclusion: always`) and separate `onboarding-flow.md` for new-user onboarding (v0.3.0)
- [x] 1.2 Add session entry logic: check `config/bootcamp_progress.json` — if exists load `session-resume.md`, if not load `onboarding-flow.md`
- [x] 1.3 Define file placement table in `agent-instructions.md`: `src/`, `scripts/`, `docs/`, `data/`, `database/`, `config/`, `data/temp/`
- [x] 1.4 Add working-directory-only rule: reject `/tmp`, `%TEMP%`, `~/Downloads`; override MCP-generated paths to project-relative equivalents

## Task 2: Language Steering Files

- [x] 2.1 Create `senzing-bootcamp/steering/lang-python.md` with `fileMatch: *.py` inclusion and Python-specific SDK patterns
- [x] 2.2 Create `senzing-bootcamp/steering/lang-java.md` with `fileMatch: *.java` inclusion and Java-specific SDK patterns
- [x] 2.3 Create `senzing-bootcamp/steering/lang-csharp.md` with `fileMatch: *.cs` inclusion and C#-specific SDK patterns
- [x] 2.4 Create `senzing-bootcamp/steering/lang-rust.md` with `fileMatch: *.rs` inclusion and Rust-specific SDK patterns
- [x] 2.5 Create `senzing-bootcamp/steering/lang-typescript.md` with `fileMatch: *.ts` inclusion and TypeScript-specific SDK patterns

## Task 3: MCP Rules and Failure Handling

- [x] 3.1 Add MCP tool routing table to `agent-instructions.md`: `mapping_workflow` for attributes, `generate_scaffold`/`sdk_guide` for code, `get_sdk_reference` for signatures, `explain_error_code` for errors, `search_docs` for docs, `find_examples` for examples
- [x] 3.2 Add rule: all Senzing facts from MCP tools, never training data; no hand-coded JSON mappings or SDK method names
- [x] 3.3 Add MCP failure rule: retry once, then load `common-pitfalls.md` "MCP Server Unavailable" section, never fabricate
- [x] 3.4 Add MCP skepticism rule: flag `sz_dm_report` tables, beta features, non-core SDK references

## Task 4: Communication Patterns and Special Handling

- [x] 4.1 Add one-question-at-a-time rule with WAIT markers to Communication section of `agent-instructions.md`
- [x] 4.2 Add 👉 input-required marker rule for all questions requiring Bootcamper response
- [x] 4.3 Add data visualization offer: "👉 Would you like me to visualize this data as a web page?" with interactive feature options, save to `docs/` or `data/temp/`
- [x] 4.4 Add zero-matches handling for Module 8: explain outcome and guide through possible causes when entity resolution produces no matches (v0.7.0)
- [x] 4.5 Add SQLite ≤1,000 record recommendation for best bootcamp experience (v0.8.0)
- [x] 4.6 Add AWS CDK guidance: recommend CDK for infrastructure-as-code when deploying to AWS (v0.4.0)
