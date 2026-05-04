# Incremental Loading

In Module 6 you loaded all your data sources in a single batch — read every record, call `add_record` for each one, process redo records, and validate the results. Batch loading works well for initial loads and full refreshes where you want to start from a clean database and ingest everything at once. But production systems rarely stop there. New records arrive daily or hourly from source systems, and you need to ingest them without purging and reloading the entire dataset. That is incremental loading: adding new or changed records to an existing Senzing database that already contains previously loaded data. Batch loading is a one-time operation; incremental loading is an ongoing process that keeps your entity resolution results current as source data grows.

> **Agent instruction:** Call `search_docs(query="incremental loading add records", version="current")` to retrieve the latest Senzing documentation on incremental loading patterns. Use the returned content to supplement the explanations below with any current SDK-specific details or best practices.

## Adding New Records

Your loading program from Module 6 already knows how to add records — the `add_record` function is the same one you used for batch loading. The difference is context: instead of loading an entire data source from scratch, you are adding new records to a database that already contains previously loaded data. Every new record goes through entity resolution against the existing records, so Senzing can determine whether the new record matches an existing entity, creates a new entity, or causes existing entities to merge.

### How Incremental Addition Works

When you call `add_record` with a `DATA_SOURCE` and `RECORD_ID` that Senzing has not seen before, the record is added to the database and resolved against all existing records. The previously loaded data is not affected unless the new record matches existing records — in which case entities may merge or grow.

The key behaviors to understand:

- **New RECORD_ID (additive):** If the `RECORD_ID` does not already exist for that `DATA_SOURCE`, Senzing adds the record as a new entry. It resolves against existing records and either joins an existing entity, creates a new entity, or causes entities to merge.
- **Same DATA_SOURCE + RECORD_ID (replace):** If a record with the same `DATA_SOURCE` and `RECORD_ID` already exists, Senzing replaces the old record data entirely with the new data. This is the update behavior covered in the [Data Updates and Deletions](DATA_UPDATES_AND_DELETIONS.md) guide.

For incremental loading, you are typically working with new records — new `RECORD_ID` values that have not been loaded before. The replace behavior matters when a source system sends corrections or updates alongside new records in the same file.

### Structuring Incremental Input Files

In batch loading, you submit the entire data source — every record, every time. In incremental loading, you submit only the new or changed records since the last load. This is more efficient and avoids unnecessary replace operations for records that have not changed.

There are several ways to structure your incremental input:

**New files per batch:** Each incremental load reads from a new file that contains only the records added or changed since the last load. For example, if your source system exports daily, you might have `customers_2024_01_15.json`, `customers_2024_01_16.json`, and so on. Each file contains only that day's new and changed records.

**Tracking last-loaded position:** If your source system appends to a single file or database table, you can track the last record you loaded (by row number, timestamp, or sequence ID) and start from that position on the next load. This avoids reprocessing records you have already loaded.

### Scenario: Daily Customer Import

Your CRM system exports new customer records daily. Yesterday you loaded 10,000 records in Module 6. Today, 50 new customers signed up and 3 existing customers updated their information.

Your incremental input file contains 53 records:

```json
[
  {
    "DATA_SOURCE": "CRM",
    "RECORD_ID": "10001",
    "NAME_FULL": "Maria Garcia",
    "ADDR_FULL": "789 Pine St, Denver, CO 80201",
    "PHONE_NUMBER": "303-555-0162"
  },
  {
    "DATA_SOURCE": "CRM",
    "RECORD_ID": "10002",
    "NAME_FULL": "James Wilson",
    "ADDR_FULL": "321 Elm Dr, Austin, TX 78701",
    "EMAIL_ADDRESS": "jwilson@example.com"
  }
]
```

The 50 new records have `RECORD_ID` values that Senzing has not seen before — they are added as new entries. The 3 updated records have `RECORD_ID` values that already exist — Senzing replaces the old data with the new data. You do not need to separate new records from updated records; `add_record` handles both cases based on whether the `RECORD_ID` already exists.

### Conceptual Approaches for Ongoing Ingestion

Once you have incremental input files, you need a way to pick them up and feed them to your loading program. Two common conceptual approaches:

**File watching** — your program monitors a directory for new files and processes each one as it arrives:

```text
watch input_directory for new files:
    for each new file:
        read records from file
        for each record:
            call add_record(data_source, record_id, record_data)
        process redo records
        move file to processed_directory
```

**Scheduled runs** — your program runs on a schedule (every hour, every night) and processes whatever new files have appeared since the last run:

```text
on schedule:
    list files in input_directory
    for each unprocessed file:
        read records from file
        for each record:
            call add_record(data_source, record_id, record_data)
        process redo records
        move file to processed_directory
```

Both approaches use the same `add_record` call from your Module 6 loading program. The difference is how you trigger the load — continuously or on a schedule. Choose the approach that fits your source system's data delivery pattern. Neither approach requires third-party scheduling frameworks; you can implement either with the tools your operating system already provides.

### Code Example

Your existing loading program from Module 6 is the starting point for incremental loading. The core loop — read records from a file and call `add_record` for each one — stays the same. The main change is that your input file contains only new or changed records instead of the entire data source.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` to produce the code example for adding new records incrementally. The generated scaffold uses `add_record` — the same function the bootcamper used in Module 6. Explain that the only difference from batch loading is the input: instead of the full data source, the input file contains only new or changed records. The loading logic itself is identical.

## Redo Processing for Incremental Loads

You already know how to process redo records from Module 6 — the functions and the workflow are the same. What changes with incremental loading is the context: instead of processing redo records once after a single batch load, you process them repeatedly after every incremental load. Getting this right is what keeps entity resolution accurate as new data arrives over time.

> **Agent instruction:** Call `search_docs(query="redo processing incremental", version="current")` to retrieve the latest Senzing documentation on redo processing in incremental loading scenarios. Use the returned content to supplement the explanations below with any current SDK-specific details or best practices.

### Why Incremental Loads Generate Redo Records

When you add new records to a database that already contains previously loaded data, those new records go through entity resolution against everything that is already there. Some new records will match existing records and join existing entities. Some will cause entities to merge. Each of these changes can affect other records in the system — records that were resolved based on relationships that now look different because of the new data.

Senzing cannot re-evaluate every potentially affected record inline during the `add_record` call without slowing down the load. Instead, it writes redo records to the redo queue — deferred work items that say "this record should be re-evaluated." Until you process those redo records, some entity resolution results may be stale: entities that should have merged might still be separate, or records that should have split apart might still be grouped together.

This is the same mechanism you saw in Module 6 after batch loading. The difference is that with incremental loading, new redo records are generated after every load cycle, not just once.

### Load Volume and Redo Queue Growth

The number of redo records generated after an incremental load is proportional to the volume and impact of the new data. A small load of 50 records that mostly create new entities with no matches to existing data will produce few or no redo records. A large load of 10,000 records with significant overlap against existing data — shared names, addresses, phone numbers — can produce a redo queue many times larger than the number of records loaded.

This is normal and expected. It reflects the interconnected nature of entity resolution: one new record that matches across multiple existing entities can trigger a cascade of re-evaluations. The important thing is not to minimize redo records (you cannot control how many the engine generates) but to make sure you process all of them before considering the load complete.

### Scheduling Redo Processing After Each Load

In batch loading, you process redo records once at the end. In incremental loading, you process them after every load cycle. The pattern is the same — check, process, drain — but it runs on a recurring schedule.

After each incremental load completes, follow this sequence:

1. **Check the redo queue**: Query the redo queue to see how many redo records are pending. This tells you the scope of re-evaluation work generated by the load you just finished.

2. **Process all pending redo records**: Work through the queue using the same redo processing functions from Module 6. Each redo record triggers a re-evaluation that Senzing deferred during the load.

3. **Verify the queue is drained**: Check the redo queue again after processing. Processing redo records can generate new redo records (cascading effects), so repeat the process cycle until the queue reports zero remaining records.

4. **Proceed to the next load**: Only start the next incremental load after the redo queue is fully drained. Loading new records on top of an unprocessed redo queue means your entity resolution results are already stale before the new data arrives — compounding the staleness with each subsequent load.

As a conceptual workflow, this looks like:

```text
after each incremental load completes:
    check redo queue size
    while redo queue is not empty:
        process all pending redo records
        check redo queue size again
    log that redo processing is complete
    ready for next incremental load
```

### Checking Whether the Redo Queue Is Empty

To verify that all redo records have been processed, query the redo queue for its current count. If the count is zero, the queue is drained and entity resolution is fully up to date. If the count is greater than zero, continue processing.

This check is especially important because processing redo records can generate additional redo records — a cascading effect where re-evaluating one record changes an entity, which flags other records for re-evaluation. A single pass through the queue may not be enough. The check-process-drain loop handles this: keep checking and processing until the count reaches zero.

### Code Example

Processing redo records after an incremental load uses the same redo processing pattern from Module 6. The workflow checks the redo queue, processes each pending record, and repeats until the queue is empty. The only difference from Module 6 is that you run this after every incremental load rather than once after a batch load.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` to produce the code example for checking and processing the redo queue after an incremental load. Show the bootcamper the check-process-drain loop: query the redo queue size, process each pending redo record, and repeat until the queue reports zero remaining records. Explain that this is the same redo processing workflow from Module 6 — the only difference is that it runs after every incremental load cycle rather than once after a batch load.

## Monitoring Incremental Load Health

Batch loading has a clear finish line — you load all the records, process redo, and validate the results. Incremental loading does not. Records keep arriving, redo records keep generating, and entity resolution keeps evolving. Without monitoring, problems can build up silently: records failing to load, redo queues growing faster than they drain, or entity resolution producing unexpected results. Monitoring gives you visibility into the ongoing health of your pipeline so you can catch issues before they affect data quality.

> **Agent instruction:** Call `search_docs(query="monitoring entity resolution health incremental", version="current")` to retrieve the latest Senzing documentation on monitoring entity resolution pipelines. Use the returned content to supplement the explanations below with any current SDK-specific details or best practices.

### Health Indicators

Four indicators give you a reliable picture of how your incremental loading pipeline is performing. Track these after every load cycle to establish baselines and spot deviations early.

**Records loaded per interval (throughput):** Count how many records your loading program successfully processes in each load cycle. If you load daily, track the daily count. If you load hourly, track the hourly count. Throughput tells you whether your pipeline is keeping up with the volume of incoming data. A stable throughput that matches your source system's output rate means the pipeline is healthy. A sudden drop means something is slowing down the load — network issues, resource contention, or records that take longer to resolve because they match many existing entities.

**Error count and error rate:** Track how many records fail during each load cycle and what percentage of the total they represent. Some errors are expected — malformed records from source systems, records with missing required fields, or records that violate data source constraints. A small, stable error rate is normal. What matters is the trend: a rising error rate suggests a systematic problem with the incoming data or a change in the source system's output format.

**Redo queue depth over time:** After each load cycle, record the redo queue size before and after redo processing. The queue should grow after loading (new records generate redo work) and shrink back to zero after redo processing completes. Tracking the peak queue depth and the time to drain gives you a sense of how much re-evaluation work each load generates. If the peak depth is growing over time, your loads are generating more cascading changes — which may be expected as the database grows, or may indicate data quality issues causing excessive entity merges.

**Entity count trend after each incremental load:** Query the total number of resolved entities after each load cycle completes (including redo processing). New records that create new entities increase the count. New records that match existing entities and cause merges decrease the count. The entity count trend tells you whether your data is behaving as expected. A data source that adds 1,000 new customer records per day should produce a roughly predictable change in entity count — if the count barely moves, most new records are matching existing entities. If the count jumps dramatically, most new records are creating new entities with no matches.

### Warning Signs of an Unhealthy Pipeline

The health indicators above establish what normal looks like for your pipeline. Deviations from normal are warning signs that something needs attention.

**Growing redo queue that never drains:** If the redo queue depth after processing is consistently greater than zero — or if it grows larger after each load cycle — your redo processing is not keeping up. This means entity resolution results are increasingly stale. Common causes: redo processing is not running after every load, the processing loop exits before the queue is fully drained, or the load volume is generating more redo work than the system can process between loads.

**Declining throughput:** If the number of records loaded per interval is dropping over time without a corresponding drop in incoming data volume, the pipeline is slowing down. This can happen as the database grows — each new record has more existing records to resolve against — but a sharp decline suggests a specific problem: resource exhaustion, lock contention, or a data pattern that causes expensive resolution operations.

**Increasing error rate:** A rising percentage of failed records means the incoming data quality is degrading or the source system's output format has changed. Investigate the specific errors: are they validation failures (bad data), connection errors (infrastructure), or resolution errors (unexpected data patterns)? A small number of errors is normal; a trend line going up is not.

**Entity count not changing despite new records:** If you are loading new records but the entity count stays flat, every new record is matching an existing entity. This could be correct — if the source system is sending updates for existing people — or it could indicate a data quality problem where overly broad matching criteria are collapsing distinct people into the same entity. Compare the entity count trend against the number of genuinely new records (new `RECORD_ID` values) to determine which case applies.

### Querying Entity and Record Counts

To track entity count trends and verify that records are being loaded, you need to query Senzing for the current counts. The SDK provides functions to retrieve the total number of entities and records in the database. You can call these before and after each load cycle to measure the impact of each incremental load.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='get_stats', version='current')` to produce a code example that queries Senzing for the current entity count and record count. If the `get_stats` workflow is not available, call `search_docs(query="get entity count record count stats", version="current")` to find the appropriate SDK functions and show the bootcamper how to call them. The example should be suitable for use in a monitoring script that runs after each incremental load cycle.
>
> **Agent instruction:** Call `find_examples(query="monitoring entity count record count", version="current")` to locate working code references from indexed Senzing repositories that demonstrate querying entity and record counts. Present any relevant examples to the bootcamper as additional reference material.

## Further Reading

The Senzing SDK and its documentation evolve over time. For the latest guidance on incremental loading — including method signatures, best practices, and new features — use the MCP tools available in your Kiro environment:

- **Search the documentation:** Call `search_docs(query="incremental loading")` to find current articles on adding records to an existing database, incremental redo processing strategies, and pipeline monitoring approaches.
- **Find working examples:** Call `find_examples(query="incremental loading")` to locate working code from indexed Senzing repositories that demonstrates incremental loading patterns, redo scheduling, and health monitoring.
- **Complementary guide:** See [Data Updates and Deletions](DATA_UPDATES_AND_DELETIONS.md) for record update and deletion patterns — replacing existing records, deleting records, and understanding how those operations affect entity resolution and redo processing.
