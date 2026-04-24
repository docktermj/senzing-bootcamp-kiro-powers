# Requirements: Better License Guidance in Module 0

## Introduction

Proactively explain the Senzing 500-record evaluation limit during SDK Setup and guide users through license placement, including Base64 decoding.

## What Happened

During Module 0 (SDK Setup), the bootcamp detected an existing license file but didn't clearly explain the 500-record evaluation limit or guide the user through license placement and Base64 decoding.

## Why It's a Problem

Without clear guidance, users hit the 500-record limit unexpectedly during later modules (SENZ9000 error at record 501). License setup should be handled proactively during SDK Setup, not discovered as an error.

## Acceptance Criteria

1. Module 0 Step 5 explicitly explains that Senzing includes a built-in 500-record evaluation license and that a custom license is needed for larger datasets
2. The step guides users to place their license at `licenses/g2.lic` as a binary file
3. If the user provides a Base64-encoded license string, the bootcamp decodes it to binary and confirms the action
4. The guidance is presented proactively (not only after an error occurs)

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Better license guidance in Module 0 (SDK Setup)"
- Module: 0 | Priority: High | Category: Workflow
