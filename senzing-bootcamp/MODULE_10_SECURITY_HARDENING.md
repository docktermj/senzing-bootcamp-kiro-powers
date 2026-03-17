# Module 10: Security Hardening

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
```python
DATABASE_URL = "postgresql://user:password123@localhost/senzing"
```

✅ **Good**: Environment variables
```python
import os
DATABASE_URL = os.getenv('DATABASE_URL')
```

✅ **Better**: Secrets manager
```python
from aws_secretsmanager import get_secret
DATABASE_URL = get_secret('prod/senzing/database_url')
```

**Tools**:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Secrets
- Environment variables (minimum)

### 2. API Authentication

Implement authentication for all APIs:

```python
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/search')
@require_api_key
def search():
    # Protected endpoint
    pass
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

```python
# Force SSL for database connections
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"
```

### 4. PII Handling Compliance

**GDPR Requirements**:
- Right to access
- Right to erasure
- Data minimization
- Consent management
- Breach notification

**Implementation**:
```python
def anonymize_pii(record):
    """Anonymize PII for non-production environments"""
    if os.getenv('ENVIRONMENT') != 'production':
        record['SSN_NUMBER'] = 'XXX-XX-' + record['SSN_NUMBER'][-4:]
        record['EMAIL_ADDRESS'] = hash_email(record['EMAIL_ADDRESS'])
    return record
```

### 5. Security Scanning

**Dependency Scanning**:
```bash
# Python
pip install safety
safety check

# Node.js
npm audit

# Java
mvn dependency-check:check
```

**Container Scanning**:
```bash
# Scan Docker images
docker scan my-senzing-app:latest

# Trivy
trivy image my-senzing-app:latest
```

**Code Scanning**:
```bash
# Bandit (Python)
bandit -r src/

# SonarQube
sonar-scanner
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

```python
import logging

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

def log_access(user, action, resource):
    security_logger.info(f"User {user} performed {action} on {resource}")

# Log authentication attempts
def authenticate(username, password):
    if valid_credentials(username, password):
        log_access(username, 'login', 'system')
        return True
    else:
        security_logger.warning(f"Failed login attempt for {username}")
        return False
```

### 9. Input Validation

Prevent injection attacks:

```python
def validate_search_input(query):
    """Validate and sanitize search input"""
    # Remove SQL injection attempts
    dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        if char in query:
            raise ValueError(f"Invalid character in query: {char}")
    
    # Limit length
    if len(query) > 1000:
        raise ValueError("Query too long")
    
    return query
```

### 10. Rate Limiting

Prevent abuse:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/search')
@limiter.limit("10 per minute")
def search():
    pass
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
# Run security tests
python src/testing/security_test.py

# Check for common vulnerabilities
bandit -r src/

# Scan dependencies
safety check

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
- `steering/steering.md` - Module 10 workflow (to be added)
- `steering/security-privacy.md` - Security best practices

## Version History

- **v3.0.0** (2026-03-17): Module 10 created for security hardening
