# Senzing Entity Resolution Glossary

> For detailed documentation on any term, use the `search_docs` MCP tool. This glossary provides quick definitions for common terms encountered during the boot camp.

---

**Attribute**
A specific piece of data within a feature. For example, a NAME feature contains attributes like `NAME_FIRST`, `NAME_LAST`, and `NAME_MIDDLE`. An ADDRESS feature contains `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, etc.

**Candidate**
A potential match identified during the scoring phase of entity resolution. Senzing finds candidates by looking up features in its internal indexes, then scores them to determine whether they truly match.

**CORD (Collections Of Relatable Data)**
Sample datasets provided by Senzing for testing and evaluation. Available datasets include Las Vegas, London, and Moscow, each containing real-world data from multiple sources useful for exploring entity resolution behavior.

**Cross-source match**
When records from different data sources resolve to the same entity. For example, a record from `CUSTOMERS_CRM` and a record from `VENDORS_ERP` resolving together because they represent the same person.

**Data source**
A named collection of records from a single system, such as `CUSTOMERS_CRM` or `WATCHLIST_FBI`. Every record loaded into Senzing must belong to a data source. Data source names are registered in the Senzing configuration before loading.

**Entity**
Senzing's resolved view of a real-world person or organization, composed of one or more records. An entity represents the "truth" that Senzing has determined from all available evidence across data sources.

**Entity ID**
Senzing's internal numeric identifier for a resolved entity. Entity IDs can change as new data is loaded and entities merge or split, so they should not be used as permanent external references.

**Entity resolution**
The process of determining which records refer to the same real-world entity. Senzing compares features across records to find matches, then groups matching records into entities.

**Feature**
A category of identifying information used during entity resolution. Examples include NAME, ADDRESS, PHONE, EMAIL, DOB, and SSN. Each feature contains one or more attributes and has its own matching rules.

**How entity**
An SDK operation (`how_entity_by_entity_id`) that shows the step-by-step resolution process for an entity. It reveals the order in which records were added and how each merge decision was made over time.

**Match key**
The combination of features that caused two records to match. Expressed as a string like `+NAME+ADDRESS+PHONE`, indicating which features contributed to the match decision.

**Match level**
The strength of a relationship between records. Levels include: resolved (same entity), possibly same (likely the same but not certain), possibly related (may be related, such as family members), and name only (names match but insufficient corroborating data).

**Record**
A single input row from a data source, uniquely identified by the combination of `DATA_SOURCE` and `RECORD_ID`. A record contains features (names, addresses, etc.) that Senzing uses for entity resolution.

**Record ID**
A unique identifier for a record within its data source. Combined with the data source name, it forms the globally unique key (`DATA_SOURCE` + `RECORD_ID`) used to reference a specific record in Senzing.

**Redo record**
A deferred re-evaluation queued when new data affects existing entity resolution decisions. When loading a record changes the scoring landscape for previously resolved entities, Senzing queues redo records so those entities can be re-evaluated.

**Resolution**
The act of determining that two or more records represent the same entity. When Senzing resolves records together, it merges them into a single entity and assigns them a shared Entity ID.

**SGES (Senzing Generic Entity Specification)**
The standard JSON format for records loaded into Senzing. Every record must include `DATA_SOURCE` and `RECORD_ID` fields, along with feature data mapped to Senzing's attribute names.

**Why entity**
An SDK operation (`why_entities` / `why_record_in_entity`) that explains why specific records resolved to the same entity. It shows the features that matched, the match key, and the scoring details behind the resolution decision.
