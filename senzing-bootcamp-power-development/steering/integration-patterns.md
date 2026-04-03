---
inclusion: manual
---

# Integration Patterns for Module 8

Common patterns for integrating Senzing query results into your applications and workflows.

## Overview

After loading data (Modules 6-7), you need to integrate entity resolution into your business processes. This guide covers common integration patterns for Module 8.

## Pattern 1: Batch Report

**Use Case**: Generate daily/weekly reports of resolved entities

**When to Use**:

- Periodic reporting needs
- Data warehouse integration
- Offline analysis
- Compliance reporting

**Implementation**:

Iterate over your known record IDs (from your loaded data sources) and retrieve each entity individually. This scales to large data sets without requiring a full entity export.

```python
# src/query/batch_report.py
import json
from senzing import SzEngine
from datetime import datetime

def report_entities_by_records(record_ids, data_source, output_file):
    """Report resolved entities by iterating over known record IDs"""
    engine = SzEngine(instance_name="BATCH_REPORT", settings={})
    # ... initialize engine with proper settings ...

    seen_entity_ids = set()

    with open(output_file, 'w') as f:
        for record_id in record_ids:
            try:
                response = engine.get_entity_by_record_id(data_source, record_id)
                entity = json.loads(response)
                entity_id = entity['RESOLVED_ENTITY']['ENTITY_ID']

                # Deduplicate — only write each entity once
                if entity_id not in seen_entity_ids:
                    seen_entity_ids.add(entity_id)
                    f.write(json.dumps(entity) + '\n')
            except Exception as e:
                print(f"Error retrieving entity for {record_id}: {e}")

    print(f"Wrote {len(seen_entity_ids)} unique entities to {output_file}")

if __name__ == "__main__":
    # Load record IDs from your source data
    record_ids = []  # Populate from your data source
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_entities_by_records(record_ids, "CUSTOMERS", f"exports/entities_{timestamp}.jsonl")
```

> **Note**: Use `generate_scaffold` and `get_sdk_reference` from the Senzing MCP server for current method signatures. The code above is illustrative — always verify against the MCP server.

**Scheduling**:

```bash
# Add to crontab for daily report at 2 AM
0 2 * * * cd /path/to/project && python src/query/batch_report.py
```

## Pattern 2: REST API

**Use Case**: Real-time entity lookup from web applications

**When to Use**:

- Web applications need entity data
- Microservices architecture
- Real-time customer lookup
- Integration with multiple systems

**Implementation**:

```python
# src/query/entity_api.py
from flask import Flask, jsonify, request
from senzing import G2Engine
import json

app = Flask(__name__)
engine = G2Engine()
# ... initialize engine ...

@app.route('/entity/<entity_id>', methods=['GET'])
def get_entity(entity_id):
    """Get entity by ID"""
    try:
        response = engine.getEntityByEntityID(int(entity_id))
        return jsonify(json.loads(response))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
def search_entities():
    """Search for entities by attributes"""
    try:
        search_attrs = request.json
        response = engine.searchByAttributes(json.dumps(search_attrs))
        return jsonify(json.loads(response))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/record/<data_source>/<record_id>', methods=['GET'])
def get_record(data_source, record_id):
    """Get which entity a record belongs to"""
    try:
        response = engine.getEntityByRecordID(data_source, record_id)
        return jsonify(json.loads(response))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Deployment**:

```bash
# Run with gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 src.query.entity_api:app
```

## Pattern 3: Streaming/Event-Driven

**Use Case**: Process entity resolution events in real-time

**When to Use**:

- Event-driven architecture
- Real-time fraud detection
- Immediate alerts on matches
- Kafka/message queue integration

**Implementation**:

```python
# src/query/stream_processor.py
from kafka import KafkaConsumer, KafkaProducer
from senzing import G2Engine
import json

def process_entity_events():
    """Process entity resolution events from Kafka"""
    consumer = KafkaConsumer(
        'entity-events',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    engine = G2Engine()
    # ... initialize engine ...

    for message in consumer:
        event = message.value

        if event['type'] == 'RECORD_ADDED':
            # Get the entity this record belongs to
            entity_response = engine.getEntityByRecordID(
                event['data_source'],
                event['record_id']
            )
            entity = json.loads(entity_response)

            # Check if this is a duplicate
            if len(entity['RESOLVED_ENTITY']['RECORDS']) > 1:
                # Publish duplicate alert
                producer.send('duplicate-alerts', {
                    'entity_id': entity['RESOLVED_ENTITY']['ENTITY_ID'],
                    'record_count': len(entity['RESOLVED_ENTITY']['RECORDS']),
                    'timestamp': event['timestamp']
                })

if __name__ == "__main__":
    process_entity_events()
```

## Pattern 4: Database Sync

**Use Case**: Keep a downstream database in sync with resolved entities

**When to Use**:

- Data warehouse integration
- BI tool integration
- Legacy system integration
- Master data management

**Implementation**:

Iterate over known record IDs from your loaded data sources and upsert each resolved entity into the target database.

```python
# src/query/db_sync.py
import psycopg2
from senzing import SzEngine
import json

def sync_entities_to_postgres(record_ids, data_source):
    """Sync resolved entities to PostgreSQL by iterating over known records"""
    # Connect to target database
    conn = psycopg2.connect(
        host="localhost",
        database="warehouse",
        user="user",
        password="password"
    )
    cur = conn.cursor()

    # Initialize Senzing
    engine = SzEngine(instance_name="DB_SYNC", settings={})
    # ... initialize engine with proper settings ...

    seen_entity_ids = set()
    synced_count = 0

    for record_id in record_ids:
        try:
            response = engine.get_entity_by_record_id(data_source, record_id)
            entity = json.loads(response)
            entity_id = entity['RESOLVED_ENTITY']['ENTITY_ID']

            # Skip entities we've already synced
            if entity_id in seen_entity_ids:
                continue
            seen_entity_ids.add(entity_id)

            records = entity['RESOLVED_ENTITY']['RECORDS']

            # Upsert to target database
            cur.execute("""
                INSERT INTO entities (entity_id, record_count, data, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (entity_id)
                DO UPDATE SET
                    record_count = EXCLUDED.record_count,
                    data = EXCLUDED.data,
                    updated_at = NOW()
            """, (entity_id, len(records), json.dumps(entity)))
            synced_count += 1
        except Exception as e:
            print(f"Error syncing record {record_id}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Synced {synced_count} unique entities to warehouse")

if __name__ == "__main__":
    record_ids = []  # Populate from your data source
    sync_entities_to_postgres(record_ids, "CUSTOMERS")
```

> **Note**: Use `generate_scaffold` and `get_sdk_reference` from the Senzing MCP server for current method signatures.

## Pattern 5: Duplicate Detection Service

**Use Case**: Find and report duplicates for data stewardship

**When to Use**:

- Data quality initiatives
- Duplicate cleanup projects
- Master data management
- Customer service tools

**Implementation**:

Iterate over known record IDs for a data source and identify entities that contain multiple records from that source.

```python
# src/query/find_duplicates.py
from senzing import SzEngine
import json
import csv

def find_duplicates_by_datasource(data_source, record_ids, output_file):
    """Find all duplicate entities for a data source"""
    engine = SzEngine(instance_name="FIND_DUPES", settings={})
    # ... initialize engine with proper settings ...

    seen_entity_ids = set()
    duplicates = []

    for record_id in record_ids:
        try:
            response = engine.get_entity_by_record_id(data_source, record_id)
            entity = json.loads(response)
            entity_id = entity['RESOLVED_ENTITY']['ENTITY_ID']

            # Skip entities we've already checked
            if entity_id in seen_entity_ids:
                continue
            seen_entity_ids.add(entity_id)

            records = entity['RESOLVED_ENTITY']['RECORDS']

            # Filter for entities with multiple records from this source
            source_records = [r for r in records if r['DATA_SOURCE'] == data_source]

            if len(source_records) > 1:
                duplicates.append({
                    'entity_id': entity_id,
                    'duplicate_count': len(source_records),
                    'record_ids': [r['RECORD_ID'] for r in source_records],
                    'best_name': entity['RESOLVED_ENTITY'].get('ENTITY_NAME', 'Unknown')
                })
        except Exception as e:
            print(f"Error checking record {record_id}: {e}")

    # Write to CSV for review
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['entity_id', 'duplicate_count', 'record_ids', 'best_name'])
        writer.writeheader()
        writer.writerows(duplicates)

    print(f"Found {len(duplicates)} entities with duplicates")
    return duplicates

if __name__ == "__main__":
    record_ids = []  # Populate from your data source
    dupes = find_duplicates_by_datasource('CUSTOMER_DB', record_ids, 'reports/duplicates.csv')
```

> **Note**: Use `generate_scaffold` and `get_sdk_reference` from the Senzing MCP server for current method signatures.

## Pattern 6: Watchlist Screening

**Use Case**: Screen entities against watchlists or sanctions lists

**When to Use**:

- Compliance requirements
- KYC/AML processes
- Fraud prevention
- Risk management

**Implementation**:

```python
# src/query/watchlist_screening.py
from senzing import G2Engine
import json

def screen_against_watchlist(entity_id, watchlist_datasource='WATCHLIST'):
    """Check if an entity matches any watchlist entries"""
    engine = G2Engine()
    # ... initialize engine ...

    # Get the entity
    entity_response = engine.getEntityByEntityID(entity_id)
    entity = json.loads(entity_response)

    # Check if any records are from watchlist
    records = entity['RESOLVED_ENTITY']['RECORDS']
    watchlist_matches = [r for r in records if r['DATA_SOURCE'] == watchlist_datasource]

    if watchlist_matches:
        return {
            'match': True,
            'entity_id': entity_id,
            'watchlist_records': watchlist_matches,
            'risk_level': 'HIGH'
        }

    # Check for possible relationships to watchlist entities
    # (implement relationship checking logic here)

    engine.destroy()
    return {'match': False, 'entity_id': entity_id}

if __name__ == "__main__":
    result = screen_against_watchlist(12345)
    print(json.dumps(result, indent=2))
```

## Pattern 7: GraphQL API

**Use Case**: Flexible querying for modern web applications

**When to Use**:

- React/Vue/Angular frontends
- Mobile applications
- Flexible query requirements
- Developer-friendly API

**Implementation**:

```python
# src/query/graphql_api.py
from ariadne import QueryType, make_executable_schema, graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify
from senzing import G2Engine
import json

type_defs = """
    type Query {
        entity(id: Int!): Entity
        searchEntities(name: String, address: String): [Entity]
    }

    type Entity {
        entityId: Int!
        entityName: String
        records: [Record]
    }

    type Record {
        dataSource: String!
        recordId: String!
    }
"""

query = QueryType()
engine = G2Engine()
# ... initialize engine ...

@query.field("entity")
def resolve_entity(_, info, id):
    response = engine.getEntityByEntityID(id)
    entity = json.loads(response)
    return {
        'entityId': entity['RESOLVED_ENTITY']['ENTITY_ID'],
        'entityName': entity['RESOLVED_ENTITY'].get('ENTITY_NAME'),
        'records': entity['RESOLVED_ENTITY']['RECORDS']
    }

@query.field("searchEntities")
def resolve_search(_, info, name=None, address=None):
    search_attrs = {}
    if name:
        search_attrs['NAME_FULL'] = name
    if address:
        search_attrs['ADDR_FULL'] = address

    response = engine.searchByAttributes(json.dumps(search_attrs))
    results = json.loads(response)
    return results.get('RESOLVED_ENTITIES', [])

schema = make_executable_schema(type_defs, query)
app = Flask(__name__)

@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return PLAYGROUND_HTML, 200

@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema, data, context_value=request)
    return jsonify(result), 200 if success else 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
```

## Choosing the Right Pattern

| Pattern             | Real-time | Complexity | Best For                       |
|---------------------|-----------|------------|--------------------------------|
| Batch Report        | No        | Low        | Reports, analytics             |
| REST API            | Yes       | Medium     | Web apps, microservices        |
| Streaming           | Yes       | High       | Event-driven, real-time alerts |
| Database Sync       | No        | Medium     | Data warehouses, BI tools      |
| Duplicate Detection | No        | Low        | Data quality, stewardship      |
| Watchlist Screening | Yes       | Medium     | Compliance, risk management    |
| GraphQL API         | Yes       | Medium     | Modern web/mobile apps         |

## When to Load This Guide

Load this steering file when:

- Starting Module 8
- User asks about integration
- User asks "how do I use the results?"
- Planning application integration
- Planning production deployment
- Designing application architecture
