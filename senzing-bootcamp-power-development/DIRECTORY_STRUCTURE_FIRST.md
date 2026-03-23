# 🚨 DIRECTORY STRUCTURE MUST BE CREATED FIRST 🚨

**STATUS**: CRITICAL REQUIREMENT  
**PRIORITY**: HIGHEST  
**ENFORCEMENT**: MANDATORY  
**NO EXCEPTIONS**: NONE

---

## THE RULE

**THE DIRECTORY STRUCTURE MUST BE CREATED BEFORE ANYTHING ELSE HAPPENS.**

Not "should be created".  
Not "it's recommended to create".  
Not "when convenient, create".  

**MUST BE CREATED FIRST.**

---

## What "FIRST" Means

**FIRST** means:
- ✅ Before greeting the user
- ✅ Before asking what they want to do
- ✅ Before presenting path options
- ✅ Before explaining modules
- ✅ Before creating any files
- ✅ Before running any commands
- ✅ Before calling any MCP tools
- ✅ Before doing ANYTHING else

**FIRST** means **FIRST**.

---

## Where This Is Enforced

### 1. Agent Instructions (`steering/agent-instructions.md`)

**Line 1-5**: 
```
⚠️ **CRITICAL: READ THIS FIRST** ⚠️

## 🚨 MANDATORY FIRST ACTION - CREATE DIRECTORY STRUCTURE 🚨

BEFORE YOU DO ANYTHING ELSE - BEFORE GREETING THE USER - 
BEFORE ASKING ANY QUESTIONS - YOU MUST:
1. Check if directory structure exists
2. If it doesn't exist, CREATE IT IMMEDIATELY
3. Only then proceed with any other activity
```

**Complete commands provided** at the top of the file.

**Module 0 and Module 1** both reference this section FIRST.

### 2. Power Documentation (`POWER.md`)

**Line 13-15**:
```
## 🚨 CRITICAL: Agent Must Read This First 🚨

TO THE AGENT: Before you do ANYTHING else - before greeting the user, 
before asking questions, before presenting options - you MUST create 
the project directory structure.
```

**Agent Behavior section**:
```
- 🚨 MANDATORY - EXECUTE FIRST 🚨: Before ANY other action, check if project structure exists
- 🚨 MANDATORY - EXECUTE FIRST 🚨: If structure doesn't exist, create it immediately
- 🚨 MANDATORY - EXECUTE FIRST 🚨: Do not greet user, do not ask questions, do not present options
- 🚨 MANDATORY - EXECUTE FIRST 🚨: This happens BEFORE everything else - no exceptions
```

### 3. Onboarding Checklist (`docs/guides/ONBOARDING_CHECKLIST.md`)

**Step 1** (first item):
```
### ✅ Step 1: Create Project Directory Structure

**This should be your first step!**
```

### 4. This Document (`DIRECTORY_STRUCTURE_FIRST.md`)

You're reading it.

---

## The Commands

```bash
# Check if structure exists
if [ ! -d "src" ] || [ ! -d "data" ] || [ ! -d "docs" ]; then
    echo "Creating project directory structure..."
    
    # Create all directories
    mkdir -p data/{raw,transformed,samples,backups}
    mkdir -p database
    mkdir -p src/{transform,load,query,utils}
    mkdir -p tests
    mkdir -p docs/feedback
    mkdir -p config
    mkdir -p docker/scripts
    mkdir -p logs
    mkdir -p monitoring
    mkdir -p scripts
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Sensitive data
.env
*.key
*.pem

# Data files
data/raw/*
data/transformed/*
!data/raw/.gitkeep
!data/transformed/.gitkeep

# Database files
database/*.db
database/*.db-journal
!database/.gitkeep

# Logs
logs/*.log

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/

# Temporary files
data/temp/*
!data/temp/.gitkeep
EOF
    
    # Create .env.example
    cat > .env.example << 'EOF'
# Senzing Configuration
SENZING_ENGINE_CONFIGURATION_JSON=

# Database
DATABASE_URL=sqlite3://na:na@database/G2C.db

# Optional: PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/senzing
EOF
    
    # Create README.md
    cat > README.md << 'EOF'
# Senzing Boot Camp Project

This project was created using the Senzing Boot Camp power.

## Quick Start

See `docs/` directory for project documentation.
EOF
    
    # Create .gitkeep files
    touch data/raw/.gitkeep
    touch data/transformed/.gitkeep
    touch data/samples/.gitkeep
    touch data/backups/.gitkeep
    touch database/.gitkeep
    touch logs/.gitkeep
    
    echo "✅ Project directory structure created successfully"
else
    echo "✅ Project directory structure already exists"
fi
```

---

## When To Execute

**TRIGGER POINTS** - Execute directory creation at ANY of these:
- User says "start the boot camp"
- User says "Module 0" or "quick demo"
- User says "Module 1" or any module number
- User selects any path (A, B, C, D)
- User asks to begin
- User says "let's get started"
- User says "I'm ready"
- **ANY indication they want to start using the power**

**BEFORE**:
- ❌ Greeting the user
- ❌ Asking what they want
- ❌ Presenting options
- ❌ Explaining anything
- ❌ Creating any files
- ❌ Running any other commands

**YOU MUST**:
- ✅ Execute the directory creation commands
- ✅ Verify they succeeded
- ✅ THEN proceed with other activities

---

## Why This Matters

### Problem Without Directory Structure
1. Agent creates files in wrong locations
2. Files end up in project root instead of `src/`
3. Data files scattered everywhere
4. No organization
5. User frustration
6. Wasted time fixing file locations

### Solution With Directory Structure First
1. All files go to correct locations from the start
2. Organized project from day one
3. No cleanup needed
4. Professional structure
5. User satisfaction
6. Smooth experience

---

## Verification

After creating the structure, the user should see:

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
├── scripts/
├── .gitignore
├── .env.example
└── README.md
```

---

## Failure Handling

If directory creation fails:
1. ❌ DO NOT proceed
2. ✅ Report error to user
3. ✅ Provide commands for manual execution
4. ✅ Wait for user to confirm structure exists
5. ✅ Verify structure before continuing

---

## No Exceptions

There are **NO EXCEPTIONS** to this rule:
- Not for experienced users
- Not for quick demos
- Not for testing
- Not for any reason

**DIRECTORY STRUCTURE FIRST. ALWAYS. NO EXCEPTIONS.**

---

## Enforcement Level

| Level | Description |
|-------|-------------|
| ⚠️ Recommended | Nice to have, but optional |
| ⚡ Important | Should do, but can skip |
| 🔥 Critical | Must do, no skipping |
| **🚨 MANDATORY** | **MUST DO FIRST, BEFORE EVERYTHING ELSE** |

**This requirement is 🚨 MANDATORY.**

---

## Summary

1. **WHAT**: Create project directory structure
2. **WHEN**: FIRST - before anything else
3. **WHERE**: Documented in 4 places
4. **WHY**: Ensures organized project from start
5. **HOW**: Execute provided bash commands
6. **EXCEPTIONS**: None

---

## Checklist for Agent

Before proceeding with ANY boot camp activity:

- [ ] Have I checked if directory structure exists?
- [ ] If it doesn't exist, have I created it?
- [ ] Have I verified the creation succeeded?
- [ ] Have I informed the user it's been created?
- [ ] Only now can I proceed with other activities

If you answered "No" to any of these, **STOP** and create the directory structure.

---

**DIRECTORY STRUCTURE FIRST.**  
**ALWAYS.**  
**NO EXCEPTIONS.**  
**THIS IS MANDATORY.**

---

**Document Created**: 2026-03-17  
**Reason**: Directory structure creation was not happening first despite multiple requests  
**Solution**: Make it impossible to miss with prominent warnings and clear instructions  
**Status**: ENFORCED

