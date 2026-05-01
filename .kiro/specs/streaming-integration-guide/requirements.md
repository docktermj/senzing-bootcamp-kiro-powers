# Requirements Document

## Introduction

Module 11 covers packaging and deployment, but stops short of addressing a critical production pattern: real-time streaming integration. Many Senzing deployments sit behind message queues — Kafka, RabbitMQ, SQS — consuming records as they arrive rather than loading them in batch. Bootcampers completing Module 11 have no guidance on how to architect a streaming pipeline around Senzing, how to handle backpressure when Senzing processing can't keep up with inbound message rates, or how to manage errors in a streaming context where failed records can't simply be retried by re-running a script.

This feature adds a conceptual guide at `docs/guides/STREAMING_INTEGRATION.md` covering real-time streaming integration patterns: consuming records from message queues, processing them through Senzing in real time, handling backpressure, and managing errors in streaming pipelines. The guide uses text-based Mermaid diagrams for architecture visualization and relies on `search_docs` and `find_examples` from the Senzing MCP server for authoritative content. Module 11 references the guide as advanced reading for production deployments. The guide stays conceptual — focusing on patterns and architecture rather than specific framework setup.

## Glossary

- **Streaming_Integration_Guide**: The Markdown document at `docs/guides/STREAMING_INTEGRATION.md` that explains real-time streaming integration patterns for Senzing entity resolution.
- **Message_Queue**: A middleware system (such as Apache Kafka, RabbitMQ, or Amazon SQS) that decouples record producers from consumers by buffering messages for asynchronous processing.
- **Backpressure**: The condition where inbound message rate exceeds the rate at which Senzing can process records, requiring the pipeline to slow down or buffer to avoid data loss or resource exhaustion.
- **Streaming_Consumer**: A component that reads records from a Message_Queue and submits them to Senzing for entity resolution processing.
- **Dead_Letter_Queue**: A secondary queue where records that fail processing after a configured number of retries are placed for later inspection and manual remediation.
- **Module_11_Steering**: The steering file at `senzing-bootcamp/steering/module-11-deployment.md` that defines the Module 11 workflow for packaging and deployment.
- **Guide_Directory**: The directory at `senzing-bootcamp/docs/guides/` containing user-facing reference documentation for the bootcamp.
- **Guides_README**: The file at `senzing-bootcamp/docs/guides/README.md` that indexes all available guides with descriptions and links.
- **Mermaid_Diagram**: A text-based diagram written in Mermaid syntax that renders as a visual flowchart, sequence diagram, or architecture diagram in Markdown-compatible viewers.

## Requirements

### Requirement 1: Streaming Integration Guide Creation

**User Story:** As a bootcamper planning a production deployment, I want a dedicated guide on real-time streaming integration patterns, so that I can architect an event-driven pipeline around Senzing instead of relying solely on batch loading.

#### Acceptance Criteria for Requirement 1

1. THE Streaming_Integration_Guide SHALL be located at `docs/guides/STREAMING_INTEGRATION.md`
2. THE Streaming_Integration_Guide SHALL open with an introduction explaining why streaming integration matters for production Senzing deployments and how it differs from the batch loading approach taught in Module 6
3. THE Streaming_Integration_Guide SHALL use a level-1 heading with the guide title, followed by an introductory paragraph, consistent with the heading and layout conventions in the Guide_Directory
4. THE Streaming_Integration_Guide SHALL maintain a conceptual focus throughout, explaining patterns and architecture rather than providing step-by-step framework setup instructions

### Requirement 2: Message Queue Consumption Patterns

**User Story:** As a bootcamper, I want to understand how to consume records from common message queues and feed them into Senzing, so that I can choose the right queue technology for my deployment.

#### Acceptance Criteria for Requirement 2

1. THE Streaming_Integration_Guide SHALL include a section covering record consumption from message queues, addressing at least Apache Kafka, RabbitMQ, and Amazon SQS
2. THE Streaming_Integration_Guide SHALL explain the general consumer pattern for each queue technology: how records are read, acknowledged, and committed, without requiring installation of any specific queue client library
3. THE Streaming_Integration_Guide SHALL describe how consumed messages are transformed into Senzing-compatible records (DATA_SOURCE, RECORD_ID, and mapped attributes) before submission to the Senzing SDK
4. THE Streaming_Integration_Guide SHALL explain the trade-offs between at-least-once and exactly-once delivery semantics and how each affects Senzing record processing (given that re-loading the same RECORD_ID replaces the existing record)

### Requirement 3: Real-Time Record Processing Through Senzing

**User Story:** As a bootcamper, I want to understand how Senzing processes records in a real-time streaming context, so that I can design a pipeline that keeps entity resolution results current as new data arrives.

#### Acceptance Criteria for Requirement 3

1. THE Streaming_Integration_Guide SHALL include a section explaining how records flow from a Streaming_Consumer through the Senzing SDK for real-time entity resolution
2. THE Streaming_Integration_Guide SHALL describe the processing lifecycle: record ingestion via `add_record`, entity resolution triggered by the new record, and redo record generation for affected entities
3. THE Streaming_Integration_Guide SHALL explain how redo processing fits into a streaming pipeline, including whether redo records should be processed inline or via a separate consumer
4. THE Streaming_Integration_Guide SHALL describe concurrency considerations: how multiple consumer threads or instances can process records in parallel when using a PostgreSQL-backed Senzing database

### Requirement 4: Backpressure Handling

**User Story:** As a bootcamper, I want to understand how to handle backpressure when Senzing processing can't keep up with the inbound message rate, so that my pipeline degrades gracefully instead of losing data or exhausting resources.

#### Acceptance Criteria for Requirement 4

1. THE Streaming_Integration_Guide SHALL include a section on Backpressure handling in streaming pipelines
2. THE Streaming_Integration_Guide SHALL explain at least three backpressure strategies: consumer-side rate limiting, queue-level buffering with retention policies, and horizontal scaling of consumer instances
3. THE Streaming_Integration_Guide SHALL describe how to detect backpressure conditions using observable metrics such as consumer lag, processing latency, and queue depth
4. THE Streaming_Integration_Guide SHALL explain the relationship between Senzing processing throughput and consumer parallelism, including how adding consumer instances affects entity resolution load

### Requirement 5: Error Handling for Streaming Pipelines

**User Story:** As a bootcamper, I want to understand how to handle errors in a streaming context, so that individual record failures do not halt the entire pipeline or cause data loss.

#### Acceptance Criteria for Requirement 5

1. THE Streaming_Integration_Guide SHALL include a section on error handling patterns specific to streaming pipelines
2. THE Streaming_Integration_Guide SHALL describe a retry strategy for transient errors (such as temporary database unavailability) with configurable retry counts and exponential backoff
3. THE Streaming_Integration_Guide SHALL describe the Dead_Letter_Queue pattern for records that fail after all retries, including what metadata to capture (original message, error details, timestamp, retry count) for later remediation
4. IF a record fails Senzing validation (malformed data, missing required fields), THEN THE Streaming_Integration_Guide SHALL recommend routing the record to a Dead_Letter_Queue rather than retrying indefinitely
5. THE Streaming_Integration_Guide SHALL explain how to monitor error rates and set alerting thresholds so that systemic issues (such as a schema change in the source system) are detected quickly

### Requirement 6: Conceptual Architecture Diagrams

**User Story:** As a bootcamper, I want visual architecture diagrams showing how streaming components connect, so that I can understand the overall pipeline structure at a glance.

#### Acceptance Criteria for Requirement 6

1. THE Streaming_Integration_Guide SHALL include at least two Mermaid_Diagrams illustrating streaming architecture
2. THE Streaming_Integration_Guide SHALL include a high-level architecture diagram showing the end-to-end flow: source systems producing messages, a Message_Queue buffering them, Streaming_Consumers processing them through Senzing, and a Dead_Letter_Queue capturing failures
3. THE Streaming_Integration_Guide SHALL include a diagram showing the error handling and retry flow: message consumption, processing attempt, retry logic, and dead-letter routing
4. WHEN including Mermaid_Diagrams, THE Streaming_Integration_Guide SHALL use fenced code blocks with the `mermaid` language identifier so that Mermaid-compatible viewers render them automatically

### Requirement 7: MCP Tool Usage for Authoritative Content

**User Story:** As a bootcamper, I want the streaming integration guide to use authoritative Senzing content, so that the patterns reflect current SDK behavior and documented best practices.

#### Acceptance Criteria for Requirement 7

1. WHEN explaining Senzing SDK behavior in a streaming context (such as `add_record` behavior, redo processing, or concurrency), THE guide author SHALL use `search_docs` from the Senzing MCP server to retrieve current documentation rather than relying on training data
2. WHEN providing example patterns or referencing Senzing streaming implementations, THE guide author SHALL use `find_examples` to locate working code from indexed Senzing GitHub repositories where applicable
3. THE Streaming_Integration_Guide SHALL include a "Further Reading" section that directs bootcampers to use `search_docs` and `find_examples` for the latest streaming integration guidance from Senzing

### Requirement 8: Module 11 Cross-Reference

**User Story:** As a bootcamper completing Module 11, I want to be pointed toward the streaming integration guide, so that I know where to learn about event-driven architectures after packaging my deployment.

#### Acceptance Criteria for Requirement 8

1. THE Module_11_Steering SHALL include a reference to the Streaming_Integration_Guide as advanced reading for production deployments
2. WHEN referencing the Streaming_Integration_Guide from Module_11_Steering, THE reference SHALL describe the guide as covering real-time streaming patterns for event-driven architectures using message queues
3. THE reference in Module_11_Steering SHALL be presented as optional further reading — it SHALL NOT be added as a required step in the Module 11 workflow

### Requirement 9: Guides README Integration

**User Story:** As a bootcamper, I want the streaming integration guide listed in the guides README, so that I can discover it from the central documentation index.

#### Acceptance Criteria for Requirement 9

1. WHEN the Streaming_Integration_Guide is created, THE Guides_README SHALL include an entry for `STREAMING_INTEGRATION.md` in the "After the Bootcamp" section or a new "Advanced Topics" section
2. WHEN listing the Streaming_Integration_Guide in the Guides_README, THE entry SHALL include the filename as a Markdown link, a bold title, and a two-to-three line description covering real-time streaming patterns, message queue integration, backpressure handling, and error management
3. THE Guides_README SHALL list `STREAMING_INTEGRATION.md` in the Documentation Structure tree under the `guides/` directory
