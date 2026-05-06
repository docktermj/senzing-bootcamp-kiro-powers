# Requirements Document

## Introduction

Address three workflow issues where the agent does not follow through on expected behavior during the senzing-bootcamp power: (1) the agent tells the bootcamper to manually start the web server instead of starting it automatically as a background process, (2) the agent skips the license configuration step in Module 2 when the SDK is already installed, and (3) the agent fails to actually start the next module after the bootcamper confirms they want to proceed. Each issue has a clear root cause in the steering files and a targeted fix.

## Glossary

- **Agent**: The Kiro AI agent executing the bootcamp steering files during a session.
- **Bootcamper**: The developer using the senzing-bootcamp power to learn entity resolution.
- **Web_Service**: The localhost HTTP server generated in Module 3 or Module 7 for interactive entity visualization.
- **Background_Process**: A long-running process started via `controlBashProcess` that runs in the background without blocking the agent's response.
- **Visualization_Web_Service_Steering**: The steering file `visualization-web-service.md` that defines web service endpoint specs, framework selection, and lifecycle management.
- **Visualization_Guide_Steering**: The steering file `visualization-guide.md` that defines the visualization workflow and delivery mode choice.
- **Module_02_Steering**: The steering file `module-02-sdk-setup.md` that defines SDK installation and configuration steps.
- **License_Step**: Step 5 in Module_02_Steering that asks the bootcamper about their Senzing license situation.
- **Conversation_Protocol**: The steering file `conversation-protocol.md` with `inclusion: auto` that defines turn-taking and module transition rules.
- **Module_Transitions_Steering**: The steering file `module-transitions.md` with `inclusion: always` that defines module start banners, journey maps, and step-level progress.
- **Module_Completion_Steering**: The steering file `module-completion.md` that handles journal entries, reflection, and next-step options at module end.
- **Affirmative_Response**: Any bootcamper message that confirms intent to proceed (yes, sure, let's go, ready, yep, etc.).
- **Context_Limit**: The point at which the agent's context window is near capacity and may trigger progress-saving behavior instead of continuing work.

## Requirements

### Requirement 1: Auto-Start Web Server as Background Process

**User Story:** As a bootcamper, I want the agent to start the web server automatically after creating the service files, so that I can immediately open the URL without switching to a terminal to run a command manually.

#### Acceptance Criteria

1. WHEN the Agent generates web service files and the Web_Service is ready to run, THE Agent SHALL start the Web_Service as a Background_Process using `controlBashProcess` before presenting the localhost URL to the Bootcamper.
2. WHEN the Agent starts the Web_Service as a Background_Process, THE Agent SHALL wait for confirmation that the server is running (by reading process output) before presenting the URL.
3. WHEN the Agent presents the Web_Service URL, THE Agent SHALL also display the manual start command so the Bootcamper knows how to restart the server independently.
4. WHEN the Agent presents the Web_Service URL, THE Agent SHALL display the stop instructions (how to terminate the background process or use Ctrl+C if restarted manually).
5. IF the Web_Service fails to start as a Background_Process (port conflict, missing dependencies, SDK error), THEN THE Agent SHALL report the error, provide troubleshooting guidance, and fall back to instructing the Bootcamper to start the server manually.
6. THE Visualization_Web_Service_Steering SHALL replace the prohibition against starting the server as a background process with an instruction to start it automatically, while retaining the manual start command for reference.
7. THE Visualization_Guide_Steering Web Service Delivery Sequence SHALL be updated to include the auto-start step before presenting the URL.

### Requirement 2: License Step Is Never Skippable

**User Story:** As a bootcamper, I want the agent to always ask about my license situation during Module 2, so that I can configure a custom license upfront and avoid hitting the 500-record evaluation limit later.

#### Acceptance Criteria

1. THE Module_02_Steering SHALL mark Step 5 (Configure License) as a mandatory gate that is never skipped, regardless of whether the SDK is already installed.
2. WHEN Step 1 detects that the SDK is already installed (V4.0+), THE Module_02_Steering SHALL explicitly state that Step 5 (Configure License) must still be executed after verification.
3. THE Module_02_Steering Step 1 skip-ahead logic SHALL list Step 5 as a required stop even when Steps 2 and 3 are skipped.
4. THE Module_02_Steering Step 5 SHALL retain the existing 👉 question and 🛑 STOP marker requiring the Bootcamper to respond before proceeding.
5. WHEN the Bootcamper confirms they have no custom license, THE Module_02_Steering SHALL record `license: evaluation` in `config/bootcamp_preferences.yaml` and inform the Bootcamper of the 500-record limit and how to obtain a larger license later.

### Requirement 3: Module Transitions Execute Immediately on Confirmation

**User Story:** As a bootcamper, I want the agent to actually start the next module immediately when I confirm I am ready, so that the conversation continues without unnecessary pauses or session-saving interruptions.

#### Acceptance Criteria

1. WHEN the Bootcamper provides an Affirmative_Response to a "Ready for Module X?" question, THE Agent SHALL immediately begin Module X in the same turn by displaying the module banner, journey map, and starting Step 1.
2. THE Conversation_Protocol Module Transition Protocol section SHALL state that saving progress and ending the session is prohibited as a response to an Affirmative_Response to a module transition question.
3. THE Module_Completion_Steering SHALL reinforce that upon receiving an Affirmative_Response to "Ready to move on to Module [N]?", the agent must immediately execute the next module's startup sequence without intermediate acknowledgment.
4. IF the Agent determines that Context_Limit is a concern before asking the transition question, THEN THE Agent SHALL transparently inform the Bootcamper about the context limitation and offer to save progress BEFORE asking "Ready for Module X?" — not after receiving the affirmative response.
5. THE Conversation_Protocol SHALL state that once a "Ready for Module X?" question has been asked, the only valid response to an Affirmative_Response is to start Module X — never to save progress, pause, or end the session.
6. THE Module_Transitions_Steering SHALL include a "Transition Integrity" rule stating that module transition questions are commitments: asking the question means the agent is prepared to execute the transition if confirmed.
