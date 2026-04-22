---
inclusion: manual
---

# Troubleshooting Commands and Escalation

Diagnostic commands, system checks, and escalation procedures for Senzing bootcamp troubleshooting.

## Quick Diagnostic Commands

Use MCP tools for diagnosis:

- **Senzing error code**: `explain_error_code(error_code="SENZXXXX", version="current")`
- **Installation issues**: `search_docs(query="installation troubleshooting", category="troubleshooting", version="current")`
- **Performance issues**: `search_docs(query="performance", category="anti_patterns", version="current")`
- **Database issues**: `search_docs(query="database troubleshooting", category="troubleshooting", version="current")`
- **Mapping issues**: `analyze_record(file_paths=["data/transformed/output.jsonl"])` to validate output
- **SDK method questions**: `get_sdk_reference(topic="functions", filter="<method_name>", version="current")`

System-level checks (cross-platform):

```python
import os, shutil
# Check database connection (SQLite)
db = os.path.join("database", "G2C.db")
print(f"SQLite DB exists: {os.path.isfile(db)}")
if os.path.isfile(db):
    print(f"  Size: {os.path.getsize(db) / 1024:.0f} KB")

# Check disk space
usage = shutil.disk_usage(os.getcwd())
print(f"Disk free: {usage.free / (1024**3):.1f} GB")
```

For PostgreSQL:

```console
psql -h localhost -U senzing -d senzing -c "SELECT 1"
```

## When All Else Fails

1. **Read the error message carefully**
   - Error messages usually explain the problem

2. **Use explain_error_code**
   - For any SENZ error codes

3. **Search documentation**
   - Use search_docs with relevant query

4. **Check anti-patterns**
   - Use `search_docs(category="anti_patterns")` with a query describing your situation

5. **Start fresh**
   - Restore from backup
   - Go back to last working state
   - Proceed more carefully

6. **Ask for help**
   - Senzing support: <support@senzing.com>
   - Documentation: docs.senzing.com

## Related Resources

For detailed pitfall descriptions and prevention strategies by module, load `steering/common-pitfalls.md`. This decision tree provides the diagnostic flow; common-pitfalls provides the detailed context and solutions for each module.

## Prevention is Better Than Cure

✅ Test with small samples first
✅ Validate at each step
✅ Backup before major operations
✅ Use MCP tools (don't guess)
✅ Read error messages
✅ Document as you go
✅ Commit to git frequently

## When to Load This Guide

Load this steering file when:

- User says "it's not working"
- User encounters any error
- User is stuck or frustrated
- Need systematic troubleshooting approach
- Multiple issues occurring
