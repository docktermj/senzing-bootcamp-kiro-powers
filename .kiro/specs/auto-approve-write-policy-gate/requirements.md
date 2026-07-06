# Requirements Document

## Introduction

During Senzing Bootcamp onboarding, file writes surface repeated "Rejected creation of ..." followed by "Accepted edits to ..." message pairs. These pairs are produced by the `write-policy-gate` preToolUse hook, which briefly intercepts each write for inspection before it is re-issued and completes. The intercept-then-retry cycle is visually noisy and can look like a failure to a new bootcamper, even though writes succeed on retry and no data is lost.

This feature adds a proactive, opt-in offer during onboarding to add the `write-policy-gate` hook to the Kiro auto-approve list. Auto-approving the hook lets writes pass through without the visible intercept cycle while preserving all of the hook's safety checks (Senzing SQL blocking, single-question enforcement, file-path policies, and root-placement policies). The offer surfaces the choice to the bootcamper rather than requiring them to discover the workaround on their own.

This feature affects onboarding steering content in `senzing-bootcamp/steering/` and the guidance the agent presents during onboarding. It does not modify the `write-policy-gate` hook's checks.

## Glossary

- **Bootcamp_Agent**: The Kiro agent executing the Senzing Bootcamp onboarding flow using the power's steering content.
- **Write_Policy_Gate**: The `write-policy-gate.kiro.hook` preToolUse hook that performs four write-policy checks (Senzing SQL blocking, single-question enforcement, file-path policies, root-placement policies) on write operations.
- **Auto_Approve_List**: The Kiro mechanism that allows a specific hook to pass through without surfacing the visible intercept-then-retry cycle, managed by the bootcamper through the Agent Hooks panel.
- **Intercept_Cycle**: The visible "Rejected creation of ..." followed by "Accepted edits to ..." message pair produced when a write is held for inspection by Write_Policy_Gate and then re-issued.
- **Auto_Approve_Offer**: The opt-in choice the Bootcamp_Agent presents during onboarding asking whether to add Write_Policy_Gate to the Auto_Approve_List.
- **Onboarding_Flow**: The onboarding steering content in `senzing-bootcamp/steering/onboarding-flow.md` (and its phase sub-files) that governs the bootcamp setup sequence.
- **Safety_Check**: Any one of the four Write_Policy_Gate policy checks: Senzing SQL blocking, single-question enforcement, file-path policy, and root-placement policy.

## Requirements

### Requirement 1: Present the auto-approve offer during onboarding

**User Story:** As a bootcamper, I want to be offered the option to auto-approve the write-policy-gate hook during onboarding, so that I can silence the noisy intercept cycle without discovering the workaround myself.

#### Acceptance Criteria

1. WHEN the Onboarding_Flow reaches the hook-installation step and Write_Policy_Gate has been installed, THE Bootcamp_Agent SHALL present the Auto_Approve_Offer to the bootcamper exactly once within that step.
2. THE Auto_Approve_Offer SHALL include text describing that auto-approving Write_Policy_Gate removes the visible Intercept_Cycle.
3. THE Auto_Approve_Offer SHALL include text stating that all four Safety_Checks remain active after auto-approval.
4. THE Auto_Approve_Offer SHALL present exactly two selectable choices and no others: one choice that accepts the auto-approval and one choice that declines the auto-approval.
5. IF the Onboarding_Flow reaches the hook-installation step and Write_Policy_Gate has not been installed, THEN THE Bootcamp_Agent SHALL NOT present the Auto_Approve_Offer.
6. WHILE the Auto_Approve_Offer is displayed and the bootcamper has selected neither choice, THE Bootcamp_Agent SHALL keep the Onboarding_Flow on the hook-installation step and SHALL NOT record any change to the Auto_Approve_List.

### Requirement 2: Treat the offer as an opt-in choice

**User Story:** As a bootcamper, I want the auto-approval to be my explicit choice, so that I stay in control of which hooks bypass the visible intercept.

#### Acceptance Criteria

1. WHILE the Bootcamp_Agent is awaiting an explicit acceptance or decline of the Auto_Approve_Offer, THE Bootcamp_Agent SHALL keep the Intercept_Cycle behavior active and SHALL NOT add Write_Policy_Gate to the Auto_Approve_List.
2. IF the bootcamper explicitly accepts the Auto_Approve_Offer, THEN THE Bootcamp_Agent SHALL provide the ordered steps to add Write_Policy_Gate to the Auto_Approve_List through the Agent Hooks panel.
3. IF the bootcamper explicitly declines the Auto_Approve_Offer, THEN THE Bootcamp_Agent SHALL continue the Onboarding_Flow with the Intercept_Cycle behavior unchanged.
4. IF the bootcamper explicitly declines the Auto_Approve_Offer, THEN THE Bootcamp_Agent SHALL inform the bootcamper that the auto-approval can be enabled later through the Agent Hooks panel.
5. IF the bootcamper's response to the Auto_Approve_Offer is neither a recognizable acceptance nor a recognizable decline, THEN THE Bootcamp_Agent SHALL re-present the Auto_Approve_Offer and SHALL continue to wait for an explicit acceptance or decline without modifying the Auto_Approve_List.

### Requirement 3: Preserve all safety checks

**User Story:** As a power maintainer, I want auto-approval to preserve every write-policy safety check, so that the bootcamper's environment stays protected after the intercept cycle is silenced.

#### Acceptance Criteria

1. THE Auto_Approve_Offer SHALL enumerate exactly four retained Safety_Checks and no others: Senzing SQL blocking, single-question enforcement, file-path policy, and root-placement policy.
2. THE feature SHALL leave the byte content of the `write-policy-gate.kiro.hook` file unchanged, so that a byte-for-byte comparison before and after the feature is applied is identical.
3. WHERE the bootcamper accepts the Auto_Approve_Offer, THE Auto_Approve_Offer guidance SHALL include text stating that a violation of any Safety_Check is still detected and blocked after auto-approval.
4. IF a write operation violates any Safety_Check after the bootcamper has accepted the Auto_Approve_Offer, THEN THE Write_Policy_Gate SHALL detect and block that write operation.

### Requirement 4: Record the bootcamper's decision

**User Story:** As a power maintainer, I want the bootcamper's auto-approve decision recorded, so that later steps do not repeat the offer and can honor the choice.

#### Acceptance Criteria

1. WHEN the bootcamper accepts the Auto_Approve_Offer, THE Bootcamp_Agent SHALL record an acceptance value under a dedicated key in `config/bootcamp_preferences.yaml`.
2. WHEN the bootcamper declines the Auto_Approve_Offer, THE Bootcamp_Agent SHALL record a decline value, distinct from the acceptance value, under the same dedicated key in `config/bootcamp_preferences.yaml`.
3. WHEN the Bootcamp_Agent records the decision in `config/bootcamp_preferences.yaml`, THE Bootcamp_Agent SHALL preserve all existing keys and values in the file and SHALL modify only the dedicated key.
4. IF the dedicated key already holds a recorded decision in `config/bootcamp_preferences.yaml`, THEN THE Bootcamp_Agent SHALL NOT present the Auto_Approve_Offer again during the same Onboarding_Flow.
5. IF `config/bootcamp_preferences.yaml` does not exist when the Bootcamp_Agent records the decision, THEN THE Bootcamp_Agent SHALL create the file with the dedicated key set to the recorded decision.
6. IF the Bootcamp_Agent cannot write the decision to `config/bootcamp_preferences.yaml`, THEN THE Bootcamp_Agent SHALL preserve the file's existing content and SHALL inform the bootcamper that the decision could not be saved.
7. IF `config/bootcamp_preferences.yaml` cannot be parsed when the Bootcamp_Agent records the decision, THEN THE Bootcamp_Agent SHALL NOT overwrite the file's existing content and SHALL inform the bootcamper that the decision could not be saved.

### Requirement 5: Align existing onboarding explanation with the offer

**User Story:** As a bootcamper, I want the existing explanation of the "Rejected"/"Accepted" messages to reference the auto-approve option, so that the guidance is consistent and I understand my options.

#### Acceptance Criteria

1. THE Onboarding_Flow section that explains the Intercept_Cycle SHALL include a reference to the Auto_Approve_Offer that states accepting the offer removes the visible "Rejected"/"Accepted" messages for all subsequent Write_Policy_Gate operations during onboarding.
2. WHERE the bootcamper has accepted the Auto_Approve_Offer, THE Onboarding_Flow SHALL describe the Intercept_Cycle as suppressed for the remainder of onboarding rather than as ongoing expected behavior.
3. WHERE the bootcamper has not accepted the Auto_Approve_Offer, THE Onboarding_Flow SHALL describe the Intercept_Cycle as the ongoing expected behavior for the remainder of onboarding.
4. THE Onboarding_Flow reference to the Auto_Approve_Offer SHALL use the exact glossary term "Auto_Approve_Offer" so that a tester can confirm the reference by exact string match within the Intercept_Cycle explanation section.
