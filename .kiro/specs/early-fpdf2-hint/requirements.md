# Requirements Document: Early fpdf2 Hint

## Introduction

The graduation recap PDF (`docs/bootcamp_recap.pdf`) is always produced via a
tiered strategy, so a valid PDF exists whether or not `fpdf2` is installed. When
`fpdf2` is present the bootcamper gets the **professionally-designed** PDF; when
it is absent they get a plainer, stdlib-rendered PDF. The `fpdf2` availability
hint currently surfaces **late** — at track completion / graduation
(`fpdf2_preflight.py` at graduation Step 0b.0 and in `module-completion-track.md`).

By then it is often too late to matter: the bootcamper is finishing and unlikely
to stop and `pip install fpdf2`. An experience audit suggested surfacing the
one-line `pip install fpdf2` hint **early — during Module 1** — so there is
ample time to install it before graduation, raising the odds graduates receive
the rich PDF.

`fpdf2` remains an **optional, lazily-imported** dependency (per the tech
conventions). This feature only adds an earlier, non-blocking, one-time hint. It
complements `fpdf2-preflight-note`, `guaranteed-recap-pdf`,
`recap-pdf-professional-design`, and `professional-recap-pdf`.

## Glossary

- **Fpdf2_Preflight**: the existing helper `scripts/fpdf2_preflight.py` that
  reports whether `fpdf2` is available and prints a one-line hint when it is not.
- **Early_Hint**: a one-line, non-blocking `pip install fpdf2` hint surfaced
  during Module 1 when `fpdf2` is absent.
- **Hint_Shown_Flag**: persisted state recording that the Early_Hint was already
  surfaced, so it is not repeated.

## Requirements

### Requirement 1: Surface the hint early (Module 1) when fpdf2 is absent

**User Story:** As a bootcamper, I want to learn early that installing `fpdf2`
upgrades my final recap PDF, so I have time to install it before graduating.

#### Acceptance Criteria

1. WHEN Module 1 reaches a natural, non-interrupting point (e.g., module
   completion), THE agent SHALL run Fpdf2_Preflight.
2. WHEN `fpdf2` is absent, THE agent SHALL surface the one-line hint that
   installing it (`pip install fpdf2`) upgrades the end-of-bootcamp recap PDF to
   the professionally-designed version.
3. WHEN `fpdf2` is present, THE agent SHALL surface nothing (silent).
4. THE hint SHALL state that a valid recap PDF is produced either way — `fpdf2`
   only upgrades its design — so it never reads as a requirement.

### Requirement 2: Non-blocking, optional, one-time

**User Story:** As a bootcamper, I never want a tooling hint to interrupt or nag.

#### Acceptance Criteria

1. THE Early_Hint SHALL be non-blocking and orientation-only — it SHALL NOT ask a
   question, gate progress, or require installation.
2. THE Early_Hint SHALL be surfaced at most once: after showing it, THE agent
   SHALL record a Hint_Shown_Flag (in `config/bootcamp_preferences.yaml`) and
   SHALL NOT repeat the hint in later modules.
3. WHERE `fpdf2` is installed later, THE existing late preflight
   (`fpdf2_preflight.py` at track completion / graduation) SHALL continue to work
   unchanged; this feature only adds the earlier surface.
4. WHERE Fpdf2_Preflight cannot run, THE agent SHALL proceed silently
   (non-blocking) and MAY surface the hint at the next natural opportunity.

### Requirement 3: Keep fpdf2 optional and lazily imported

#### Acceptance Criteria

1. THE feature SHALL NOT make `fpdf2` a hard dependency and SHALL NOT import it
   at module top level anywhere (consistent with the tech conventions:
   `fpdf2` is imported lazily only inside the PDF render path).
2. THE Early_Hint SHALL NOT attempt to auto-install `fpdf2` during Module 1; it
   only informs. (Best-effort auto-install remains solely in the graduation-time
   tiered render path, unchanged.)

## Non-Goals

- Auto-installing `fpdf2` during Module 1.
- Making `fpdf2` required or changing the tiered guaranteed-PDF behavior.
- Removing or altering the existing late (graduation-time) preflight.
