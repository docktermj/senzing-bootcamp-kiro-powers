# Tasks: Complete Module 0 License Configuration

## Task 1: Add license priority order documentation to Step 5
- [x] 1.1 Insert a "License Resolution Priority" block at the top of Step 5, immediately after the heading, documenting the four-level priority: project-local `licenses/g2.lic`, `SENZING_LICENSE_PATH` env var, system CONFIGPATH `g2.lic`, built-in evaluation mode
- [x] 1.2 Verify the priority order block is present and correctly ordered in the file

## Task 2: Add SENZING_LICENSE_PATH discovery to the license check sequence
- [x] 2.1 Insert a new discovery check for the `SENZING_LICENSE_PATH` environment variable between the existing CONFIGPATH check and the "no license found" user prompt
- [x] 2.2 Include handling for when `SENZING_LICENSE_PATH` is set and valid, and when it is set but the file doesn't exist

## Task 3: Add license acquisition guidance
- [x] 3.1 Add evaluation license contact info (support@senzing.com, 1-2 business days, 30-90 day validity) and production license contact info (sales@senzing.com) to the "no license" section

## Task 4: Add licenses/README.md reference
- [x] 4.1 Add a reference to `licenses/README.md` at the end of Step 5 for complete licensing information

## Task 5: Validate all changes
- [x] 5.1 Verify all existing Step 5 content is preserved (CONFIGPATH discovery, BASE64 handling, LICENSEFILE pipeline config, evaluation fallback, bootcamp_preferences.yaml recording)
- [x] 5.2 Verify the steering file has no markdown formatting issues

## Post-Implementation Updates

After initial implementation, Step 5 was condensed from ~80 verbose lines to ~20 prescriptive lines per Kiro best practices. Removed scenario-by-scenario descriptions, kept only the prescriptive rules and essential commands. Module 0 total reduced from 255 to 174 lines.
