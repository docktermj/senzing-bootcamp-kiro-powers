# Removed Hooks

This directory contains hooks that were removed from the Power distribution because they are generic software engineering practices rather than bootcamp-specific automation.

## Why These Were Removed

These hooks were moved to the development repository on March 23, 2026 because:

1. **Generic Content**: They contain standard software engineering practices, not bootcamp-specific automation
2. **Conflicts with Workflow**: Some conflict with bootcamp agent instructions
3. **May Be Disruptive**: Trigger on every file save, which may annoy users
4. **Users Can Create Own**: Users who want these can easily create their own hooks

## Files in This Directory (2 files)

### 1. test-before-commit.kiro.hook

**Purpose**: Run pytest tests when source files are saved
**Trigger**: When any source file is edited (`src/**/*.py`)
**Action**: Runs `python -m pytest tests/ -v`

**Why Removed**:

- **Conflicts with agent instructions**: Agent instructions say "DO NOT automatically add tests unless explicitly requested"
- **Assumes tests exist**: Bootcamp doesn't require tests in early modules
- **May fail**: If pytest not installed or no tests directory exists
- **Disruptive**: Runs on every file save
- **Generic practice**: Not specific to bootcamp workflow

**Replacement**: Users who want automated testing can create their own hook or use git pre-commit hooks

### 2. update-documentation.kiro.hook

**Purpose**: Remind to update documentation when programs are modified
**Trigger**: When any source file is edited (`src/**/*.py`)
**Action**: Agent reminds to update docs and add comments

**Why Removed**:

- **Generic reminder**: Not specific to bootcamp workflow
- **Repetitive**: Triggers on every file save
- **Vague**: Generic reminder without specific guidance
- **Already covered**: Bootcamp workflows already emphasize documentation
- **May be annoying**: Users may find it disruptive

**Replacement**: Bootcamp module workflows already include documentation steps

## What Remains in Power (4 hooks)

The Power distribution now contains only bootcamp-specific hooks:

1. **pep8-check.hook** - Enforces bootcamp PEP-8 standards (100 char limit)
2. **data-quality-check.kiro.hook** - Bootcamp quality thresholds (>70%)
3. **backup-before-load.kiro.hook** - References bootcamp scripts
4. **validate-senzing-json.kiro.hook** - Uses bootcamp MCP tool (`lint_record`)

## Impact

**Before**: 6 hooks
**After**: 4 hooks
**Reduction**: 33% fewer hooks

## For Users Who Want These Hooks

If you want automated testing or documentation reminders, you can:

### Option 1: Copy from Development Repository

```bash
# Copy specific hook
cp senzing-bootcamp-power-development/hooks/test-before-commit.kiro.hook .kiro/hooks/

# Or copy both
cp senzing-bootcamp-power-development/hooks/*.kiro.hook .kiro/hooks/
```

### Option 2: Create Your Own

Use Kiro's Hook UI to create custom hooks:

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Search for "Open Kiro Hook UI"
3. Click "Create New Hook"
4. Configure trigger and action

### Option 3: Use Git Pre-commit Hooks

For testing, consider using git pre-commit hooks instead:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python -m pytest tests/ -v
```

## For Future Maintainers

### When Adding New Hooks

Ask these questions:

1. **Is this bootcamp-specific?**
   - If no → Don't add it to Power distribution

2. **Does it conflict with agent instructions?**
   - If yes → Don't add it

3. **Is it disruptive?**
   - If triggers on every save → Consider if it's worth it

4. **Is it generic best practice?**
   - If yes → Let users create their own

5. **Does it provide unique value?**
   - If no → Don't add it

### Bootcamp-Specific Hooks Should

- Enforce bootcamp standards (PEP-8 with 100 char limit)
- Reference bootcamp tools (MCP tools, bootcamp scripts)
- Support bootcamp workflows (quality checks, backups)
- Trigger at appropriate times (not every save)
- Provide specific, actionable guidance

## References Updated

All references to removed hooks have been updated in:

- `senzing-bootcamp/hooks/README.md`
- `senzing-bootcamp/POWER.md`
- `senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md` (if needed)

## Date

**Moved**: March 23, 2026
**Phase**: 7 (Hooks Cleanup)
**Files Moved**: 2 hooks
