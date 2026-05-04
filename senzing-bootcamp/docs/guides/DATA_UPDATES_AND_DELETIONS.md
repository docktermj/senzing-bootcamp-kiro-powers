# Data Updates and Deletions

Production entity resolution systems rarely work with static data. Customers move, phone numbers change, businesses close, and records get removed from source systems. When source data changes after initial loading, Senzing needs to know — an outdated record can cause incorrect entity merges, and a stale record that no longer exists in the source can pollute resolution results. This guide covers how to update existing records, delete records that are no longer valid, understand how entity resolution re-evaluates after each operation, and manage the redo processing implications that follow.

## Updating Records

Updating a record in Senzing works the same way as loading one — you call `add_record` with the same `DATA_SOURCE` and `RECORD_ID` as the existing record, but with the new record data. Senzing treats this as a **replace** operation: the old record data is fully replaced by the new data, not merged with it. Any fields present in the old record but absent from the new record are removed, not preserved.

This means your loading program from Module 6 already knows how to update records. The only difference is the intent: instead of loading a record for the first time, you are loading a replacement for a record that already exists.

### How It Works

1. You load a record with a specific `DATA_SOURCE` and `RECORD_ID` combination
2. Later, the source data changes — a customer moves, corrects a phone number, or updates their name
3. You call `add_record` again with the **same** `DATA_SOURCE` and `RECORD_ID`, passing the updated record data
4. Senzing replaces the old record data entirely with the new data
5. Senzing re-evaluates the updated record against all other records, which may cause entities to merge, split, or change composition

### Scenario: Customer Address Change

A customer named Robert Smith moves from New York to Chicago. The CRM system updates their address, and you need to push that change to Senzing.

**Before** — the original record loaded in Module 6:

```json
{
  "DATA_SOURCE": "CRM",
  "RECORD_ID": "1001",
  "NAME_FULL": "Robert Smith",
  "ADDR_FULL": "123 Main St, New York, NY 10001",
  "PHONE_NUMBER": "212-555-0147",
  "EMAIL_ADDRESS": "rsmith@example.com"
}
```

**After** — the replacement record with the updated address:

```json
{
  "DATA_SOURCE": "CRM",
  "RECORD_ID": "1001",
  "NAME_FULL": "Robert Smith",
  "ADDR_FULL": "456 Oak Ave, Chicago, IL 60601",
  "PHONE_NUMBER": "312-555-0198",
  "EMAIL_ADDRESS": "rsmith@example.com"
}
```

Because the `DATA_SOURCE` and `RECORD_ID` match, Senzing replaces the entire old record with this new one. The New York address and old phone number are gone — only the Chicago address and new phone number remain.

### Entity Re-evaluation Impact

After the replacement, Senzing re-evaluates the updated record against all other records in the system. This can change entity composition:

- **Entity merge**: The new address or phone number might match a record in another entity, causing the two entities to merge into one
- **Entity split**: The old address might have been the only link holding two records together in the same entity — removing it could cause the entity to split
- **No change**: If the updated fields are not used for matching (or the matches remain the same), the entity stays intact with the new data

### Code Example

Your existing loading program from Module 6 handles updates without modification — call `add_record` with the same `DATA_SOURCE` and `RECORD_ID` and the new record data.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` to produce the code example for updating a record. The generated scaffold uses `add_record` — the same function the bootcamper used in Module 6. Explain that the only difference from initial loading is that the record data contains updated field values while the `DATA_SOURCE` and `RECORD_ID` remain the same.

## Deleting Records

When a record is removed from a source system — an account is closed, a duplicate is purged, or a business shuts down — the corresponding record in Senzing should be deleted. Deleting a record tells Senzing to remove it from whatever entity it belongs to and re-evaluate the remaining records. If the deleted record was the glue holding parts of an entity together, the entity may split. If it was the only record in the entity, the entity disappears entirely.

You delete a record by calling `delete_record` with the record's `DATA_SOURCE` and `RECORD_ID`. No record data is needed — just the two identifiers that uniquely locate the record.

### How It Works

1. A record exists in Senzing with a specific `DATA_SOURCE` and `RECORD_ID` combination
2. The source system removes that record — an account is closed, a row is deleted, or a correction removes a duplicate
3. You call `delete_record` with the **same** `DATA_SOURCE` and `RECORD_ID`
4. Senzing removes the record data and detaches the record from its entity
5. Senzing re-evaluates the remaining records in the affected entity, which may cause the entity to shrink, split into multiple entities, or be removed entirely

### Scenario: Account Closure

A loyalty program account is closed, and the record needs to be removed from Senzing. Before deletion, the customer's entity contains three records from different sources that all resolved together.

**Before deletion** — the entity contains three records:

| DATA_SOURCE | RECORD_ID | NAME_FULL | PHONE_NUMBER |
| --- | --- | --- | --- |
| CRM | 1001 | Robert Smith | 212-555-0147 |
| LOYALTY | 2001 | Rob Smith | 212-555-0147 |
| BILLING | 3001 | Robert J Smith | 312-555-0198 |

All three records resolved into a single entity because of overlapping name and phone number matches. The LOYALTY record shares a phone number with the CRM record, and the BILLING record shares a name variant with both.

**Deletion** — the loyalty program closes the account, so you delete the LOYALTY record:

- `DATA_SOURCE`: `LOYALTY`
- `RECORD_ID`: `2001`

**After deletion** — Senzing removes the LOYALTY record and re-evaluates the remaining two records:

| DATA_SOURCE | RECORD_ID | NAME_FULL | PHONE_NUMBER |
| --- | --- | --- | --- |
| CRM | 1001 | Robert Smith | 212-555-0147 |
| BILLING | 3001 | Robert J Smith | 312-555-0198 |

The CRM and BILLING records may still resolve together based on the name match alone — or they may split into separate entities if the deleted LOYALTY record was the bridge linking them. The outcome depends on the strength of the remaining matches.

### Entity Impact After Deletion

When Senzing removes a record from an entity, three outcomes are possible:

- **Entity shrinks**: The remaining records still match each other, so the entity stays intact but with one fewer record
- **Entity splits**: The deleted record was the link between two groups of records — without it, the entity splits into two or more separate entities
- **Entity removed**: The deleted record was the only record in the entity, so the entity no longer exists

### Code Example

Deleting a record requires the `delete_record` method with the record's `DATA_SOURCE` and `RECORD_ID`. Unlike updates, you do not pass any record data — just the identifiers.

> **Agent instruction:** Call `get_sdk_reference(topic='functions', filter='delete_record', version='current')` to retrieve the current method signature for deleting a record. Show the bootcamper how to call `delete_record` with a `DATA_SOURCE` and `RECORD_ID`. Explain that no record data is needed — only the two identifiers that locate the record in Senzing.

## Entity Re-evaluation After Changes

Every time a record is updated or deleted, Senzing automatically recalculates the entity composition for all affected entities. You do not need to trigger this manually — re-evaluation happens as part of the `add_record` (for updates) and `delete_record` (for deletions) calls. The engine looks at the remaining and changed records, recalculates which ones match, and adjusts entity boundaries accordingly.

Understanding re-evaluation helps you predict what will happen to your resolved entities when source data changes, and verify that the results match your expectations.

### Update-Triggered Re-evaluation

When you update a record by calling `add_record` with the same `DATA_SOURCE` and `RECORD_ID`, Senzing replaces the old record data and re-evaluates the record against every other record in the system. Because the record still exists — just with different data — the re-evaluation focuses on whether the updated fields change which entities the record matches.

Possible outcomes:

- **Entity stays the same**: The updated fields do not affect matching, so the record remains in its current entity with the new data
- **Record moves to a different entity**: The new data matches records in a different entity more strongly, so the record shifts from one entity to another
- **Entities merge**: The new data introduces a match to a record in a separate entity, causing the two entities to combine
- **Entity splits**: The old data was the link holding records together — replacing it removes that link, and the entity splits into two or more entities

The key point is that the record itself always survives an update. It may end up in a different entity, but it is never removed from the system.

### Deletion-Triggered Re-evaluation

When you delete a record by calling `delete_record`, Senzing removes the record entirely and re-evaluates the remaining records in the affected entity. Because the record is gone — not just changed — the re-evaluation focuses on whether the remaining records still have enough matching evidence to stay together.

Possible outcomes:

- **Entity shrinks**: The remaining records still match each other, so the entity stays intact with one fewer record
- **Entity splits**: The deleted record was the bridge connecting two groups of records — without it, the groups separate into distinct entities
- **Entity disappears**: The deleted record was the only record in the entity, so the entity no longer exists

The key difference from update-triggered re-evaluation is permanence: a deleted record is gone from the system, while an updated record remains and may form new connections.

### Verifying Entity Changes

After an update or deletion, you should verify that the entity composition matches your expectations. Two approaches work well:

1. **Query by record**: Use the `DATA_SOURCE` and `RECORD_ID` of the changed record to look up which entity it belongs to now (for updates) or confirm it no longer exists (for deletions). This tells you the direct impact on the record you changed.

2. **Query by entity ID**: If you know the entity ID from before the change, query it directly to see the current composition — which records are in the entity, what data they contain, and whether the entity still exists. This tells you the broader impact on the entity as a whole.

For updates, querying by record is usually the most direct path — you get back the entity the updated record now belongs to, and you can inspect its composition. For deletions, querying by entity ID shows you what happened to the entity after the record was removed: did it shrink, split, or disappear?

### Code Example

Verifying entity changes after an update or deletion requires querying the affected entity. The query method retrieves the current entity composition so you can confirm the re-evaluation result.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='query', version='current')` or `get_sdk_reference(topic='functions', filter='get_entity', version='current')` to produce the code example for querying an entity after a change. Show the bootcamper how to retrieve an entity by record key (DATA_SOURCE + RECORD_ID) to verify the re-evaluation result. Explain that this is the same query pattern used elsewhere in the bootcamp — the only difference is the context: you are confirming that an update or deletion produced the expected entity composition.

## Redo Processing Implications

You already worked with redo records in Module 6 — they are not new. What is new is understanding why updates and deletions generate them and why processing them matters for keeping entity resolution accurate across your entire dataset.

When you update or delete a record, Senzing re-evaluates the entity that record belongs to. But the impact does not stop there. Other records in the system may have been resolved based on relationships that included the changed record. Those records need to be re-evaluated too, and Senzing flags them by writing redo records to the redo queue. Until you process those redo records, some entity resolution results in your system may be stale.

### Why Updates and Deletions Generate Redo Records

A record update or deletion directly affects the entity that contains the changed record — Senzing handles that re-evaluation immediately as part of the `add_record` or `delete_record` call. But entity resolution is interconnected. Other records that shared an entity with the changed record, or that were close to matching it, may need re-evaluation too. Senzing cannot re-evaluate every potentially affected record inline without slowing down the update or delete call, so it writes redo records instead — deferred work items that say "this record should be re-evaluated when you get a chance."

Processing redo records is what keeps entity resolution fully accurate. Without it, some entities may contain records that should have split apart, or miss records that should have merged in.

### Cascading Redo Effects

A single record update or deletion can generate **multiple** redo records. This happens because the changed record may have participated in matches with several other records across different entities. Each of those related records gets flagged for re-evaluation.

For example, if you delete a record that was part of an entity with five other records, Senzing may generate redo records for some or all of those remaining records — each one needs to be re-evaluated to confirm it still belongs where it is. If those re-evaluations cause further entity changes, additional redo records may be generated in turn.

The cascading nature means that a batch of updates or deletions can produce a redo queue significantly larger than the number of records you changed. This is normal and expected — it reflects the interconnected nature of entity resolution.

### Recommended Pattern: Check, Process, Drain

After performing a batch of updates or deletions, follow this pattern to ensure entity resolution is fully up to date:

1. **Check the redo queue**: Query the redo queue to see how many redo records are pending. This tells you the scope of deferred re-evaluation work.

2. **Process all pending redo records**: Work through the redo queue, processing each redo record. This triggers the deferred re-evaluations that Senzing could not perform inline during the original updates or deletions.

3. **Verify the queue is drained**: After processing, check the redo queue again to confirm it is empty. Processing redo records can generate new redo records (cascading effects), so you may need to repeat the process cycle until the queue is fully drained.

This is the same redo processing workflow you used in Module 6 after loading data — the only difference is the context. In Module 6, redo records were generated by initial record loading. Here, they are generated by updates and deletions. The processing mechanics are identical.

### Code Example

Checking and processing the redo queue after updates or deletions uses the same redo processing pattern from Module 6. The workflow reads redo records from the queue, processes each one, and repeats until the queue is empty.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` to produce the code example for checking and processing the redo queue. Show the bootcamper the check-process-drain loop: query the redo queue size, process each pending redo record, and repeat until the queue reports zero remaining records. Explain that this is the same redo processing workflow from Module 6 — the only difference is that the redo records were generated by updates and deletions rather than initial loading.

## Further Reading

The Senzing SDK and its documentation evolve over time. For the latest guidance on record management — including method signatures, best practices, and new features — use the MCP tools available in your Kiro environment:

- **Search the documentation**: Call `search_docs(query="record management")` to find current articles on updating and deleting records, entity re-evaluation behavior, and redo processing strategies. Try narrower queries like `search_docs(query="delete record entity impact")` for specific topics.
- **Look up SDK method signatures**: Call `get_sdk_reference(topic="functions", filter="add_record")` or `get_sdk_reference(topic="functions", filter="delete_record")` to retrieve the current method signatures, parameters, and return values for the functions covered in this guide.

These tools pull directly from the Senzing documentation and SDK reference, so the results always reflect the version you are working with.
