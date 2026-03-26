# File Storage Policy Implementation

## Overview

Implemented a comprehensive file storage policy to ensure all project files are stored in appropriate project directories and never in system temporary directories like `/tmp`.

## Changes Made

### 1. Fixed /tmp Reference

**File**: `docs/modules/MODULE_5_SDK_SETUP.md`

**Change**: Updated Linux installation instructions to download to home directory instead of `/tmp`

```bash
# Before
wget -qO - https://senzing-production-apt.s3.amazonaws.com/senzingrepo_1.0.0-1_amd64.deb \
  -O /tmp/senzingrepo_1.0.0-1_amd64.deb
sudo apt install /tmp/senzingrepo_1.0.0-1_amd64.deb

# After
wget -qO - https://senzing-production-apt.s3.amazonaws.com/senzingrepo_1.0.0-1_amd64.deb \
  -O ~/senzingrepo_1.0.0-1_amd64.deb
sudo apt install ~/senzingrepo_1.0.0-1_amd64.deb
```

### 2. Created File Storage Policy

**File**: `docs/policies/FILE_STORAGE_POLICY.md`

**Content**: Comprehensive policy document defining where all file types should be stored:

- **Source code** → `src/` directory
- **Shell scripts** → `scripts/` directory
- **Documentation** → `docs/` directory
- **Data files** → `data/` directory
- **Configuration** → `config/` directory or root (for .env)
- **Temporary files** → `data/temp/` (never `/tmp`)
- **Downloads** → `~` (home directory, never `/tmp`)

### 3. Updated Policies Index

**File**: `docs/policies/README.md`

**Changes**:

- Added File Storage Policy to the list of available policies
- Updated policy summary table
- Enhanced file organization overview with all directories
- Added note about never using `/tmp`
- Updated version history

### 4. Updated Agent Instructions

**File**: `steering/agent-instructions.md`

**Changes**:

- Added data file directory structure to File Management section
- Added critical note about never using `/tmp`
- Added note about using `data/temp/` for temporary files
- Added note about using `~` for downloads

## Policy Rules Summary

### Core Principle

**Never use system temporary directories like `/tmp` for project files.**

### File Type Rules

| File Type       | Directory         | Examples                     |
|-----------------|-------------------|------------------------------|
| Source code     | `src/`            | `.py`, `.java`, `.cs`, `.rs` |
| Shell scripts   | `scripts/`        | `.sh`                        |
| Documentation   | `docs/`           | `.md`                        |
| Data files      | `data/`           | `.json`, `.jsonl`, `.csv`    |
| Configuration   | `config/` or root | `.json`, `.yaml`, `.env`     |
| Temporary files | `data/temp/`      | Any temporary working files  |
| Downloads       | `~`               | Installation packages        |

### Why Not /tmp?

1. **Persistence**: Files in `/tmp` may be deleted on system reboot
2. **Permissions**: `/tmp` may have different permissions
3. **Organization**: Project files should stay within project structure
4. **Portability**: Paths like `/tmp` are system-specific
5. **Debugging**: Easier to find files in project directories
6. **Version Control**: Project directories can be properly gitignored
7. **Cleanup**: Easier to clean up project-specific files

## Verification

Verified no other `/tmp` references exist:

```bash
grep -r "/tmp" senzing-bootcamp/**/*.md
# Result: Only found in MODULE_5_SDK_SETUP.md (now fixed)
```

Verified no tempfile usage:

```bash
grep -r "tempfile\|mktemp\|NamedTemporaryFile" senzing-bootcamp/**/*.md
# Result: No matches found
```

## Impact

### For Users

- Clear guidance on where to store files
- No risk of losing files due to `/tmp` cleanup
- Consistent project organization
- Better debugging experience

### For Agents

- Clear rules for file placement
- No ambiguity about temporary files
- Consistent recommendations
- Policy-compliant code generation

### For Maintainers

- Easier to find and manage files
- Consistent project structure
- Clear cleanup procedures
- Better version control

## Examples

### Before (Wrong)

```bash
# ❌ Using /tmp
wget https://example.com/package.deb -O /tmp/package.deb
python /tmp/transform.py
echo "data" > /tmp/output.json
```

### After (Correct)

```bash
# ✅ Using project directories
wget https://example.com/package.deb -O ~/package.deb
python src/transform/transform.py
echo "data" > data/transformed/output.json
```

## Related Policies

1. **MODULE_0_CODE_LOCATION.md** - Module 0 code placement
2. **SHELL_SCRIPT_LOCATIONS.md** - Shell script placement
3. **PYTHON_REQUIREMENTS_POLICY.md** - Python package management
4. **FILE_STORAGE_POLICY.md** - Comprehensive file storage rules (new)

## Enforcement

This policy is enforced through:

1. **Documentation**: All docs follow this policy
2. **Agent Instructions**: Agent is instructed to follow this policy
3. **Code Review**: All code examples must follow this policy
4. **Automated Checks**: Grep searches for policy violations
5. **Policy Document**: Clear reference for all contributors

## Future Considerations

### Potential Additions

1. **Log files** → `logs/` directory
2. **Test files** → `tests/` directory
3. **Build artifacts** → `build/` or `dist/` directory
4. **Cache files** → `.cache/` directory (gitignored)

### Monitoring

Periodically check for policy violations:

```bash
# Check for /tmp usage
grep -r "/tmp" senzing-bootcamp/**/*.md

# Check for tempfile usage
grep -r "tempfile\|mktemp" senzing-bootcamp/**/*.md

# Should return no results (except policy documentation)
```

## Date

**Implemented**: 2026-03-17

## Version

**Boot Camp Version**: 3.0.0
**Policy Version**: 1.0.0

## Files Created

1. `docs/policies/FILE_STORAGE_POLICY.md` - Comprehensive policy document
2. `docs/development/FILE_STORAGE_POLICY_IMPLEMENTATION.md` - This file

## Files Modified

1. `docs/modules/MODULE_5_SDK_SETUP.md` - Fixed /tmp reference
2. `docs/policies/README.md` - Added new policy to index
3. `steering/agent-instructions.md` - Added file storage rules
