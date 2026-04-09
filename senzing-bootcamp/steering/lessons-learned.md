---
inclusion: manual
---

# Lessons Learned Template

Document insights for future projects and continuous improvement.

## Purpose

After completing the bootcamp, capture what you learned to improve future entity resolution projects. Use the short template for Paths A/B (quick explorations) and the full template for Paths C/D (complete projects).

## Which Template to Use

Read `path` from `config/bootcamp_preferences.yaml`:

- **Path A or B:** → Use the Short Template below
- **Path C or D:** → Use the Full Template below
- **If path is unknown:** → Ask the user which template they prefer

---

## Short Template (Paths A and B)

Create `docs/lessons_learned.md`:

```markdown
# Lessons Learned

**Project:** [Project Name]
**Date:** [Date]
**Path:** [A or B]

## First Impressions

What stood out about Senzing entity resolution?

## What Worked Well

- [Thing that went smoothly and why]

## Challenges

- [Challenge encountered and how it was resolved]

## Key Takeaway

[Single most important thing you learned]

## Would You Change Anything?

[What you'd do differently next time]

## Next Steps

- [ ] [What you plan to do next with Senzing]
```

---

## Full Template (Paths C and D)

Create `docs/lessons_learned.md` and fill it out after Module 8 (Path C) or Module 12 (Path D):

```markdown
# Lessons Learned

**Project:** [Project Name]
**Date Completed:** [Date]
**Team Members:** [Names]

## Executive Summary

[2-3 sentence summary of the project and outcomes]

## What Worked Well

### Data Mapping (Module 5)

- **Success:** [What went smoothly]
- **Why:** [Reasons for success]
- **Recommendation:** [How to replicate]

### Loading Performance (Module 6-7)

- **Success:** [What worked]
- **Metrics:** [Performance numbers]
- **Recommendation:** [Best practices identified]

### Query Results (Module 8)

- **Success:** [Accurate results, good performance, UAT passed]
- **Impact:** [Business value delivered]
- **Recommendation:** [Query patterns that worked well]

## Challenges Encountered

### Challenge 1: [Description]

- **Impact:** [How it affected the project]
- **Root Cause:** [Why it happened]
- **Resolution:** [How we solved it]
- **Prevention:** [How to avoid in future]
- **Time Lost:** [Estimate]

### Challenge 2: [Description]

[Same structure]

## Key Decisions

### Decision 1: [e.g., "Used PostgreSQL instead of SQLite"]

- **Context:** [Why this decision was needed]
- **Options Considered:** [Alternatives]
- **Decision:** [What we chose]
- **Rationale:** [Why we chose it]
- **Outcome:** [How it worked out]

## Metrics and Outcomes

### Data Quality

- **Before:** [Baseline metrics]
- **After:** [Final metrics]
- **Improvement:** [Percentage or absolute]

### Performance

- **Transformation:** [Records/second]
- **Loading:** [Records/second]
- **Query:** [Response time]

### Business Impact

- **Duplicates Found:** [Number]
- **Data Quality Improvement:** [Percentage]
- **Time Saved:** [Hours/week]
- **Cost Savings:** [Dollar amount]
- **ROI:** [Percentage]

## Technical Insights

### Matching Behavior

- [Observation 1]: [What we learned about how Senzing matches]
- [Observation 2]: [Unexpected matching behavior]

### Performance Optimization

- [Optimization 1]: [What we did and impact]
- [Optimization 2]: [What we did and impact]

## Recommendations for Future Projects

### Do More Of

1. [Practice or approach that worked well]
2. [Another successful practice]

### Do Less Of

1. [Practice or approach that didn't work]
2. [Another unsuccessful practice]

### Start Doing

1. [New practice to adopt]

### Stop Doing

1. [Practice to eliminate]

## Timeline Retrospective

- **Estimated:** [Original estimate]
- **Actual:** [Actual time taken]
- **Variance:** [Difference and reasons]

## Action Items for Next Project

1. [ ] [Specific action based on lessons learned]
2. [ ] [Another action item]

## Conclusion

[Final thoughts and overall assessment]
```

---

## When to Use This Template

- After completing any bootcamp path (A, B, C, or D)
- Path A/B → use the Short Template (quick reflection)
- Path C → use the Full Template after Module 8
- Path D → use the Full Template after Module 12
- Before closing out the project
- During project retrospectives

## When to Load This Guide

Load this steering file when:

- Completing the final module of any path (Module 1 for Path A, Module 6 for Path B, Module 8 for Path C, Module 12 for Path D)
- User asks about lessons learned or retrospectives
- Preparing final project documentation
- Planning future entity resolution projects
