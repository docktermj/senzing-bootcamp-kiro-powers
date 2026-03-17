# Senzing Boot Camp Hooks

This directory contains pre-configured Kiro hooks to support the Senzing Boot Camp workflow.

## Available Hooks

### 1. Data Quality Check (`data-quality-check.kiro.hook`)
**Trigger**: When transformation programs are saved
**Action**: Reminds to validate data quality
**Use case**: Ensures transformation changes don't degrade data quality

### 2. Backup Before Load (`backup-before-load.kiro.hook`)
**Trigger**: When loading programs are modified
**Action**: Reminds to backup database before running
**Use case**: Prevents data loss from failed loads

### 3. Test Before Commit (`test-before-commit.kiro.hook`)
**Trigger**: When source files are saved
**Action**: Runs pytest test suite
**Use case**: Catches bugs early in development

### 4. Validate Senzing JSON (`validate-senzing-json.kiro.hook`)
**Trigger**: When Senzing JSON output files are modified
**Action**: Suggests validating with lint_record
**Use case**: Ensures output conforms to SGES

### 5. Update Documentation (`update-documentation.kiro.hook`)
**Trigger**: When programs are modified
**Action**: Reminds to update documentation
**Use case**: Keeps documentation in sync with code

## Installation

### Option 1: Copy to Workspace Hooks Directory
```bash
# Copy all hooks to your project
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/

# Or copy individual hooks
cp senzing-bootcamp/hooks/data-quality-check.kiro.hook .kiro/hooks/
```

### Option 2: Use Kiro Command Palette
1. Open Command Palette (Cmd/Ctrl + Shift + P)
2. Search for "Open Kiro Hook UI"
3. Click "Import Hook"
4. Select hook file from `senzing-bootcamp/hooks/`

### Option 3: Ask the Agent
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

### Module 3 (Data Mapping)
- ✅ Data Quality Check
- ✅ Validate Senzing JSON
- ✅ Test Before Commit

### Module 5 (Data Loading)
- ✅ Backup Before Load
- ✅ Test Before Commit

### Module 6 (Query Programs)
- ✅ Test Before Commit
- ✅ Update Documentation

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
- Kiro documentation: https://kiro.dev/docs/hooks/
- Command Palette: "Open Kiro Hook UI"
- Ask the agent: "How do I create a hook?"
