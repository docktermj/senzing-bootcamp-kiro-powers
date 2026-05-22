# Requirements Document

## Introduction

MCP Response Caching adds a transparent caching layer for Senzing MCP server tool responses during bootcamp sessions. The agent manages cache files directly in the user workspace, guided by a steering file. Cached responses reduce redundant MCP calls within a module session, improving responsiveness. The cache is keyed by tool name plus parameters, scoped to the current module session (invalidated on module boundary), and fails with a clear error rather than serving stale data.

## Glossary

- **Cache_Steering_File**: The steering file at `senzing-bootcamp/steering/mcp-response-caching.md` with `inclusion: auto` frontmatter that instructs the agent on caching behavior.
- **Cache_Directory**: The directory `config/mcp_cache/` within the `senzing-bootcamp/` power root where cached MCP responses are stored as JSON files at runtime.
- **Cache_Key**: A deterministic identifier derived from the MCP tool name concatenated with its serialized parameters, used to locate a cached response file.
- **Module_Session**: The period during which a bootcamper is actively working within a single bootcamp module; a new module session begins when the agent transitions to a different module.
- **Cache_Entry**: A single JSON file in the Cache_Directory containing the cached response payload and metadata (tool name, parameters hash, module identifier, timestamp).
- **Steering_Index**: The file `senzing-bootcamp/steering/steering-index.yaml` that registers all steering files with their token counts and keyword mappings.
- **Gitignore_File**: The repository `.gitignore` file that excludes runtime artifacts from version control.

## Requirements

### Requirement 1: Steering File Creation

**User Story:** As a power maintainer, I want a steering file that instructs the agent on MCP response caching behavior, so that caching logic is declarative and maintainable.

#### Acceptance Criteria

1. THE Cache_Steering_File SHALL reside at path `senzing-bootcamp/steering/mcp-response-caching.md`.
2. THE Cache_Steering_File SHALL contain YAML frontmatter with `inclusion: auto`.
3. THE Cache_Steering_File SHALL define the Cache_Directory path as `config/mcp_cache/`.
4. THE Cache_Steering_File SHALL specify that the Cache_Key is computed from the MCP tool name concatenated with the JSON-serialized parameters sorted by key.
5. THE Cache_Steering_File SHALL specify that cache entries are invalidated when the agent transitions to a different module (module boundary).
6. THE Cache_Steering_File SHALL instruct the agent to create the Cache_Directory on first cache write if the directory does not exist.

### Requirement 2: Cache Storage Format

**User Story:** As a power maintainer, I want cached responses stored in a predictable file format, so that the agent can reliably read and write cache entries.

#### Acceptance Criteria

1. WHEN the agent writes a Cache_Entry, THE Cache_Steering_File SHALL instruct the agent to store the entry as a JSON file in the Cache_Directory.
2. THE Cache_Steering_File SHALL specify that each Cache_Entry file contains the fields: `tool_name`, `parameters_hash`, `module_id`, `timestamp`, and `response`.
3. THE Cache_Steering_File SHALL specify that the Cache_Entry filename is derived from the Cache_Key using a deterministic hash (SHA-256 hex digest, truncated to 16 characters).
4. THE Cache_Steering_File SHALL specify that all MCP tool responses are cached uniformly with the same TTL policy (module session scope).

### Requirement 3: Cache Lookup Behavior

**User Story:** As a bootcamper, I want MCP responses served from cache when available within my current module session, so that repeated queries respond faster without visible difference.

#### Acceptance Criteria

1. WHEN the agent prepares to call an MCP tool, THE agent SHALL first compute the Cache_Key and check for a matching Cache_Entry in the Cache_Directory.
2. WHEN a matching Cache_Entry exists and the `module_id` matches the current Module_Session, THE agent SHALL use the cached response instead of calling the MCP server.
3. WHEN a matching Cache_Entry exists but the `module_id` does not match the current Module_Session, THE agent SHALL treat the entry as expired and delete the stale Cache_Entry file.
4. THE Cache_Steering_File SHALL instruct the agent to perform caching transparently so that the bootcamper observes no difference in behavior between cached and live responses.

### Requirement 4: Cache Miss with Network Failure

**User Story:** As a bootcamper, I want a clear error message when the MCP server is unreachable and no valid cache exists, so that I understand the problem and can take action.

#### Acceptance Criteria

1. IF a cache miss occurs and the MCP server call fails due to network error, THEN THE agent SHALL report a clear error message to the bootcamper indicating the MCP server is unreachable.
2. IF a cache miss occurs and the MCP server call fails, THEN THE agent SHALL NOT serve an expired or stale Cache_Entry as a fallback.
3. IF a cache miss occurs and the MCP server call fails, THEN THE agent SHALL suggest the bootcamper check network connectivity or retry.

### Requirement 5: Cache Invalidation at Module Boundary

**User Story:** As a power maintainer, I want the cache invalidated when the bootcamper transitions between modules, so that stale data from a previous module context is never used.

#### Acceptance Criteria

1. WHEN the agent transitions to a new module, THE agent SHALL invalidate all Cache_Entry files by deleting the contents of the Cache_Directory.
2. THE Cache_Steering_File SHALL specify that invalidation occurs before any MCP calls in the new module session.
3. THE Cache_Steering_File SHALL instruct the agent to log the invalidation action (number of entries cleared) at diagnostic verbosity level.

### Requirement 6: Steering Index Registration

**User Story:** As a power maintainer, I want the caching steering file registered in the steering index, so that the agent framework can discover and load the file.

#### Acceptance Criteria

1. THE Steering_Index SHALL contain a keyword entry mapping `cache` to `mcp-response-caching.md`.
2. THE Steering_Index SHALL contain a keyword entry mapping `mcp cache` to `mcp-response-caching.md`.
3. THE Steering_Index SHALL contain a `file_metadata` entry for `mcp-response-caching.md` with accurate `token_count` and `size_category` values.

### Requirement 7: Gitignore Configuration

**User Story:** As a power maintainer, I want the cache directory excluded from version control, so that runtime cache files are never committed to the repository.

#### Acceptance Criteria

1. THE Gitignore_File SHALL contain an entry that excludes `senzing-bootcamp/config/mcp_cache/` from version control.
2. THE Gitignore_File SHALL include a comment indicating the entry is for MCP response cache runtime state.
