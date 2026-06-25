---
inclusion: manual
---

# Module 8 Phase A: Requirements & Baselines (Steps 1–3)

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, tailor to RDS/Aurora and EC2 instance types. Also read `deployment_target` from `config/bootcamp_preferences.yaml`. When `deployment_target` is set but `cloud_provider` is not (e.g., container platform or local target), use the deployment target to inform performance target guidance — container platform targets (Kubernetes, Docker Swarm) differ from bare-metal or local targets in resource constraints, networking overhead, and scaling characteristics.

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

## Step 1: Define Performance Requirements

**Before setting targets**, direct the user to review `docs/guides/PERFORMANCE_BASELINES.md` for reference throughput, hardware requirements, and database comparison data at different data volumes. This helps them set realistic targets.

Call `search_docs(query='performance benchmarks', version='current')` for current expectations. Document in `docs/performance_requirements.md`.

Ask ONE AT A TIME:

### Step 1a: Loading Throughput Target

"What loading throughput do you need? (records per second)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1a to `config/bootcamp_progress.json`.

### Step 1b: Query Latency Target

"What query latency target do you need? (milliseconds per query)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1b to `config/bootcamp_progress.json`.

### Step 1c: Concurrent Users

"How many concurrent users or processes will query the system?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1c to `config/bootcamp_progress.json`.

### Step 1d: Data Volume and Growth

"What's your expected data volume and growth rate?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1d to `config/bootcamp_progress.json`.

### Step 1e: Database Choice

"Would you like to use SQLite (simpler, single-file) or PostgreSQL (better for production scale)?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1e to `config/bootcamp_progress.json`.

## Step 2: Check Anti-Patterns

Call `search_docs(query='loading performance', category='anti_patterns', version='current')`. Share relevant anti-patterns with user before benchmarking.

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Hardware Clarification (On-Premises Only)

**Condition:** `deployment_target == "on_premises"` AND `hardware_target` is NOT already stored in `config/bootcamp_preferences.yaml`.

If both conditions are true, ask the following question before proceeding to benchmarking:

👉 "Will you deploy to this machine or a different on-premises server?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

**After receiving the answer**, process the response as follows:

### Response: "This machine"

If the bootcamper indicates they will deploy to the current dev machine:

1. Store in `config/bootcamp_preferences.yaml`:

   ```yaml
   hardware_target: "current_machine"
   ```

2. Proceed with the current machine's specs for all benchmarking and recommendations in Steps 3–13.

### Response: Different server with specs provided

If the bootcamper says they will deploy to a different server AND provides hardware details:

1. Store in `config/bootcamp_preferences.yaml`:

   ```yaml
   hardware_target: "different_server"
   production_specs:
     cpu_cores: <provided value>
     ram_gb: <provided value>
     storage_type: "<provided value>"
     database: "<provided value>"
   ```

2. Use the provided `production_specs` when making performance recommendations and sizing guidance in Steps 3–13.
3. When presenting benchmark results, clearly note: "Benchmarks were run on your dev machine; recommendations target your production hardware (`<cpu_cores>` cores, `<ram_gb>` GB RAM, `<storage_type>`, `<database>`)."
4. If benchmark results on the dev machine differ significantly from what the production hardware would achieve, call that out and explain the expected difference.

### Response: Different server but specs unknown or incomplete

If the bootcamper says they will deploy to a different server but does NOT provide specs (or provides only partial specs), ask a follow-up:

👉 "To give you accurate performance recommendations, I need a few details about your production server:

- CPU cores (e.g., 8, 16, 32)?
- RAM in GB (e.g., 32, 64, 128)?
- Storage type (HDD, SATA SSD, NVMe SSD)?
- Database server (PostgreSQL version, or SQLite)?"

> **🛑 STOP — End your response here.** Wait for the bootcamper to provide the missing details before continuing.

Once the missing details are provided, store them as described in the "Different server with specs provided" section above and proceed.

---

If `deployment_target` is NOT "on_premises", or `hardware_target` is already stored, skip this entire Hardware Clarification section.

## Step 3: Baseline Environment

Capture system info (CPU, RAM, disk, OS, SDK version, DB version). Back up current database. Save to `docs/benchmark_environment.md`.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.
