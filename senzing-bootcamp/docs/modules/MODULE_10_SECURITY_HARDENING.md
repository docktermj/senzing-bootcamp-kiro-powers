```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 10: SECURITY HARDENING  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 10: Security Hardening

> **Agent workflow:** The agent follows `steering/module-10-security.md` for this module's step-by-step workflow.

## Overview

Module 10 focuses on securing your entity resolution application for production deployment. This module ensures your solution follows security best practices.

## Purpose

After performance testing in Module 9, Module 10 helps you:

1. **Implement secrets management** (no hardcoded credentials)
2. **Configure API authentication/authorization**
3. **Enable data encryption** (at rest and in transit)
4. **Ensure PII handling compliance** (GDPR, CCPA, HIPAA)
5. **Run security scanning** (dependency vulnerabilities)
6. **Conduct vulnerability assessment**
7. **Document security audit**

## Security Checklist

### 1. Secrets Management

❌ **Bad**: Hardcoded credentials

```text
DATABASE_URL = "postgresql://user:password123@localhost/senzing"
```

✅ **Good**: Environment variables

```text
Read DATABASE_URL from environment variable
```

✅ **Better**: Secrets manager

```text
Retrieve "prod/senzing/database_url" from secrets manager service
```

**Tools**:

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Secrets
- Environment variables (minimum)

### 2. API Authentication

Implement authentication for all APIs:

```text
function require_api_key(handler):
    Extract "X-API-Key" header from request
    If key is missing or invalid:
        Return 401 Unauthorized
    Otherwise:
        Proceed to handler

Route GET /api/search through require_api_key:
    function search():
        // Protected endpoint logic
```

**Authentication Methods**:

- API Keys
- OAuth 2.0
- JWT tokens
- mTLS (mutual TLS)

### 3. Data Encryption

**At Rest**:

- Database encryption (PostgreSQL: pgcrypto, TDE)
- File system encryption
- Backup encryption

**In Transit**:

- HTTPS/TLS for all connections
- Database SSL connections
- VPN for internal traffic

```text
Connect to database with SSL mode = "require"
Example connection string: "postgresql://user:pass@host/db?sslmode=require"
```

### 4. PII Handling Compliance

**GDPR Requirements**:

- Right to access
- Right to erasure
- Data minimization
- Consent management
- Breach notification

**Implementation**:

```text
function anonymize_pii(record):
    If environment is not "production":
        Mask SSN_NUMBER: keep last 4 digits, replace rest with "XXX-XX-"
        Hash EMAIL_ADDRESS
    Return record
```

### 5. Security Scanning

**Dependency Scanning**:

```bash
# Use the appropriate scanner for your language:
# Python:     pip install safety && safety check
# Node.js:    npm audit
# Java:       mvn dependency-check:check
# C#:         dotnet list package --vulnerable
# Rust:       cargo audit
```

**Container Scanning**:

```bash
# Trivy
trivy image my-senzing-app:latest
```

**Code Scanning**:

```bash
# Use the appropriate static analysis tool for your language:
# Python:     bandit -r src/
# Java:       spotbugs, PMD
# C#:         Roslyn analyzers
# Rust:       cargo clippy
# TypeScript: eslint --ext .ts src/
# General:    SonarQube (sonar-scanner)
```

### 6. Network Security

**Firewall Rules**:

- Allow only necessary ports
- Restrict database access to application servers
- Use security groups/network policies

**Example AWS Security Group**:

```yaml
SecurityGroup:
  Ingress:
    - Port: 443
      Source: 0.0.0.0/0  # HTTPS from anywhere
    - Port: 5432
      Source: 10.0.0.0/16  # PostgreSQL from VPC only
```

### 7. Access Control

**Principle of Least Privilege**:

- Application uses read-only database user for queries
- Separate users for loading vs querying
- Admin access only when needed

```sql
-- Read-only user for queries
CREATE USER senzing_query WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO senzing_query;

-- Write user for loading
CREATE USER senzing_load WITH PASSWORD 'secure_password';
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO senzing_load;
```

### 8. Audit Logging

Log all security-relevant events:

```text
Create a dedicated security logger

function log_access(user, action, resource):
    Write info log: "User {user} performed {action} on {resource}"

function authenticate(username, password):
    If credentials are valid:
        log_access(username, "login", "system")
        Return true
    Else:
        Write warning log: "Failed login attempt for {username}"
        Return false
```

### 9. Input Validation

Prevent injection attacks:

```text
function validate_search_input(query):
    Define dangerous patterns: [";", "--", "/*", "*/", "xp_", "sp_"]
    For each pattern in dangerous patterns:
        If pattern found in query:
            Raise error: "Invalid character in query"

    If length of query > 1000:
        Raise error: "Query too long"

    Return sanitized query
```

### 10. Rate Limiting

Prevent abuse:

```text
Configure rate limiter:
    Default limit: 100 requests per hour per IP

Route GET /api/search:
    Rate limit: 10 requests per minute per IP
    function search():
        // Search logic
```

## Security Audit Checklist

- [ ] No hardcoded credentials
- [ ] Secrets stored in secrets manager
- [ ] API authentication implemented
- [ ] HTTPS/TLS enabled
- [ ] Database connections encrypted
- [ ] PII handling compliant
- [ ] Dependency vulnerabilities scanned
- [ ] Container images scanned
- [ ] Code security scanned
- [ ] Firewall rules configured
- [ ] Access control implemented
- [ ] Audit logging enabled
- [ ] Input validation implemented
- [ ] Rate limiting configured
- [ ] Security documentation complete

## Security Testing

```bash
# Run security tests (use the appropriate command for your language)
# The agent generates test scripts via generate_scaffold

# Scan dependencies for known vulnerabilities
# Python: safety check | Java: mvn dependency-check:check | Rust: cargo audit
# C#: dotnet list package --vulnerable | Node.js: npm audit

# Run static analysis
# Python: bandit -r src/ | Rust: cargo clippy | TypeScript: eslint src/

# Test authentication
curl -H "X-API-Key: invalid" https://api.example.com/search
# Should return 401 Unauthorized
```

## Agent Behavior

When a user is in Module 10, the agent should:

1. **Review current security posture**
2. **Identify hardcoded credentials** and move to secrets manager
3. **Implement API authentication**
4. **Enable encryption** (at rest and in transit)
5. **Add PII handling** compliance measures
6. **Run security scans** (dependencies, containers, code)
7. **Configure network security**
8. **Implement access control**
9. **Set up audit logging**
10. **Add input validation** and rate limiting
11. **Generate security audit report**
12. **Document security measures** in `docs/security_audit.md`

## Validation Gates

Before completing Module 10:

- [ ] Security checklist complete
- [ ] No hardcoded secrets
- [ ] Authentication working
- [ ] Encryption enabled
- [ ] PII compliance verified
- [ ] Security scans passed
- [ ] Audit logging functional
- [ ] Security documentation complete

## Success Indicators

Module 10 is complete when:

- All security checklist items addressed
- Security scans pass with no critical issues
- Authentication and authorization working
- Encryption enabled everywhere
- PII handling compliant
- Security audit documented
- Ready for security review

## Output Files

- `docs/security_audit.md` - Security audit report
- `docs/security_checklist.md` - Completed checklist
- `config/security_config.yaml` - Security configuration
- `src/security/` - Security utilities

## Related Documentation

- `POWER.md` - Module 10 overview
- `steering/module-10-security.md` - Module 10 workflow
- `steering/security-privacy.md` - Security best practices

## Version History

- **v3.0.0** (2026-03-17): Module 10 created for security hardening
- **v4.0.0** (2026-04-17): Renumbered from Module 10 to Module 10 (merge of old Modules 4+5)
