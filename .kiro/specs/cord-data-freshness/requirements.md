# Requirements: CORD Data Freshness Indicator

## Overview

Cache CORD dataset metadata (version/date) during Module 4 data collection and verify consistency when loading in Module 6, preventing subtle issues from dataset changes during multi-week bootcamp sessions.

## Requirements

1. During Module 4 when CORD data is downloaded via `get_sample_data`, capture and store dataset metadata (dataset name, source, record count, download timestamp) in `config/cord_metadata.yaml`
2. The metadata file must include: dataset name, sources used, record counts per source, download date (ISO 8601), and a content hash (SHA-256 of the first 100 records or the download URL)
3. During Module 6 before loading, check `config/cord_metadata.yaml` against the current data files on disk — verify file sizes and record counts haven't changed
4. If a mismatch is detected, warn the bootcamper: "Your CORD data files may have changed since download. This could affect entity resolution results. Options: (a) re-download fresh data, (b) proceed with current files, (c) check what changed"
5. The freshness check must be advisory only — never block loading
6. Add the freshness check to `module-06-load-data.md` as a pre-load verification step
7. Update `module-04-data-collection.md` to include metadata capture instructions when CORD data is selected
8. Handle the case where bootcampers use their own data (not CORD) — skip freshness checks entirely
9. Write tests covering: metadata file creation, freshness check pass, freshness check fail (size mismatch), missing metadata file (skip gracefully)
