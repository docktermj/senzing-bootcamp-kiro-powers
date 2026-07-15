# Requirements Document: Entity Resolution Intro Interactive Illustration

## Introduction

The preface entity-resolution introduction (`entity-resolution-intro.md`) is
strong but **text-only**: it explains what entity resolution is, why matching is
hard, the pipeline, relationships, and outputs, all sourced from the Senzing MCP
server. The first time the concept becomes *concrete* is the Module 3 "wow"
visualization — several modules later.

An experience audit suggested making the concept concrete **up front** by
offering a tiny **two-record match / no-match illustration** during the intro:
a clear "same real-world entity → match" pair and a "looks similar but is a
different entity → no match" pair, each with plain-language reasoning. This
grounds the false-positive/false-negative idea the intro already describes,
before the Module 3 visualization, without requiring the SDK, a database, or any
loaded data.

It complements `entity-resolution-conceptual-intro`,
`entity-resolution-intro-refresh`, and `confidence-and-features-explanation`, and
must not duplicate or pre-empt the Module 3 "wow" visualization
(`module3-wow-visualization`, `module3-entity-graph-relationships`).

## Glossary

- **ER_Illustration**: a tiny, conceptual, text/inline illustration of two record
  pairs — one clear match, one clear non-match (or ambiguous "possible match") —
  with plain-language reasoning.
- **Illustration_Offer**: the 👉 offer to view the ER_Illustration, presented in
  the intro before the mandatory exploration gate.
- **Exploration_Gate**: the existing ⛔ MANDATORY GATE at the end of
  `entity-resolution-intro.md` where the agent waits for the bootcamper to
  explore or signal readiness.

## Requirements

### Requirement 1: Offer a concrete two-record illustration in the intro

**User Story:** As a new bootcamper, I want a tiny concrete example of a match
and a non-match, so entity resolution clicks before the Module 3 visualization.

#### Acceptance Criteria

1. WHEN the entity-resolution introduction is presented, THE agent SHALL offer
   the ER_Illustration as an explicit, optional 👉 Illustration_Offer.
2. WHEN the bootcamper accepts, THE agent SHALL present at least two record
   pairs: (a) a clear **match** (same real-world entity despite surface
   differences) and (b) a clear **non-match** or **possible-match** (similar
   surface attributes, different entities), each with one or two lines of
   plain-language reasoning tied to the intro's concepts (name variation,
   address-over-time, false positive vs. false negative).
3. THE ER_Illustration SHALL be conceptual and self-contained — it SHALL NOT
   require the Senzing SDK, a database, loaded data, or any code execution.
4. WHERE Senzing MCP examples are available (`find_examples` / `search_docs`),
   THE illustration content SHALL be sourced from them rather than from training
   data, consistent with the intro's MCP-first sourcing; WHERE MCP examples are
   unavailable, THE agent SHALL fall back to a generic, clearly-generic pair.

### Requirement 2: Optional, never blocking, gate-safe

**User Story:** As a bootcamper who already gets it, I want to skip the example.

#### Acceptance Criteria

1. THE Illustration_Offer SHALL be optional — declining proceeds without penalty.
2. THE Illustration_Offer and the ER_Illustration SHALL NOT alter the
   Exploration_Gate semantics: the mandatory gate still waits for a real
   readiness signal or follow-up question, and the ER_Concepts_Banner is still
   shown exactly once.
3. THE offer SHALL obey the One Question Rule (exactly one 👉, non-compound) and
   the bootcamper's verbosity settings.
4. WHERE the bootcamper asks a follow-up after the illustration, THE agent SHALL
   answer it via MCP and re-present the Exploration_Gate, per the existing intro
   flow.

### Requirement 3: Do not duplicate the Module 3 visualization

#### Acceptance Criteria

1. THE ER_Illustration SHALL be a lightweight conceptual teaser — it SHALL NOT
   render the interactive entity graph, start a web service, or otherwise
   reproduce the Module 3 "wow" visualization.
2. THE intro SHALL frame the illustration as a preview and point forward to the
   Module 3 hands-on visualization on the bootcamper's own data/TruthSet.

## Non-Goals

- Running the SDK, loading data, or standing up a server during the preface.
- Replacing or moving the Module 3 visualization.
- Turning the illustration into a required step or a gate.
