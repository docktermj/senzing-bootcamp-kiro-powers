# Senzing Boot Camp Hooks

This directory contains pre-configured Kiro hooks to support the Senzing Boot Camp workflow.

## Available Hooks

### 1. PEP-8 Compliance Check (`pep8-check.kiro.hook`) ⭐

**Trigger**: When Python files are edited
**Action**: Checks for PEP-8 compliance and suggests fixes
**Use case**: Ensures all Python code follows PEP-8 standards
**Recommended**: Install for all modules that generate Python code

### 2. Data Quality Check (`data-quality-check.kiro.hook`)

**Trigger**: When transformation programs are saved
**Action**: Reminds to validate data quality
**Use case**: Ensures transformation changes don't degrade data quality

### 3. Backup Before Load (`backup-before-load.kiro.hook`)

**Trigger**: When loading programs are modified
**Action**: Reminds to backup database before running
**Use case**: Prevents data loss from failed loads

### 4. Validate Senzing JSON (`validate-senzing-json.kiro.hook`)

**Trigger**: When Senzing JSON output files are modified
**Action**: Suggests validating with lint_record
**Use case**: Ensures output conforms to SGES

### 5. Backup Project on Request (`backup-project-on-request.kiro.hook`)

**Trigger**: When user submits a prompt requesting a backup
**Action**: Automatically runs the project backup script
**Use case**: Quick project backups via natural language commands
**Example prompts**: "backup my project", "create a backup", "make a backup"

## Installation

### Option 1: Use Install Script (Recommended)

```bash
# Interactive installation with guided options
./scripts/install_hooks.sh
```

This script provides:

- Install all hooks at once
- Install essential hooks only
- Select hooks individually
- Prevents duplicate installations
- Shows descriptions of each hook

### Option 2: Copy to Workspace Hooks Directory

```bash
# Copy all hooks to your project
cp senzing-bootcamp/hooks/*.kiro.hook .kiro/hooks/

# Or copy individual hooks
cp senzing-bootcamp/hooks/data-quality-check.kiro.hook .kiro/hooks/
```

### Option 3: Use Kiro Command Palette

1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Search for "Open Kiro Hook UI"
3. Click "Import Hook"
4. Select hook file from `senzing-bootcamp/hooks/`

### Option 4: Ask the Agent

Simply ask: "Please install the Senzing Boot Camp hooks from the power directory"

## Enabling/Disabling Hooks

Hooks are enabled by default when copied to `.kiro/hooks/`. To disable a hook:

1. Open the hook file in `.kiro/hooks/`
2. Set `"enabled": false` in the JSON
3. Or delete the hook file

## Customizing Hooks

You can customize any hook by editing the JSON file:

- **patterns**: Change which files trigger the hook
- **prompt**: Modify what the agent says
- **command**: Change what command runs
- **timeout**: Adjust command timeout

Example customization:

```json
{
  "name": "My Custom Hook",
  "when": {
    "type": "fileEdited",
    "patterns": ["my-custom-pattern/*.py"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "My custom message"
  }
}
```

## Recommended Hooks by Module

### All Modules

- ✅ **PEP-8 Compliance Check** (ensures code quality for Python)
- ✅ **Backup Project on Request** (quick backups via voice commands)

### Module 5 (Data Mapping)

- ✅ PEP-8 Compliance Check
- ✅ Data Quality Check
- ✅ Validate Senzing JSON

### Module 6 (Data Loading)

- ✅ PEP-8 Compliance Check
- ✅ Backup Before Load

### Module 7 (Query Programs)

- ✅ PEP-8 Compliance Check

## Troubleshooting

**Hook not triggering?**

- Check that the file pattern matches your files
- Verify the hook is in `.kiro/hooks/` directory
- Check that the hook JSON is valid
- Look for errors in Kiro's output panel

**Hook triggering too often?**

- Adjust the file patterns to be more specific
- Consider using `userTriggered` instead of `fileEdited`

**Command timeout?**

- Increase the `timeout` value in seconds
- Or set `timeout: 0` to disable timeout

## Support

For more information about Kiro hooks, see:

- Kiro documentation: <https://kiro.dev/docs/hooks/>
- Command Palette: "Open Kiro Hook UI"
- Ask the agent: "How do I create a hook?"
