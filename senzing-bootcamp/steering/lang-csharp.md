---
inclusion: fileMatch
fileMatchPattern: "**/*.cs"
---

# C# + Senzing SDK

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess class names or method parameters
- Use `using` statements or `IDisposable` patterns to guarantee engine cleanup — call `get_sdk_reference` for the current cleanup method name
- Load engine configuration from JSON files using `File.ReadAllText()` with `Encoding.UTF8` — never hardcode configuration
- Catch the Senzing-specific exception type (call `get_sdk_reference` for the current exception class name) separately from `System.Exception` for clear error diagnosis
- Initialize the engine once at application startup and reuse — do not create/destroy per record
- Use `explain_error_code` via MCP for any Senzing error codes encountered at runtime

## Common Pitfalls

- **Missing Dispose calls**: Senzing engine wraps native resources — always use `using` blocks or implement `IDisposable` on wrapper classes to ensure cleanup (call `get_sdk_reference` for the current cleanup method)
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
- On macOS, set `DYLD_LIBRARY_PATH` to include the Senzing `lib` directory — native library resolution requires this for .NET P/Invoke calls
- On Windows, Senzing DLLs are typically on `PATH` after installation — verify if running from IDE or CI
- Target `net6.0` or later in `.csproj` — earlier frameworks have limited cross-platform support
- Use `dotnet publish -r linux-x64` (or `win-x64`, `osx-x64`) for self-contained deployments that bundle the runtime

## Common Environment Issues

### .NET SDK Version Conflicts

**Symptom**: `The current .NET SDK does not support targeting .NET 6.0` or `NETSDK1045` error during build
**Cause**: The installed .NET SDK is older than 6.0, which is the minimum required for Senzing bootcamp projects
**Fix**:

1. Check current version: `dotnet --list-sdks`
2. Download and install .NET 6.0+ SDK from <https://dotnet.microsoft.com/download>
3. If multiple SDKs installed, pin the version with a `global.json` file: `{ "sdk": { "version": "6.0.0", "rollForward": "latestMajor" } }`
4. Verify with: `dotnet --version` — should show 6.0 or higher

### NuGet Package Restore Failures

**Symptom**: `Unable to resolve package` or NuGet cannot find the Senzing SDK package during restore
**Cause**: The NuGet package source for Senzing is not configured, or network access to the feed is blocked
**Fix**:

1. Check configured sources: `dotnet nuget list source`
2. Add the Senzing NuGet source if missing: `dotnet nuget add source <url> --name senzing`
3. Clear the NuGet cache and retry: `dotnet nuget locals all --clear && dotnet restore`
4. Verify with: `dotnet restore --verbosity normal`

### Runtime Identifier (RID) Mismatches

**Symptom**: `System.DllNotFoundException` or publish fails with "no RID-specific assets" warnings
**Cause**: The runtime identifier in the project or publish command does not match the target platform's native libraries
**Fix**:

1. Check your platform RID: `dotnet --info` (look for "RID" in the output)
2. Set the correct RID in `.csproj`: `<RuntimeIdentifier>linux-x64</RuntimeIdentifier>` (or `win-x64`, `osx-x64`)
3. For publish: `dotnet publish -r linux-x64 --self-contained`
4. Verify with: `dotnet run --runtime linux-x64` — should start without DLL errors

### DLL Loading Failures for Native Senzing Libraries

**Symptom**: `System.DllNotFoundException: Unable to load shared library 'Sz'` or `libSz.so not found`
**Cause**: The Senzing native libraries are not in a directory the .NET runtime searches for platform-specific binaries
**Fix**:

1. On Linux: `export LD_LIBRARY_PATH=/opt/senzing/lib:$LD_LIBRARY_PATH`
2. On macOS: `export DYLD_LIBRARY_PATH=/opt/senzing/lib:$DYLD_LIBRARY_PATH`
3. On Windows: add the Senzing `lib` directory to the system `PATH`
4. Verify with: `dotnet run` — should execute without DllNotFoundException

### Project File Configuration Issues

**Symptom**: `error MSB4019: The imported project was not found` or PackageReference warnings during build
**Cause**: The `.csproj` file uses an incompatible format or is missing required SDK-style project elements
**Fix**:

1. Ensure the project uses SDK-style format: `<Project Sdk="Microsoft.NET.Sdk">`
2. Set target framework: `<TargetFramework>net6.0</TargetFramework>` (or `net7.0`, `net8.0`)
3. Use PackageReference format for dependencies (not `packages.config`)
4. Verify with: `dotnet build --verbosity minimal` — should complete without MSB errors
