# Requirements Document

## Introduction

The stated bootcamp outcome is that the trophy document `docs/bootcamp_recap.pdf` is **always** created at graduation. In practice it is not guaranteed as a PDF: the recap renderer lazy-imports the optional `fpdf2` dependency, and when `fpdf2` is absent, `ensure_graduation_artifacts.py` falls back to producing `docs/bootcamp_recap.html` (plus the Markdown) and prints a `pip install fpdf2` hint. So a bootcamper without `fpdf2` graduates with an HTML file, not a PDF.

This feature guarantees that a real, valid PDF at `docs/bootcamp_recap.pdf` is always produced at every graduation/stopping point, even when `fpdf2` is not already installed — including by installing `fpdf2` when possible, and by falling back to a stdlib-only PDF writer when installation is not possible. The repository constraint that `fpdf2` remains an *optional, lazily imported* dependency (never a hard/top-level import) is preserved.

## Glossary

- **Recap_PDF**: The file `docs/bootcamp_recap.pdf` — a valid PDF document rendered from the reconciled recap Markdown (`docs/bootcamp_recap.md`).
- **Rich_Renderer**: The existing `fpdf2`-based renderer (`generate_recap_pdf.py` / `recap_pdf_render.py`) that produces the professionally designed PDF.
- **Fpdf2_Autoinstall**: A best-effort, guarded attempt to install `fpdf2` at render time when it is absent.
- **Stdlib_PDF_Writer**: A new stdlib-only module that emits a valid (if visually plain) PDF from the parsed recap when `fpdf2` cannot be used, so a PDF is produced with zero third-party dependencies.
- **HTML_Fallback**: The current `docs/bootcamp_recap.html` output produced when no PDF can be made.
- **Artifact_Orchestrator**: `scripts/ensure_graduation_artifacts.py`, the Stop-hook-invoked guarantee that regenerates missing/empty/stale recap artifacts.
- **Offline_Environment**: An environment where package installation cannot succeed (no network, restricted pip, or install disabled by preference).

## Requirements

### Requirement 1: A Real PDF Is Always Produced

**User Story:** As a graduating bootcamper, I want my trophy recap to always be a real PDF file, so that I have a consistent, shareable, professional artifact regardless of my environment.

#### Acceptance Criteria

1. WHEN a graduation / track-completion stopping point is reached, THE Artifact_Orchestrator SHALL produce a valid Recap_PDF at `docs/bootcamp_recap.pdf`.
2. THE Recap_PDF SHALL be a structurally valid PDF (parseable header/trailer, extractable text) reflecting the reconciled recap content.
3. THE guarantee SHALL hold whether or not `fpdf2` is installed at the time of rendering.
4. THE guarantee SHALL hold in an Offline_Environment (no network, no installable `fpdf2`).
5. THE `--check` mode of the Artifact_Orchestrator SHALL verify the presence of `docs/bootcamp_recap.pdf` specifically (not merely an HTML fallback) as the satisfied rendered-recap artifact.

### Requirement 2: Tiered Rendering Strategy

**User Story:** As a bootcamper, I want the best-looking PDF my environment allows, so that graduation feels professional when possible and still guaranteed when not.

#### Acceptance Criteria

1. WHEN `fpdf2` is available, THE renderer SHALL use the Rich_Renderer to produce the professionally designed Recap_PDF (unchanged behavior).
2. WHEN `fpdf2` is not available, THE renderer SHALL attempt Fpdf2_Autoinstall (subject to Requirement 3) and, on success, use the Rich_Renderer.
3. WHEN `fpdf2` is unavailable and Fpdf2_Autoinstall does not succeed, THE renderer SHALL use the Stdlib_PDF_Writer to produce a valid Recap_PDF from the same parsed recap content.
4. THE tier actually used SHALL be reported (logged/printed) so the maintainer can see which path produced the PDF.
5. THE HTML_Fallback MAY still be produced as a supplementary artifact, but SHALL NOT be the substitute for the Recap_PDF — the PDF is always produced.

### Requirement 3: Guarded, Best-Effort Autoinstall

**User Story:** As a bootcamper, I want the bootcamp to be able to install the PDF library for me, so that I get the nicer PDF without manual setup — but without surprising or unsafe behavior.

#### Acceptance Criteria

1. THE Fpdf2_Autoinstall SHALL be best-effort: it SHALL have a bounded timeout and SHALL never hang the graduation flow.
2. WHEN Fpdf2_Autoinstall fails for any reason (offline, permissions, pip missing, timeout), THE flow SHALL fall through to the Stdlib_PDF_Writer without error and without blocking graduation.
3. THE Fpdf2_Autoinstall SHALL be controllable via an opt-out (e.g., an environment variable or a `config/bootcamp_preferences.yaml` key) so environments that forbid installs can disable it; when disabled, the flow goes straight to the Stdlib_PDF_Writer.
4. THE Fpdf2_Autoinstall SHALL install into the active Python environment using the standard installer (`python -m pip install fpdf2`), and SHALL NOT modify system state beyond that package.
5. THE Fpdf2_Autoinstall SHALL be attempted at most once per render invocation (no retry loops).

### Requirement 4: Stdlib-Only PDF Fallback

**User Story:** As a bootcamp maintainer, I want a dependency-free way to emit a valid PDF, so that the guarantee never depends on network access or third-party packages.

#### Acceptance Criteria

1. THE Stdlib_PDF_Writer SHALL be implemented using only the Python standard library (no `fpdf2`, no other third-party packages).
2. THE Stdlib_PDF_Writer SHALL emit a structurally valid PDF (e.g., PDF 1.4) containing the recap's module sections and their labeled subsections (Information Shared, Questions & Responses, Actions Taken, Journal).
3. THE Stdlib_PDF_Writer SHALL never be imported at module top level in a way that makes `fpdf2` a hard dependency; it is independent of `fpdf2`.
4. THE Stdlib_PDF_Writer SHALL reuse the existing recap parser/model so no recap content is dropped, consistent with the tolerant raw-Markdown fallback.
5. THE Stdlib_PDF_Writer output SHALL pass the same "valid PDF + extractable text" verification used to confirm the Recap_PDF.

### Requirement 5: Preserve Existing Constraints and Behavior

**User Story:** As a bootcamp maintainer, I want the guarantee to respect existing repository conventions and graduation behavior, so that nothing else regresses.

#### Acceptance Criteria

1. THE `fpdf2` dependency SHALL remain optional and lazily imported (never a top-level import), per the repository Python conventions.
2. THE recap generation SHALL remain non-blocking with respect to the celebration flow: a rendering problem SHALL never crash graduation, and the guarantee is fulfilled by the tiered strategy rather than by raising.
3. THE Artifact_Orchestrator SHALL remain idempotent: regenerating an already-valid Recap_PDF SHALL be a no-op or a byte-stable refresh, and it regenerates only when absent, empty, or stale.
4. THE reconcile-then-render ordering (recap reconciliation before PDF render) defined in `graduation.md` / `module-completion-track.md` SHALL be preserved.
5. THE steering language that currently says the recap "degrades to HTML/Markdown when `fpdf2` is absent" SHALL be updated to state that a PDF is guaranteed via the tiered strategy.

### Requirement 6: Professional Appearance Is Retained Where Possible

**User Story:** As a graduating bootcamper, I want the PDF to look professional, so that it is a credible trophy to share.

#### Acceptance Criteria

1. WHEN the Rich_Renderer is used (fpdf2 present or autoinstalled), THE Recap_PDF SHALL retain the existing professional design (cover page, styled sections) owned by the professional-recap-pdf design.
2. WHEN the Stdlib_PDF_Writer is used, THE Recap_PDF SHALL be clean and readable (title, per-module headings, labeled subsections) even though it is visually simpler than the Rich_Renderer output.
3. THE difference in appearance between tiers SHALL be acceptable given that a guaranteed valid PDF is the priority; the maintainer SHALL be able to tell which tier produced a given PDF (Requirement 2.4).

### Requirement 7: Tests

**User Story:** As a bootcamp maintainer, I want tests that prove the PDF is always produced, so that the guarantee does not regress.

#### Acceptance Criteria

1. THE test suite SHALL include a property-based/behavioral test that, with `fpdf2` simulated as unavailable AND autoinstall disabled, the Stdlib_PDF_Writer still produces a valid Recap_PDF with extractable text.
2. THE test suite SHALL assert that the Artifact_Orchestrator `--check` reports satisfied only when `docs/bootcamp_recap.pdf` exists.
3. THE test suite SHALL assert the Rich_Renderer path is unchanged when `fpdf2` is present.
4. THE test suite SHALL assert the tiered selection logic: present → rich; absent+install-off → stdlib; absent+install-on+install-fails → stdlib.
5. WHEN the full suite runs, THE suite SHALL pass.
