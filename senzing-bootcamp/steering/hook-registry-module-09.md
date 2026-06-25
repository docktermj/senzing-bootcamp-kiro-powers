---
inclusion: manual
---

# Hook Registry — Module 9 (Full Prompts)

Full hook prompts for Module 9, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 9 Hooks

**security-scan-on-save** (fileEdited → askAgent, filePatterns: `src/security/*.*, config/*credentials*, config/*secret*, .env*`)

Prompt:

````text
A security-related file was just modified. If the bootcamper is in Module 9 (Security Hardening), remind them to re-run the appropriate vulnerability scanner for their language (Python: bandit; Java: spotbugs; C#: dotnet list package --vulnerable; Rust: cargo audit; TypeScript: npm audit) to verify no new vulnerabilities were introduced. If not in Module 9, produce no output.
````

- id: `security-scan-on-save`
- name: `to run a security scan`
- description: `When security-related files are modified during Module 9, reminds the agent to re-run vulnerability scanning to catch regressions.`
