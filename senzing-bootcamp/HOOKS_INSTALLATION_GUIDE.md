# Senzing Boot Camp Hooks - Installation Guide

## Quick Start

The easiest way to install hooks for the Senzing Boot Camp power:

### Method 1: Ask the Agent (Recommended)
Simply ask Kiro:
```
"Please install the Senzing Boot Camp hooks"
```

The agent will copy the pre-configured hooks to your project's `.kiro/hooks/` directory.

### Method 2: Command Line
```bash
# From your project root
mkdir -p .kiro/hooks
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/
```

### Method 3: Kiro UI
1. Open Command Palette: `Cmd/Ctrl + Shift + P`
2. Search: "Open Kiro Hook UI"
3. Click "Import Hook"
4. Navigate to `senzing-bootcamp/hooks/`
5. Select hooks to import

## What Gets Installed

Five pre-configured hooks that support the boot camp workflow:

| Hook | Trigger | Action | Module |
|------|---------|--------|--------|
| Data Quality Check | Save transformation program | Remind to validate quality | Module 3 |
| Backup Before Load | Save loading program | Remind to backup database | Module 5 |
| Test Before Commit | Save any source file | Run pytest tests | All |
| Validate Senzing JSON | Save transformed data | Validate with lint_record | Module 3 |
| Update Documentation | Save source file | Remind to update docs | All |

## When to Install

**Recommended**: Install hooks at the start of Module 3 (Data Mapping)

This gives you automated quality checks as you develop transformation programs.

## Customization

All hooks can be customized by editing the JSON files in `.kiro/hooks/`:

```json
{
  "name": "My Custom Hook",
  "version": "1.0.0",
  "description": "What this hook does",
  "when": {
    "type": "fileEdited",
    "patterns": ["src/**/*.py"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Your custom message"
  }
}
```

### Common Customizations

**Change file patterns**:
```json
"patterns": ["my-custom-path/*.py"]
```

**Change command**:
```json
"then": {
  "type": "runCommand",
  "command": "npm test"
}
```

**Disable a hook**:
Delete the hook file or add:
```json
"enabled": false
```

## Troubleshooting

### Hook not triggering?
1. Check file pattern matches your files
2. Verify hook is in `.kiro/hooks/`
3. Validate JSON syntax
4. Check Kiro output panel for errors

### Hook triggering too often?
1. Make file patterns more specific
2. Use `userTriggered` instead of `fileEdited`

### Command timeout?
Increase timeout in hook file:
```json
"timeout": 120
```

## Best Practices

1. **Install early**: Set up hooks before Module 3
2. **Commit to git**: Include hooks in version control
3. **Team alignment**: Ensure team agrees on hook behavior
4. **Test hooks**: Verify they work as expected
5. **Document changes**: Note any customizations in README

## Support

- Full documentation: `senzing-bootcamp/hooks/README.md`
- Kiro docs: https://kiro.dev/docs/hooks/
- Ask the agent: "How do I customize hooks?"

## Example Workflow

```bash
# 1. Start boot camp
cd my-senzing-project

# 2. Install hooks (Module 3)
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/

# 3. Verify installation
ls .kiro/hooks/

# 4. Test a hook
# Save a file in src/transform/ and watch for agent reminder

# 5. Commit hooks
git add .kiro/hooks/
git commit -m "Add Senzing Boot Camp hooks"

# 6. Continue with boot camp
# Hooks will now provide automated assistance
```

## Uninstalling

To remove hooks:
```bash
rm .kiro/hooks/*.kiro.hook
```

Or delete individual hook files.
