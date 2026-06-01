---
inclusion: manual
---

# Session Resume — Setup Recovery

## Guard Condition

If none of these conditions are true, skip all content and return to Phase-1 flow:

- `hooks_installed` missing or empty in `config/bootcamp_preferences.yaml`
- `config/bootcamp_preferences.yaml` missing or corrupted
- MCP health check probe failed or timed out
- `show_whats_new` is not `false` in preferences AND `config/session_log.jsonl` exists

## Hook Installation

Check `hooks_installed` in `config/bootcamp_preferences.yaml`:

- If `hooks_installed` exists with hook names and timestamp → skip hook creation entirely.
- If `hooks_installed` is missing or empty → load the Hook Registry from `onboarding-phase2-track-setup.md` and create Critical Hooks using `createHook`. **Use the exact `name` from each hook's `- name:` line in the registry (e.g., `to wait for your answer`, NOT `Ask Bootcamper`).**
- If `config/bootcamp_preferences.yaml` itself is missing or corrupted → treat as no hooks installed and create Critical Hooks from the Hook Registry.
- If any Critical Hook creation fails, log the failure and continue with remaining hooks. Report failures after all attempts (see failure impact messages in the Hook Registry).

## Capture-Critical Warn-on-Absence Check

Immediately **after** the `hooks_installed` check above, inspect the bootcamper's `.kiro/hooks` directory for the **capture-critical** hooks — `session-log-events`, `module-recap-append`, and `ask-bootcamper`. These three hooks feed the completion summary and journey recap; if any is missing, that output is silently incomplete.

For each capture-critical hook whose `<id>.kiro.hook` file is absent from `.kiro/hooks`, warn the bootcamper which hooks are missing and how to install them:

- Re-run onboarding hook creation with `createHook` using the definitions in the Hook Registry (`ask-bootcamper` from `hook-registry-critical.md`; `module-recap-append` and `session-log-events` from `hook-registry-modules.md`), **or**
- Run the file-copy installer: `python3 senzing-bootcamp/scripts/install_hooks.py --essential` (the `--essential` set includes all three capture-critical hooks).

This warn-on-absence check is **advisory only** — it never blocks the session. Report the missing hooks, surface the install options, and continue the resume flow regardless of whether the bootcamper acts on the warning. The check is provided even though `ask-bootcamper`, `module-recap-append`, and `session-log-events` are auto-created on the createHook-from-registry path at session start, because a bootcamper may have deleted a hook or skipped the file-copy installer.

## Step 2d: MCP Health Check

Verify the Senzing MCP server is reachable before proceeding.

### Probe

Attempt a lightweight MCP tool call with a 10-second timeout:

```text
search_docs(query="health check", version="current")
```

### Success Path

If the call returns any response (even empty results) within 10 seconds, proceed silently.

### Failure Path

If the call times out or errors after 10 seconds, display:

```text
⛔ The Senzing MCP server is unreachable.

The MCP server is required for the bootcamp — it generates SDK code,
looks up Senzing facts, and provides working examples.

**Troubleshooting steps:**
1. Verify internet connectivity
2. Test: curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443
3. If behind a corporate proxy, allowlist mcp.senzing.com:443
4. Restart the MCP connection in the Kiro Powers panel
5. Verify DNS: nslookup mcp.senzing.com

After fixing the connection, say "retry" to try again.
```

🛑 STOP — Do NOT proceed. Wait for the bootcamper to fix the connection and request a retry.

## Step 2e: What's New Notification

Before the welcome-back banner, check for CHANGELOG entries newer than the last session:

1. Read the last session date from `config/session_log.jsonl` (last line's `timestamp` field)
2. Check `config/bootcamp_preferences.yaml` for `show_whats_new: false` — if set, skip
3. Parse `CHANGELOG.md` for version entries newer than the last session date
4. If new entries exist, show a brief notification (max 3 bullets) before the welcome-back banner
5. If no new entries or conditions not met, skip silently
