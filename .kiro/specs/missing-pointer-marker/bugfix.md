# Bugfix Requirements Document

## Introduction

During Onboarding Step 4c (Comprehension Check), the agent asked "That was a lot of ground to cover — does everything so far make sense?" without the required 👉 prefix marker. The bootcamp conversation protocol mandates that all questions directed at the bootcamper use the 👉 marker to signal that input is expected. While the `onboarding-flow.md` steering file does include the 👉 prefix in the Step 4c template text, the instruction format embeds the marker inside a quoted string (`👉 "That was a lot of ground to cover..."`), which the agent may interpret as descriptive prose rather than a literal output requirement. The fix should make the 👉 prefix requirement unambiguous and enforceable at the point where the comprehension check question is defined.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent executes Onboarding Step 4c (Comprehension Check) and presents the comprehension question THEN the system outputs the question text without the 👉 prefix marker, producing "That was a lot of ground to cover — does everything so far make sense?" instead of "👉 That was a lot of ground to cover — does everything so far make sense?"

1.2 WHEN the agent paraphrases the Step 4c comprehension check question from onboarding-flow.md THEN the system drops the 👉 prefix because the marker is embedded inside a quoted string in the steering file instruction rather than being presented as a mandatory output format requirement

### Expected Behavior (Correct)

2.1 WHEN the agent executes Onboarding Step 4c (Comprehension Check) and presents the comprehension question THEN the system SHALL output the question with the 👉 prefix marker: "👉 That was a lot of ground to cover — does everything so far make sense?"

2.2 WHEN the agent formats any question directed at the bootcamper during Step 4c THEN the system SHALL include the 👉 prefix marker regardless of whether the agent paraphrases or quotes the question verbatim from the steering file

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent presents informational content during Step 4 (overview, module table, track descriptions) that does not require bootcamper input THEN the system SHALL CONTINUE TO omit the 👉 prefix from that content

3.2 WHEN the agent executes other onboarding steps that contain 👉 questions (Steps 2, 3a, 3b, 4b, 5) THEN the system SHALL CONTINUE TO include the 👉 prefix on those questions as currently specified

3.3 WHEN the bootcamper responds to the Step 4c comprehension check with an acknowledgment (e.g., "makes sense", "got it") THEN the system SHALL CONTINUE TO proceed directly to Step 5 (Track Selection) without asking follow-up questions about the overview

3.4 WHEN the bootcamper responds to the Step 4c comprehension check with a clarification question THEN the system SHALL CONTINUE TO answer using the bootcamper's verbosity settings and then check for additional questions before proceeding

3.5 WHEN the enforce-single-question hook validates the question written to config/.question_pending THEN the system SHALL CONTINUE TO enforce the single-question rule on the comprehension check question
