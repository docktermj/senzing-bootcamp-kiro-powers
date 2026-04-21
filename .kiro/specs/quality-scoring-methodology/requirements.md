# Requirements Document

## Introduction

Module 4 (Data Quality) calculates quality scores but does not explain how those scores are derived or what the thresholds mean. Users see a score like 72% with no understanding of why. This feature adds a Quality Scoring Methodology guide that explains the scoring formula, defines actionable thresholds, and provides concrete examples of low, medium, and high quality data with sample scores. The Module 4 steering file is updated to reference the new guide.

## Glossary

- **Quality_Score**: A numeric value from 0 to 100 representing overall data quality, computed as a weighted combination of Completeness, Consistency, Format_Compliance, and Uniqueness scores.
- **Completeness_Score**: A metric measuring the percentage of non-null, non-empty values across critical fields in a data source.
- **Consistency_Score**: A metric measuring how uniformly data values conform to a single format pattern within each field type.
- **Format_Compliance_Score**: A metric measuring the percentage of field values that pass validation rules for their data type (email patterns, phone formats, date ranges, postal codes).
- **Uniqueness_Score**: A metric measuring the proportion of non-duplicate records in a data source.
- **Methodology_Guide**: The user-facing document at `docs/guides/QUALITY_SCORING_METHODOLOGY.md` that explains scoring calculations, thresholds, and examples.
- **Steering_File**: The agent workflow file at `steering/module-04-data-quality.md` that guides agent behavior during Module 4.
- **Threshold**: A Quality_Score boundary that determines the recommended action: proceed, warn, or fix.

## Requirements

### Requirement 1: Scoring Formula Documentation

**User Story:** As a bootcamp user, I want to understand how my quality score is calculated, so that I can identify which dimensions are dragging my score down.

#### Acceptance Criteria

1. THE Methodology_Guide SHALL document the weighted scoring formula: Quality_Score = (Completeness_Score × 0.40) + (Consistency_Score × 0.30) + (Format_Compliance_Score × 0.20) + (Uniqueness_Score × 0.10).
2. THE Methodology_Guide SHALL explain each of the four scoring dimensions (Completeness, Consistency, Format_Compliance, Uniqueness) with a description of what the dimension measures and how the sub-score is computed.
3. THE Methodology_Guide SHALL include a worked example showing a sample data source with specific sub-scores and the resulting overall Quality_Score calculation.

### Requirement 2: Threshold Definitions and Actions

**User Story:** As a bootcamp user, I want to know what my quality score means in practical terms, so that I can decide whether to proceed with mapping or fix my data first.

#### Acceptance Criteria

1. THE Methodology_Guide SHALL define three threshold bands: scores at or above 80 percent, scores from 70 to 79 percent, and scores below 70 percent.
2. WHEN the Quality_Score is at or above 80 percent, THE Methodology_Guide SHALL recommend proceeding to Module 5 (data mapping).
3. WHEN the Quality_Score is between 70 and 79 percent inclusive, THE Methodology_Guide SHALL warn the user about quality gaps and present the choice to proceed or improve data first.
4. WHEN the Quality_Score is below 70 percent, THE Methodology_Guide SHALL recommend fixing data quality issues before proceeding and list the specific dimensions that need improvement.
5. THE Methodology_Guide SHALL include a visual summary table mapping each threshold band to its recommended action.

### Requirement 3: Quality Examples with Sample Scores

**User Story:** As a bootcamp user, I want to see examples of low, medium, and high quality data with their scores, so that I can compare my data against concrete benchmarks.

#### Acceptance Criteria

1. THE Methodology_Guide SHALL include a high-quality data example with sub-scores and an overall Quality_Score at or above 80 percent.
2. THE Methodology_Guide SHALL include a medium-quality data example with sub-scores and an overall Quality_Score between 70 and 79 percent inclusive.
3. THE Methodology_Guide SHALL include a low-quality data example with sub-scores and an overall Quality_Score below 70 percent.
4. WHEN presenting each example, THE Methodology_Guide SHALL show sample data rows, per-dimension sub-scores, the overall Quality_Score calculation, and the recommended action based on the threshold.

### Requirement 4: Steering File Cross-Reference

**User Story:** As an agent running Module 4, I want the steering file to reference the methodology guide, so that I can direct users to the explanation when they ask about their scores.

#### Acceptance Criteria

1. THE Steering_File SHALL contain a reference to the Methodology_Guide with its file path (`docs/guides/QUALITY_SCORING_METHODOLOGY.md`).
2. THE Steering_File SHALL instruct the agent to direct users to the Methodology_Guide when users ask how their Quality_Score was calculated or what their score means.

### Requirement 5: Guide Discoverability

**User Story:** As a bootcamp user, I want to find the quality scoring methodology guide from the guides index, so that I can access it without needing to know the exact file path.

#### Acceptance Criteria

1. THE guides README at `docs/guides/README.md` SHALL list the Methodology_Guide with its title and a brief description.
2. THE Methodology_Guide SHALL include a link back to the Module 4 documentation (`docs/modules/MODULE_4_DATA_QUALITY_SCORING.md`) and the Steering_File for related context.
