# Implementation Plan: Better License Guidance in Module 0

## Overview

Improve license guidance across four documentation/steering files so that the 500-record evaluation limit, license placement, and Base64 decoding are explained proactively during Module 0 (SDK Setup). All changes are Markdown content updates — no code changes.

## Tasks

- [ ] 1. Rewrite Step 5 in the Module 0 steering file
  - [ ] 1.1 Rewrite Step 5 ("Configure License") in `senzing-bootcamp/steering/module-00-sdk-setup.md`
    - Lead with a proactive explanation that Senzing includes a built-in 500-record evaluation license and no file is needed for small datasets
    - Explain that loading more than 500 records triggers SENZ9000 at record 501
    - Add a prompt asking the user if they have a license file or Base64-encoded key
    - Add Base64 decode instructions for Linux/macOS (`base64 --decode`) and Windows (PowerShell `FromBase64String`)
    - Add a verification step to confirm the decoded file is binary (`file licenses/g2.lic`)
    - Include the path for users who have a `.lic` file directly (`cp` to `licenses/g2.lic`)
    - Include the fallback path for users with no license: confirm evaluation is active, mention `support@senzing.com` for free evaluation license
    - Preserve the existing `LICENSEFILE` engine config instruction and preference recording
    - _Requirements: 1, 2, 3, 4_

- [ ] 2. Update the FAQ license Q&A
  - [ ] 2.1 Update the "Do I need a Senzing license?" answer in `senzing-bootcamp/docs/guides/FAQ.md`
    - Lead the answer with the 500-record evaluation limit explanation and what happens at record 501 (SENZ9000)
    - Add explicit Base64 decoding instructions (decode before placing as `licenses/g2.lic`)
    - Cross-reference `licenses/README.md` for full details
    - Ensure the tone is proactive ("here's what you need to know") rather than reactive
    - _Requirements: 1, 3, 4_

- [ ] 3. Checkpoint — Review steering and FAQ changes
  - Ensure the 500-record limit explanation, Base64 decode commands, and `licenses/g2.lic` path are consistent between the steering file and FAQ. Ask the user if questions arise.

- [ ] 4. Add Base64 decoding section to licenses/README.md
  - [ ] 4.1 Add a "Decoding a Base64-Encoded License" section to `senzing-bootcamp/licenses/README.md`
    - Insert the new section between "How to Obtain a Senzing License" and "License File Placement"
    - Explain when a user would have a Base64 string (received via email, copied from a portal)
    - Provide decode commands for Linux/macOS and Windows (PowerShell)
    - Include a verification step to confirm the decoded file is binary
    - _Requirements: 3_

- [ ] 5. Update the MODULE_0_SDK_SETUP.md license section
  - [ ] 5.1 Update the "Senzing License Requirements" section in `senzing-bootcamp/docs/modules/MODULE_0_SDK_SETUP.md`
    - Explicitly state the 500-record built-in evaluation limit
    - Explain what happens at record 501 (SENZ9000 error)
    - Add Base64 decoding instructions for Linux/macOS and Windows
    - Make the tone proactive ("here's what you need to know before you start loading data")
    - Ensure consistency with the steering file and FAQ wording
    - _Requirements: 1, 2, 3, 4_

- [ ] 6. Final checkpoint — Cross-reference consistency and validation
  - Verify the 500-record limit explanation, Base64 decode commands, and license placement path (`licenses/g2.lic`) are consistent across all four modified files
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` on modified Markdown files to ensure formatting compliance
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- No code changes — all tasks modify Markdown documentation and steering content
- Property-based testing is not applicable; validation is via cross-reference consistency and CommonMark checks
- Each task references specific acceptance criteria from the requirements document (numbered 1–4)
- Checkpoints ensure incremental validation of consistency across files
