---
inclusion: manual
---

# Hook Registry — Module 10 (Full Prompts)

Full hook prompts for Module 10, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 10 Hooks

**validate-alert-config** (fileCreated → askAgent, filePatterns: `monitoring/alerts/*.*, monitoring/dashboards/*.*`)

Prompt:

````text
A monitoring configuration file was just created. Validate: (1) Alert rules have required fields: name, condition, severity, and action. (2) Severity levels are one of: Critical, Warning, Info. (3) Thresholds are numeric and reasonable (e.g., error rate percentages between 0-100, latency in milliseconds). (4) Dashboard configs reference metrics that are actually collected by the metrics_collector. Report any issues to the bootcamper with suggested fixes.
````

- id: `validate-alert-config`
- name: `to validate alert configuration`
- description: `When monitoring configuration files are created or modified during Module 10, validates alert rule syntax and completeness.`
