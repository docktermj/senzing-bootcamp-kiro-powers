# Requirements: Language-Specific Troubleshooting Sections

## Overview

The common-pitfalls and FAQ guides are language-agnostic, but the bootcamp supports 5 languages (Python, Java, C#, Rust, TypeScript) each with distinct environment issues. This feature adds language-specific troubleshooting content to the existing language steering files so the agent can provide targeted help for environment and tooling problems that aren't Senzing-specific.

## Requirements

1. Each language steering file (`lang-python.md`, `lang-java.md`, `lang-csharp.md`, `lang-rust.md`, `lang-typescript.md`) gains a "Common Environment Issues" section
2. The Python section covers: virtual environment activation failures, pip vs pip3 confusion, Python version conflicts (3.11+ required), `ModuleNotFoundError` for Senzing bindings, PATH issues on Windows vs Linux/macOS
3. The Java section covers: JAVA_HOME not set, classpath configuration for Senzing JAR, Maven vs Gradle dependency resolution failures, JDK version conflicts (17+ required), module system access errors
4. The C# section covers: .NET SDK version conflicts (6.0+ required), NuGet package restore failures, runtime identifier (RID) mismatches, DLL loading failures for native Senzing libraries, project file configuration issues
5. The Rust section covers: Senzing sys crate build failures (missing C compiler, pkg-config), linking errors for native libraries, cargo feature flag configuration, MSVC vs GNU toolchain issues on Windows, lifetime/borrow checker patterns specific to Senzing FFI
6. The TypeScript section covers: Node.js version conflicts (18+ required), native addon build failures (node-gyp), ESM vs CommonJS module resolution with Senzing bindings, TypeScript strict mode type errors, package manager conflicts (npm vs yarn vs pnpm)
7. Each troubleshooting entry follows a consistent format: symptom (what the bootcamper sees), cause (why it happens), fix (step-by-step resolution)
8. The agent uses these sections reactively — when the bootcamper reports an error that matches a known symptom, the agent references the relevant troubleshooting entry before escalating to MCP tools
9. The troubleshooting sections are placed after the existing language-specific content but before any "Further Reading" sections
10. Token budget impact is tracked — each language file's `file_metadata` entry in `steering-index.yaml` is updated after additions
11. If a troubleshooting section would push a language file over the 5000-token split threshold, it is split into a separate `lang-{language}-troubleshooting.md` file with appropriate `steering-index.yaml` entries

## Non-Requirements

- This does not replace MCP-based error resolution (MCP is still the primary source for Senzing-specific errors)
- This does not cover Senzing API errors (those are handled by `explain_error_code` MCP tool)
- This does not add new dependencies or scripts
