# Bugfix Requirements Document

## Introduction

When a bootcamper's stated record count exceeds 500 during Module 1 (Business Problem), the bootcamp mentions the 500-record evaluation limit and links to the license request page, but fails to proactively guide the bootcamper through the license configuration process. It also assumes the bootcamper does not have a license, rather than asking first. This creates a dead-end experience where enterprise users who already have a license are directed to request one they don't need, and users without a license receive no actionable guidance on how to obtain and configure one.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a bootcamper's record count exceeds 500 during Module 1 discovery THEN the system mentions the 500-record limit and links to the license request page without asking whether the bootcamper already has a Senzing license

1.2 WHEN a bootcamper's record count exceeds 500 during Module 1 discovery THEN the system does not walk the bootcamper through the step-by-step license configuration process (requesting, receiving, and configuring LICENSESTRINGBASE64)

1.3 WHEN a bootcamper who already has a license indicates a record count exceeding 500 THEN the system directs them to request a new license instead of asking them to provide their existing license key or file path for immediate configuration

### Expected Behavior (Correct)

2.1 WHEN a bootcamper's record count exceeds 500 during Module 1 discovery THEN the system SHALL first ask "Do you already have a Senzing license?" before providing any license-related guidance

2.2 WHEN a bootcamper confirms they already have a license THEN the system SHALL ask them to provide the Base64-encoded license string or file path and guide them through configuring it (decoding to `licenses/g2.lic` and adding `LICENSEFILE` to the engine config PIPELINE section)

2.3 WHEN a bootcamper confirms they do not have a license THEN the system SHALL guide them step-by-step through requesting an evaluation license (contact support@senzing.com, mention bootcamp use case, expect 1–2 business day turnaround, 30–90 day validity) and explain how to configure it once received

2.4 WHEN a bootcamper's record count exceeds 500 and they do not yet have a license THEN the system SHALL explain what to expect during the license process: where to request, what information to provide, how long it takes, and how to configure the license once received (decode Base64 to `licenses/g2.lic`, add LICENSEFILE to engine config)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a bootcamper's record count is 500 or fewer THEN the system SHALL CONTINUE TO proceed through Module 1 without mentioning license requirements (the built-in evaluation license is sufficient)

3.2 WHEN the bootcamper reaches Module 2 Step 5 (Configure License) THEN the system SHALL CONTINUE TO perform the existing mandatory license gate check regardless of what happened in Module 1

3.3 WHEN a bootcamper provides data source information with record counts during Module 1 Step 6 THEN the system SHALL CONTINUE TO parse and infer all five categories (record types, source count, problem category, matching criteria, desired outcome) without interruption from license guidance

3.4 WHEN a bootcamper's record count exceeds 500 and they choose to defer license configuration THEN the system SHALL CONTINUE TO allow them to proceed through Module 1 with a note that license configuration will be addressed in Module 2
