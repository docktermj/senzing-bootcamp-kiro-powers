# Requirements: Rename "path" to "track"

## Introduction

Replace the word "path" with "track" (or "learning track") throughout the bootcamp when referring to the four learning options (A–D), to avoid confusion with file system paths.

## What Happened

During onboarding, the bootcamp refers to learning options as "paths." In a programming context, "path" strongly implies a file or directory path, creating momentary confusion for developers.

## Why It's a Problem

Developers reading "Which path sounds right for you?" may briefly think about file system paths. The word "track" is unambiguous and already used in option B ("Fast Track").

## Acceptance Criteria

1. All instances of "path" meaning "learning option" in `onboarding-flow.md`, `POWER.md`, `agent-instructions.md`, and `session-resume.md` are replaced with "track" or "learning track"
2. File system path references remain unchanged
3. The four learning options (A–D) are consistently called "tracks" across all steering and documentation files
4. No ambiguous uses of "path" remain in user-facing onboarding content

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Rename path to track to avoid confusion with directory paths"
- Module: General | Priority: Medium | Category: UX
