# Bugfix Requirements Document

## Introduction

When entering Module 5 (Data Quality & Mapping), the agent jumps straight into the mapping workflow without asking the bootcamper whether they want verbose mode (detailed step-by-step mapping output) or concise mode (quick mapping with minimal output). The bootcamp already has a verbosity preference system (`config/bootcamp_preferences.yaml` with `verbosity_preset`), but it is not applied specifically to the mapping workflow at the point where it matters most — before the first `mapping_workflow` call. Users who want to understand the mapping process don't get the option to see each step explained, while experienced users who want to move quickly aren't offered the concise path.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent begins Module 5's mapping workflow (Phase 2: Data Mapping) THEN the agent starts calling `mapping_workflow` immediately without asking the bootcamper about their preferred level of detail for the mapping process

1.2 WHEN the bootcamper has no `verbosity_preset` set in `config/bootcamp_preferences.yaml` or has a general preset that doesn't specifically address mapping detail THEN the agent defaults to an unspecified level of mapping output without offering a choice

1.3 WHEN the mapping workflow produces intermediate results (field detection, attribute mapping decisions, transformation previews) THEN the agent does not adjust the level of detail shown based on an explicit mapping verbosity preference

### Expected Behavior (Correct)

2.1 WHEN the agent reaches the mapping workflow start point in Module 5 (Phase 2, before the first `mapping_workflow` call) THEN the agent SHALL ask a single 👉 question offering verbose mode (shows each mapping step in detail — field detection, attribute selection rationale, transformation preview) or concise mode (maps quickly, shows only the final mapped record and any warnings)

2.2 WHEN the bootcamper selects verbose or concise mapping mode THEN the agent SHALL record the choice in `config/bootcamp_preferences.yaml` under a `mapping_verbosity` key (values: `verbose` or `concise`) and apply it to all subsequent `mapping_workflow` interactions in this module

2.3 WHEN the bootcamper has a previously saved `mapping_verbosity` preference from a prior session THEN the agent SHALL use that preference without re-asking, but mention it briefly ("Using your verbose mapping preference from last time — say 'switch to concise' if you'd prefer less detail")

2.4 WHEN in verbose mode and the agent presents mapping steps THEN the agent SHALL show: (a) detected fields and their types, (b) the attribute mapping decision for each field with rationale, (c) a preview of the transformed record, and (d) any warnings or unmapped fields — each as a distinct step

2.5 WHEN in concise mode and the agent presents mapping results THEN the agent SHALL show only: (a) the final mapped record preview, (b) any warnings or errors, and (c) a count of mapped vs. unmapped fields — without intermediate step details

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper has already set a general `verbosity_preset` in preferences (concise/standard/detailed/custom) THEN the system SHALL CONTINUE TO respect that preset for non-mapping interactions — the `mapping_verbosity` key is additive, not a replacement

3.2 WHEN the agent is in any module other than Module 5 THEN the system SHALL CONTINUE TO use the general verbosity system without offering mapping-specific verbosity choices

3.3 WHEN the bootcamper explicitly asks to "switch to verbose" or "switch to concise" mid-mapping THEN the system SHALL CONTINUE TO honor inline verbosity changes as it does today, updating the `mapping_verbosity` preference accordingly

3.4 WHEN the `mapping_workflow` MCP tool returns state checkpoints THEN the system SHALL CONTINUE TO pass exact `state` without modification regardless of verbosity mode — verbosity only affects what the agent shows the bootcamper, not what it sends to the MCP tool
