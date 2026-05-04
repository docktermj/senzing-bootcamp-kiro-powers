# Tasks

## Task 1: Create the Streaming Integration Guide

- [x] 1.1 Create `senzing-bootcamp/docs/guides/STREAMING_INTEGRATION.md` with level-1 heading "Streaming Integration" and introductory paragraph explaining why streaming integration matters for production Senzing deployments and how it differs from batch loading (Module 6) and incremental loading
  > **Requirements:** 1.1, 1.2, 1.3, 1.4
- [x] 1.2 Add the high-level architecture Mermaid diagram showing end-to-end flow: source systems → message queue → streaming consumers → Senzing → dead letter queue, using a fenced code block with the `mermaid` language identifier
  > **Requirements:** 6.1, 6.2, 6.4

## Task 2: Write Message Queue Consumption Patterns Section

- [x] 2.1 Add a "Message Queue Consumption Patterns" section covering Apache Kafka, RabbitMQ, and Amazon SQS consumer patterns — how records are read, acknowledged, and committed — without requiring installation of any specific queue client library
  > **Requirements:** 2.1, 2.2
- [x] 2.2 Add a subsection on message transformation describing how consumed messages are transformed into Senzing-compatible records (DATA_SOURCE, RECORD_ID, and mapped attributes) before submission to the Senzing SDK
  > **Requirements:** 2.3
- [x] 2.3 Add a subsection on delivery semantics explaining the trade-offs between at-least-once and exactly-once delivery and how each affects Senzing record processing (re-loading the same RECORD_ID replaces the existing record)
  > **Requirements:** 2.4

## Task 3: Write Real-Time Record Processing Section

- [x] 3.1 Add a "Real-Time Record Processing Through Senzing" section explaining how records flow from a streaming consumer through the Senzing SDK, including the processing lifecycle: `add_record` ingestion, entity resolution, and redo record generation. Include an agent instruction callout to use `search_docs` for current SDK behavior
  > **Requirements:** 3.1, 3.2, 7.1
- [x] 3.2 Add a subsection on redo processing in streaming pipelines, explaining whether redo records should be processed inline or via a separate consumer
  > **Requirements:** 3.3
- [x] 3.3 Add a subsection on concurrency considerations: how multiple consumer threads or instances can process records in parallel with a PostgreSQL-backed Senzing database. Include an agent instruction callout to use `find_examples` for streaming implementation patterns
  > **Requirements:** 3.4, 7.2

## Task 4: Write Backpressure Handling Section

- [x] 4.1 Add a "Backpressure Handling" section explaining at least three strategies: consumer-side rate limiting, queue-level buffering with retention policies, and horizontal scaling of consumer instances
  > **Requirements:** 4.1, 4.2
- [x] 4.2 Add a subsection on detecting backpressure conditions using observable metrics: consumer lag, processing latency, and queue depth
  > **Requirements:** 4.3
- [x] 4.3 Add a subsection explaining the relationship between Senzing processing throughput and consumer parallelism, including how adding consumer instances affects entity resolution load
  > **Requirements:** 4.4

## Task 5: Write Error Handling Section

- [x] 5.1 Add an "Error Handling for Streaming Pipelines" section describing a retry strategy for transient errors with configurable retry counts and exponential backoff
  > **Requirements:** 5.1, 5.2
- [x] 5.2 Add the error handling and retry flow Mermaid diagram showing message consumption → processing attempt → retry logic → dead-letter routing, using a fenced code block with the `mermaid` language identifier
  > **Requirements:** 6.1, 6.3, 6.4
- [x] 5.3 Add a subsection on the Dead Letter Queue pattern: what metadata to capture (original message, error details, timestamp, retry count) and the recommendation to route validation failures (malformed data, missing required fields) to the DLQ rather than retrying indefinitely
  > **Requirements:** 5.3, 5.4
- [x] 5.4 Add a subsection on monitoring error rates and setting alerting thresholds to detect systemic issues (such as schema changes in source systems)
  > **Requirements:** 5.5

## Task 6: Add Further Reading Section and MCP Tool References

- [x] 6.1 Add a "Further Reading" section directing bootcampers to use `search_docs` and `find_examples` for the latest streaming integration guidance, and linking to related guides (INCREMENTAL_LOADING.md, DATA_UPDATES_AND_DELETIONS.md)
  > **Requirements:** 7.3
- [x] 6.2 Review the full guide to ensure all Senzing SDK behavior explanations include agent instruction callouts for `search_docs` and all example pattern references include callouts for `find_examples`
  > **Requirements:** 7.1, 7.2

## Task 7: Update Module 11 Steering with Cross-Reference

- [x] 7.1 Add a "Further Reading" section to `senzing-bootcamp/steering/module-11-deployment.md` after the Phase Gate section, referencing the Streaming Integration Guide as optional advanced reading for production deployments covering real-time streaming patterns for event-driven architectures using message queues. Ensure the reference is NOT added as a required step in the Module 11 workflow
  > **Requirements:** 8.1, 8.2, 8.3

## Task 8: Update Guides README

- [x] 8.1 Add an entry for `STREAMING_INTEGRATION.md` in the "After the Bootcamp" section of `senzing-bootcamp/docs/guides/README.md` with the filename as a Markdown link, a bold title, and a 2-3 line description covering real-time streaming patterns, message queue integration, backpressure handling, and error management
  > **Requirements:** 9.1, 9.2
- [x] 8.2 Add `STREAMING_INTEGRATION.md` to the Documentation Structure tree in the guides README under the `guides/` directory
  > **Requirements:** 9.3

## Task 9: Validate Guide Structure

- [x] 9.1 Verify the guide maintains conceptual focus throughout — no language-specific import statements, no framework installation commands, no step-by-step setup instructions
  > **Requirements:** 1.4
- [x] 9.2 Verify the guide contains at least two Mermaid diagrams in fenced code blocks with the `mermaid` language identifier, the level-1 heading convention is followed, and all cross-references use correct relative paths
  > **Requirements:** 1.3, 6.1, 6.4
