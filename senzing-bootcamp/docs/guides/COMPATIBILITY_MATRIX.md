# Senzing Compatibility Matrix

## Senzing Version Support

This boot camp uses Senzing V4.0 exclusively.

| Feature | Senzing 4.0 | Notes |
|---------|-------------|-------|
| **Core Engine** | ✅ | Full support |
| **SQLite** | ✅ | Evaluation only |
| **PostgreSQL** | ✅ | Production recommended |
| **MySQL** | ✅ | Supported |
| **MSSQL** | ✅ | Supported |
| **Oracle** | ✅ | Enterprise only |
| **Python SDK** | ✅ | Python 3.8+ |
| **Java SDK** | ✅ | Java 11+ |
| **C# SDK** | ✅ | .NET 6+ |
| **Rust SDK** | ✅ | V4 only |
| **REST API** | ✅ | Full support |
| **Batch Loading** | ✅ | Full support |
| **Real-time Loading** | ✅ | Full support |
| **Export** | ✅ | Full support |
| **Why Analysis** | ✅ | Enhanced in V4 |
| **Virtual Entities** | ✅ | Full support |
| **Redo Processing** | ✅ | Enhanced in V4 |

## Platform Support

| Platform | Senzing 4.0 | Recommended |
|----------|-------------|-------------|
| **Ubuntu 20.04** | ✅ | ✅ |
| **Ubuntu 22.04** | ✅ | ✅ |
| **RHEL 8** | ✅ | ✅ |
| **RHEL 9** | ✅ | ✅ |
| **Debian 11** | ✅ | ✅ |
| **macOS Intel** | ✅ | Dev only |
| **macOS ARM** | ✅ | Dev only |
| **Windows (WSL2)** | ✅ | Dev only |
| **Docker** | ✅ | ✅ |

## Database Versions

| Database | Min Version | Recommended | Max Tested |
|----------|-------------|-------------|------------|
| **PostgreSQL** | 11 | 14+ | 16 |
| **MySQL** | 5.7 | 8.0+ | 8.2 |
| **MSSQL** | 2017 | 2019+ | 2022 |
| **Oracle** | 12c | 19c+ | 21c |
| **SQLite** | 3.24 | 3.40+ | 3.44 |

## Python Package Versions

| Package | Min Version | Recommended | Notes |
|---------|-------------|-------------|-------|
| **Python** | 3.8 | 3.11+ | 3.12 supported |
| **senzing** | 4.0.0 | 4.0.0+ | Latest stable |
| **psycopg2** | 2.8 | 2.9+ | PostgreSQL |
| **pymysql** | 0.9 | 1.0+ | MySQL |
| **pyodbc** | 4.0 | 4.0+ | MSSQL |

## Boot Camp Module Compatibility

All modules are designed for Senzing V4.0.

| Module | V4.0 | Notes |
|--------|------|-------|
| Module 0 | ✅ | Full support |
| Module 1 | ✅ | Full support |
| Module 2 | ✅ | Full support |
| Module 3 | ✅ | Full support |
| Module 4 | ✅ | Use mapping_workflow |
| Module 5 | ✅ | Platform-specific |
| Module 6 | ✅ | Full support |
| Module 7 | ✅ | Full support |
| Module 8 | ✅ | Enhanced in V4 |
| Module 9 | ✅ | Full support |
| Module 10 | ✅ | Full support |
| Module 11 | ✅ | Full support |
| Module 12 | ✅ | Full support |

## Version History

- **v3.0.0** (2026-03-17): Compatibility matrix created
