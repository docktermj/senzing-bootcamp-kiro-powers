---
inclusion: manual
---

# Module 8: Performance Testing

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_8_PERFORMANCE_TESTING.md` for background.

**Prerequisites:** Module 7 (Query and Visualize) complete, representative data loaded, cloud provider set at 7→8 gate.

**Before/After:** Entity resolution works but you don't know how it performs at scale. After this module, you'll have benchmarks, bottleneck analysis, and optimizations — confidence that it'll handle production volumes.

## Deferred Deployment Question (conditional)

**Read** `config/bootcamp_preferences.yaml` and check both the `track` value and whether `deployment_target` is present.

**IF `track` is `advanced_topics` AND `deployment_target` is NOT present in the file:**

This bootcamper upgraded to the advanced track (or started it) but was never asked the deployment question. Ask it now before proceeding with the module.

Ask the bootcamper:

"Before we dive into performance testing, I need to know where you plan to deploy the final entity resolution solution. Here are some common options:

**Cloud hyperscalers:**
- AWS
- Azure
- GCP

**Container platforms:**
- Kubernetes
- Docker Swarm

**Local / on-premises:**
- Current machine
- Other internal infrastructure

Or if you're **not sure yet**, that's perfectly fine too."

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue with the module. Wait for the bootcamper's real input.

Reassure the bootcamper: "No matter what you choose, we'll develop everything locally first. Deployment-specific code and configuration will be created later in Module 11 — so there's no pressure to commit right now."

Once the bootcamper responds, persist their choice to `config/bootcamp_preferences.yaml` as `deployment_target`:

- **Cloud hyperscaler selected** (AWS, Azure, or GCP): persist `deployment_target` with the value (`aws`, `azure`, or `gcp`). Also persist `cloud_provider` in `config/bootcamp_preferences.yaml` using the same value format — `aws` for AWS, `azure` for Azure, `gcp` for GCP.
- **Container platform selected** (Kubernetes or Docker Swarm): persist `deployment_target` as `kubernetes` or `docker_swarm`.
- **Local / on-premises selected**: persist `deployment_target` as `local` or `on_premises`.
- **"Not sure yet" selected**: persist `deployment_target: undecided` in `config/bootcamp_preferences.yaml` and reassure the bootcamper that the choice can be revisited later in Module 11.

After persisting the deployment target, **update `docs/business_problem.md`**: find the "Deployment Target" section and replace its content (which currently reads "Not applicable — current track does not include Module 11 (Deployment).") with the chosen platform. Use this format:

- **Platform:** [selected option, e.g., AWS, Kubernetes, Local machine]
- **Category:** [Cloud hyperscaler / Container platform / Local/on-premises / Undecided]
- **Note:** Deployment-specific configuration will be created in Module 11.

Then proceed with the module normally.

**IF the conditions are NOT met** (track is not `advanced_topics`, OR `deployment_target` already exists):

Skip this section — proceed with the module normally.

---

Use the bootcamper's chosen language. Read `cloud_provider` and `deployment_target` from `config/bootcamp_preferences.yaml`. When `deployment_target` is set but `cloud_provider` is not, use the deployment target to inform performance guidance.

## Phases

This module is split into three phases. Load the phase file matching the bootcamper's current step:

| Phase | Steps | File | Focus |
|-------|-------|------|-------|
| A | 1–3 | `module-08-phaseA-requirements.md` | Requirements, anti-patterns, environment baseline |
| B | 4–7 | `module-08-phaseB-benchmarking.md` | Transformation, loading, query, and resource benchmarks |
| C | 8–13 | `module-08-phaseC-optimization.md` | Database tuning, scalability, optimization, final report |

Load Phase A to begin.

**Success indicator**: ✅ Baselines captured (transformation, loading, query) + bottlenecks documented + optimizations applied + performance report complete

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

**Success:** Performance baselines captured, bottlenecks identified, optimizations documented, report complete.
