---
inclusion: manual
---


# Module 5: Data Quality & Mapping

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`.
>
> **Quality Scoring Methodology:** For a full explanation of how quality scores are calculated, what each dimension measures, and what thresholds mean, see `docs/guides/QUALITY_SCORING_METHODOLOGY.md`. When a user asks how their score was calculated or what their score means, direct them to this guide.
>
> **Multi-language data:** If your data contains non-Latin characters (Chinese, Arabic, Cyrillic, etc.), see `docs/guides/MULTI_LANGUAGE_DATA.md` for guidance on UTF-8 encoding, non-Latin character support, cross-script name matching, and multi-language data quality best practices.

**Before/After:** You have raw data files but don't know if Senzing can use them directly. After this module, each source is scored for quality, categorized, and transformed into Senzing JSON — validated and ready to load.

**Prerequisites:** ✅ Module 4 complete (data sources collected, files in `data/raw/`)

---

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

## Phase Sub-Files

- **Phase 1 — Quality Assessment** (steps 1–7): `module-05-phase1-quality-assessment.md`
- **Phase 2 — Data Mapping** (steps 8–20): `module-05-phase2-data-mapping.md`
- **Phase 3 — Test Load and Validate (Optional)** (steps 21–26): `module-05-phase3-test-load.md`

