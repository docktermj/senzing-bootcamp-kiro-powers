# Bugfix Requirements Document

## Introduction

The Senzing Bootcamp agent surfaces question-related control markers to the
bootcamper that should never have been visible, and it can show the same
question twice. Both defects are driven entirely by the steering files (there is
no application code path involved) and were observed during onboarding — once at
programming-language selection and once at the comprehension check before track
selection.

This spec combines two related UX feedback items into a single bugfix because
both concern how question-adjacent markers reach the bootcamper:

- **Bug 1 — Internal gate/stop directives leak into user-facing output.** When
  the agent asks a 👉 question, internal control directives such as
  `⛔ **MANDATORY GATE** — ...` and `🛑 **STOP** — ...` are rendered to the
  bootcamper alongside the question. These directives govern agent behavior
  (end-the-turn, wait-for-input, never-skip) and are not information the
  bootcamper needs, so they read as visual noise.

- **Bug 2 — The same question is displayed twice.** A comprehension-check 👉
  question was phrased first as a prose "or" compound question, the
  compound-question self-correction regenerated it as a clean single question,
  and from the bootcamper's point of view the question appeared twice.

A tension the fix must reconcile: the `🛑 STOP` marker is currently treated as a
real emitted line. The conversational-eval harness
(`senzing-bootcamp/tests/test_eval_conversations.py`) uses the
`🛑 STOP — End your response here.` line as its `_BOUNDARY_LINE` convention — a
valid turn boundary that the `_ends_with_question_then_stop` and `_no_self_answer`
predicates accept. The correct behavior keeps the stop/gate semantics as
internal-only directives (they still govern agent behavior) while ensuring a
question turn is recognized as correctly bounded from the trailing 👉 question
alone, without a rendered `🛑 STOP` line.

## Bug Analysis

### Current Behavior (Defect)

The bootcamper sees internal control markers next to questions, and can see the
same question emitted twice.

1.1 WHEN the agent presents a 👉 question to the bootcamper THEN the system renders the internal `🛑 STOP — End your response here.` directive (or `🛑 **STOP** — ...`) on its own line in the user-facing output alongside the question.

1.2 WHEN the agent reaches a ⛔ mandatory gate while presenting a question THEN the system renders the `⛔ **MANDATORY GATE** — ...` directive to the bootcamper as visible output.

1.3 WHEN a steering file or its examples define a question presentation THEN the emitted example embeds the `🛑 STOP` line as a literal rendered boundary line — the convention the eval harness `_BOUNDARY_LINE` treats as a valid boundary — conflating an internal control directive with user-facing content.

1.4 WHEN the agent composes the comprehension-check 👉 question THEN the system phrases it as a prose "or" compound question ("Does everything make sense so far, or is there anything you'd like me to clarify?"), which triggers the compound-question self-correction.

1.5 WHEN an internal correction pass (e.g., the compound-question self-correction) fires after the 👉 question was already surfaced to the bootcamper THEN the system re-emits the regenerated question, so the bootcamper sees the same question twice.

### Expected Behavior (Correct)

Only the question itself reaches the bootcamper, exactly once; the stop/gate
semantics remain internal.

2.1 WHEN the agent presents a 👉 question to the bootcamper THEN the system SHALL render only the question itself (e.g., `👉 **Which programming language would you like to use for the bootcamp?**`) with no `🛑 STOP` directive visible in the output.

2.2 WHEN the agent reaches a ⛔ mandatory gate while presenting a question THEN the system SHALL keep the gate semantics internal and SHALL NOT render the `⛔ MANDATORY GATE` directive to the bootcamper.

2.3 WHEN a steering file or its examples define a question presentation THEN the system SHALL treat `🛑 STOP` and `⛔ MANDATORY GATE` as internal-only directives (still governing end-the-turn, wait-for-input, and never-skip behavior) and SHALL define a question-turn boundary that is recognizable from the trailing 👉 question alone, so no literal `🛑 STOP` line is required in user-facing output.

2.4 WHEN the agent composes the comprehension-check (or any) 👉 question THEN the system SHALL compose a clean, single, non-compound question the first time (e.g., `👉 **Does the overview make sense before we choose a track?**`) so no compound-question self-correction or regeneration is triggered.

2.5 WHEN an internal correction pass fires after a 👉 question was already surfaced to the bootcamper THEN the system SHALL suppress the duplicate and SHALL NOT re-display a question that has already been shown, unless the bootcamper explicitly asks to see it again.

### Unchanged Behavior (Regression Prevention)

The turn-taking guarantees, gate enforcement, and eval harness must all keep
working; only the visible rendering of internal markers and the duplicate
emission change.

3.1 WHEN a yielding turn ends THEN the system SHALL CONTINUE TO end with exactly one 👉 leading question wrapped in bold (the One Question Rule and leading-question guarantee are preserved).

3.2 WHEN the agent asks a 👉 question or reaches a ⛔ gate THEN the system SHALL CONTINUE TO stop and wait for the bootcamper's real input — no self-answering, no assuming a response, no proceeding to the next step.

3.3 WHEN a ⛔ mandatory gate step is reached THEN the system SHALL CONTINUE TO execute it unconditionally and never skip it, even though the `⛔ MANDATORY GATE` directive is no longer rendered.

3.4 WHEN the compound-question rule (Rule 3) detects an actual compound or ambiguous question THEN the system SHALL CONTINUE TO rewrite it into a single unambiguous question before presenting it.

3.5 WHEN the bootcamper explicitly asks to see a question again THEN the system SHALL CONTINUE TO re-display that question.

3.6 WHEN a hook produces genuine corrective output (e.g., a rewritten question that has not yet been surfaced) THEN the system SHALL CONTINUE TO display that corrective content per the existing hook-output rules.

3.7 WHEN the shipped eval fixtures are evaluated THEN the system SHALL CONTINUE TO pass with zero failures so the conversational-eval-harness CI step remains at exit code 0.
