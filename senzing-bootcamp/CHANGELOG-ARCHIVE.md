# Changelog Archive

Older releases of the Senzing Bootcamp power. For recent changes, see [CHANGELOG.md](CHANGELOG.md).

## [0.8.0] - 2026-04-17

Added setup preamble, `👉` input-required markers across all modules, Goldilocks detail check every 3 modules, welcome-back banner in session resume, SQLite ≤1,000 record recommendation, and explicit Module 3 closure before Module 1 transition. Module 1 Steps 1-3 received explicit WAIT markers.

## [0.7.0] - 2026-04-17

Added one-question-at-a-time rule, license discovery in Module 2, interactive visualization features, zero-matches handling in Module 8, first-term explanation rule, guided troubleshooting diagnostics, validate_power.py script, system architecture diagram, iterate-vs-proceed decision gates, and next-step options in module completion. Trimmed onboarding-flow.md, COLLABORATION_GUIDE.md, and ONBOARDING_CHECKLIST.md significantly.

## [0.6.0] - 2026-04-16

Added glossary reference in onboarding, iterate-vs-proceed decision gates, system architecture diagram, next-step options after every module, guided troubleshooting in common-pitfalls.md, stakeholder summary templates, data visualization triggers, and validate_power.py script. Restructured Module 11 into Phase 1 (Packaging) and Phase 2 (Deployment). Made language selection MCP-driven and rewrote onboarding-flow.md from 333 to 85 lines.

## [0.5.0] - 2026-04-14

Added MCP offline guidance, mapping state checkpointing, summarize-on-stop and verify-generated-code hooks, module-completion.md steering file, and use-case bridging questions in Module 3. Major rewrites to reduce context usage: agent-instructions.md (98→54 lines), security-privacy.md (80→27), project-structure.md (130→44), module-transitions.md split into lean auto (27 lines) + manual module-completion.md (49 lines).

## [0.4.0] - 2026-04-09

Streamlined onboarding to two user-visible questions (language and path). Added session-resume.md, enforce-working-directory hook, PowerShell equivalents for all bash commands, and AWS CDK guidance. Condensed common-pitfalls.md (514→150 lines), module-prerequisites.md (401→54 lines), and complexity-estimator.md (352→53 lines). Removed `#[[file:]]` references from always-loaded agent-instructions.md.

## [0.3.0] - 2026-04-08

Split agent-instructions.md into always-loaded core + manual onboarding-flow.md. Trimmed Modules 8-11 from 1,100-1,500 lines each to 78-119 lines. Added 5 language-specific steering files (Python, Java, C#, Rust, TypeScript), cloud-provider-setup.md, and foundational steering file generation during onboarding. Removed templates/ directory (replaced by MCP dynamic generation).

## [0.2.0] - 2026-04-06

Standardized "boot camp" → "bootcamp" across all 55+ files. Removed time estimates from module listings (complexity estimator provides personalized estimates). Added MCP failure recovery, language switching, progress corruption recovery, and AWS/cloud provider guidance across steering files, docs, scripts, and examples.
