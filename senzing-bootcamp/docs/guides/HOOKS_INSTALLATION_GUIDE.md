# Senzing Bootcamp Hooks - Installation Guide

## Quick Start

The easiest way to install hooks for the Senzing Bootcamp power:

### Method 1: Ask the Agent (Recommended)

Simply ask Kiro:

```text
"Please install the Senzing Bootcamp hooks"
```

The agent will:

1. Verify the `.kiro/hooks/` directory exists (create if needed)
2. Copy the pre-configured hooks to your project's `.kiro/hooks/` directory

### Method 2: Command Line

```bash
# From your project root (Linux/macOS)
mkdir -p .kiro/hooks
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/
```

```powershell
# From your project root (Windows PowerShell)
New-Item -ItemType Directory -Force -Path .kiro\hooks | Out-Null
Copy-Item senzing-bootcamp\hooks\*.hook .kiro\hooks\
```

### Method 3: Kiro UI

1. Open Command Palette: `Cmd/Ctrl + Shift + P`
2. Search: "Open Kiro Hook UI"
3. Click "Import Hook"
4. Navigate to `senzing-bootcamp/hooks/`
5. Select hooks to import

## What Gets Installed

Nine pre-configured hooks that support the bootcamp workflow:

| Hook                      | Trigger                     | Action                       | Module     |
|---------------------------|-----------------------------|------------------------------|------------|
| Code Style Check          | Save source code file       | Check coding standards       | All        |
| Data Quality Check        | Save transformation program | Remind to validate quality   | Module 4-5 |
| Backup Before Load        | Save loading program        | Remind to backup database    | Module 6   |
| Validate Senzing JSON     | Save transformed data       | Validate with analyze_record | Module 5   |
| Backup Project on Request | Manual trigger (button)     | Run project backup script    | All        |
| CommonMark Validation     | Save Markdown file          | Check CommonMark compliance  | All        |
| Verify Senzing Facts      | Before any write operation  | Verify facts via MCP tools   | All        |
| Analyze After Mapping     | New file in data/transformed| Run analyze_record           | Module 5-6 |
| Run Tests After Change    | Save src/ code files        | Remind to run tests          | Module 6-8 |

## When to Install

**Recommended:**
Install hooks during initial project setup (the agent offers this automatically), or at any time by saying "install hooks".

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
    "patterns": ["src/**/*.py", "src/**/*.java", "src/**/*.cs", "src/**/*.rs", "src/**/*.ts"]
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
"patterns": ["my-custom-path/*.*"]
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

1. **Install early:** Set up hooks during initial project setup (the agent offers this automatically)
2. **Commit to git:** Include hooks in version control
3. **Team alignment:** Ensure team agrees on hook behavior
4. **Test hooks:** Verify they work as expected
5. **Document changes:** Note any customizations in README

## Support

- Full documentation: `senzing-bootcamp/hooks/README.md`
- Kiro docs: <https://kiro.dev/docs/hooks/>
- Ask the agent: "How do I customize hooks?"

## Example Workflow

```bash
# 1. Start bootcamp
cd my-senzing-project

# 2. Install hooks (recommended: use the Python installer)
python scripts/install_hooks.py

# 3. Verify installation
ls .kiro/hooks/          # Linux/macOS
dir .kiro\hooks\         # Windows

# 4. Test a hook
# Save a file in src/transform/ and watch for agent reminder

# 5. Commit hooks
git add .kiro/hooks/
git commit -m "Add Senzing Bootcamp hooks"

# 6. Continue with bootcamp
# Hooks will now provide automated assistance
```

## Uninstalling

Remove hook files from `.kiro/hooks/`:

```bash
# Linux/macOS
rm .kiro/hooks/*.kiro.hook

# Windows (PowerShell)
Remove-Item .kiro\hooks\*.kiro.hook
```

Or delete individual hook files.
