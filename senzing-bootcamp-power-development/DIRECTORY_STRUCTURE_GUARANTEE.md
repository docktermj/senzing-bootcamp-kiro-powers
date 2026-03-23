# Directory Structure Creation - Guaranteed First Step

**Status**: ✅ GUARANTEED  
**Last Updated**: 2026-03-17

## Guarantee Statement

The Senzing Boot Camp power **GUARANTEES** that the project directory structure will be created automatically at the very beginning of the boot camp, before any other activity occurs.

## Where This is Enforced

### 1. Agent Instructions (`steering/agent-instructions.md`)

**Core Principle #1** (highest priority):
```
1. ALWAYS CREATE DIRECTORY STRUCTURE FIRST - Before doing ANYTHING else 
   in the boot camp (Module 0 or Module 1), check if the project directory 
   structure exists. If it doesn't exist, create it immediately using the 
   commands below. This is MANDATORY and must happen before any other boot 
   camp activity.
```

**Dedicated Section**: "MANDATORY: Directory Structure Creation"
- Specifies when to create (before ANY module)
- Provides exact commands to execute
- Lists what NOT to do (no skipping, no asking permission)

**Module 0 Behavior**:
```
- FIRST: Ensure project directory structure exists
- If structure doesn't exist, create it immediately before proceeding
```

**Module 1 Behavior**:
```
- FIRST: Ensure project directory structure exists
- If structure doesn't exist, create it immediately before proceeding
```

### 2. Main Power Documentation (`POWER.md`)

**"Getting Started" Section** - Added prominent notice:
```
### CRITICAL FIRST STEP: Create Directory Structure

Before doing anything else, the agent will automatically create 
the project directory structure. This happens at the very beginning 
of Module 0 or Module 1, whichever you start with.
```

**Module Descriptions**:
- Module 0: "FIRST: Agent creates project directory structure automatically"
- Module 1: "FIRST: Agent creates project directory structure automatically (if not already created in Module 0)"

**Agent Behavior Section**:
```
- MANDATORY: Check if project structure exists at the start of Module 0 or Module 1
- MANDATORY: If structure doesn't exist, create it immediately before proceeding
- MANDATORY: Do not skip this step or ask user permission - just create it
```

### 3. Onboarding Checklist (`docs/guides/ONBOARDING_CHECKLIST.md`)

**Step 1** (first item in checklist):
```
### ✅ Step 1: Create Project Directory Structure

**This should be your first step!** Create the organized directory 
layout for your Senzing project...
```

Includes:
- Complete mkdir commands
- Visual directory tree
- Verification steps
- Explanation of why this is first

### 4. Steering Workflows (`steering/steering.md`)

**Module 0 Workflow** - Step 1:
```
1. Create project structure (if needed): Check if the project 
   structure exists... If the structure doesn't exist, create it...
```

**Module 1 Workflow** - Step 1:
```
1. Set up project directory structure: The agent will create an 
   organized project structure for the user. Execute the following 
   command to create the directory structure...
```

## What Gets Created

### Directory Structure
```
my-senzing-project/
├── data/
│   ├── raw/
│   ├── transformed/
│   ├── samples/
│   └── backups/
├── database/
├── src/
│   ├── transform/
│   ├── load/
│   ├── query/
│   └── utils/
├── tests/
├── docs/
│   └── feedback/
├── config/
├── docker/
│   └── scripts/
├── logs/
├── monitoring/
└── scripts/
```

### Initial Files
- `.gitignore` - Excludes sensitive data, databases, logs
- `.env.example` - Template for environment variables
- `README.md` - Project description
- `.gitkeep` files - Preserve empty directories in git

## Enforcement Mechanism

### Agent Behavior
1. **Check**: At start of Module 0 or Module 1, check if `src/`, `data/`, and `docs/` directories exist
2. **Create**: If any are missing, execute mkdir commands immediately
3. **Inform**: Tell user "I've created the project directory structure for you"
4. **Proceed**: Continue with module activities

### No User Intervention Required
- ❌ Agent does NOT ask permission
- ❌ Agent does NOT skip this step
- ❌ Agent does NOT assume structure exists
- ✅ Agent ALWAYS checks and creates if needed

## Benefits

1. **Consistency**: All projects have the same structure
2. **Organization**: Files go to correct locations from the start
3. **No Errors**: Prevents "directory not found" errors
4. **Best Practices**: Follows standard project layout conventions
5. **Git Ready**: Structure includes .gitignore and .gitkeep files

## Verification

Users can verify the structure was created:
```bash
tree -L 2  # or ls -R
```

Expected output shows all directories and initial files.

## Failure Handling

If directory creation fails:
1. Agent reports the error to user
2. Agent suggests manual creation using provided commands
3. Agent does not proceed until structure exists

## Documentation Trail

This guarantee is documented in:
- ✅ `steering/agent-instructions.md` - Core Principle #1 + Mandatory section
- ✅ `POWER.md` - Getting Started section + Agent behavior
- ✅ `docs/guides/ONBOARDING_CHECKLIST.md` - Step 1
- ✅ `steering/steering.md` - Module 0 and Module 1 workflows
- ✅ `docs/DIRECTORY_STRUCTURE_GUARANTEE.md` - This document

## Version History

- **v3.0.0** (2026-03-17): Directory creation made mandatory first step
  - Added Core Principle #1
  - Added MANDATORY section to agent instructions
  - Updated all module workflows
  - Made onboarding Step 1
  - Added prominent notice in POWER.md

---

**Guarantee Level**: MANDATORY  
**Enforcement**: Automatic  
**User Action Required**: None  
**Failure Mode**: Agent reports error and provides manual commands
