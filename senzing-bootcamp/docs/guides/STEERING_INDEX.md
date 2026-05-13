# Steering Index

The steering index file at `senzing-bootcamp/steering/steering-index.yaml` is the machine-readable mapping that controls how the agent selects steering files during a bootcamp session. It maps module numbers to steering file paths, defines keyword-triggered file lookups, lists language and deployment file mappings, stores per-file token counts and size categories, and tracks the overall context budget. If you are adding a new module, registering a keyword, or updating token counts after editing a steering file, this is the file you need to understand.

## Top-Level Sections

The steering index contains six top-level sections:

| Section         | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| `modules`       | Maps module numbers to steering filenames or split-phase definitions    |
| `keywords`      | Maps trigger words to steering filenames for context-relevant loading   |
| `languages`     | Maps language names to language-specific steering filenames             |
| `deployment`    | Maps deployment targets to deployment-specific steering filenames       |
| `file_metadata` | Stores token count and size category for every steering file            |
| `budget`        | Tracks total token usage and context window thresholds                  |

Each section is described in detail below.

## Modules

The `modules` section maps module numbers (integers 1 through 11) to their steering files. There are two entry formats: simple and split.

### Simple Format

A simple entry maps a module number directly to a steering filename string:

```yaml
modules:
  2: module-02-sdk-setup.md
  3: module-03-system-verification.md
```

The agent loads the single file when the bootcamper enters that module.

### Split Format

A split entry maps a module number to an object with a `root` key and a `phases` mapping. Split modules are used when a steering file exceeds the `split_threshold_tokens` budget limit and has been divided into phases for incremental loading.

```yaml
modules:
  1:
    root: module-01-business-problem.md
    phases:
      phase1-discovery:
        file: module-01-business-problem.md
        token_count: 2487
        size_category: large
        step_range: [1, 9]
      phase2-document-confirm:
        file: module-01-phase2-document-confirm.md
        token_count: 1686
        size_category: medium
        step_range: [10, 18]
```

Each phase entry contains:

| Field           | Type              | Description                                                  |
|-----------------|-------------------|--------------------------------------------------------------|
| `file`          | string            | Steering filename for this phase                             |
| `token_count`   | integer           | Approximate token count for this phase file                  |
| `size_category` | string            | Size classification: `"small"`, `"medium"`, or `"large"`     |
| `step_range`    | list of 2 integers| `[start_step, end_step]` — the step range this phase covers  |

The `root` key identifies the original (unsplit) steering file. The agent uses `step_range` to load only the phase relevant to the bootcamper's current step, keeping context usage within budget.

In the current index, modules 1, 5, 6, and 11 use the split format.

## Keywords

The `keywords` section maps trigger words (strings the bootcamper might mention) to steering filenames. When the agent detects a keyword in the conversation, it loads the corresponding steering file to provide context-relevant guidance.

```yaml
keywords:
  error: common-pitfalls.md
  stuck: common-pitfalls.md
  troubleshoot: troubleshooting-decision-tree.md
  resume: session-resume.md
  onboard: onboarding-flow.md
```

Each entry is a simple key-value pair:

| Field   | Type   | Description                                              |
|---------|--------|----------------------------------------------------------|
| key     | string | Trigger word that activates the lookup                   |
| value   | string | Steering filename to load when the keyword is detected   |

Multiple keywords can map to the same steering file (e.g., `error` and `stuck` both map to `common-pitfalls.md`).

## Languages

The `languages` section maps programming language names to their language-specific steering filenames. The agent loads the appropriate file based on the language the bootcamper selected during onboarding.

```yaml
languages:
  python: lang-python.md
  java: lang-java.md
  csharp: lang-csharp.md
  rust: lang-rust.md
  typescript: lang-typescript.md
```

Each entry maps a language identifier (lowercase string) to a steering filename containing language-specific SDK patterns, code conventions, and module adaptations.

## Deployment

The `deployment` section maps deployment target names to their deployment-specific steering filenames. The agent loads the appropriate file when the bootcamper reaches Module 11 (deployment) or mentions a deployment target.

```yaml
deployment:
  onpremises: deployment-onpremises.md
  docker: deployment-onpremises.md
  azure: deployment-azure.md
  gcp: deployment-gcp.md
  kubernetes: deployment-kubernetes.md
```

Note that multiple targets can share a steering file — `onpremises` and `docker` both map to `deployment-onpremises.md`.

## File Metadata

The `file_metadata` section stores size information for every steering file referenced in the index. Each key is a steering filename, and each value is an object with two fields:

| Field | Type | Description |
| --- | --- | --- |
| `token_count` | integer | Approximate token count, calculated as file character count ÷ 4 |
| `size_category` | string | Size classification: `"small"` (< threshold), `"medium"`, or `"large"` |

```yaml
file_metadata:
  agent-instructions.md:
    token_count: 1761
    size_category: medium
  common-pitfalls.md:
    token_count: 3132
    size_category: large
  lessons-learned.md:
    token_count: 434
    size_category: small
```

The `token_count` values are approximations based on dividing the file's character count by 4. The `size_category` provides a quick classification for budget decisions — the agent may defer loading `"large"` files when approaching context budget thresholds.

## Budget

The `budget` section tracks the total token footprint of all steering files and defines the thresholds that govern the agent's context loading behavior.

| Field | Type | Description |
| --- | --- | --- |
| `total_tokens` | integer | Sum of all `token_count` values across `file_metadata` entries |
| `reference_window` | integer | Context window size (in tokens) used for threshold calculations |
| `warn_threshold_pct` | integer | Percentage of `reference_window` at which the agent starts deferring file loads |
| `critical_threshold_pct` | integer | Percentage of `reference_window` at which the agent unloads non-essential files |
| `split_threshold_tokens` | integer | Token count above which a steering file should be split into phases |

```yaml
budget:
  total_tokens: 87710
  reference_window: 200000
  warn_threshold_pct: 60
  critical_threshold_pct: 80
  split_threshold_tokens: 5000
```

When the agent's loaded token count reaches `warn_threshold_pct` of `reference_window` (60% of 200,000 = 120,000 tokens), it begins deferring non-essential file loads. At `critical_threshold_pct` (80% = 160,000 tokens), it actively unloads non-essential files. The percentage fields are authoritative — absolute thresholds are derived as `reference_window × (pct / 100)`. If `reference_window` changes, the absolute thresholds adjust automatically. Files whose `token_count` exceeds `split_threshold_tokens` (5,000) are candidates for splitting into phases via `split_steering.py`.

## Complete Example

The following shows a valid steering index with representative entries from each section:

```yaml
modules:
  1:
    root: module-01-business-problem.md
    phases:
      phase1-discovery:
        file: module-01-business-problem.md
        token_count: 2487
        size_category: large
        step_range: [1, 9]
      phase2-document-confirm:
        file: module-01-phase2-document-confirm.md
        token_count: 1686
        size_category: medium
        step_range: [10, 18]
  2: module-02-sdk-setup.md
  3: module-03-system-verification.md

keywords:
  error: common-pitfalls.md
  resume: session-resume.md

languages:
  python: lang-python.md

deployment:
  docker: deployment-onpremises.md

file_metadata:
  module-02-sdk-setup.md:
    token_count: 3166
    size_category: large
  common-pitfalls.md:
    token_count: 3132
    size_category: large

budget:
  total_tokens: 87710
  reference_window: 200000
  warn_threshold_pct: 60
  critical_threshold_pct: 80
  split_threshold_tokens: 5000
```

## Read By

- **The agent** — uses the steering index for module steering selection (loading the correct file or phase for the current module and step), keyword lookup (loading context-relevant files when trigger words are detected), and context budget tracking (deciding when to defer or unload files)
- **`validate_power.py`** — cross-references the steering index against actual files on disk to detect missing or orphaned steering files
- **`measure_steering.py --check`** — verifies that `token_count` values in `file_metadata` match the actual file sizes and that `total_tokens` in `budget` equals the sum of all file token counts
- **`lint_steering.py`** — validates the structural integrity of the steering index (required keys, correct types, valid references)

## Written By

- **`measure_steering.py`** — scans all steering files, recalculates token counts and size categories, updates the `file_metadata` section, and recomputes `total_tokens` in the `budget` section
- **`split_steering.py`** — converts a simple module entry into a split entry by generating phase files and adding the corresponding `phases` mapping with `file`, `token_count`, `size_category`, and `step_range` for each phase
- **Maintainers** — manually edit the `modules` section (adding or reordering modules), `keywords` section (registering new trigger words), `languages` section (adding language support), and `deployment` section (adding deployment targets)

---

**Last Updated:** 2026-04-17
