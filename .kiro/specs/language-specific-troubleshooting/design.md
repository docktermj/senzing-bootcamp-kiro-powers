# Design: Language-Specific Troubleshooting Sections

## Overview

Each language steering file gains a "Common Environment Issues" section with structured troubleshooting entries. The agent uses these reactively when the bootcamper reports errors matching known symptoms.

## Entry Format

Each troubleshooting entry follows a consistent three-part structure:

```markdown
### [Symptom Title]

**Symptom**: What the bootcamper sees (error message, behavior)
**Cause**: Why it happens (one sentence)
**Fix**:
1. Step one
2. Step two
3. Verify with: `command`
```

## Content Per Language

### Python (`lang-python.md`)

1. Virtual environment activation failures (Windows vs Unix path differences)
2. pip vs pip3 confusion (system Python conflicts)
3. Python version conflicts (3.11+ required, checking with `python --version`)
4. `ModuleNotFoundError` for Senzing bindings (not installed in active venv)
5. PATH issues on Windows vs Linux/macOS (Senzing lib directory)

### Java (`lang-java.md`)

1. JAVA_HOME not set (platform-specific resolution)
2. Classpath configuration for Senzing JAR
3. Maven vs Gradle dependency resolution failures
4. JDK version conflicts (17+ required)
5. Module system access errors (Java 9+ module boundaries)

### C# (`lang-csharp.md`)

1. .NET SDK version conflicts (6.0+ required)
2. NuGet package restore failures (source configuration)
3. Runtime identifier (RID) mismatches (linux-x64 vs win-x64)
4. DLL loading failures for native Senzing libraries
5. Project file configuration issues (PackageReference format)

### Rust (`lang-rust.md`)

1. Senzing sys crate build failures (missing C compiler, pkg-config)
2. Linking errors for native libraries (LD_LIBRARY_PATH)
3. Cargo feature flag configuration
4. MSVC vs GNU toolchain issues on Windows
5. Lifetime/borrow checker patterns specific to Senzing FFI wrappers

### TypeScript (`lang-typescript.md`)

1. Node.js version conflicts (18+ required)
2. Native addon build failures (node-gyp, Python dependency)
3. ESM vs CommonJS module resolution with Senzing bindings
4. TypeScript strict mode type errors (missing type definitions)
5. Package manager conflicts (npm vs yarn vs pnpm lockfile issues)

## Token Budget Considerations

Each language file currently has a token count tracked in `steering-index.yaml`. Adding 5 troubleshooting entries (~100-150 tokens each) adds approximately 500-750 tokens per file.

**Split threshold check**: If any language file exceeds 5000 tokens after additions, it gets split:

- `lang-python.md` → keeps existing content
- `lang-python-troubleshooting.md` → new file with troubleshooting section only
- `steering-index.yaml` updated with new file entry and keyword routing

## Agent Behavior

The agent uses troubleshooting sections **reactively**:

1. Bootcamper reports an error
2. Agent checks if error matches a known symptom in the loaded language file
3. If match found: reference the fix steps directly
4. If no match: escalate to MCP tools (`explain_error_code`, `search_docs`)

The agent does NOT proactively warn about potential issues — that would be noisy.

## Files Modified

- `senzing-bootcamp/steering/lang-python.md` — add troubleshooting section
- `senzing-bootcamp/steering/lang-java.md` — add troubleshooting section
- `senzing-bootcamp/steering/lang-csharp.md` — add troubleshooting section
- `senzing-bootcamp/steering/lang-rust.md` — add troubleshooting section
- `senzing-bootcamp/steering/lang-typescript.md` — add troubleshooting section
- `senzing-bootcamp/steering/steering-index.yaml` — update token counts (and add split files if needed)

## Testing

- Unit test: each language file contains "Common Environment Issues" section
- Unit test: each troubleshooting entry has Symptom, Cause, and Fix subsections
- Unit test: token counts in steering-index.yaml are updated
- Property test: no language file exceeds split threshold without being split
