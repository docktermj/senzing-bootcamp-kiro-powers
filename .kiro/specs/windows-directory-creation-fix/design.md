# Windows Directory Creation Fix — Bugfix Design

## Overview

On Windows, the agent defaults to `mkdir dir1 dir2 dir3...` syntax when creating the project directory structure during Module 0 onboarding. PowerShell's `mkdir` (an alias for `New-Item`) does not accept multiple positional path arguments, causing immediate failure. The `project-structure.md` steering file already documents correct cross-platform patterns but presents them as unlabelled alternatives without explicit platform-selection logic. The fix restructures the steering file's "Create Structure" section to make platform detection mandatory and the correct command unambiguous, so the agent reliably picks the right pattern on every OS.

## Glossary

- **Bug_Condition (C)**: The agent is on Windows AND attempts to create directories using multi-argument `mkdir` syntax
- **Property (P)**: On Windows, the agent uses either the Python `os.makedirs` loop or the PowerShell `ForEach-Object` pipeline, succeeding without error on the first attempt
- **Preservation**: On Linux/macOS the agent continues to use `mkdir -p` with brace expansion; the final directory layout is unchanged on all platforms
- **project-structure.md**: The steering file at `senzing-bootcamp/steering/project-structure.md` that instructs the agent how to create the project directory tree
- **Steering file**: A Markdown document with YAML frontmatter loaded by the Kiro agent to guide its behavior during bootcamp sessions

## Bug Details

### Bug Condition

The bug manifests when the agent runs on Windows and creates the project directory structure during onboarding. The steering file presents three command alternatives (Python, Linux shell, PowerShell) without an explicit "choose based on platform" instruction, so the agent defaults to the familiar `mkdir dir1 dir2 ...` pattern which is invalid on PowerShell.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type DirectoryCreationCommand
  OUTPUT: boolean

  RETURN input.platform == "Windows"
         AND input.commandSyntax == "mkdir <path1> <path2> ... <pathN>"
         AND numberOfPaths(input.commandSyntax) > 1
END FUNCTION
```

### Examples

- **Example 1**: Agent on Windows issues `mkdir data/raw data/transformed data/samples` → PowerShell error "A positional parameter cannot be found that accepts argument 'data/transformed'"
- **Example 2**: Agent on Windows retries with incorrectly quoted pipeline `'data/raw' 'data/transformed' | ForEach-Object { mkdir $_ }` → fails due to quoting issues
- **Example 3**: Agent on Linux issues `mkdir -p data/{raw,transformed,samples}` → succeeds (not a bug condition)
- **Edge case**: Agent on Windows issues `mkdir data/raw` (single path) → succeeds because PowerShell `mkdir` accepts one positional argument (not a bug condition)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- On Linux/macOS, the agent continues to use `mkdir -p` with brace expansion to create all directories in a single command
- When directories already exist, the agent skips creation and proceeds without error on all platforms
- The final directory layout is identical on all platforms: all 18 required subdirectories are created
- The steering file continues to be auto-included (YAML frontmatter `inclusion: auto` unchanged)

**Scope:**
All inputs where the platform is NOT Windows should be completely unaffected by this fix. This includes:
- Linux directory creation via `mkdir -p`
- macOS directory creation via `mkdir -p`
- Any scenario where directories already exist (no creation needed)
- The Python `os.makedirs` loop (cross-platform, already correct)

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Ambiguous command presentation**: The steering file lists three alternatives (Python loop, Linux shell, PowerShell pipeline) as a flat sequence without an explicit "IF Windows THEN use X, ELSE use Y" decision structure. The agent treats them as interchangeable options rather than platform-specific requirements.

2. **Missing platform-detection instruction**: There is no explicit instruction telling the agent to detect the OS before choosing a command. The agent defaults to the most familiar pattern (`mkdir` with multiple args) regardless of platform.

3. **Recommended command not prominent enough**: The Python `os.makedirs` loop is listed first and works on all platforms, but the steering file does not mark it as the preferred/default approach. The agent may skip it in favor of a shell command.

4. **No "DO NOT" constraint**: The steering file lacks an explicit prohibition against multi-argument `mkdir` on Windows, which would serve as a guardrail even if the agent misidentifies the platform.

## Correctness Properties

Property 1: Bug Condition - Windows Directory Creation Uses Valid Syntax

_For any_ directory creation command issued on Windows where multiple directories need to be created, the steering file content SHALL cause the agent to use either the Python `os.makedirs` loop or the PowerShell `ForEach-Object` pipeline, never the multi-argument `mkdir` syntax, resulting in all directories being created without error on the first attempt.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Windows Behavior Unchanged

_For any_ directory creation command issued on Linux or macOS, the fixed steering file SHALL produce the same agent behavior as the original steering file, preserving the use of `mkdir -p` with brace expansion and the identical final directory layout.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/project-structure.md`

**Section**: "Create Structure (execute before any other action)"

**Specific Changes**:

1. **Add explicit platform-selection instruction**: Insert a clear directive at the top of the section: "Detect the operating system first. Use the platform-specific command below that matches the detected OS."

2. **Restructure as conditional blocks**: Replace the flat list of alternatives with labelled, mutually exclusive blocks using headers like "### On Windows (PowerShell)" and "### On Linux / macOS" so the agent cannot conflate them.

3. **Promote Python loop as default/fallback**: Mark the Python `os.makedirs` loop as "Preferred (all platforms)" and place it first with a note that it is always safe to use regardless of OS detection.

4. **Add explicit prohibition**: Add a constraint: "NEVER use `mkdir path1 path2 path3` on Windows — PowerShell's mkdir does not accept multiple positional arguments."

5. **Keep existing commands intact**: The actual command content (the Python loop, the `mkdir -p` brace expansion, the PowerShell `ForEach-Object` pipeline) remains unchanged — only the surrounding structure and selection logic changes.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering content, then verify the fix works correctly and preserves existing behavior. Since the "code under test" is steering file content (not executable code), tests operate on the parsed text of the steering file and simulate agent command selection.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Parse the current `project-structure.md` and verify whether the steering content contains explicit platform-selection logic. Simulate an agent reading the file on Windows and check whether the structure unambiguously directs it to the PowerShell or Python command.

**Test Cases**:
1. **Missing platform gate test**: Verify the current steering file lacks an explicit "if Windows" conditional instruction (will fail on unfixed content — i.e., confirms the gap)
2. **Ambiguous alternatives test**: Verify the current file presents commands as a flat list without mutual exclusivity markers (will fail on unfixed content)
3. **No prohibition test**: Verify the current file lacks a "NEVER use multi-arg mkdir on Windows" constraint (will fail on unfixed content)
4. **Command validity test**: Parse the Linux command and verify it uses `mkdir -p` with brace expansion (should pass — confirms Linux path is fine)

**Expected Counterexamples**:
- The steering file does not contain platform-conditional language
- Possible causes: flat alternative listing, no OS-detection instruction, no prohibition of invalid syntax

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (Windows + multiple directories), the fixed steering file content unambiguously directs the agent to a valid command.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := parseSteeringAndSelectCommand(fixedContent, platform="Windows")
  ASSERT result.command NOT MATCHES "mkdir <path1> <path2>"
  ASSERT result.command MATCHES pythonOsMakedirs OR powershellForEach
  ASSERT result.containsExplicitPlatformGate == True
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (Linux/macOS, or single-directory creation), the fixed steering file produces the same agent behavior as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT parseSteeringAndSelectCommand(originalContent, input.platform)
       == parseSteeringAndSelectCommand(fixedContent, input.platform)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many combinations of platform × directory list to verify no regressions
- It catches edge cases (single directory, empty list, already-existing directories)
- It provides strong guarantees that Linux/macOS behavior is unchanged

**Test Plan**: Parse both the original and fixed steering file content. For non-Windows platforms, verify the Linux/macOS command block is textually identical. For the directory list, verify all 18 required paths appear in every platform variant.

**Test Cases**:
1. **Linux command preservation**: Verify the `mkdir -p` brace-expansion command is textually unchanged after the fix
2. **Directory list preservation**: Verify all 18 required directory paths appear in every platform-specific command block
3. **Python loop preservation**: Verify the Python `os.makedirs` loop content is textually unchanged
4. **Auto-inclusion preservation**: Verify the YAML frontmatter `inclusion: auto` is unchanged

### Unit Tests

- Parse the fixed steering file and assert it contains explicit platform-conditional language (e.g., "On Windows", "On Linux")
- Assert the Windows section does NOT contain multi-argument `mkdir` syntax
- Assert the Windows section contains either `os.makedirs` or `ForEach-Object`
- Assert the prohibition text ("NEVER use `mkdir path1 path2 path3` on Windows") is present
- Assert all 18 required directory paths appear in each platform block

### Property-Based Tests

- Generate random subsets of the 18 directory paths and verify the Windows command template produces valid PowerShell for any subset
- Generate random platform identifiers and verify the steering file's conditional structure routes to the correct command block
- Generate random directory names (with spaces, special chars) and verify the Python `os.makedirs` loop handles them correctly

### Integration Tests

- Load the full fixed `project-structure.md` through the steering parser and verify it passes CommonMark validation
- Verify the fixed file's token count stays within the budget defined in `steering-index.yaml`
- Verify the fixed file retains `inclusion: auto` frontmatter and is picked up by the steering loader
