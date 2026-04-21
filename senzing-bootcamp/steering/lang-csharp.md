---
inclusion: conditional
fileMatchPattern: "**/*.cs"
---

# C# + Senzing SDK

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess class names or method parameters
- Use `using` statements or `IDisposable` patterns to guarantee engine cleanup — ensures `Destroy()` is called on exit and exceptions
- Load engine configuration from JSON files using `File.ReadAllText()` with `Encoding.UTF8` — never hardcode configuration
- Catch the Senzing-specific exception type separately from `System.Exception` for clear error diagnosis
- Initialize the engine once at application startup and reuse — do not create/destroy per record
- Use `explain_error_code` via MCP for any Senzing error codes encountered at runtime

## Common Pitfalls

- **Missing Dispose calls**: Senzing engine wraps native resources — always use `using` blocks or implement `IDisposable` on wrapper classes
- **Using `async void`**: Never use `async void` except for event handlers — use `async Task` so exceptions propagate correctly
- **Encoding mismatches**: Always specify `Encoding.UTF8` when reading data files — `File.ReadAllText()` defaults to UTF-8 but `StreamReader` may not on all platforms
- **Blocking on async code**: Never call `.Result` or `.Wait()` on async SDK calls — use `await` throughout to avoid deadlocks
- **Ignoring nullable warnings**: Enable `<Nullable>enable</Nullable>` in the project file — Senzing API responses may contain null fields

## Performance Considerations

- Use `Task.WhenAll` with `SemaphoreSlim` to throttle concurrent record loading — limit concurrency to CPU core count
- Use `Channel<T>` (producer-consumer) for streaming records from file readers to engine workers
- Process records in batches of 100-1000 — use `IAsyncEnumerable<T>` for memory-efficient streaming from large files
- Use `Span<T>` and `Memory<T>` for zero-allocation JSON parsing where performance is critical
- Profile with `dotnet-trace` and `dotnet-counters` before optimizing — identify whether bottleneck is I/O or CPU
- Senzing native memory is outside the .NET GC heap — monitor process memory, not just GC metrics

## Code Style for Generated Code

- Use standard .NET project layout: `src/ProjectName/` with `.csproj`, `Program.cs`, and organized folders
- Use `ILogger<T>` via `Microsoft.Extensions.Logging` — configure in `Program.cs` with console and file sinks
- Store configuration in `appsettings.json` — load with `IConfiguration` from `Microsoft.Extensions.Configuration`
- Use top-level statements for simple CLI tools — use `HostBuilder` for more complex applications
- Define record types or DTOs for Senzing JSON structures — avoid passing raw `string` or `JsonElement` through layers

## Platform Notes

- .NET 6+ runs cross-platform — but Senzing native libraries differ per OS; follow `sdk_guide` output for library paths
- On Linux, set `LD_LIBRARY_PATH` to include Senzing shared library directory before running `dotnet run`
- On Windows, Senzing DLLs are typically on `PATH` after installation — verify if running from IDE or CI
- Target `net6.0` or later in `.csproj` — earlier frameworks have limited cross-platform support
- Use `dotnet publish -r linux-x64` (or `win-x64`) for self-contained deployments that bundle the runtime
