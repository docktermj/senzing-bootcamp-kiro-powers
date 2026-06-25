---
inclusion: manual
---

# Hook Registry — Module 2 (Full Prompts)

Full hook prompts for Module 2, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 2 Hooks

**verify-sdk-setup** (fileEdited → askAgent, filePatterns: `config/senzing_config.*, config/bootcamp_preferences.yaml, database/*.*`)

Prompt:

````text
A configuration or database file was modified. If the bootcamper is in Module 2 (SDK Setup), run a quick verification: check that database/G2C.db exists and is accessible, and that the Senzing engine can initialize with the current config. If not in Module 2, produce no output. If verification fails, present the error and suggest running: python3 src/scripts/verify_sdk.py
````

- id: `verify-sdk-setup`
- name: `to verify SDK setup`
- description: `After config or environment files change during Module 2, re-verifies that the Senzing SDK setup is still valid.`
