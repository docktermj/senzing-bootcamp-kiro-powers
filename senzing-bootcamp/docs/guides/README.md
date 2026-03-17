# Guides and Tutorials Index

This directory contains user-facing guides and tutorials for the Senzing Boot Camp.

## Available Guides

### Quick Start Guide
**File**: [QUICK_START.md](QUICK_START.md)

**Purpose**: Get started with Senzing in 10 minutes, 30 minutes, or 2 hours

**Content**:
- Three quick start paths (Demo, Fast Track, Complete)
- Prerequisites for each path
- Step-by-step instructions
- Quick commands and examples
- Success indicators

**When to Use**: Before starting the boot camp - choose your learning path

---

### Onboarding Checklist
**File**: [ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)

**Purpose**: Pre-flight checklist before starting the boot camp

**Content**:
- System requirements
- Data preparation checklist
- Database setup requirements
- Development environment setup
- Time and resource planning
- Quick validation commands

**When to Use**: Before Module 1 - ensure you're ready to start

---

### Progress Tracker
**File**: [PROGRESS_TRACKER.md](PROGRESS_TRACKER.md)

**Purpose**: Track your progress through all 13 modules

**Content**:
- Checklist for each module
- Time estimates
- Skip ahead options
- Overall progress summary
- Notes section

**When to Use**: Throughout the boot camp - track completion

---

### Compatibility Matrix
**File**: [COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md)

**Purpose**: Understand version and platform compatibility

**Content**:
- Senzing V4.0 feature support
- Platform support (Linux, macOS, Windows)
- Database version requirements
- Python package versions
- Module compatibility

**When to Use**: Before Module 5 (SDK Setup) - verify compatibility

---

### Design Patterns Gallery
**File**: [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md)

**Purpose**: Explore common entity resolution design patterns

**Content**:
- 10 common entity resolution patterns
- Use case descriptions
- Key matching attributes
- Typical ROI for each pattern
- When to use each pattern
- Pattern selection guidance

**Patterns Covered**:
- Customer 360 - Unified customer view
- Fraud Detection - Identify fraud rings
- Data Migration - Merge legacy systems
- Compliance Screening - Watchlist matching
- Marketing Dedup - Eliminate duplicates
- Patient Matching - Unified medical records
- Vendor MDM - Clean vendor master
- Claims Fraud - Detect staged accidents
- KYC/Onboarding - Verify identity
- Supply Chain - Unified supplier view

**When to Use**: Module 1 (Business Problem) - helps identify which pattern fits your use case

---

### Hooks Installation Guide
**File**: [HOOKS_INSTALLATION_GUIDE.md](HOOKS_INSTALLATION_GUIDE.md)

**Purpose**: Install and configure Kiro automation hooks

**Content**:
- What are hooks and why use them
- Available hooks for Senzing Boot Camp
- Installation instructions
- Hook configuration
- Testing hooks
- Troubleshooting

**Available Hooks**:
- `data-quality-check.kiro.hook` - Validates quality when transformations change
- `backup-before-load.kiro.hook` - Reminds to backup before loading
- `test-before-commit.kiro.hook` - Runs tests automatically
- `validate-senzing-json.kiro.hook` - Validates output format
- `update-documentation.kiro.hook` - Reminds to update docs

**When to Use**: Before Module 4 (Data Mapping) - automates quality checks

---

### Installation Verification Guide
**File**: [INSTALLATION_VERIFICATION.md](INSTALLATION_VERIFICATION.md)

**Purpose**: Verify Senzing SDK installation is working correctly

**Content**:
- Pre-installation checklist
- Installation verification steps
- Test script examples
- Common installation issues
- Platform-specific notes
- Troubleshooting guide

**Verification Steps**:
1. Check Senzing version
2. Verify environment variables
3. Test database connection
4. Run simple test script
5. Verify all components working

**When to Use**: After Module 5 (SDK Setup) - ensures installation is correct

---

## Guide Categories

### Getting Started
- **Quick Start** - Three fast paths to get started
- **Onboarding Checklist** - Pre-flight requirements
- **Design Patterns** - Choose your use case
- **Compatibility Matrix** - Version and platform support

### Progress Tracking
- **Progress Tracker** - Track module completion

### Setup and Installation
- **Installation Verification** - Verify SDK setup

### Automation
- **Hooks Installation** - Automate quality checks

### Troubleshooting
- See `../../steering/common-pitfalls.md`
- See `../../steering/troubleshooting-decision-tree.md`

## Quick Reference

| Guide | Module | Time | Purpose |
|-------|--------|------|---------|
| Quick Start | Before 1 | 10-120 min | Choose path |
| Onboarding Checklist | Before 1 | 15 min | Verify readiness |
| Progress Tracker | All | Ongoing | Track completion |
| Compatibility Matrix | Before 5 | 5 min | Check compatibility |
| Design Patterns | 1 | 10 min | Choose pattern |
| Hooks Installation | Before 4 | 15 min | Automate checks |
| Installation Verification | 5 | 10 min | Verify SDK |

## Related Documentation

### For Planning
- **Design Patterns** → Helps with Module 1 (Business Problem)
- **Cost Calculator** → See `../../steering/cost-calculator.md`
- **Complexity Estimator** → See `../../steering/complexity-estimator.md`

### For Setup
- **Installation Verification** → Helps with Module 5 (SDK Setup)
- **Environment Setup** → See `../../steering/environment-setup.md`

### For Automation
- **Hooks Installation** → Automates quality checks
- **Testing Strategy** → See `../../steering/testing-strategy.md`

### For Troubleshooting
- **Common Pitfalls** → See `../../steering/common-pitfalls.md`
- **Troubleshooting Decision Tree** → See `../../steering/troubleshooting-decision-tree.md`
- **Recovery Procedures** → See `../../steering/recovery-procedures.md`

## How to Use These Guides

### For New Users
1. Start with **Quick Start** to choose your path
2. Complete **Onboarding Checklist** before starting
3. Use **Progress Tracker** throughout the boot camp
4. Reference **Design Patterns** in Module 1
5. Check **Compatibility Matrix** before Module 5
6. Use **Installation Verification** after SDK setup
7. Install **Hooks** before data mapping

### For Experienced Users
- Jump directly to relevant guide
- Use as reference during boot camp
- Customize hooks for your workflow

### For Troubleshooting
1. Check **Installation Verification** if SDK issues
2. Review **Common Pitfalls** for known issues
3. Use **Troubleshooting Decision Tree** for systematic diagnosis

## Additional Resources

### Steering Files
Detailed workflows and guidance:
- `../../steering/steering.md` - Main workflows
- `../../steering/agent-instructions.md` - Agent behavior
- `../../steering/quick-reference.md` - MCP tool reference

### Module Documentation
Detailed module information:
- `../modules/` - Module-specific docs

### Policies
Coding standards:
- `../policies/` - Policy documents

## For Agents

When users need guidance:
1. **Before starting** → Suggest Quick Start and Onboarding Checklist
2. **Module 1** → Suggest Design Patterns guide
3. **Before Module 4** → Suggest Hooks Installation
4. **Before Module 5** → Suggest Compatibility Matrix
5. **After Module 5** → Suggest Installation Verification
6. **Throughout** → Remind about Progress Tracker
7. **Troubleshooting** → Point to relevant guides

## For Users

### When to Read
- **Before starting** → Quick Start, Onboarding Checklist
- **Module 1** → Design Patterns
- **Before Module 5** → Compatibility Matrix
- **During setup** → Installation Verification
- **Before mapping** → Hooks Installation
- **Throughout** → Progress Tracker
- **When stuck** → Troubleshooting guides

### How to Read
- Skim for overview
- Deep dive when needed
- Use as reference
- Follow step-by-step instructions

## Version History

- **v3.0.0** (2026-03-17): Added new guides
  - QUICK_START.md
  - ONBOARDING_CHECKLIST.md
  - PROGRESS_TRACKER.md
  - COMPATIBILITY_MATRIX.md
- **v1.0.0** (2026-03-17): Initial guides
  - DESIGN_PATTERNS.md
  - HOOKS_INSTALLATION_GUIDE.md
  - INSTALLATION_VERIFICATION.md

## Navigation

- [← Back to docs/](../)
- [→ Modules](../modules/)
- [→ Policies](../policies/)
- [→ Development](../development/)
