# Tasks

- [x] 1. Expand `senzing-bootcamp/steering/lang-python.md` with new sections
  - [x] 1.1 Append "Senzing SDK Best Practices" section with Python-specific guidance (context managers, MCP-first, json handling)
  - [x] 1.2 Append "Common Pitfalls" section with Python-specific pitfalls (GIL, encoding, resource leaks, error handling)
  - [x] 1.3 Append "Performance Considerations" section (multiprocessing, batch sizes, memory-efficient iteration)
  - [x] 1.4 Append "Code Style for Generated Code" section (project structure, logging, config patterns)
  - [x] 1.5 Append "Platform Notes" section (python3 vs python, OS-specific paths, venv)
  - [x] 1.6 Verify file is 50-100 lines and all existing content is preserved
- [x] 2. Expand `senzing-bootcamp/steering/lang-java.md` with new sections
  - [x] 2.1 Append "Senzing SDK Best Practices" section with Java-specific guidance (try-with-resources, SzException, config loading)
  - [x] 2.2 Append "Common Pitfalls" section with Java-specific pitfalls (unclosed engines, classpath, encoding)
  - [x] 2.3 Append "Performance Considerations" section (ExecutorService, JVM tuning, batch processing)
  - [x] 2.4 Append "Code Style for Generated Code" section (Maven/Gradle structure, logging, exception hierarchy)
  - [x] 2.5 Append "Platform Notes" section (JVM memory flags, OS-specific library paths)
  - [x] 2.6 Verify file is 50-100 lines and all existing content is preserved
- [x] 3. Expand `senzing-bootcamp/steering/lang-csharp.md` with new sections
  - [x] 3.1 Append "Senzing SDK Best Practices" section with C#-specific guidance (IDisposable, using statements, async patterns)
  - [x] 3.2 Append "Common Pitfalls" section with C#-specific pitfalls (disposal, async void, platform runtime)
  - [x] 3.3 Append "Performance Considerations" section (Task.WhenAll, SemaphoreSlim, Span<T>, channels)
  - [x] 3.4 Append "Code Style for Generated Code" section (.NET project structure, ILogger, appsettings.json)
  - [x] 3.5 Append "Platform Notes" section (Windows vs Linux runtime, NuGet, .NET version targeting)
  - [x] 3.6 Verify file is 50-100 lines and all existing content is preserved
- [x] 4. Expand `senzing-bootcamp/steering/lang-rust.md` with new sections
  - [x] 4.1 Append "Senzing SDK Best Practices" section with Rust-specific guidance (ownership, RAII, Result types)
  - [x] 4.2 Append "Common Pitfalls" section with Rust-specific pitfalls (lifetime errors, unsafe FFI, serde)
  - [x] 4.3 Append "Performance Considerations" section (rayon, zero-copy parsing, memory safety advantages)
  - [x] 4.4 Append "Code Style for Generated Code" section (cargo project layout, modules, error types)
  - [x] 4.5 Append "Platform Notes" section (FFI/linking, experimental SDK status, cross-compilation)
  - [x] 4.6 Verify file is 50-100 lines and all existing content is preserved
- [x] 5. Expand `senzing-bootcamp/steering/lang-typescript.md` with new sections
  - [x] 5.1 Append "Senzing SDK Best Practices" section with TypeScript-specific guidance (async/await, strict typing, cleanup)
  - [x] 5.2 Append "Common Pitfalls" section with TypeScript-specific pitfalls (unhandled promises, any types, memory leaks)
  - [x] 5.3 Append "Performance Considerations" section (worker_threads, streaming, backpressure, event loop)
  - [x] 5.4 Append "Code Style for Generated Code" section (src layout, interfaces for Senzing types, error classes)
  - [x] 5.5 Append "Platform Notes" section (Node.js native addons, ESM vs CJS, OS-specific bindings)
  - [x] 5.6 Verify file is 50-100 lines and all existing content is preserved

## Post-Implementation Updates

After initial implementation, generic language standards (PEP-8, Java conventions, etc.) were removed from all 5 language files per Kiro best practices — the model already knows these. Only Senzing SDK-specific content retained. Files trimmed from ~55 to ~47-51 lines each.
