# Requirements: Consolidate Redundant agentStop Hooks

## Introduction

After every agent turn, two separate agentStop hooks fire visibly in the UI: "Ask Bootcamper" and "Feedback Submission Reminder." The Feedback Submission Reminder almost never produces output (it only acts after track completion), yet it still appears as a visible hook invocation every time. This creates visual noise and confusion for the bootcamper, who sees two hook invocations firing after every question.

## What Happened

Both hooks appear in the UI every time the agent stops, even though the Feedback Submission Reminder almost always produces no output. The bootcamper sees two hook invocations firing after every question, which feels redundant and clutters the interaction.

## Why It's a Problem

It creates visual noise and confusion. The bootcamper raises the question: why are both needed if one almost never does anything? Two visible hook invocations after every turn make the experience feel over-engineered and distracting.

## Acceptance Criteria

1. After an agent turn completes, the bootcamper SHALL see at most one agentStop hook invocation in the UI (not two separate ones)
2. The consolidated hook SHALL handle both responsibilities: (a) recap/closing question logic from Ask Bootcamper, and (b) the conditional feedback reminder check that only triggers near track completion
3. The feedback reminder logic SHALL only produce visible output when the bootcamper is approaching or has completed a track — it SHALL remain silent in all other cases
4. The existing Ask Bootcamper behavior (recap of work done + contextual closing question when no 👉 question is pending) SHALL be preserved exactly as-is
5. The existing Ask Bootcamper suppression behavior (produce zero output when a 👉 question is pending) SHALL be preserved exactly as-is

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Redundant agentStop hooks (Ask Bootcamper + Feedback Submission Reminder)"
- Module: General (Onboarding) | Priority: High | Category: UX
