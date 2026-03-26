# Hooks Directory Analysis - March 23, 2026

## Question

Are all files in `senzing-bootcamp/hooks/` needed by the Power?

## Current Structure

```text
hooks/
├── README.md
├── pep8-check.hook
├── data-quality-check.kiro.hook
├── backup-before-load.kiro.hook
├── test-before-commit.kiro.hook
├── update-documentation.kiro.hook
└── validate-senzing-json.kiro.hook
```

**Total**: 7 files (1 README + 6 hook definitions)

## What Are Hooks?

Kiro hooks are automation triggers that:

- Execute actions when specific events occur (file edits, saves, etc.)
- Remind users to perform quality checks
- Run automated tests or validations
- Help maintain code quality and best practices

## Analysis of Each Hook

### 1. pep8-check.hook ✅ KEEP

**Purpose**: Check Python files for PEP-8 compliance
**Trigger**: When any `.py` file is edited
**Action**: Agent checks for PEP-8 violations and suggests fixes

**Boot camp-specific?**: Yes

- Boot camp requires PEP-8 compliance (max line length 100)
- Referenced in POWER.md and PEP8_COMPLIANCE.md
- Essential for maintaining code quality standards

**Value**: Enforces boot camp code quality standards automatically

### 2. data-quality-check.kiro.hook ✅ KEEP

**Purpose**: Remind to validate data quality after transformation changes
**Trigger**: When transformation programs are saved (`src/transform/*.py`)
**Action**: Agent reminds to run quality validation (>70% coverage)

**Boot camp-specific?**: Yes

- Module 3 focuses on data quality scoring
- Boot camp has specific quality thresholds (>70%)
- Prevents quality degradation during mapping iterations

**Value**: Maintains data quality throughout Module 4 iterations

### 3. backup-before-load.kiro.hook ✅ KEEP

**Purpose**: Remind to backup database before loading
**Trigger**: When loading programs are modified (`src/load/*.py`)
**Action**: Agent reminds to backup using `./scripts/backup_database.sh`

**Boot camp-specific?**: Yes

- References boot camp script location (`./scripts/`)
- Critical for Module 6 (loading)
- Prevents data loss during boot camp

**Value**: Protects users from data loss during loading experiments

### 4. test-before-commit.kiro.hook ⚠️ QUESTION

**Purpose**: Run pytest tests when source files are saved
**Trigger**: When any source file is edited (`src/**/*.py`)
**Action**: Runs `python -m pytest tests/ -v`

**Boot camp-specific?**: Partially

- Generic testing practice (not boot camp-specific)
- Boot camp doesn't require tests (agent instructions say "DO NOT automatically add tests")
- May annoy users who don't have tests

**Concerns**:

- Runs on every file save (could be disruptive)
- Assumes pytest is installed
- Assumes tests exist in `tests/` directory
- Boot camp doesn't emphasize testing until later modules

**Value**: Good practice but may not fit boot camp workflow

### 5. update-documentation.kiro.hook ⚠️ QUESTION

**Purpose**: Remind to update documentation when code changes
**Trigger**: When any source file is edited (`src/**/*.py`)
**Action**: Agent reminds to update docs and add comments

**Boot camp-specific?**: No

- Generic software engineering practice
- Not specific to boot camp workflow
- May be annoying if triggered on every save

**Concerns**:

- Triggers on every file save (could be disruptive)
- Generic reminder, not boot camp-specific
- Users may find it repetitive

**Value**: Good practice but generic, not boot camp-specific

### 6. validate-senzing-json.kiro.hook ✅ KEEP

**Purpose**: Validate Senzing JSON output format
**Trigger**: When transformed data files are modified (`data/transformed/*.jsonl`)
**Action**: Agent suggests using `lint_record` MCP tool

**Boot camp-specific?**: Yes

- Validates against Senzing Generic Entity Specification (SGES)
- Uses boot camp MCP tool (`lint_record`)
- Critical for Module 4 (data mapping)
- Ensures output quality before loading

**Value**: Catches mapping errors early, prevents loading bad data

### 7. README.md ✅ KEEP

**Purpose**: Documentation for hooks
**Content**:

- Description of each hook
- Installation instructions
- Customization guide
- Troubleshooting
- Recommended hooks by module

**Value**: Essential documentation for users to understand and use hooks

## References to Hooks

### From POWER.md

```markdown
## Recommended Hooks

Install pre-configured hooks to automate quality checks and reminders.
See `hooks/README.md` and `docs/guides/HOOKS_INSTALLATION_GUIDE.md` for details.

Available hooks:
- Data Quality Check
- Backup Before Load
- Test Before Commit
- Validate Senzing JSON
- Update Documentation
- PEP-8 Compliance Check

# Copy hooks
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/
```

### From steering/steering.md

```markdown
## Workflow: Install Senzing Boot Camp Hooks (Before Module 4)

1. Check if `.kiro/hooks/` exists
2. Create with `mkdir -p .kiro/hooks` if needed
3. Copy hook files
4. Verify installation
5. Explain hook behavior
6. Commit to git
```

### From docs/guides/HOOKS_INSTALLATION_GUIDE.md

Complete guide for installing and customizing hooks.

### From steering/agent-instructions.md

```markdown
### Module 6: Loading
- **Verify `.kiro/hooks/` exists** before installing hooks
- **Remind to backup** before loading (or use backup hook)
```

## Hook Usage by Module

| Module       | Recommended Hooks                        |
|--------------|------------------------------------------|
| **Module 3** | PEP-8, Data Quality, Validate JSON, Test |
| **Module 5** | PEP-8, Backup Before Load, Test          |
| **Module 6** | PEP-8, Test, Update Docs                 |

## Analysis: Generic vs Boot Camp-Specific

### Boot Camp-Specific Hooks (4) ✅

1. **pep8-check.hook** - Enforces boot camp PEP-8 standards (100 char limit)
2. **data-quality-check.kiro.hook** - Boot camp quality thresholds (>70%)
3. **backup-before-load.kiro.hook** - References boot camp scripts
4. **validate-senzing-json.kiro.hook** - Uses boot camp MCP tool

### Generic Hooks (2) ⚠️

1. **test-before-commit.kiro.hook** - Generic testing practice
2. **update-documentation.kiro.hook** - Generic documentation reminder

## Concerns with Generic Hooks

### test-before-commit.kiro.hook

**Issues**:

1. **Conflicts with agent instructions**: Agent instructions say "DO NOT automatically add tests unless explicitly requested"
2. **Assumes tests exist**: Boot camp doesn't require tests until later modules
3. **May fail**: If pytest not installed or no tests exist
4. **Disruptive**: Runs on every file save
5. **Not boot camp workflow**: Testing isn't emphasized in early modules

**Alternative**: Users can create their own test hooks if needed

### update-documentation.kiro.hook

**Issues**:

1. **Generic reminder**: Not specific to boot camp workflow
2. **Repetitive**: Triggers on every file save
3. **Not actionable**: Vague reminder without specific guidance
4. **Annoying**: Users may find it disruptive

**Alternative**: Boot camp already emphasizes documentation in module workflows

## Recommendation

### KEEP (5 files) ✅

1. **README.md** - Essential documentation
2. **pep8-check.hook** - Boot camp code quality standards
3. **data-quality-check.kiro.hook** - Boot camp quality thresholds
4. **backup-before-load.kiro.hook** - Boot camp-specific safety
5. **validate-senzing-json.kiro.hook** - Boot camp MCP tool integration

### REMOVE (2 files) ⚠️

1. **test-before-commit.kiro.hook** - Generic, conflicts with boot camp workflow
2. **update-documentation.kiro.hook** - Generic, not boot camp-specific

## Rationale for Removal

### test-before-commit.kiro.hook (2)

**Why remove**:

- Conflicts with agent instructions (no automatic tests)
- Boot camp doesn't require tests in early modules
- May fail if pytest not installed
- Generic practice, not boot camp-specific
- Users can create their own if needed

**Impact of removal**:

- ✅ Aligns with agent instructions
- ✅ Reduces potential errors (missing pytest)
- ✅ Less disruptive to users
- ✅ Users who want testing can add their own hook

### update-documentation.kiro.hook (3)

**Why remove**:

- Generic software engineering practice
- Not specific to boot camp workflow
- May be annoying (triggers on every save)
- Boot camp already emphasizes documentation
- Vague reminder without specific guidance

**Impact of removal**:

- ✅ Less disruptive to users
- ✅ Removes generic content
- ✅ Boot camp workflows already cover documentation
- ✅ Users can create their own if needed

## Updated Structure

After removal:

```text
hooks/
├── README.md
├── pep8-check.hook
├── data-quality-check.kiro.hook
├── backup-before-load.kiro.hook
└── validate-senzing-json.kiro.hook
```

**Total**: 5 files (1 README + 4 boot camp-specific hooks)

## Update README.md

The README.md should be updated to:

1. Remove references to removed hooks
2. Update "Available Hooks" section
3. Update "Recommended Hooks by Module" section
4. Keep installation and customization instructions

## Update References

Files that reference the removed hooks:

- **POWER.md** - Update "Available hooks" list
- **hooks/README.md** - Remove from "Available Hooks" section
- **steering/steering.md** - Update hook installation workflow (if specific hooks mentioned)

## Comparison with Previous Cleanups

### What We Removed (Phases 1-5)

1. **Generic best practices** - Not boot camp-specific
2. **Duplicate MCP content** - MCP server provides it
3. **Static demo scripts** - MCP generates dynamically

### Why These Hooks Are Similar

The two hooks to remove are:

- **Generic practices** (testing, documentation)
- **Not boot camp-specific**
- **May conflict with boot camp workflow** (test-before-commit)
- **Users can create their own** if needed

## Alternative: Keep But Mark as Optional

Instead of removing, we could:

1. Keep the hooks but mark them as "optional"
2. Update README to indicate they're generic
3. Don't recommend them in POWER.md
4. Let users decide if they want them

**Decision**: Remove is better because:

- Cleaner distribution
- Avoids confusion about what's recommended
- Aligns with boot camp workflow
- Users can easily create their own

## File Count Impact

**Before**: 7 files (1 README + 6 hooks)
**After**: 5 files (1 README + 4 hooks)
**Reduction**: 2 files (29% reduction)

## Conclusion

**REMOVE 2 FILES** from `senzing-bootcamp/hooks/`:

- test-before-commit.kiro.hook (generic, conflicts with workflow)
- update-documentation.kiro.hook (generic, not boot camp-specific)

**KEEP 5 FILES**:

- README.md (documentation)
- pep8-check.hook (boot camp code standards)
- data-quality-check.kiro.hook (boot camp quality thresholds)
- backup-before-load.kiro.hook (boot camp safety)
- validate-senzing-json.kiro.hook (boot camp MCP integration)

All remaining hooks are boot camp-specific and provide value aligned with the boot camp workflow.

## Version

- **Date**: March 23, 2026
- **Analysis**: Complete
- **Recommendation**: Remove 2 generic hooks, keep 5 boot camp-specific hooks
- **Status**: ⚠️ Action needed
