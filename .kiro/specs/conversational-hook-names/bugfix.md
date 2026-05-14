# Bugfix Requirements Document

## Introduction

The `name` field on bootcamp hooks is user-facing — the Kiro UI renders it as "Ask Kiro Hook {name}" every time a hook fires. Currently, most hook names use internal implementation labels (e.g., "Ask Bootcamper", "Review Bootcamper Input", "Code Style Check") or inconsistent phrasing ("I will make sure the file is in the project directory"). These labels are jargony, treat the bootcamper as a data object, and break the warm conversational tone the bootcamp aims for. The fix is to rewrite every hook's `name` field to follow a consistent conversational pattern — "to {verb phrase}" — so the UI reads naturally as "Ask Kiro Hook to {do something}".

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `ask-bootcamper` hook fires THEN the Kiro UI displays "Ask Kiro Hook Ask Bootcamper" — a jargony label that treats the bootcamper as an object rather than a person

1.2 WHEN the `review-bootcamper-input` hook fires THEN the Kiro UI displays "Ask Kiro Hook Review Bootcamper Input" — an implementation-oriented label not addressed to the bootcamper

1.3 WHEN the `enforce-file-path-policies` hook fires THEN the Kiro UI displays "Ask Kiro Hook I will make sure the file is in the project directory" — uses future tense ("I will") instead of the infinitive pattern, reading as a promise rather than a description of what is happening

1.4 WHEN any other bootcamp hook fires (code-style-check, commonmark-validation, validate-business-problem, verify-sdk-setup, verify-demo-results, validate-data-files, analyze-after-mapping, data-quality-check, enforce-mapping-spec, backup-before-load, run-tests-after-change, verify-generated-code, enforce-visualization-offers, validate-benchmark-results, security-scan-on-save, validate-alert-config, deployment-phase-gate, backup-project-on-request, error-recovery-context, git-commit-reminder, module-completion-celebration) THEN the Kiro UI displays "Ask Kiro Hook {name}" where {name} is a Title Case implementation label (e.g., "Code Style Check", "Validate Business Problem") rather than a conversational phrase

1.5 WHEN a contributor adds a new hook to hook-registry.md THEN there is no documented style guide for the `name` field, leading to inconsistent naming across hooks

### Expected Behavior (Correct)

2.1 WHEN the `ask-bootcamper` hook fires THEN the system SHALL display "Ask Kiro Hook to wait for your answer" — a conversational phrase using the infinitive "to {verb}" pattern

2.2 WHEN the `review-bootcamper-input` hook fires THEN the system SHALL display "Ask Kiro Hook to review what you said" — a conversational phrase addressed to the bootcamper as a person

2.3 WHEN the `enforce-file-path-policies` hook fires THEN the system SHALL display "Ask Kiro Hook to make sure the file is in the project directory" — using the infinitive "to {verb}" pattern consistently

2.4 WHEN any other bootcamp hook fires THEN the system SHALL display "Ask Kiro Hook to {conversational verb phrase}" where the name field follows the pattern "to {lowercase verb phrase}" so the full UI string reads as a natural sentence (e.g., "Ask Kiro Hook to check code style", "Ask Kiro Hook to check Markdown style", "Ask Kiro Hook to validate your business problem")

2.5 WHEN a contributor adds a new hook to hook-registry.md THEN the system SHALL have a documented style guide line in hook-registry.md stating that the `name` field is user-facing and must follow the "to {verb phrase}" pattern so the Kiro UI renders as "Ask Kiro Hook to {action}"

### Unchanged Behavior (Regression Prevention)

3.1 WHEN any hook fires THEN the system SHALL CONTINUE TO use the same `id` field value — internal hook IDs must not change

3.2 WHEN any hook fires THEN the system SHALL CONTINUE TO execute the same `prompt`, `description`, `when`, and `then` configuration — only the `name` field changes

3.3 WHEN the onboarding flow installs Critical Hooks THEN the system SHALL CONTINUE TO install the same set of hooks with the same event types and trigger patterns

3.4 WHEN CI validation runs (`sync_hook_registry.py --verify`) THEN the system SHALL CONTINUE TO pass — the registry and hook files must remain in sync after the name changes

3.5 WHEN a hook file is loaded by the Kiro framework THEN the system SHALL CONTINUE TO parse correctly — the JSON structure of `.kiro.hook` files must remain valid
