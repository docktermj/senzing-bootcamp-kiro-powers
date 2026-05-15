# Bugfix Requirements Document

## Introduction

Module 3 Step 9 (Web Service + Visualization) is the "wow moment" of the bootcamp — a rich interactive visualization demonstrating entity resolution value with a D3.js force-directed graph, record merges view, merge statistics, and probe panel. The agent skipped this step entirely, jumping from data loading/validation (Steps 6–8) directly to cleanup (Step 11) and marking the module complete. The existing `enforce-visualization-offers` hook only checks whether a visualization was *offered*, not whether Step 9 was actually *executed*. There is no enforcement mechanism preventing the agent from bypassing mandatory steps before module completion.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN Module 3 Steps 1–8 complete successfully THEN the agent skips Step 9 (Web Service + Visualization) and proceeds directly to Step 10/11 (cleanup and module completion) without generating the web service, API endpoints, or visualization page

1.2 WHEN the agent reaches the Module 3 completion workflow THEN the system marks Module 3 as complete even though `config/bootcamp_progress.json` has no `web_service` or `web_page` checkpoint entries confirming Step 9 execution

1.3 WHEN the `enforce-visualization-offers` hook fires at agent stop THEN it only verifies that a visualization was *offered* via the visualization tracker, not that Step 9's web service was actually generated, started, and verified

### Expected Behavior (Correct)

2.1 WHEN Module 3 Steps 1–8 complete successfully THEN the system SHALL execute Step 9 (Web Service + Visualization) — generating the web service files, starting the server, verifying all 3 API endpoints, and presenting the visualization URL to the bootcamper — before proceeding to Step 10

2.2 WHEN the agent attempts to complete Module 3 THEN the system SHALL verify that `config/bootcamp_progress.json` contains `web_service` and `web_page` checkpoint entries with `"status": "passed"` before allowing module completion to proceed; if these entries are missing or failed, the system SHALL block completion and instruct the agent to execute Step 9

2.3 WHEN enforcement checks detect that Step 9 was not executed THEN the system SHALL direct the agent to load `module-03-phase2-visualization.md` and execute the full visualization step before any cleanup or module completion can occur

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper explicitly requests to skip Step 9 via the skip-step protocol THEN the system SHALL CONTINUE TO follow the existing skip-step protocol (acknowledge, record skip reason, assess consequences) rather than forcing execution

3.2 WHEN Module 3 Steps 1–8 fail (any verification check reports "failed" status) THEN the system SHALL CONTINUE TO report failures and block module completion without requiring Step 9 execution for failed modules

3.3 WHEN modules other than Module 3 reach completion THEN the system SHALL CONTINUE TO use their existing completion criteria without requiring web service checkpoint verification

3.4 WHEN the `enforce-visualization-offers` hook fires for modules 5, 7, or 8 THEN the system SHALL CONTINUE TO check visualization offers for those modules using the existing tracker-based mechanism without applying Module 3 Step 9 enforcement logic
