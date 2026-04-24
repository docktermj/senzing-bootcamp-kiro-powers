# Senzing Bootcamp Progress Tracker

Track your progress through the bootcamp modules.

To auto-generate this file from your actual progress, run:

```text
python scripts/status.py --sync
```

This reads `config/bootcamp_progress.json` (maintained by the agent) and overwrites this file with your current state. No more manual tracking.

## Quick Reference

- ⬜ Not started
- 🔄 In progress
- ✅ Complete
- ⏭️ Skipped

## Modules

- ⬜ Module 0: SDK Setup
- ⬜ Module 1: Quick Demo (Optional)
- ⬜ Module 2: Business Problem
- ⬜ Module 3: Data Collection
- ⬜ Module 4: Data Quality & Mapping
- ⬜ Module 5: Single Source Loading
- ⬜ Module 6: Multi-Source Orchestration
- ⬜ Module 7: Query and Validation
- ⬜ Module 8: Performance Testing
- ⬜ Module 9: Security Hardening
- ⬜ Module 10: Monitoring
- ⬜ Module 11: Deployment

## Skip Ahead Options

- Have Senzing Entity Specification (SGES)-compliant data? → Skip to Module 4 mapping phase
- Senzing already installed? → Skip Module 0
- Single data source only? → Skip Module 6
- Not deploying to production? → Skip Modules 8-11

## Notes

Use this space to track notes, blockers, or questions:

```text
[Your notes here]
```

---

**Tip**: Run `python scripts/status.py` for a detailed console view with project health checks.
