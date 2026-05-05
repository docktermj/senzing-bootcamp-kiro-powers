---
inclusion: manual
---

# Module 8 Phase A: Requirements & Baselines (Steps 1–3)

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, tailor to RDS/Aurora and EC2 instance types. Also read `deployment_target` from `config/bootcamp_preferences.yaml`. When `deployment_target` is set but `cloud_provider` is not (e.g., container platform or local target), use the deployment target to inform performance target guidance — container platform targets (Kubernetes, Docker Swarm) differ from bare-metal or local targets in resource constraints, networking overhead, and scaling characteristics.

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

👉 "Will you deploy to this machine, or a different on-premises server? If different, what are the specs (CPU cores, RAM, storage type, database server)?"

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
