# Design Document

## Overview

This feature creates a Quality Scoring Methodology guide (`senzing-bootcamp/docs/guides/QUALITY_SCORING_METHODOLOGY.md`) that explains how Module 4 quality scores are calculated, what thresholds mean, and provides concrete examples. The Module 4 steering file and guides README are updated to reference the new guide.

## Architecture

### File Changes

1. **New file**: `senzing-bootcamp/docs/guides/QUALITY_SCORING_METHODOLOGY.md` — The main methodology guide
2. **Modified file**: `senzing-bootcamp/steering/module-04-data-quality.md` — Add reference to methodology guide and agent instruction
3. **Modified file**: `senzing-bootcamp/docs/guides/README.md` — Add entry for the new guide

### Guide Structure

The methodology guide follows this structure:

```
QUALITY_SCORING_METHODOLOGY.md
├── Introduction (what this guide covers)
├── Scoring Formula
│   ├── Overall formula with weights
│   └── Worked calculation example
├── Scoring Dimensions
│   ├── Completeness (40% weight) — what it measures, how computed
│   ├── Consistency (30% weight) — what it measures, how computed
│   ├── Format Compliance (20% weight) — what it measures, how computed
│   └── Uniqueness (10% weight) — what it measures, how computed
├── Threshold Bands and Actions
│   ├── Summary table
│   ├── ≥80%: Proceed
│   ├── 70-79%: Warn / user decides
│   └── <70%: Recommend fixing
├── Examples
│   ├── High Quality (score ≥80%)
│   ├── Medium Quality (score 70-79%)
│   └── Low Quality (score <70%)
└── Related Documentation (links to Module 4 docs and steering)
```

### Steering File Update

Add a new section near the top of the Module 4 steering file (after the user reference line) that:
- References the methodology guide path
- Instructs the agent to direct users to the guide when they ask about score calculations or meanings

### Guides README Update

Add an entry in the "Reference Documentation" section of the guides README linking to the new guide with a brief description.

## Correctness Properties

All acceptance criteria for this feature are documentation-content checks (verifying specific text, sections, and links exist in markdown files). These are best verified as example-based checks rather than property-based tests.

### Verification Approach

1. **Formula correctness**: The worked example in the guide uses the formula `Quality_Score = (Completeness × 0.40) + (Consistency × 0.30) + (Format_Compliance × 0.20) + (Uniqueness × 0.10)` and the arithmetic is verifiable by inspection.
2. **Threshold consistency**: The guide's threshold bands (≥80%, 70-79%, <70%) align with the steering file's decision gate thresholds (updated from the previous 70%/50-69%/<50% to the new ≥80%/70-79%/<70% bands per the requirements).
3. **Example score ranges**: Each example's computed score falls within its stated threshold band.
4. **Cross-references**: The steering file contains the guide path, the guide links back to Module 4 docs, and the README lists the guide.
