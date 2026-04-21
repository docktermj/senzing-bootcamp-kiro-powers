# Design Document: Data Collection Checklist Template

## Overview

Create a `data_collection_checklist.md` template in `senzing-bootcamp/templates/` and update the Module 3 steering file to reference it. This is a content-only change involving two markdown files — no code.

## Current State

- Module 3 steering file (`senzing-bootcamp/steering/module-03-data-collection.md`) guides users through data collection but has no template for structured documentation
- The `senzing-bootcamp/templates/` directory does not yet exist
- Users must create their data inventory from scratch, leading to inconsistency and missed fields
- The steering file's Step 4 asks users to create `docs/data_source_locations.md` but provides only an inline example, not a reusable template

## Changes

### Change 1: Create templates directory and data_collection_checklist.md

**File:** `senzing-bootcamp/templates/data_collection_checklist.md`

**Structure:**

1. Title and purpose header explaining when to use the checklist (during Module 3)
2. Instructions section with brief usage guidance
3. Data Inventory Table — a markdown table with columns:
   - Source Name (human-readable name)
   - DATA_SOURCE (Senzing identifier, uppercase with underscores)
   - Record Count (approximate or exact)
   - Data Format (CSV/JSON/JSONL/XML/Excel/Parquet/DB/API)
   - File Location (path relative to project root, e.g., `data/raw/customers.csv`)
   - Access Method (upload, URL, database query, API call)
   - Update Frequency (one-time, daily, weekly, monthly, real-time)
   - Contact Person (data owner or system admin)
   - Data Sensitivity (Public/Internal/Confidential/Restricted)
4. One example row filled in with realistic sample data (e.g., a CRM customer export)
5. Reference section: Data Format Values — lists each supported format with a one-line description
6. Reference section: Data Sensitivity Levels — defines Public, Internal, Confidential, Restricted
7. Reference section: DATA_SOURCE Naming Conventions — uppercase, underscores, no spaces
8. Validation Checklist — markdown checkboxes for Module 4 readiness:
   - All source files exist in `data/raw/`
   - Record counts verified
   - Data formats documented
   - DATA_SOURCE identifiers assigned and follow naming conventions
   - `docs/data_source_locations.md` created or updated
   - Data sensitivity levels assigned

### Change 2: Update Module 3 steering file

**File:** `senzing-bootcamp/steering/module-03-data-collection.md`

**Location:** Insert a new sub-step within Step 4 ("Document data source locations"), before the existing markdown template.

**Content:** Add instructions for the agent to:

1. Offer to copy `senzing-bootcamp/templates/data_collection_checklist.md` into the bootcamper's `docs/` directory as `docs/data_collection_checklist.md`
2. Guide the bootcamper to fill in the Data Inventory Table for each collected source
3. Guide the bootcamper to complete the Validation Checklist before proceeding to Module 4

**Preservation:** All existing Step 4 content (the inline `data_source_locations.md` example and instructions) remains unchanged. The template reference is additive.

## Correctness Properties

### Property 1: Template file exists at correct path

- **Criteria:** 1.1
- **Validation:** File `senzing-bootcamp/templates/data_collection_checklist.md` exists

### Property 2: Data Inventory Table contains all required columns

- **Criteria:** 1.2, 1.3
- **Validation:** The template contains a markdown table with headers: Source Name, DATA_SOURCE, Record Count, Data Format, File Location, Access Method, Update Frequency, Contact Person, Data Sensitivity; and at least one non-header data row

### Property 3: Supported data formats are documented

- **Criteria:** 2.1, 2.2
- **Validation:** The template contains a reference section listing CSV, JSON, JSONL, XML, Excel, Parquet, DB, and API with descriptions

### Property 4: Validation Checklist is complete

- **Criteria:** 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
- **Validation:** The template contains a section with `- [ ]` checkbox items covering: files in `data/raw/`, record counts verified, formats documented, DATA_SOURCE identifiers valid, `data_source_locations.md` exists

### Property 5: Steering file references template

- **Criteria:** 4.1, 4.2, 4.3
- **Validation:** The steering file contains the path `senzing-bootcamp/templates/data_collection_checklist.md` and instructions to copy it; all existing key content preserved (verified by presence of existing phrases like "data_source_locations.md", "data/raw/", "Option A", "Option B", "Option C", "Option D")

### Property 6: Data sensitivity levels are defined

- **Criteria:** 5.1, 5.2
- **Validation:** The template contains definitions for Public, Internal, Confidential, and Restricted sensitivity levels
