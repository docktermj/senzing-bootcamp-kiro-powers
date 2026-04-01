# Dependency Management Policy

## Overview

When generating source code for the Senzing Boot Camp, a dependency file appropriate for the chosen programming language must be created or updated in the project root.

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

- Module 1: Quick Demo scripts
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

## Related Documentation

- `CODE_QUALITY_STANDARDS.md` — Coding standards by language
- `FILE_STORAGE_POLICY.md` — Where to store project files

## Version History

- **v2.0.0** (2026-04-01): Expanded from Python-only to multi-language dependency management
- **v1.0.0** (2026-03-17): Initial Python requirements policy
