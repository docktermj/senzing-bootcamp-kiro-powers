# Audit Finding: Runtime interpretation of `inclusion: auto`

_Feature: steering-inclusion-auto-audit — satisfies Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 6.4_

## Finding (Audit_Finding data model)

```yaml
runtime_behavior:   loads-manual-only          # Req 1.1 — one of {loads-always, loads-on-file-match, loads-manual-only, ignored}
evidence_source:    runtime-test               # Req 1.1 — documentation was consulted first (see below) but does not define `auto`
citation:           n/a                         # not applicable: the value was established by runtime test, not documentation
probe_observations:                             # Req 1.3
  condition_a_idle:         absent
  condition_b_file_match:   absent
  condition_c_explicit_ref: present
  mapping_conclusion:       loads-manual-only    # per design mapping table: absent in (a)+(b), present in (c)
verified_on:        2026-07-08                  # Req 1.4 (calendar date)
kiro_version:       "IDE host build 1.127.0 (commit 4fe60c8b1cdac1c4c174f2fb180d0d758272d713, x64) on Linux 6.17.0-29-generic (Ubuntu 24.04); no discrete Kiro release string was exposed by the environment, so an environment description is recorded in its place per Req 1.4"
baseline_if_always: n/a                          # Req 1.5 applies only WHERE runtime_behavior == loads-always; see "Baseline consequence" below
```

## Summary

The Kiro runtime does **not** treat `inclusion: auto` as `always`. An `auto`-declared
steering file is **not** injected into a session at start; instead the runtime recognizes
it and surfaces it as an on-demand ("auto inclusion") steering file that is loaded into
context only when it is explicitly activated / referenced. Mapped onto the four-value
`Runtime_Behavior` enum required by Req 1.1, this is **`loads-manual-only`**.

This means the eleven `Auto_File`s are **not** always-loaded, so the project's current
budget accounting (which sums only `inclusion: always` files for the `Baseline_Footprint`)
is **not** silently invalidated by `auto`. It also means files the workflow expects to be
reliably present are only guaranteed present on explicit reference — the concern that
motivates the Decision_Record in Requirement 2.

## Evidence source resolution (Req 1.2 → Req 1.3)

**Documentation consulted first (Req 1.2).** Authoritative Kiro steering documentation
("Steering", https://kiro.dev/docs/steering/, and the "Slash commands" page,
https://kiro.dev/docs/chat/slash-commands/) defines exactly three inclusion modes —
`always` (the default, loaded into every session), `fileMatch` (loaded when an edited file
matches `fileMatchPattern`), and `manual` (loaded only on explicit reference / as a slash
command). The documentation does **not** define a fourth `auto` value nor state how an
unrecognized inclusion value is handled. Because the documentation does not define the
handling of `auto`, the finding falls to the runtime test path (Req 1.3) rather than a
documentation citation.
_(Content was rephrased for compliance with licensing restrictions.)_

**Runtime test performed (Req 1.3).** A single throwaway probe steering file was authored
at `.kiro/steering/zzz-audit-probe-auto.md` (repo-root workspace steering directory —
deliberately **not** under `senzing-bootcamp/`), declaring `inclusion: auto`, a plausible
`fileMatchPattern: "**/*.audit-probe-target"`, and a unique sentinel string
`QZX7-AUTO-PROBE-SENTINEL-9F42K` in its body. Sentinel presence was then observed across the
three defined session conditions. The probe file was deleted after observation and is not
committed anywhere (verified: repo-wide search for the sentinel / probe name returns no
matches).

### Calibration (baseline for the observation)

The repo-root workspace steering directory `.kiro/steering/` contains eight files with known
modes: four `always` (`product.md`, `structure.md`, `tech.md`, `security.md`), one
`fileMatch` (`python-conventions.md`, `**/*.py`), and three `manual` (`add-new-module.md`,
`add-new-script.md`, `validation-suite.md`). In an idle session (no matching-file edit, no
explicit reference) exactly the four `always` files were injected and the `fileMatch` /
`manual` files were not — confirming the runtime honors the three documented modes as
expected, so the probe observation is trustworthy.

### Probe observations

| Condition | Setup | Sentinel | Interpretation |
|---|---|---|---|
| (a) idle | Fresh session, no matching-file edit, no explicit reference | **absent** | Not always-loaded |
| (b) file-match | No auto-injection occurred without explicit activation; the file was offered only as an on-demand activatable item, not auto-loaded | **absent** | Not file-match-triggered auto-load |
| (c) explicit reference | The `auto` file was explicitly activated / referenced | **present** | Loads on explicit reference |

Two independent observations established condition (a): (1) this audit session's own injected
context contained only the four `always` files and not the probe; and (2) a freshly spawned
session reported `SENTINEL ABSENT` while separately noting that the probe file was "listed as
available for activation" but not active at session start. In both, the `auto` file appeared
as an available on-demand ("auto inclusion") steering item rather than injected context.
Condition (c) was confirmed by explicitly activating the probe, which then loaded the sentinel
body into context.

**Mapping (per the design decision table):** absent in (a) and (b), present in (c) →
**`loads-manual-only`**.

## Verification metadata (Req 1.4)

- **Verified on:** 2026-07-08
- **Environment (in place of a discrete Kiro version identifier):** IDE host build `1.127.0`,
  commit `4fe60c8b1cdac1c4c174f2fb180d0d758272d713`, architecture `x64`, on
  `Linux 6.17.0-29-generic` (Ubuntu 24.04). No standalone "Kiro" release version string was
  exposed by the environment; this environment description is recorded in its place as
  permitted by Req 1.4.

## Baseline consequence (Req 1.5)

Req 1.5 requires a `loads-always` baseline total **only where** the verified
`Runtime_Behavior` is `loads-always`. The verified behavior is `loads-manual-only`, so
`baseline_if_always` is **not applicable**: the eleven `Auto_File`s are not counted in the
`Baseline_Footprint`, and the existing always-loaded baseline (the three `senzing-bootcamp/`
`inclusion: always` files — `agent-instructions.md`, `module-transitions.md`,
`security-privacy.md`, ≈6,668 measured tokens) remains correct.

_Informational only (not the governing value):_ had the behavior been `loads-always`, the
baseline with the eleven `Auto_File`s counted as always-loaded would have been ≈24,830 tokens
(≈6,668 + ≈18,162), still under the 30,000-token ceiling. This is recorded solely for context
and is not used because the finding is `loads-manual-only`.

## Downstream implication (feeds Task 2 / Req 2, Req 6.3)

Under the design's audit contingency rule, because `Runtime_Behavior != loads-always`, no
`Auto_File` was unconditionally present in every session before the change; Req 6.3 therefore
imposes no "must stay always" constraint arising from these files. The provisional
3×`always` / 1×`fileMatch` / 7×`manual` split in the Decision_Record stands, and it aligns
with what the current budget accounting already assumes.

## Scope compliance (Req 6.4)

All actions were confined to files within the repository. The runtime probe file lived at
`.kiro/steering/zzz-audit-probe-auto.md` (outside `senzing-bootcamp/`), was deleted after
observation, and is not committed. No resource outside the repository was modified.

## The eleven Auto_Files (current state, confirmed)

`agent-behavior-rules.md`, `agent-context-management.md`, `conversation-protocol.md`,
`design-patterns.md`, `file-placement.md`, `mcp-response-caching.md`,
`module-prerequisites.md`, `project-structure.md` (no `description`), `qa-transcript.md`,
`session-resume.md`, `verbosity-control.md` — all currently declare `inclusion: auto` in
`senzing-bootcamp/steering/`.
