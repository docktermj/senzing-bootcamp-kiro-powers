# Tasks: Feedback Loop Closure

## Task 1: Create whats-new.md steering file

- [x] 1.1 Create `senzing-bootcamp/steering/whats-new.md` with YAML frontmatter (`inclusion: manual`)
- [x] 1.2 Document the three conditions for showing the notification (session log exists, new CHANGELOG entries, not suppressed)
- [x] 1.3 Document the generation steps: read last session date, parse CHANGELOG, filter by date, score by relevance, select top 3
- [x] 1.4 Document the relevance scoring criteria (current module +3, language +2, bug fix +1, feature +1)
- [x] 1.5 Document the notification format template (📢 header, max 3 bullets, attribution note)
- [x] 1.6 Document suppression behavior: "don't show updates" sets preference, "show updates" re-enables

## Task 2: Update session-resume.md with What's New step

- [x] 2.1 Read the current `senzing-bootcamp/steering/session-resume.md` to identify insertion point (after welcome-back, before "Ready to continue?")
- [x] 2.2 Add "Step 2e: What's New Notification" section
- [x] 2.3 Document the condition check: session log exists AND new CHANGELOG entries AND not suppressed
- [x] 2.4 Document the skip behavior: if conditions not met, proceed silently (no "nothing new" message)
- [x] 2.5 Ensure the notification is shown before the 👉 "Ready to continue?" question

## Task 3: Update steering-index.yaml

- [x] 3.1 Add keyword entries: "what's new" → whats-new.md, "changelog" → whats-new.md, "updates" → whats-new.md
- [x] 3.2 Add `file_metadata` entry for `whats-new.md` with token count and size category
- [x] 3.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py` to compute accurate token count

## Task 4: Write tests

- [x] 4.1 Create `senzing-bootcamp/tests/test_feedback_loop_closure.py`
- [x] 4.2 Unit test: `whats-new.md` exists and has `inclusion: manual` frontmatter
- [x] 4.3 Unit test: `whats-new.md` documents all three conditions for showing notification
- [x] 4.4 Unit test: `whats-new.md` documents relevance scoring with four criteria
- [x] 4.5 Unit test: `session-resume.md` contains "What's New" step reference
- [x] 4.6 Unit test: `steering-index.yaml` has keyword entries for "what's new", "changelog", "updates"
- [x] 4.7 Property test: relevance scoring always produces 0 to 3 results (never more than 3)
- [x] 4.8 Property test: filtering by date always returns a subset of all CHANGELOG entries
- [x] 4.9 Unit test: notification format includes attribution note text
- [x] 4.10 Unit test: suppression preference key documented as `show_whats_new`

## Task 5: Validate

- [x] 5.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on new/modified files
- [x] 5.2 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
- [x] 5.3 Run `pytest senzing-bootcamp/tests/test_feedback_loop_closure.py -v`
