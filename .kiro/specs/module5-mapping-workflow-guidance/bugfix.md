# Bugfix Requirements Document

## Introduction

The Module 5 (Data Quality & Mapping) Phase 2 mapping-workflow guidance in the senzing-bootcamp power is brittle at two points during a per-source `mapping_workflow` run:

1. **Unexecutable hard gate on 404 validation scripts.** The MCP server's `mapping_workflow` advertises three validation scripts at Step 1 and requires all three at Step 4 (generate/validate). Two of them — `sz_verbatim_check.py` (verbatim-fidelity gate) and `sz_routing_report.py` (routing-coverage report) — currently return HTTP 404 from the server's resource endpoint, while `sz_json_analyzer.py` is still hosted (HTTP 200). Because the verbatim-fidelity check is framed as a hard gate ("Do NOT proceed until it passes"), an unavailable script leaves the bootcamper blocked or confused, with no confirmed inline fallback.

2. **No forward guidance after the Step 5 menu.** After a source's mapping is approved at Step 4, `mapping_workflow` returns Step 5 (`detect_environment`) with a four-option menu (skip / test_load / load+resolve / done). The Module 5 guidance does not relay a recommendation or next action, so the bootcamper hits a dead end mid-module without knowing that Steps 5–8 are optional sandbox validation or that they can skip and continue to the next source.

Re-hosting the missing scripts is a server-side concern outside the power's control. The fix scoped here is **power-side only**: make the Module 5 Phase 2 guidance resilient so the agent (a) degrades the verbatim-fidelity and routing-coverage checks to optional/best-effort when their scripts are unavailable, proceeding with the hosted `sz_json_analyzer.py`, and (b) explicitly handles the Step 5 menu by surfacing the optional nature of Steps 5–8, recommending a skip when multiple sources remain, and continuing to the next unmapped source.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `mapping_workflow` Step 4 requires the verbatim-fidelity check but `sz_verbatim_check.py` returns HTTP 404 (and no working inline fallback is available) THEN the Module 5 guidance treats the verbatim-fidelity check as a hard blocking gate that cannot be executed, leaving the mapping workflow blocked or confused.

1.2 WHEN `mapping_workflow` Step 4 requires the routing-coverage report but `sz_routing_report.py` returns HTTP 404 (and no working inline fallback is available) THEN the Module 5 guidance still requires running it, leaving no defined way to complete validation and proceed.

1.3 WHEN `mapping_workflow` returns the Step 5 menu (`detect_environment`: skip / test_load / load+resolve / done) after a source's mapping is approved at Step 4 THEN the Module 5 guidance provides no recommendation or next action, leaving the bootcamper at a dead end mid-module.

1.4 WHEN the Step 5 menu is returned and multiple unmapped sources remain THEN the Module 5 guidance does not surface that Steps 5–8 are optional sandbox validation, does not recommend skipping the per-source test load, and does not continue to the next unmapped source.

### Expected Behavior (Correct)

2.1 WHEN the verbatim-fidelity script (`sz_verbatim_check.py`) is unavailable (HTTP 404 or no working inline fallback) THEN the system SHALL treat the verbatim-fidelity check as optional/best-effort, inform the bootcamper it is being skipped because the script is unavailable, and proceed without blocking the mapping workflow.

2.2 WHEN the routing-coverage script (`sz_routing_report.py`) is unavailable (HTTP 404 or no working inline fallback) THEN the system SHALL treat the routing-coverage check as optional/best-effort, inform the bootcamper it is being skipped because the script is unavailable, and proceed without blocking the mapping workflow.

2.3 WHEN the verbatim/routing scripts are unavailable but `sz_json_analyzer.py` is available THEN the system SHALL proceed using `sz_json_analyzer.py` (structural + Entity-Specification validation) as the primary mapping validation and continue the mapping workflow.

2.4 WHEN `mapping_workflow` returns the Step 5 menu after Step 4 approval THEN the system SHALL state that Steps 5–8 are optional sandbox validation and explain the available choices.

2.5 WHEN the Step 5 menu is returned and one or more unmapped sources remain THEN the system SHALL recommend skipping the per-source test load (noting the real load happens in Module 6) and automatically continue to the next unmapped source.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `sz_json_analyzer.py` is available THEN the system SHALL CONTINUE TO run structural + Entity-Specification validation as the primary mapping validation.

3.2 WHEN the verbatim-fidelity and routing-coverage scripts ARE available (hosted, or via a working inline fallback) THEN the system SHALL CONTINUE TO run the verbatim-fidelity and routing-coverage checks as before.

3.3 WHEN mapping a data source THEN the system SHALL CONTINUE TO follow the normal `mapping_workflow` progression, including per-source mapping and approval at Step 4.

3.4 WHEN the bootcamper explicitly chooses `test_load` or `load+resolve` at the Step 5 menu THEN the system SHALL CONTINUE TO follow that path (Phase 3 Steps 5–8) as before.

3.5 WHEN data is loaded for real THEN the system SHALL CONTINUE TO defer the production load to Module 6.
