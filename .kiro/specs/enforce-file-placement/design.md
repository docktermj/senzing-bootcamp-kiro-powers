# Design Document

## Overview

This feature adds a fourth check (CHECK 4) to the existing `write-policy-gate.kiro.hook` that enforces file placement rules at the project root level. The hook blocks writes of disallowed file types (`.py`, `.md`, `.jsonl`, `.csv`, non-config `.json`) to the project root and provides corrective routing instructions. Supporting steering files are updated with explicit prohibition language for defense-in-depth enforcement.

## Architecture

This feature adds a fourth check (CHECK 4) to the existing `write-policy-gate.kiro.hook` that enforces file placement rules at the project root level. The design follows the existing hook architecture: a single `preToolUse` hook with multiple sequential checks sharing a fast-path/slow-path pattern. Supporting steering files are updated with explicit prohibition language to provide defense-in-depth.

### Design Principles

1. **Additive-only hook change** — CHECK 4 is appended after CHECK 3; existing checks remain character-for-character identical.
2. **Fast-path preservation** — The existing FAST PATH GATE conditions are extended (not replaced) so that root-whitelisted files still pass silently.
3. **Belt-and-suspenders** — Steering files (agent-instructions.md, project-structure.md) provide first-line prevention; the hook provides hard enforcement.
4. **Content-aware routing for .py** — The hook prompt instructs the agent to inspect file content for keywords (transform/mapper, load, query) to determine the correct subdirectory.

## Components and Interfaces

### Component 1: CHECK 4 — Root File Placement Enforcement

**Location:** `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` (appended after CHECK 3's CONTENT CHECK section)

**Logic Flow:**

```text
CHECK 4: ROOT FILE PLACEMENT
│
├─ Q1: Is the target path in the Project_Root? (no subdirectory segments)
│   └─ NO → This check does not apply. Proceed silently.
│
├─ Q2: Is the filename on the Root_Whitelist?
│   └─ YES → Proceed silently.
│
├─ Q3: Does the filename have a Blocked_Extension?
│   ├─ .py → STOP. Corrective routing (content-aware: src/transform/, src/load/, src/query/, or scripts/)
│   ├─ .md → STOP. Corrective routing → docs/
│   ├─ .jsonl → STOP. Corrective routing → data/ subdirectory
│   ├─ .csv → STOP. Corrective routing → data/ subdirectory
│   └─ .json → STOP. Corrective routing → data/ or config/ based on content
│
└─ Otherwise → Proceed silently (unknown extensions are not blocked).
```

**Root Detection Logic:**

The hook determines a file is "in the Project_Root" by checking that the path has no directory separators after the project base. In prompt terms: the file path is just a filename (e.g., `main.py`) or is at the top level of the working directory (e.g., `my-senzing-project/main.py` with no further nesting).

**Root Whitelist (exact filenames):**

| Filename | Reason |
|----------|--------|
| `.gitignore` | Git configuration |
| `.env` | Environment variables |
| `.env.example` | Environment template |
| `README.md` | Project documentation root |
| `requirements.txt` | Python dependencies |
| `pom.xml` | Java/Maven dependencies |
| `Cargo.toml` | Rust dependencies |
| `package.json` | Node.js dependencies |

**Root Whitelist (pattern-based):**

| Pattern | Reason |
|---------|--------|
| `*.csproj` | .NET project files (any name) |

### Component 2: Corrective Routing Logic

The corrective routing output is part of the CHECK 4 STOP response. It provides the agent with an exact target directory.

**Routing Table:**

| Extension | Content Signal | Target Directory |
|-----------|---------------|-----------------|
| `.py` | Contains `transform`, `mapper`, `mapping` | `src/transform/` |
| `.py` | Contains `load`, `loader`, `ingest` | `src/load/` |
| `.py` | Contains `query`, `search`, `find`, `get_entity` | `src/query/` |
| `.py` | No specific signal (default) | `scripts/` |
| `.md` | Any | `docs/` |
| `.jsonl` | Contains raw/source data | `data/raw/` |
| `.jsonl` | Contains transformed data | `data/transformed/` |
| `.jsonl` | Sample/example data | `data/samples/` |
| `.jsonl` | Temporary/intermediate | `data/temp/` |
| `.csv` | Same content signals as `.jsonl` | `data/raw/`, `data/transformed/`, `data/samples/`, or `data/temp/` |
| `.json` | Data payload (not config) | `data/` subdirectory |
| `.json` | Configuration-like | `config/` |

**Content-Aware .py Routing Prompt Structure:**

```text
STOP. The file `{filename}` is a Python source file and cannot be placed in the project root.

Examine the file content to determine the correct location:
- If it contains transformation/mapping logic (keywords: transform, mapper, mapping, convert): → src/transform/{filename}
- If it contains data loading logic (keywords: load, loader, ingest, import_data): → src/load/{filename}
- If it contains query/search logic (keywords: query, search, find, get_entity, get_record): → src/query/{filename}
- Otherwise (utility scripts, CLI tools, one-off tasks): → scripts/{filename}

Rewrite the file path and retry the write.
```

### Component 3: Agent Instructions Update

**Location:** `senzing-bootcamp/steering/agent-instructions.md` — File Placement section

**Changes:**

Add explicit prohibition language after the existing table and warning:

```markdown
### Root Prohibitions

🚫 **NEVER place these file types in the project root:**

| Blocked Type | Reason | Correct Location |
|---|---|---|
| `.py` files | Source code belongs in `src/` or `scripts/` | `src/transform/`, `src/load/`, `src/query/`, or `scripts/` |
| `.md` files (except `README.md`) | Documentation belongs in `docs/` | `docs/` |
| `.jsonl` files | Data files belong in `data/` | `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/` |
| `.csv` files | Data files belong in `data/` | `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/` |
| Non-config `.json` files | Data payloads belong in `data/` | `data/` or `config/` |

✅ **Only these files are permitted in the project root:**
`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`
```

### Component 4: Project Structure Steering Update

**Location:** `senzing-bootcamp/steering/project-structure.md` — Rules section

**Changes:**

Add explicit prohibition and routing rules after the existing rules:

```markdown
### Root File Placement Enforcement

🚫 **The following file types are NEVER permitted in the project root:**

- **Source code (`.py`)** → Route to `src/transform/`, `src/load/`, `src/query/`, or `scripts/`
- **Documentation (`.md`, except `README.md`)** → Route to `docs/`
- **Data files (`.jsonl`, `.csv`)** → Route to `data/raw/`, `data/transformed/`, `data/samples/`, or `data/temp/`
- **Non-config JSON (`.json`, except `package.json`)** → Route to `data/` or `config/`

✅ **Exhaustive root-permitted file list:**
`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`

No other files may exist in the project root. The `write-policy-gate` hook enforces this at write time.
```

## Interfaces and Data Flow

### Hook Prompt Interface (CHECK 4 Addition)

The CHECK 4 text is appended to the existing `then.prompt` string in the hook JSON. It follows the same structural pattern as CHECKs 1-3:

```text
---

CHECK 4: ROOT FILE PLACEMENT ENFORCEMENT

Examine the target file path for this write operation.

Q1: Is the file being written directly to the project root? (The path has no subdirectory — it's just a filename like `main.py` or `data.jsonl` at the top level of the working directory.)

If NO (file is in a subdirectory like src/transform/main.py or data/raw/input.jsonl): This check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If YES (file is in the project root), continue:

Q2: Is the filename on the ROOT WHITELIST?

ROOT WHITELIST (these files ARE permitted in the project root):
- .gitignore
- .env
- .env.example
- README.md
- requirements.txt
- pom.xml
- Any file ending in .csproj
- Cargo.toml
- package.json

If the filename matches any entry on the ROOT WHITELIST: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If the filename is NOT on the ROOT WHITELIST, check the extension:

BLOCKED EXTENSIONS AND CORRECTIVE ROUTING:

.py files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — Python source files cannot be placed in the project root.
Examine the file content to determine the correct location:
- Transformation/mapping logic (transform, mapper, mapping, convert) → src/transform/{filename}
- Data loading logic (load, loader, ingest, import_data) → src/load/{filename}
- Query/search logic (query, search, find, get_entity, get_record) → src/query/{filename}
- Otherwise (utility scripts, CLI tools) → scripts/{filename}
Rewrite the path and retry.

.md files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — Markdown files (other than README.md) cannot be placed in the project root.
Correct location: docs/{filename}
Rewrite the path and retry.

.jsonl files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — JSONL data files cannot be placed in the project root.
Correct location based on content:
- Raw/source data → data/raw/{filename}
- Transformed/processed data → data/transformed/{filename}
- Sample/example data → data/samples/{filename}
- Temporary/intermediate data → data/temp/{filename}
Rewrite the path and retry.

.csv files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — CSV data files cannot be placed in the project root.
Correct location based on content:
- Raw/source data → data/raw/{filename}
- Transformed/processed data → data/transformed/{filename}
- Sample/example data → data/samples/{filename}
- Temporary/intermediate data → data/temp/{filename}
Rewrite the path and retry.

.json files (not on whitelist):
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — Non-config JSON files cannot be placed in the project root.
Correct location based on content:
- Data payloads → data/raw/{filename} or data/transformed/{filename}
- Configuration → config/{filename}
Rewrite the path and retry.

Any other extension not listed above: Do not acknowledge. Do not explain. Do not print anything. Proceed silently. (Only the listed extensions are blocked.)
```

### FAST PATH GATE Update

The existing FAST PATH GATE conditions must be extended to include the root placement check. The current fast-path condition:

> If ALL of the following are true, produce no output at all:
> - The target path is a normal project-relative file (inside the working directory)
> - The target path does NOT end with '.question_pending'
> - The content does NOT contain SQL patterns...

Becomes:

> If ALL of the following are true, produce no output at all:
> - The target path is a normal project-relative file (inside the working directory)
> - The target path does NOT end with '.question_pending'
> - The content does NOT contain SQL patterns...
> - The target path is NOT a blocked file type in the project root (or if it is in the root, it is on the ROOT WHITELIST)

## Data Models

### Root Whitelist Set

```python
ROOT_WHITELIST_EXACT: set[str] = {
    ".gitignore",
    ".env",
    ".env.example",
    "README.md",
    "requirements.txt",
    "pom.xml",
    "Cargo.toml",
    "package.json",
}

ROOT_WHITELIST_PATTERNS: list[str] = [
    "*.csproj",  # Any .csproj file
]

BLOCKED_EXTENSIONS: set[str] = {".py", ".md", ".jsonl", ".csv", ".json"}

ROUTING_TABLE: dict[str, str | dict[str, str]] = {
    ".py": {
        "transform": "src/transform/",
        "load": "src/load/",
        "query": "src/query/",
        "default": "scripts/",
    },
    ".md": "docs/",
    ".jsonl": "data/",  # with subdirectory based on content
    ".csv": "data/",    # with subdirectory based on content
    ".json": "data/",   # or config/ based on content
}
```

### Decision Logic (Pseudocode)

```python
def check_root_placement(filepath: str) -> str | None:
    """Return corrective message if blocked, None if allowed."""
    filename = basename(filepath)
    directory = dirname(filepath)

    # Not in root → pass
    if directory != "" and directory != ".":
        return None

    # On whitelist → pass
    if filename in ROOT_WHITELIST_EXACT:
        return None
    if any(filename.endswith(pat.lstrip("*")) for pat in ROOT_WHITELIST_PATTERNS):
        return None

    # Check extension
    ext = get_extension(filename)
    if ext not in BLOCKED_EXTENSIONS:
        return None

    # Special case: .md exception for README.md already handled by whitelist
    # Special case: .json exception for package.json already handled by whitelist

    # Blocked → return corrective routing
    return generate_corrective_message(filename, ext)
```

## Error Handling

1. **Unknown extensions in root** — Files with extensions not in `BLOCKED_EXTENSIONS` are allowed through silently. The hook only blocks known problematic types.
2. **Ambiguous .py content** — When the hook cannot determine the correct `src/` subdirectory from content keywords, it defaults to `scripts/`. This is safe because `scripts/` is always a valid location for Python files.
3. **Ambiguous data file routing** — When the hook cannot determine which `data/` subdirectory is appropriate, it lists all options and asks the agent to choose based on content inspection.
4. **Edge case: dotfiles** — Files like `.pylintrc` or `.flake8` do not have blocked extensions (their extension is the full filename) and pass through silently.
5. **Edge case: compound extensions** — Files like `data.json.bak` have extension `.bak`, not `.json`, and pass through silently. Only the final extension is checked.

## Testing Strategy

Tests use **pytest + Hypothesis** and live in `tests/` (repo-level hook tests per project conventions).

### Test File Structure

```text
tests/
├── test_enforce_file_placement_properties.py   # Property-based tests (Hypothesis)
└── test_enforce_file_placement.py              # Example-based unit tests
```

### Test Approach

The tests validate the hook prompt text and steering file content by:
1. Loading the actual hook JSON file and extracting the prompt
2. Parsing the prompt to verify CHECK 4 structure and content
3. Loading steering files and verifying prohibition/routing language
4. Using Hypothesis to generate random filenames and verify classification correctness

### Key Test Helpers

```python
def is_root_path(path: str) -> bool:
    """Determine if a path targets the project root (no subdirectory)."""
    ...

def is_whitelisted(filename: str) -> bool:
    """Check if filename is on the root whitelist."""
    ...

def has_blocked_extension(filename: str) -> bool:
    """Check if filename has a blocked extension."""
    ...

def get_expected_routing(filename: str) -> str:
    """Return the expected corrective routing destination for a blocked file."""
    ...
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Blocked extensions are rejected in root

*For any* filename with a blocked extension (`.py`, `.md` excluding `README.md`, `.jsonl`, `.csv`, `.json` excluding `package.json`) that is not on the Root Whitelist, the hook prompt SHALL contain blocking logic that covers that extension with a STOP directive and corrective routing output.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 2: Whitelisted files are permitted

*For any* filename on the Root Whitelist (including pattern-matched `.csproj` files), the hook prompt SHALL contain whitelist logic that permits the file to proceed silently without blocking.

**Validates: Requirements 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

### Property 3: Corrective routing maps blocked extensions to valid destinations

*For any* blocked file extension, the hook prompt SHALL contain corrective routing that directs the agent to a valid project subdirectory (`src/transform/`, `src/load/`, `src/query/`, `scripts/`, `docs/`, `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/`, or `config/`).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 4: Steering files enumerate all whitelist entries

*For any* file on the Root Whitelist, both `agent-instructions.md` and `project-structure.md` SHALL contain that filename (or its pattern) in their root-permitted file lists.

**Validates: Requirements 4.5, 5.6**

### Property 5: Steering files enumerate all routing destinations

*For any* blocked extension, `project-structure.md` SHALL contain the corrective routing destination(s) for that extension.

**Validates: Requirements 5.5**

### Property 6: Existing hook checks are preserved

*For any* valid hook prompt, the CHECK 1 (SQL blocking), CHECK 2 (single-question enforcement), and CHECK 3 (file path policies) sections SHALL remain character-for-character identical after CHECK 4 is added.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**
