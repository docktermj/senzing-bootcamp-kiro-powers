# Requirements: On-Premises Hardware Clarification in Performance Modules

## Introduction

When the bootcamper selected "on_premises" as their deployment target in Module 1, the agent in Module 8 (Performance Testing) captured the current dev machine's hardware specs and used them for benchmarking without asking whether the production system is the same machine or a different on-premises server. This produces misleading recommendations if the actual production hardware differs.

## What Happened

In Module 8, the agent captured the current machine's hardware specs and used them for benchmarking without asking whether the production system is the same machine or a different on-premises server with different CPU, RAM, storage, and database specs.

## Why It's a Problem

The bootcamper may intend to deploy to a completely different on-premises server. Benchmarking on the current dev machine and making recommendations based on its hardware is misleading if production runs on different hardware. The performance targets and optimization recommendations need to be relevant to the actual production system.

## Acceptance Criteria

1. WHEN `deployment_target` is "on_premises" AND the module involves hardware-dependent recommendations (Modules 8, 9, 11), the agent SHALL ask: "Will you deploy to this machine, or a different on-premises server? If different, what are the specs (CPU cores, RAM, storage type, database server)?"
2. The hardware clarification question SHALL be asked before any benchmarking or hardware-dependent recommendations are generated
3. IF the bootcamper indicates they will deploy to the current machine, THEN the agent SHALL proceed with the current machine's specs as the benchmark target
4. IF the bootcamper provides different production hardware specs, THEN the agent SHALL use those specs for performance recommendations and clearly note that benchmarks were run on the dev machine but recommendations target the production hardware
5. The hardware clarification question SHALL be stored in the bootcamper's preferences or checkpoint so it is not re-asked in subsequent modules (Modules 9, 11)
6. WHEN `deployment_target` is NOT "on_premises" (e.g., AWS, Azure, GCP), this question SHALL NOT be asked — cloud deployments have their own sizing workflows

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "On-premises deployment target needs hardware clarification in Module 8"
- Module: 8 (Performance Testing) | Priority: Medium | Category: Workflow
