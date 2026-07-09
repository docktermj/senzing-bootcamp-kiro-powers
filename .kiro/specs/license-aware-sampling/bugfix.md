# Bugfix Requirements Document

## Introduction

The senzing-bootcamp Kiro Power steering assumes the built-in ~500-record evaluation
license and plans to downsample collected data to fit that assumed cap, without ever
querying the license the SDK will actually use. In Module 2 the bootcamper can configure
a custom Senzing license (from `licenses/g2.lic`, `SENZING_LICENSE_PATH`, or the system
CONFIGPATH such as `/etc/opt/senzing`). At the sampling and capacity decision points in
Module 4 (Step 6), Module 6 (loading), and Module 8 (performance) — and at the Module 1
Step 6a record-count threshold check — the agent repeatedly cites the hardcoded
500-record evaluation limit and recommends downsampling (for example, 5,726 records →
≤500) instead of reading the active license via `SzProduct.get_license()`.

When a custom license is present, its actual `recordLimit` may differ from 500 — a real
session observed EVAL / STANDARD with `recordLimit: 0` (no record cap), expiring
2027-03-12. Assuming the default 500 limit forces unnecessary downsampling, under-loads
the data, and reduces the cross-source matches and relationships that are the whole point
of the fraud/due-diligence use case — degrading the core deliverable. It also effectively
ignores the license the bootcamper explicitly supplied in Module 2.

The fix makes the sampling decision license-aware: after license setup in Module 2, and
again before any sampling or capacity decision, the agent should read the active license's
real `recordLimit` (a value of `0` means no cap), drive the decision from that value,
persist the detected limit to `config/bootcamp_progress.json` for reuse by later modules,
and stop restating the hardcoded 500 figure as authoritative once a custom license is
present. All Senzing SDK facts (the `get_license` call, `recordLimit` semantics, and the
built-in evaluation capacity) must come from the Senzing MCP server, never training data.
This bug lives primarily in the steering Markdown and may require a small stdlib-only
helper and a config contract; it does not change how Senzing itself enforces licensing.

## Bug Analysis

### Current Behavior (Defect)

The agent drives every capacity and sampling decision from the hardcoded 500-record
built-in evaluation limit and never inspects the license the SDK will actually use.

1.1 WHEN a custom Senzing license has been configured in Module 2 AND the agent reaches a sampling or capacity decision (Module 4 Step 6, Module 6 loading, or Module 8 performance) THEN the agent assumes the built-in ~500-record evaluation limit and never calls `SzProduct.get_license()` to read the active license.

1.2 WHEN the active license imposes no record cap (`recordLimit` of 0) or a cap greater than the dataset size THEN the agent still recommends downsampling the data toward ≤500 records, under-loading the dataset.

1.3 WHEN a custom license is present THEN the agent restates the hardcoded 500-record figure — and the "SENZ9000 error at record 501" claim — as the authoritative record limit.

1.4 WHEN a license is configured in Module 2 THEN the agent does not record the active license's actual `recordLimit` in `config/bootcamp_progress.json`, so later modules re-derive the 500 assumption instead of reusing a detected limit.

1.5 WHEN the record-count threshold or capacity check runs (Module 1 Step 6a, Module 4 Step 6, Module 6, Module 8) THEN the agent compares the dataset total against the hardcoded 500 figure rather than against the effective license `recordLimit`.

### Expected Behavior (Correct)

The agent reads the active license and drives every capacity and sampling decision from
the real `recordLimit`, treating the hardcoded 500 only as the built-in evaluation
default when no other license applies.

2.1 WHEN a custom Senzing license has been configured in Module 2 AND the agent reaches a sampling or capacity decision (Module 4 Step 6, Module 6 loading, or Module 8 performance) THEN the agent SHALL call `SzProduct.get_license()` and drive the decision from the active license's actual `recordLimit`.

2.2 WHEN the active license reports a `recordLimit` of 0 (no cap, confirmed via the Senzing MCP server) or a cap greater than or equal to the dataset size THEN the agent SHALL NOT recommend downsampling for license reasons and SHALL support loading the full dataset.

2.3 WHEN a custom license is present THEN the agent SHALL present the detected `recordLimit` and SHALL NOT restate the hardcoded 500-record figure (or the "SENZ9000 at record 501" claim) as the authoritative limit.

2.4 WHEN a license is configured in Module 2 THEN the agent SHALL record the detected active `recordLimit` in `config/bootcamp_progress.json` so later modules reuse it instead of re-deriving the 500 assumption.

2.5 WHEN the record-count threshold or capacity check runs (Module 1 Step 6a, Module 4 Step 6, Module 6, Module 8) THEN the agent SHALL compare the dataset total against the effective `recordLimit` (from `get_license()` when a license is configured) and SHALL recommend sampling only when the actual limit is exceeded.

### Unchanged Behavior (Regression Prevention)

The fix must not disturb the demo/evaluation flow, non-license uses of the number 500, or
the MCP-sourced-facts rule.

3.1 WHEN no custom license is configured (only the built-in evaluation license is active) AND the dataset is within the evaluation capacity THEN the agent SHALL CONTINUE TO proceed through the demo/evaluation flow without recommending sampling.

3.2 WHEN no custom license is present THEN the agent SHALL CONTINUE TO explain the built-in evaluation license (capacity confirmed via the Senzing MCP server) and the SENZ9000-at-limit behavior in Module 2 Step 5a.

3.3 WHEN a dataset is very large or unwieldy (for example, >1GB) or the bootcamper wants faster iteration THEN the agent SHALL CONTINUE TO offer sampling as an option for speed or size reasons, independent of the license limit.

3.4 WHEN the dataset total genuinely exceeds the effective record limit THEN the agent SHALL CONTINUE TO present the Module 1 licensing paths (apply an existing license, external request, or the in-flow MCP request when available) as choices rather than forcing downsampling.

3.5 WHEN any Senzing SDK fact is needed THEN the agent SHALL CONTINUE TO source it from the Senzing MCP server, never from training data.

3.6 WHEN the number 500 is used for a non-license purpose (Module 6 volume tiers, Module 8 performance thresholds, or the visualization entity cap) THEN the agent SHALL CONTINUE TO use those figures unchanged, since they are not the license record limit.
