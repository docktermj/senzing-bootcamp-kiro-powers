# Requirements Document

## Introduction

The mandatory exploration gate at the end of the entity-resolution concepts intro
(`senzing-bootcamp/steering/entity-resolution-intro.md`, the "Explore Further"
section) currently ends its turn with a single 👉 call-to-action that offers a
two-record match / non-match illustration: "Want to see a quick two-record
example of a match and a non-match before we move on?". While the gate's prose
already invites open questions, the closing 👉 nudges the bootcamper toward a
yes/no on a specific illustration and skips over the more valuable open-ended
exploration step.

This feature reorders the gate's calls-to-action so the bootcamper is first given
an explicit open 👉 prompt — "Do you have any questions about Entity
Resolution?" — as the closing call-to-action of the gate. Only after that open
prompt has been handled (the bootcamper's questions answered via the Senzing MCP
server, or the bootcamper signals readiness / has no questions) does the agent
present the two-record illustration offer as a subsequent 👉.

The change preserves everything already established for this gate: the wait/stop
semantics (the agent stops and waits for real input), MCP-first answering of
follow-up questions, the once-only concepts banner, and the illustration offer's
existing properties (optional, non-compound, ask-once, verbosity-aware, and a
preview that points forward to the Module 3 hands-on visualization). It builds on
`er-intro-interactive-illustration` and must not duplicate or pre-empt the
Module 3 "wow" visualization.

## Glossary

- **Agent**: the Kiro agent presenting the bootcamp onboarding flow to the
  bootcamper.
- **Bootcamper**: the developer working through the Senzing bootcamp.
- **ER**: Entity Resolution.
- **Exploration_Gate**: the existing ⛔ MANDATORY GATE in the "Explore Further"
  section of `entity-resolution-intro.md` where the Agent stops and waits for the
  Bootcamper to explore or signal readiness.
- **Open_Questions_Prompt**: a new open, optional 👉 call-to-action reading "Do
  you have any questions about Entity Resolution?", presented as the closing
  call-to-action of the Exploration_Gate.
- **Illustration_Offer**: the existing 👉 offer to view the ER_Illustration (a
  tiny two-record match / non-match teaser).
- **ER_Illustration**: the tiny, conceptual match / non-match teaser rendered
  inline when the Bootcamper accepts the Illustration_Offer.
- **ER_Concepts_Banner**: the "ENTITY RESOLUTION CONCEPTS" banner displayed once
  per Preface run.
- **Readiness_Signal**: a Bootcamper response indicating readiness to move on
  (for example "ready", "let's go", "continue", "next", or "no questions").
- **One_Question_Rule**: the existing convention that a gate turn ends with
  exactly one 👉 call-to-action that is non-compound.

## Requirements

### Requirement 1: Present the open questions prompt first

**User Story:** As a bootcamper finishing the ER concepts intro, I want an open invitation to ask my own questions before being offered a specific example, so that I can dig into whatever sparked my curiosity.

#### Acceptance Criteria

1. WHEN the Exploration_Gate is presented, THE Agent SHALL end the gate turn with the Open_Questions_Prompt as the single 👉 call-to-action.
2. WHEN the Exploration_Gate is presented, THE Agent SHALL NOT present the Illustration_Offer in the same turn as the Open_Questions_Prompt.
3. THE Open_Questions_Prompt SHALL comply with the One_Question_Rule (exactly one 👉, non-compound).
4. THE Open_Questions_Prompt SHALL be presented in accordance with the Bootcamper's verbosity settings.
5. WHEN the Bootcamper responds to the Open_Questions_Prompt with a Readiness_Signal indicating no further questions, THE Agent SHALL present the Illustration_Offer in the next turn.
6. WHEN the Bootcamper asks a question in response to the Open_Questions_Prompt, THE Agent SHALL answer that question before presenting the Illustration_Offer.

### Requirement 2: Preserve gate wait and answer semantics

**User Story:** As a bootcamper, I want the gate to keep waiting for my real input and to answer my ER questions from Senzing documentation, so that exploration stays accurate and unhurried.

#### Acceptance Criteria

1. WHEN the Open_Questions_Prompt is presented, THE Agent SHALL halt all output and wait for input actually submitted by the Bootcamper before taking any subsequent action.
2. WHILE the Agent is waiting for the Bootcamper's input at the Exploration_Gate, THE Agent SHALL NOT fabricate, simulate, or assume a Bootcamper response, and SHALL NOT proceed past the Exploration_Gate.
3. WHEN the Bootcamper asks a follow-up question about ER, THE Agent SHALL answer it using only content retrieved from the Senzing MCP server (`search_docs`) and THEN re-present the Exploration_Gate.
4. IF the Bootcamper's response is ambiguous, THEN THE Agent SHALL treat it as a follow-up question, answer it using only content retrieved from the Senzing MCP server (`search_docs`), and re-present the Exploration_Gate.
5. IF `search_docs` returns no relevant results or fails, THEN THE Agent SHALL state that no documentation was found, suggest a rephrase, and re-present the Exploration_Gate without proceeding past it.
6. WHEN the Exploration_Gate is re-presented, THE Agent SHALL NOT re-display the ER_Concepts_Banner.

### Requirement 3: Offer the illustration after the open prompt is handled

**User Story:** As a bootcamper who has finished asking open questions, I want the two-record example offered next, so that I can still see a concrete illustration before moving on.

#### Acceptance Criteria

1. WHEN the Bootcamper responds to the Open_Questions_Prompt with a Readiness_Signal or indicates no questions, THE Agent SHALL present the Illustration_Offer as the single 👉 call-to-action.
2. THE Illustration_Offer SHALL comply with the One_Question_Rule (exactly one 👉, non-compound) and the Bootcamper's verbosity settings.
3. THE Illustration_Offer SHALL be optional, requiring no acceptance for the Bootcamper to continue past the Exploration_Gate.
4. WHEN the Bootcamper declines the Illustration_Offer or sends a Readiness_Signal, THE Agent SHALL proceed past the Exploration_Gate.
5. WHEN the Illustration_Offer has been answered once, THE Agent SHALL NOT offer the Illustration_Offer again (ask-once).
6. WHEN the Bootcamper accepts the Illustration_Offer, THE Agent SHALL render the ER_Illustration inline and THEN re-present the Exploration_Gate.
7. IF the Bootcamper's response to the Illustration_Offer is not recognized as an acceptance, a decline, or a Readiness_Signal, THEN THE Agent SHALL re-present the Illustration_Offer once as the single 👉 with an indication that an accept-or-decline response is expected, and SHALL NOT proceed past the Exploration_Gate until a recognized response is received.

### Requirement 4: Keep the illustration a conceptual preview

**User Story:** As a bootcamper, I want the illustration to remain a lightweight preview, so that it does not pre-empt the Module 3 hands-on visualization.

#### Acceptance Criteria

1. THE ER_Illustration SHALL be presented as static, text-based conceptual content of no more than 25 lines, and SHALL NOT render an interactive entity graph.
2. THE ER_Illustration SHALL NOT start a web service or launch any external or background process to produce a visualization.
3. WHEN the ER_Illustration is rendered, THE Agent SHALL include an explicit forward reference stating that the interactive, hands-on entity visualization occurs in Module 3 using the Bootcamper's own data.
4. IF the Bootcamper requests the interactive entity graph or full visualization while the ER_Illustration is displayed, THEN THE Agent SHALL decline to render it, SHALL leave the conceptual preview unchanged, and SHALL direct the Bootcamper to the Module 3 hands-on visualization.

## Non-Goals

- Changing the content of the ER_Illustration or the concepts intro prose.
- Adding new gate stop/wait behavior beyond the existing semantics.
- Replacing, moving, or duplicating the Module 3 visualization.
- Making either the Open_Questions_Prompt or the Illustration_Offer a required
  step that blocks progress.
