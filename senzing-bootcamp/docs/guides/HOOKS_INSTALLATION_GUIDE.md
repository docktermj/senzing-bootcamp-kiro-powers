# Senzing Bootcamp Hooks - Installation Guide

## Automatic Installation

Hooks are installed automatically when you start the bootcamp. The agent copies all pre-configured hooks from `senzing-bootcamp/hooks/` to `.kiro/hooks/` during onboarding — no action needed.

## Manual Installation

If you need to reinstall or add hooks later:

### Method 1: Ask the Agent

```text
"Please install the Senzing Bootcamp hooks"
```

### Method 2: Install Script

```bash
python scripts/install_hooks.py
```

### Method 3: Command Line

```bash
# Linux / macOS
mkdir -p .kiro/hooks
cp senzing-bootcamp/hooks/*.kiro.hook .kiro/hooks/
```

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path .kiro\hooks | Out-Null
Copy-Item senzing-bootcamp\hooks\*.kiro.hook .kiro\hooks\
```

### Method 4: Kiro UI

1. Open Command Palette (`Cmd/Ctrl + Shift + P`)
2. Search: "Open Kiro Hook UI"
3. Click "Import Hook"
4. Navigate to `senzing-bootcamp/hooks/`

## What Gets Installed

11 pre-configured hooks:

| Hook | Trigger | Purpose |
| ---- | ------- | ------- |
| Code Style Check | Save source code | Check coding standards |
| Data Quality Check | Save transformation program | Remind to validate quality |
| Backup Before Load | Save loading program | Remind to backup database |
| Validate Senzing JSON | Save transformed data | Validate with analyze_record |
| Backup Project on Request | Manual trigger (button) | Run project backup script |
| CommonMark Validation | Save Markdown file | Check CommonMark compliance |
| Verify Senzing Facts | Before any write | Verify facts via MCP tools |
| Analyze After Mapping | New file in data/transformed/ | Run analyze_record |
| Run Tests After Change | Save src/ code files | Remind to run tests |
| Git Commit Reminder | Manual trigger (button) | Suggest descriptive commit |
| Enforce Working Directory | Before any write | Block /tmp and external paths |

## Customization

Edit hook JSON files in `.kiro/hooks/`. Common changes:

- **File patterns:** `"patterns": ["my-custom-path/*.*"]`
- **Disable a hook:** Delete the file or add `"enabled": false`
- **Change timeout:** `"timeout": 120`

## Uninstalling

```bash
# Linux / macOS
rm .kiro/hooks/*.kiro.hook

# Windows (PowerShell)
Remove-Item .kiro\hooks\*.kiro.hook
```

## Support

- Full hook details: `senzing-bootcamp/hooks/README.md`
- Kiro docs: <https://kiro.dev/docs/hooks/>
