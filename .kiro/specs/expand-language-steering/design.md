# Design Document

## Overview

Expand each of the five language steering files in `senzing-bootcamp/steering/` from their current 10-20 lines to 50-100 lines by appending four new sections after the existing content: Senzing SDK Best Practices, Common Pitfalls, Performance Considerations, Code Style for Generated Code, and Platform Notes.

## Architecture

No new files are created. Each existing `lang-*.md` file is modified in-place by appending new sections after the existing content. The frontmatter and existing sections remain untouched.

## Expanded Section Structure

Each language steering file will follow this consistent structure:

```
---
(existing frontmatter — unchanged)
---

# {Language} Standards
(existing content — unchanged)

## Senzing SDK Best Practices
- Language-idiomatic patterns for engine init, config, records, cleanup
- MCP-first guidance for method signatures
- Resource lifecycle management

## Common Pitfalls
- Resource leaks, error handling mistakes, encoding issues
- Each pitfall: problem → correct approach

## Performance Considerations
- Threading/concurrency model for record loading
- Memory management for large datasets
- Batch processing guidance

## Code Style for Generated Code
- Project structure conventions
- Error handling and logging patterns
- Configuration management

## Platform Notes
- OS-specific Senzing SDK considerations
- Installation and runtime differences
```

## Language-Specific Design Decisions

### Python (`lang-python.md`)
- Emphasize context managers for engine lifecycle
- Cover GIL implications — recommend `multiprocessing` over `threading` for CPU-bound ER
- Address `json.loads`/`json.dumps` encoding for Senzing JSON records
- Note `python3` vs `python` command differences across platforms

### Java (`lang-java.md`)
- Emphasize try-with-resources for engine cleanup
- Cover `ExecutorService` thread pool patterns for concurrent loading
- Address `SzException` handling hierarchy
- Note JVM memory tuning (`-Xmx`) for large datasets

### C# (`lang-csharp.md`)
- Emphasize `IDisposable`/`using` for engine lifecycle
- Cover `Task.WhenAll` and `SemaphoreSlim` for async loading
- Address .NET runtime differences (Windows vs Linux deployment)
- Note NuGet package management for Senzing SDK

### Rust (`lang-rust.md`)
- Emphasize ownership model alignment with Senzing engine lifecycle
- Cover `rayon` for parallel record processing
- Address `Result<T, E>` error propagation patterns
- Note that Rust SDK support should be verified via MCP — it may be community/experimental

### TypeScript (`lang-typescript.md`)
- Emphasize `async/await` patterns for SDK calls
- Cover `worker_threads` for CPU-bound ER operations (Node.js)
- Address strict typing for Senzing JSON structures
- Note Node.js native addon considerations for Senzing bindings

## Correctness Properties

### Property 1: Existing Content Preservation
For each language steering file, all lines present before expansion must appear identically in the expanded file. The frontmatter block must be byte-identical.

### Property 2: Line Count Within Range
Each expanded file must be between 50 and 100 lines (inclusive), counted including frontmatter.

### Property 3: Section Ordering
New sections must appear after all existing content. The order within new sections must be: Senzing SDK Best Practices → Common Pitfalls → Performance Considerations → Code Style for Generated Code → Platform Notes.

### Property 4: Consistent Section Headings
All five files must use identical `##` heading names for the new sections to maintain cross-language consistency.

## Files to Modify

| File | Current Lines | Target Lines |
|------|--------------|-------------|
| `senzing-bootcamp/steering/lang-python.md` | ~14 | 50-100 |
| `senzing-bootcamp/steering/lang-java.md` | ~12 | 50-100 |
| `senzing-bootcamp/steering/lang-csharp.md` | ~12 | 50-100 |
| `senzing-bootcamp/steering/lang-rust.md` | ~11 | 50-100 |
| `senzing-bootcamp/steering/lang-typescript.md` | ~12 | 50-100 |
