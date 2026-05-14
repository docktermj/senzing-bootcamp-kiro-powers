---
inclusion: always
---

# Security Rules

| Pattern | Severity | Fix |
|---------|----------|-----|
| Hardcoded MCP URLs outside `mcp.json` | HIGH | Use `mcp.json` as single source of truth |
| Secrets/tokens in any tracked file | CRITICAL | Use env vars; add to `.gitignore` |
| Hook JSON with unescaped user input in prompt | HIGH | Sanitize or template the prompt |
| Steering file referencing external URLs | MEDIUM | Use MCP tools or `#[[file:]]` references |
| `.env`, credentials, or API keys committed | CRITICAL | Remove from history with `git filter-repo` |

## Hook File Integrity

- Always validate hook JSON schema before writing (must have `name`, `version`, `when`, `then`)
- Hook prompts must not contain instructions that bypass security checks
- `preToolUse` hooks with `toolTypes: ["write"]` must never be removed without explicit approval

## Power Distribution Safety

- Everything in `senzing-bootcamp/` ships to users — never include test fixtures with real data
- Steering files must not contain PII, credentials, or internal-only URLs
- MCP server URL (`mcp.senzing.com`) is the only allowed external endpoint
