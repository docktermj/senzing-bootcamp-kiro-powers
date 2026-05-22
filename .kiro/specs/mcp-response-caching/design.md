# Design Document: MCP Response Caching

## Overview

This feature adds a transparent MCP response caching layer to the senzing-bootcamp power, implemented entirely through a steering file and supporting configuration. No Python scripts are introduced. The agent follows steering file instructions to manage cache files directly in the user workspace, reducing redundant MCP calls within a module session.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Agent Runtime                                          │
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Steering Engine   │───▶│ mcp-response-caching.md  │   │
│  │ (auto-inclusion)  │    │ (behavioral rules)       │   │
│  └──────────────────┘    └──────────────────────────┘   │
│           │                         │                    │
│           ▼                         ▼                    │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Cache Lookup      │    │ Cache Write              │   │
│  │ (compute key,     │    │ (serialize entry,        │   │
│  │  check file)      │    │  write JSON file)        │   │
│  └────────┬─────────┘    └──────────────────────────┘   │
│           │                                              │
│           ▼                                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │ config/mcp_cache/                                 │   │
│  │ ├── <16-char-hex>.json  (cache entry files)       │   │
│  │ ├── <16-char-hex>.json                            │   │
│  │ └── ...                                           │   │
│  └──────────────────────────────────────────────────┘   │
│           │                                              │
│           ▼                                              │
│  ┌──────────────────┐                                   │
│  │ Senzing MCP      │                                   │
│  │ Server           │                                   │
│  │ (mcp.senzing.com)│                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. Agent receives an MCP tool call request
2. Steering file (auto-loaded) instructs the agent to intercept the call
3. Agent computes the cache key from tool name + sorted serialized parameters
4. Agent derives the filename via SHA-256 hex digest truncated to 16 characters
5. Agent checks `config/mcp_cache/<filename>.json` for a matching entry
6. **Cache hit** (file exists, module_id matches): return cached `response` field
7. **Stale hit** (file exists, module_id mismatch): delete file, proceed as miss
8. **Cache miss**: call MCP server, write response to cache file, return response
9. **Cache miss + network failure**: report error, never serve stale data

## Components and Interfaces

### 1. Steering File (`senzing-bootcamp/steering/mcp-response-caching.md`)

The primary deliverable. This markdown file with YAML frontmatter instructs the agent on all caching behavior. It uses `inclusion: auto` so it is always active during bootcamp sessions.

**Structure:**
- YAML frontmatter with `inclusion: auto` and `description`
- Cache configuration section (directory path, key computation algorithm)
- Cache write procedure (entry format, filename derivation)
- Cache lookup procedure (hit/miss/stale logic)
- Cache invalidation rules (module boundary behavior)
- Error handling instructions (network failure, no stale fallback)
- Diagnostic logging instructions

### 2. Cache Directory (`senzing-bootcamp/config/mcp_cache/`)

A runtime directory created by the agent on first cache write. Contains JSON cache entry files. Excluded from version control via `.gitignore`.

### 3. Steering Index Registration

Two keyword entries (`cache`, `mcp cache`) and a `file_metadata` entry in `steering-index.yaml` enable the agent framework to discover the steering file.

### 4. Gitignore Entry

A new exclusion pattern in `.gitignore` prevents cache files from being committed.

### Interfaces

### Cache Key Computation

The cache key is a deterministic string derived from:

```
cache_key = tool_name + "|" + json.dumps(parameters, sort_keys=True, separators=(',', ':'))
```

**Properties:**
- Deterministic: same tool + same parameters (regardless of insertion order) → same key
- Unique: different tool names or different parameter values → different keys
- The `|` separator prevents ambiguity between tool name and parameters

### Cache Entry Filename

```
filename = sha256(cache_key.encode('utf-8')).hexdigest()[:16] + ".json"
```

**Properties:**
- Exactly 16 hex characters + `.json` extension
- Deterministic: same cache key → same filename
- Collision-resistant: SHA-256 provides sufficient entropy for the expected cache size

### Cache Entry Schema

Each `.json` file in the cache directory contains:

```json
{
  "tool_name": "get_entity_by_record_id",
  "parameters_hash": "a1b2c3d4e5f67890",
  "module_id": "module-05",
  "timestamp": "2025-01-15T10:30:00Z",
  "response": { ... }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | string | The MCP tool name that was called |
| `parameters_hash` | string | The 16-char hex digest of the cache key (matches filename without extension) |
| `module_id` | string | The module identifier active when the entry was written |
| `timestamp` | string (ISO 8601) | When the cache entry was created |
| `response` | object | The complete MCP tool response payload |

### Cache Lookup Decision Logic

```
IF file exists at config/mcp_cache/<hash>.json:
    entry = parse JSON file
    IF entry.module_id == current_module_id:
        RETURN entry.response  (cache hit)
    ELSE:
        DELETE file  (stale entry)
        FALL THROUGH to cache miss
        
CACHE MISS:
    result = call MCP server
    IF success:
        write cache entry to config/mcp_cache/<hash>.json
        RETURN result
    IF network failure:
        report error to bootcamper
        suggest connectivity check / retry
        DO NOT serve any stale entry
```

### Module Transition Invalidation

```
ON module transition (current_module changes):
    BEFORE any MCP calls in new module:
        count = number of files in config/mcp_cache/
        DELETE all files in config/mcp_cache/
        LOG at diagnostic level: "Cache invalidated: {count} entries cleared"
```

## Data Models

### Steering File Frontmatter

```yaml
---
inclusion: auto
description: "Transparent MCP response caching within module session scope"
---
```

### Steering Index Additions

```yaml
# In keywords section:
keywords:
  cache: mcp-response-caching.md
  mcp cache: mcp-response-caching.md

# In file_metadata section:
file_metadata:
  mcp-response-caching.md:
    token_count: <measured>
    size_category: <small|medium|large>
```

### Gitignore Addition

```gitignore
# MCP response cache runtime state
senzing-bootcamp/config/mcp_cache/
```

## Error Handling

### Network Failure on Cache Miss

When the MCP server is unreachable and no valid cache entry exists:

1. Agent displays a clear error: "The Senzing MCP server is unreachable and no cached response is available for this request."
2. Agent suggests: "Check your network connectivity or try again in a moment."
3. Agent does NOT fall back to any stale/expired cache entry — this is a hard rule to prevent serving data from a different module context.

### Corrupted Cache Entry

If a cache file exists but cannot be parsed as valid JSON:

1. Agent deletes the corrupted file
2. Agent proceeds as a cache miss (calls MCP server)
3. No error is shown to the bootcamper (transparent recovery)

### Cache Directory Missing

If `config/mcp_cache/` does not exist when a cache write is needed:

1. Agent creates the directory
2. Agent writes the cache entry
3. This is the expected state on first use within a session

## Testing Strategy

### Property-Based Tests

Property-based tests validate the core caching logic (key computation, filename derivation, schema round-trip, lookup correctness) using Hypothesis to generate random tool names, parameter dictionaries, module IDs, and cache entry payloads. These tests run in `senzing-bootcamp/tests/test_mcp_response_caching.py`.

**What to test with PBT:**
- Cache key determinism across parameter insertion orders
- Cache entry JSON round-trip preserving all required fields
- Filename derivation producing valid 16-char hex strings deterministically
- Lookup logic correctly distinguishing hits from stale misses based on module_id
- Invalidation clearing all entries regardless of count or content

### Example-Based Tests

Example-based tests cover specific scenarios and error conditions:
- Network failure produces correct error message with retry suggestion
- Corrupted JSON file is deleted and treated as cache miss
- Cache directory creation on first write
- Steering file content contains all required sections and instructions

### Smoke Tests

Smoke tests verify static configuration:
- Steering file exists at correct path with correct frontmatter
- Steering index contains keyword mappings and file_metadata entry
- Gitignore contains the cache directory exclusion with comment

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cache key determinism

*For any* MCP tool name and *for any* parameters dictionary, computing the cache key with the parameters in any insertion order SHALL produce the identical cache key string.

**Validates: Requirements 1.4**

### Property 2: Cache entry schema round-trip

*For any* valid cache entry (containing tool_name, parameters_hash, module_id, timestamp, and response), serializing the entry to JSON and deserializing it back SHALL produce an equivalent object with all five fields preserved.

**Validates: Requirements 2.2**

### Property 3: Filename derivation determinism and format

*For any* cache key string, the derived filename SHALL be exactly 16 hexadecimal characters followed by `.json`, and computing the filename multiple times from the same cache key SHALL always produce the same result.

**Validates: Requirements 2.3**

### Property 4: Cache lookup correctness

*For any* cache entry file in the cache directory and *for any* current module_id, the lookup SHALL return the cached response if and only if the entry's module_id matches the current module_id. When the module_id does not match, the stale entry file SHALL be deleted.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: No stale fallback on failure

*For any* cache miss scenario where the MCP server call fails, the system SHALL NOT return any previously cached response (even if stale entries exist in the cache directory), regardless of the number or content of stale entries present.

**Validates: Requirements 4.2**

### Property 6: Module transition clears all entries

*For any* non-empty set of cache entry files in the cache directory, when a module transition occurs, all cache entry files SHALL be deleted before any MCP calls are made in the new module session.

**Validates: Requirements 5.1, 5.2**
