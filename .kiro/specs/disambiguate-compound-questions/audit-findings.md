# Compound Question Audit Findings

## Summary

Scanned all files in `senzing-bootcamp/steering/` for 👉 prompts containing compound questions.

**Methods used:**
1. Automated test (`test_question_disambiguation.py`) — regex pattern: `?\s*.{0,80}?\b(Does|Is|Are|Would|Should|Could|Can|Will|Anything|Or\s)\b`
2. Manual grep for patterns the regex misses: `? Have `, `? And `, `? Want `
3. Manual review of all 👉 question blocks for multi-question-mark patterns

**Total violations found: 11** (4 from automated test including 1 false positive, 6 additional from manual scan, plus 2 already identified in Requirements 3.1/3.2)

- **Real violations needing rewrite: 10**
- **False positive (test issue): 1** (conversation-protocol.md:73 — rule definition text, not an actual question)

---

## Automated Test Findings (4 violations)

### 1. conversation-protocol.md:73 — FALSE POSITIVE

**Original text:**
> **Compound Question anti-pattern:** A 👉 prompt that combines a Confirmation Question with a Follow-Up Question. Example: "Does that look right? Anything I missed?" — "yes" could mean "yes it's right" OR "yes you missed something."

**Assessment:** This is the rule definition itself, not an actual question directed at the bootcamper. The 👉 emoji appears inside a quoted example within the definition text. This is a **false positive** — the test should skip this line (it's not inside a WRONG header section, but it's part of the rule definition, not an actual prompt).

**Proposed fix:** Add this to the test's skip logic (it's in the Question Disambiguation section definition, not an actual question block). Alternatively, remove the 👉 from the inline example text.

---

### 2. deployment-onpremises.md:19

**Step:** Prerequisites check (first 👉 question in file)

**Original text:**
> 👉 "Do you have Docker and Docker Compose installed on your target deployment host(s)? And is PostgreSQL already running, or do we need to set that up too?"

**Issue:** Two distinct questions joined by "And" — (1) Docker installed? (2) PostgreSQL running? A "yes" could mean "yes to Docker" or "yes to both."

**Proposed rewrite:**
> 👉 "Do you have Docker, Docker Compose, and PostgreSQL all installed and running on your target deployment host(s)?"

Single question: "yes" = all prerequisites met, "no" = something is missing (agent asks what's missing next turn).

---

### 3. module-08-phaseA-requirements.md:69

**Step:** Hardware Clarification (conditional question)

**Original text:**
> 👉 "Will you deploy to this machine, or a different on-premises server? If different, what are the specs (CPU cores, RAM, storage type, database server)?"

**Issue:** Two distinct questions — (1) this machine or different? (2) what are the specs? The second question is conditional on the first answer being "different," but combining them forces the bootcamper to parse the conditional logic.

**Proposed rewrite:**
> 👉 "Will you deploy to this machine or a different on-premises server?"

Single question: "this machine" or "different server." If different, the agent asks for specs in the next turn (the existing "Response: Different server" handling already does this).

---

### 4. onboarding-flow.md:347

**Step:** 4c. Comprehension Check

**Original text:**
> 👉 "That was a lot of ground to cover. Does everything so far makes sense? Do you have any questions about the modules, the data, licensing, or anything else before we move on to choosing a track?"

**Issue:** Two distinct questions — (1) Does it make sense? (2) Do you have questions? A "yes" is ambiguous: "yes it makes sense" vs "yes I have questions."

**Proposed rewrite:**
> 👉 "That was a lot of ground to cover — does everything so far make sense?"

Single question: "yes" = understood, proceed. "no" or questions = agent addresses them before moving on. (The existing "Clarification handling" paragraph already handles follow-up questions.)

---

## Manual Scan Findings (6 additional violations)

### 5. deployment-aws.md:19

**Step:** Prerequisites check (first 👉 question in file)

**Original text:**
> 👉 "Do you have an AWS account and the AWS CLI installed? Have you already selected a region and created a VPC for this deployment?"

**Issue:** Two distinct questions joined by separate sentences — (1) AWS account + CLI installed? (2) Region/VPC selected? "Yes" is ambiguous.

**Why regex missed it:** "Have" is not in the pattern word list.

**Proposed rewrite:**
> 👉 "Do you have an AWS account with the CLI installed, a region selected, and a VPC ready for this deployment?"

Single question: "yes" = all prerequisites met, "no" = something is missing (agent asks what's needed next turn).

---

### 6. deployment-azure.md:19

**Step:** Prerequisites check (first 👉 question in file)

**Original text:**
> 👉 "Do you have an Azure subscription and the Azure CLI installed? Have you already created a resource group for this deployment?"

**Issue:** Two distinct questions — (1) subscription + CLI? (2) resource group created? "Yes" is ambiguous.

**Why regex missed it:** "Have" is not in the pattern word list.

**Proposed rewrite:**
> 👉 "Do you have an Azure subscription, the Azure CLI installed, and a resource group created for this deployment?"

Single question: "yes" = all prerequisites met, "no" = something is missing.

---

### 7. deployment-gcp.md:19

**Step:** Prerequisites check (first 👉 question in file)

**Original text:**
> 👉 "Do you have a GCP project set up with the gcloud CLI installed? Have you created an Artifact Registry repository for container images?"

**Issue:** Two distinct questions — (1) GCP project + CLI? (2) Artifact Registry created? "Yes" is ambiguous.

**Why regex missed it:** "Have" is not in the pattern word list.

**Proposed rewrite:**
> 👉 "Do you have a GCP project with the gcloud CLI installed and an Artifact Registry repository created for container images?"

Single question: "yes" = all prerequisites met, "no" = something is missing.

---

### 8. deployment-kubernetes.md:19

**Step:** Prerequisites check (first 👉 question in file)

**Original text:**
> 👉 "What Kubernetes cluster are you targeting — a managed service (EKS, AKS, GKE), an on-premises cluster, or a local cluster (minikube, kind)? And do you have Helm v3 installed?"

**Issue:** Two distinct questions joined by "And" — (1) which cluster type? (2) Helm installed? These require different answer types (a choice vs yes/no).

**Why regex missed it:** "And" is not in the pattern word list (only "Or\s" is checked).

**Proposed rewrite:**
> 👉 "What Kubernetes cluster are you targeting — a managed service (EKS, AKS, GKE), an on-premises cluster, or a local cluster (minikube, kind)?"

Single question asking for cluster type. Agent asks about Helm in the next turn.

---

### 9. visualization-guide.md:34

**Step:** 2. Gather requirements

**Original text:**
> 👉 "Which data source(s) should the graph include? And which features: force layout, detail panel, cluster highlighting, search/filter, summary statistics?"

**Issue:** Two distinct questions joined by "And" — (1) which data sources? (2) which features? These are independent choices requiring separate answers.

**Why regex missed it:** "And" is not in the pattern word list, and "which" is not a flagged question-starting word.

**Proposed rewrite:**
> 👉 "Which data source(s) should the graph include?"

Single question. Agent asks about feature selection in the next turn.

---

### 10. visualization-guide.md:54

**Step:** 4. Generate HTML visualization (review)

**Original text:**
> 👉 "Open the HTML file — does it look right? Want changes?"

**Issue:** Two questions — (1) does it look right? (2) want changes? "Yes" is ambiguous: "yes it looks right" vs "yes I want changes."

**Why regex missed it:** "Want" is not in the pattern word list.

**Proposed rewrite:**
> 👉 "Open the HTML file — does it look right?"

Single question: "yes" = looks good, proceed. "no" = agent asks what to change next turn.

---

## Additional Notes

### module-01-business-problem.md:162 (already known from Requirement 3)

**Original text:**
> Does that sound right? Anything I missed or got wrong?"

**Proposed rewrite (from design doc):**
> Does that summary capture your situation accurately?"

### module-01-phase2-document-confirm.md:127 (already known from Requirement 3)

**Original text:**
> "Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"

**Proposed rewrite (from design doc):**
> "Does this accurately capture your problem and approach?"

---

## Files NOT Flagged (confirmed clean or excluded)

| File | Reason |
|------|--------|
| `conversation-protocol.md` (WRONG examples) | Inside "WRONG" violation example headers — intentionally showing bad patterns |
| `session-resume.md` (lines 97, 104, 248) | Inside fenced code blocks — showing examples |
| `module-07-query-validation.md` (line 59) | Agent instruction text, not a 👉 question block |
| `skip-step-protocol.md` (line 25) | Single question with lettered options (a, b, c) — not compound |
| `module-08-phaseA-requirements.md` (line 110) | Single question with structured list of needed details — one request |
| `visualization-guide.md` (line 21) | Single question with numbered choice list — not compound |
| `feedback-workflow.md` | All questions are single, unambiguous |
| `module-02-sdk-setup.md` | All questions are single, unambiguous |

---

## Test Improvement Recommendations

The automated test regex should be expanded to also catch:
- `? Have ` — "Have you..." is a common question starter
- `? And ` — "And" joining a second question
- `? Want ` — "Want..." as an informal question starter

This would catch violations 5–10 automatically in future CI runs.
