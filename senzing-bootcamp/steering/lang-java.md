---
inclusion: fileMatch
fileMatchPattern: "**/*.java"
---

# Java + Senzing SDK

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess class names or method parameters
- Use try-with-resources or explicit `try/finally` to guarantee engine `destroy()` is called on shutdown and exceptions
- Load engine configuration from a JSON file using `Files.readString(Path)` — never hardcode configuration
- Catch `SzException` (or the SDK-specific exception hierarchy) separately from general exceptions for clear error diagnosis
- Initialize the Senzing engine once at application startup and reuse the instance — do not create/destroy per record
- Use `explain_error_code` via MCP for any Senzing error codes encountered at runtime

## Common Pitfalls

- **Unclosed engine instances**: Forgetting `destroy()` leaks native resources — always use try-with-resources or a shutdown hook (`Runtime.addShutdownHook`)
- **Classpath misconfiguration**: Senzing JARs must be on the classpath — verify with `java -cp` or Maven/Gradle dependency declarations
- **String encoding assumptions**: Always use `StandardCharsets.UTF_8` when converting between `String` and `byte[]` for record payloads
- **Swallowing exceptions**: Never catch and ignore `SzException` — log the error code and message, then use `explain_error_code` for diagnosis
- **Thread-unsafe engine sharing**: The Senzing engine is thread-safe for concurrent calls, but configuration and initialization are not — init once, then share

## Performance Considerations

- Use `ExecutorService` with a fixed thread pool for parallel record loading — Senzing engine handles concurrent `addRecord` calls
- Size the thread pool to match available CPU cores (start with `Runtime.getRuntime().availableProcessors()`)
- Process records in batches of 100-1000 — read a batch, submit to the pool, then read the next
- Tune JVM heap with `-Xmx` (e.g., `-Xmx4g`) for large datasets — Senzing native memory is separate from JVM heap
- Use `BufferedReader` for line-by-line JSONL processing — avoids loading entire files into memory
- Profile with `jvisualvm` or `async-profiler` to identify bottlenecks before optimizing

## Code Style for Generated Code

- Use Maven or Gradle project structure: `src/main/java/` for source, `src/main/resources/` for configs
- One public class per file — match filename to class name
- Use `java.util.logging` or SLF4J for logging — never `System.out.println` in production code
- Store Senzing configuration in `src/main/resources/` or a `config/` directory — load via classpath or file path
- Define a custom exception class wrapping `SzException` if the project needs application-specific error context

## Platform Notes

- Senzing native libraries require `LD_LIBRARY_PATH` (Linux), `DYLD_LIBRARY_PATH` (macOS), or `PATH` additions (Windows) — follow `sdk_guide` output exactly
- JVM version: use Java 11+ — verify with `java -version` before running
- On Linux, ensure the Senzing SDK shared libraries (`.so` files) are accessible — set paths in shell profile or launch script
- On macOS, set `DYLD_LIBRARY_PATH` to include the Senzing `lib` directory — follow `sdk_guide` output
- On Windows, Senzing DLLs must be on `PATH` — the installer typically handles this, but verify if running from IDE. If missing, add the Senzing `lib` directory to `PATH` in your environment script or system settings
