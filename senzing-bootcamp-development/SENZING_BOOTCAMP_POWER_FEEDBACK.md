# Senzing Boot Camp Power - Improvement Feedback

**Date**: 2026-03-17  
**Power Version**: 3.0.0  
**Submitted By**: Boot Camp User

---

## Instructions

This file captures issues, confusion points, and improvement suggestions encountered during the Senzing Boot Camp. Please document problems as you encounter them, then share this file with the power author after completing the boot camp.

---

## Your Feedback

### Issue #1: Database Location Inconsistency

**Module**: Module 0 (Quick Demo) / Module 5 (SDK Setup)

**Category**: Configuration

**Priority**: High

**What Happened**:
The SDK guide tool returns database path as `/tmp/sqlite/G2C.db`, but the boot camp creates a `database/` directory in the project structure. This creates inconsistency - the SDK guide points to `/tmp` while the project structure expects `database/G2C.db` in the project root.

**Why This Is a Problem**:
- Users following the SDK guide will create databases in `/tmp` instead of their project directory
- The `/tmp` location is ephemeral and may be cleared on reboot
- The project's `database/` directory remains empty and unused
- Creates confusion about where the database should actually live
- Breaks the principle of keeping all project artifacts in the project directory

**Impact**:
- Data loss risk (databases in `/tmp` can be deleted)
- Confusion about project structure
- Inconsistent behavior between modules
- Users may not realize their database is outside the project

**Suggested Fix**:
1. Update the SDK guide to use project-relative paths: `./database/G2C.db` or `$(pwd)/database/G2C.db`
2. Update engine configuration examples to use project-relative database paths
3. Ensure all modules (0, 5, 6) consistently reference `database/G2C.db`
4. Update the `.env.example` file to show the correct path
5. Add a note in the documentation explaining why project-relative paths are preferred

**Alternative Approach**:
If `/tmp/sqlite/` is intentional for quick demos, add explicit documentation explaining:
- Module 0 uses `/tmp/sqlite/` for throwaway demos
- Modules 5+ use `database/` for persistent project work
- How to migrate from demo to project database

---

## Additional Feedback

(Add more issues below as you encounter them)

---

## Submission

When you complete the boot camp, please share this file with the power author.
