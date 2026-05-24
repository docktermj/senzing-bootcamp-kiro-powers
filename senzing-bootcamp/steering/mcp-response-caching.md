---
inclusion: auto
description: "Transparent MCP response caching within module session scope"
---

# MCP Response Caching

This steering file instructs the agent to cache Senzing MCP server responses within a module session. Caching reduces redundant MCP calls when the same tool is invoked with the same parameters during a single module. The cache is transparent to the bootcamper — cached and live responses are indistinguishable.

## Cache Directory

Store all cache entry files in:

```text
config/mcp_cache/
```

This path is relative to the `senzing-bootcamp/` power root. Create the directory on first cache write if it does not exist.

## Cache Key Computation

Compute the cache key as a deterministic string from the MCP tool name and its parameters:

```text
cache_key = tool_name + "|" + JSON-serialized parameters sorted by key
```

Serialization rules:
- Sort parameters dictionary by key (alphabetical, recursive for nested objects)
- Use compact JSON separators: `(',', ':')`  — no extra whitespace
- The `|` character separates tool name from parameters to prevent ambiguity

Example:

```text
tool_name: "get_entity_by_record_id"
parameters: {"data_source": "CUSTOMERS", "record_id": "1001"}

cache_key: get_entity_by_record_id|{"data_source":"CUSTOMERS","record_id":"1001"}
```

The same parameters in any insertion order produce the identical cache key because keys are sorted before serialization.

## Filename Derivation

Derive the cache entry filename from the cache key:

```text
filename = SHA-256 hex digest of cache_key (UTF-8 encoded), truncated to 16 characters + ".json"
```

Properties:
- Exactly 16 hexadecimal characters followed by `.json`
- Deterministic: same cache key always produces the same filename
- Collision-resistant for the expected cache size

Example:

```text
cache_key: get_entity_by_record_id|{"data_source":"CUSTOMERS","record_id":"1001"}
SHA-256:   a1b2c3d4e5f67890abcdef1234567890...
filename:  a1b2c3d4e5f67890.json
```

## Cache Entry Schema

Each cache entry file is a JSON object with these fields:

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
| `parameters_hash` | string | The 16-char hex digest (matches filename without `.json`) |
| `module_id` | string | The module identifier active when the entry was written |
| `timestamp` | string (ISO 8601) | When the cache entry was created |
| `response` | object | The complete MCP tool response payload |

All five fields are required. Write entries with compact JSON formatting.

## Cache Lookup Procedure

Before every MCP tool call, perform this lookup:

1. Compute the cache key from tool name and parameters
2. Derive the filename from the cache key
3. Check if `config/mcp_cache/<filename>` exists

**Cache hit** — file exists and `module_id` matches the current module:
- Parse the JSON file
- Return the `response` field directly
- Do not call the MCP server
- The bootcamper sees no difference from a live response

**Stale hit** — file exists but `module_id` does not match the current module:
- Delete the stale file
- Fall through to cache miss handling

**Cache miss** — file does not exist (or was just deleted as stale):
- Call the MCP server
- On success: write a new cache entry file with all five fields populated
- Return the response to the bootcamper

## Module Transition Invalidation

When the agent transitions to a new module (the current module identifier changes):

1. **Before any MCP calls in the new module**, delete all files in `config/mcp_cache/`
2. Count the number of entries cleared
3. Log at diagnostic level: `"Cache invalidated: {count} entries cleared"`

This ensures no data from a previous module context is ever served in the new module session. The cache starts fresh for each module.

## Error Handling

### Network Failure on Cache Miss

When the MCP server is unreachable and no valid cache entry exists:

1. Display a clear error to the bootcamper:
   ```text
   The Senzing MCP server is unreachable and no cached response is available for this request.
   ```
2. Suggest a remedy:
   ```text
   Check your network connectivity or try again in a moment.
   ```
3. **Never serve a stale or expired cache entry as fallback** — this is a hard rule. Even if stale entries exist in the cache directory, do not return them when the MCP call fails.

### Corrupted Cache File Recovery

If a cache file exists but cannot be parsed as valid JSON:

1. Delete the corrupted file silently
2. Proceed as a cache miss (call the MCP server)
3. Do not display any error to the bootcamper — recovery is transparent

### Cache Directory Creation

If `config/mcp_cache/` does not exist when a cache write is needed:

1. Create the directory (including any parent directories)
2. Write the cache entry
3. This is the expected state on first use within a session — no error or notification needed

## Diagnostic Logging

Log cache operations at diagnostic verbosity level (not shown to bootcamper unless diagnostic mode is active):

- **Cache hit**: `"Cache hit: {tool_name} [{parameters_hash}]"`
- **Cache miss**: `"Cache miss: {tool_name} [{parameters_hash}] — calling MCP server"`
- **Stale entry deleted**: `"Stale cache entry deleted: {parameters_hash} (module_id mismatch)"`
- **Cache write**: `"Cache write: {tool_name} [{parameters_hash}]"`
- **Invalidation**: `"Cache invalidated: {count} entries cleared"`
- **Corrupted file**: `"Corrupted cache file deleted: {filename}"`
- **Directory created**: `"Cache directory created: config/mcp_cache/"`
