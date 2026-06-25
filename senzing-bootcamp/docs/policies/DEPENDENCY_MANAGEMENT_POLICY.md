# Dependency Management Policy

## Overview

When generating source code for the Senzing Bootcamp, a dependency file appropriate for the chosen programming language must be created or updated in the project root.

## Dependency Files by Language

| Language   | File                | Tool     |
|------------|---------------------|----------|
| Python     | `requirements.txt`  | pip      |
| Java       | `pom.xml`           | Maven    |
| Java       | `build.gradle`      | Gradle   |
| C#         | `*.csproj`          | dotnet   |
| Rust       | `Cargo.toml`        | cargo    |
| TypeScript | `package.json`      | npm/yarn |

## When to Create/Update

Create or update the dependency file when generating code in:

- Module 3: System Verification scripts
- Module 5: Data transformation programs
- Module 6: Data loading programs
- Module 8: Query programs
- Any utility scripts in `src/utils/`

## File Location

The dependency file goes in the project root:

```text
project/
├── requirements.txt / pom.xml / Cargo.toml / package.json
├── src/
│   ├── quickstart_demo/
│   ├── transform/
│   ├── load/
│   ├── query/
│   └── utils/
└── ...
```

## Agent Behavior

When generating code, the agent should:

1. Check if the appropriate dependency file exists
2. If not, create it in the project root
3. If yes, update it with new dependencies
4. Use version constraints appropriate for the language
5. Organize dependencies by category with comments
6. Avoid duplicates

## Version Pinning Strategy

### Development/Evaluation

Use minimum version constraints to get latest compatible versions.

### Production

Pin exact versions for reproducible builds.

## Power Tooling Scripts (this repository)

The bootcamp's own Python tooling in `senzing-bootcamp/scripts/` is standard-library only, with two narrow exceptions:

- **PyYAML** — used only by `validate_dependencies.py`.
- **fpdf2** (`import fpdf`) — an OPTIONAL, lazily-imported dependency used only by the two PDF-generation scripts, `generate_recap_pdf.py` and `generate_completion_summary.py`. It is imported lazily inside the rendering functions (never at module top level), so the scripts import and run their markdown/parsing paths without it. When `fpdf2` is absent the scripts degrade gracefully: they keep the Markdown output and print an install hint (`pip install fpdf2`) instead of failing. `fpdf2` MUST NOT be promoted to a hard/top-level dependency, and the stdlib-only import audit (in `tests/test_eval_conversations.py`) covers `eval_conversations.py` only — it does not apply to these two generators.

## Related Documentation

- `CODE_QUALITY_STANDARDS.md` — Coding standards by language
- `FILE_STORAGE_POLICY.md` — Where to store project files

## Version History

- **v2.0.0** (2026-04-01): Expanded from Python-only to multi-language dependency management
- **v1.0.0** (2026-03-17): Initial Python requirements policy
