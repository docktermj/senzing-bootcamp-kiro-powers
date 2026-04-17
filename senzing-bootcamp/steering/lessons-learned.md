---
inclusion: manual
---

# Lessons Learned

Load at path completion. Generate `docs/lessons_learned.md` based on the user's path.

## Which Template

Read `path` from `config/bootcamp_preferences.yaml`:

- **Path A or B:** Short reflection (5 sections)
- **Path C or D:** Full retrospective (all sections below)
- **Unknown:** Ask the user

## Short Reflection (Paths A/B)

Generate `docs/lessons_learned.md` with these sections:

1. **First Impressions** — what stood out about entity resolution
2. **What Worked Well** — things that went smoothly
3. **Challenges** — issues encountered and how resolved
4. **Key Takeaway** — single most important thing learned
5. **Next Steps** — what they plan to do next with Senzing

## Full Retrospective (Paths C/D)

Generate `docs/lessons_learned.md` with all Short sections plus:

- **Data Quality Insights** — before/after quality scores, what improved
- **Matching Behavior** — observations about how Senzing matched, any surprises
- **Performance** — transformation/loading/query throughput numbers
- **Key Decisions** — choices made (database, language, architecture) and outcomes
- **Challenges with Root Causes** — for each challenge: impact, root cause, resolution, prevention
- **Business Impact** — duplicates found, quality improvement, time/cost savings
- **Recommendations** — do more of / do less of / start doing / stop doing
- **Action Items** — specific next steps for the project

## Agent Behavior

1. Ask the user each section's question one at a time
2. Fill in their responses
3. Save to `docs/lessons_learned.md`
4. Don't pre-fill with generic content — use the user's actual experience
5. Reference the bootcamp journal (`docs/bootcamp_journal.md`) for factual details
