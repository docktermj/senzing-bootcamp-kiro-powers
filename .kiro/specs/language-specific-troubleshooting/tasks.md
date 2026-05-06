# Tasks: Language-Specific Troubleshooting Sections

## Task 1: Add troubleshooting section to lang-python.md

- [x] 1.1 Read the current `senzing-bootcamp/steering/lang-python.md` to understand its structure and find the insertion point
- [x] 1.2 Add "## Common Environment Issues" section after existing content but before any "Further Reading" section
- [x] 1.3 Add entry: Virtual environment activation failures (Windows `Scripts\activate` vs Unix `bin/activate`)
- [x] 1.4 Add entry: pip vs pip3 confusion (system Python vs venv Python)
- [x] 1.5 Add entry: Python version conflicts (3.11+ required, `python3 --version` check)
- [x] 1.6 Add entry: ModuleNotFoundError for Senzing bindings (install in active venv)
- [x] 1.7 Add entry: PATH issues for Senzing libraries (platform-specific lib paths)

## Task 2: Add troubleshooting section to lang-java.md

- [x] 2.1 Read the current `senzing-bootcamp/steering/lang-java.md`
- [x] 2.2 Add "## Common Environment Issues" section
- [x] 2.3 Add entry: JAVA_HOME not set
- [x] 2.4 Add entry: Classpath configuration for Senzing JAR
- [x] 2.5 Add entry: Maven/Gradle dependency resolution failures
- [x] 2.6 Add entry: JDK version conflicts (17+ required)
- [x] 2.7 Add entry: Module system access errors

## Task 3: Add troubleshooting section to lang-csharp.md

- [x] 3.1 Read the current `senzing-bootcamp/steering/lang-csharp.md`
- [x] 3.2 Add "## Common Environment Issues" section
- [x] 3.3 Add entry: .NET SDK version conflicts (6.0+ required)
- [x] 3.4 Add entry: NuGet package restore failures
- [x] 3.5 Add entry: Runtime identifier (RID) mismatches
- [x] 3.6 Add entry: DLL loading failures for native Senzing libraries
- [x] 3.7 Add entry: Project file configuration issues

## Task 4: Add troubleshooting section to lang-rust.md

- [x] 4.1 Read the current `senzing-bootcamp/steering/lang-rust.md`
- [x] 4.2 Add "## Common Environment Issues" section
- [x] 4.3 Add entry: Senzing sys crate build failures (missing C compiler, pkg-config)
- [x] 4.4 Add entry: Linking errors for native libraries
- [x] 4.5 Add entry: Cargo feature flag configuration
- [x] 4.6 Add entry: MSVC vs GNU toolchain issues on Windows
- [x] 4.7 Add entry: Lifetime/borrow checker patterns for Senzing FFI

## Task 5: Add troubleshooting section to lang-typescript.md

- [x] 5.1 Read the current `senzing-bootcamp/steering/lang-typescript.md`
- [x] 5.2 Add "## Common Environment Issues" section
- [x] 5.3 Add entry: Node.js version conflicts (18+ required)
- [x] 5.4 Add entry: Native addon build failures (node-gyp)
- [x] 5.5 Add entry: ESM vs CommonJS module resolution
- [x] 5.6 Add entry: TypeScript strict mode type errors
- [x] 5.7 Add entry: Package manager conflicts

## Task 6: Update steering-index.yaml token counts

- [x] 6.1 Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get updated token counts for all modified language files
- [x] 6.2 Check if any language file exceeds the 5000-token split threshold
- [x] 6.3 If threshold exceeded: split the troubleshooting section into a separate `lang-{language}-troubleshooting.md` file and add it to steering-index.yaml
- [x] 6.4 Update file_metadata entries in steering-index.yaml for all modified/new files

## Task 7: Write tests

- [x] 7.1 Create `senzing-bootcamp/tests/test_language_troubleshooting.py`
- [x] 7.2 Unit test: each of the 5 language files contains "Common Environment Issues" heading
- [x] 7.3 Unit test: each troubleshooting entry contains "Symptom", "Cause", and "Fix" markers
- [x] 7.4 Unit test: each language file has at least 5 troubleshooting entries
- [x] 7.5 Property test: no language file exceeds split threshold without a corresponding split file existing
- [x] 7.6 Unit test: steering-index.yaml token counts are consistent with actual file sizes (within 10% tolerance)

## Task 8: Validate

- [x] 8.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on all modified steering files
- [x] 8.2 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify no budget overruns
- [x] 8.3 Run `pytest senzing-bootcamp/tests/test_language_troubleshooting.py -v`
