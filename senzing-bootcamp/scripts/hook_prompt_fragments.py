"""Single-source definitions of shared Module 3 gate-hook prompt fragments.

This module is the sole authoritative location for the hook-prompt text that is
shared (verbatim) across the three Module 3 gate hooks. The companion
``compose_hook_prompts.py`` script expands ``{{fragment:NAME}}`` markers in its
per-hook templates using the ``FRAGMENTS`` mapping defined here, reproducing the
on-disk ``.kiro.hook`` files byte-for-byte (a no-op refactor verified in CI).

Every value below is a *verbatim extract* of the corresponding text in the
current on-disk gate hooks. Do not paraphrase or reformat — the composer relies
on byte-identical reproduction.

Fragment provenance
--------------------
``module3_condition_a``
    The CONDITION A checkpoint-check block. Appears verbatim in ALL THREE gate
    hooks: ``gate-module3-visualization.kiro.hook``,
    ``enforce-mandatory-gate.kiro.hook``, and ``enforce-gate-on-stop.kiro.hook``.
``module3_gate_on_stop_violation``
    The ⛔ output string used only by ``enforce-gate-on-stop.kiro.hook``
    (the agentStop mandatory-gate safety net).
``module3_block_completion``
    The ⛔ output string used only by ``gate-module3-visualization.kiro.hook``
    (the preToolUse module-completion gate).
``module3_block_advancement``
    The ⛔ output string used only by ``enforce-mandatory-gate.kiro.hook``
    (the preToolUse advance-past-Step-9 gate).

Only Python standard-library features are used; importing this module yields the
fragments directly with no parsing layer.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Shared fragment text (verbatim extracts from the on-disk gate hooks).
#
# WARNING: these literals are byte-sensitive. The em dash (—), the backtick
# code spans, and the single quotes around 'passed' are all significant. Editing
# this text without re-running ``compose_hook_prompts.py --write`` will cause the
# CI drift check to fail.
# ---------------------------------------------------------------------------

#: CONDITION A checkpoint-check block — shared verbatim by all three gate hooks.
_MODULE3_CONDITION_A = """CONDITION A — Step 9 checkpoints exist:
- `module_3_verification.checks.web_service.status` equals `"passed"`
- `module_3_verification.checks.web_page.status` equals `"passed"`"""

#: ⛔ output string for enforce-gate-on-stop (agentStop gate-violation message).
_MODULE3_GATE_ON_STOP_VIOLATION = (
    "⛔ MANDATORY GATE VIOLATION DETECTED: Step 9 (Web Service + Visualization) has not been "
    "executed but the agent has advanced past it. This step CANNOT be skipped by the agent under "
    "any circumstances. Load `module-03-phase2-visualization.md` and execute Step 9 NOW — generate "
    "the web service, start the server, verify all 3 API endpoints, and present the URL to the "
    "bootcamper. Do not proceed with any other work until Step 9 is complete and checkpoints are "
    "written to bootcamp_progress.json."
)

#: ⛔ output string for gate-module3-visualization (block module-completion write).
_MODULE3_BLOCK_COMPLETION = (
    "⛔ BLOCKED: Module 3 cannot be marked complete — Step 9 (Web Service + Visualization) has not "
    "been executed. Load `module-03-phase2-visualization.md` and execute the full visualization "
    "step (generate web service, start server, verify 3 API endpoints, present URL to bootcamper). "
    "Only after web_service and web_page checkpoints show 'passed' can Module 3 be completed."
)

#: ⛔ output string for enforce-mandatory-gate (block advance past Step 9).
_MODULE3_BLOCK_ADVANCEMENT = (
    "⛔ BLOCKED: Cannot advance past Step 9 — this is a mandatory gate step (Web Service + "
    "Visualization). The ⛔ designation means this step must be executed unconditionally. No "
    "agent-internal reason (session length, context budget, perceived redundancy) can justify "
    "skipping a mandatory gate. Load `module-03-phase2-visualization.md` and execute the full "
    "visualization step (generate web service, start server, verify 3 API endpoints, present URL "
    "to bootcamper). Only after web_service and web_page checkpoints show 'passed' in "
    "bootcamp_progress.json can current_step advance past 9."
)

#: Authoritative mapping of fragment name -> shared prompt text.
FRAGMENTS: dict[str, str] = {
    "module3_condition_a": _MODULE3_CONDITION_A,
    "module3_gate_on_stop_violation": _MODULE3_GATE_ON_STOP_VIOLATION,
    "module3_block_completion": _MODULE3_BLOCK_COMPLETION,
    "module3_block_advancement": _MODULE3_BLOCK_ADVANCEMENT,
}
