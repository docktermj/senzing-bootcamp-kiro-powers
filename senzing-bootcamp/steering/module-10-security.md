---
inclusion: manual
---

# Module 10: Security Hardening

**Purpose**: Implement production-grade security measures.

**Prerequisites**:

- ✅ Module 9 complete (performance validated)
- ✅ Security requirements identified
- ✅ Compliance needs documented

**Agent Workflow**:

1. **Assess security requirements**:

   Ask: "What are your security and compliance requirements?"

   Common requirements:
   - SOC 2, ISO 27001
   - GDPR, CCPA
   - HIPAA, PCI-DSS
   - Industry-specific regulations

   WAIT for response.

2. **Implement secrets management**:

   Never hard-code credentials!

   Options:
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Environment variables (minimum)

   Create `src/security/secrets_manager.py`:

   ```python
   import boto3

   def get_database_password():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='prod/db/password')
       return response['SecretString']
   ```

3. **Implement authentication**:

   For APIs and services:
   - JWT tokens
   - OAuth 2.0
   - API keys with rotation
   - Multi-factor authentication

   Create `src/security/auth.py`.

4. **Implement authorization**:

   Role-based access control (RBAC):
   - Admin: Full access
   - Analyst: Read-only
   - Service: API access only

   Create `src/security/rbac.py`.

5. **Encrypt sensitive data**:

   - Data at rest: Database encryption
   - Data in transit: TLS/SSL
   - PII fields: Field-level encryption

   Create `src/security/encryption.py`.

6. **Implement audit logging**:

   Log all access and changes:
   - Who accessed what
   - When
   - What changed
   - Why (if available)

   Create `src/security/audit_log.py`.

7. **Scan for vulnerabilities**:

   Run security scans:

   ```bash
   # Python dependencies
   pip install safety
   safety check

   # Code scanning
   bandit -r src/

   # Container scanning
   trivy image your-image:latest
   ```

8. **Create security checklist**:

   Document in `docs/security_checklist.md`:

   ```markdown
   # Security Checklist

   ## Secrets Management
   - [ ] No hard-coded credentials
   - [ ] Secrets in vault/manager
   - [ ] Regular secret rotation

   ## Authentication
   - [ ] Strong password policy
   - [ ] MFA enabled
   - [ ] Session timeout configured

   ## Authorization
   - [ ] RBAC implemented
   - [ ] Least privilege principle
   - [ ] Regular access reviews

   ## Encryption
   - [ ] TLS/SSL for all connections
   - [ ] Database encryption enabled
   - [ ] PII fields encrypted

   ## Audit Logging
   - [ ] All access logged
   - [ ] Logs retained per policy
   - [ ] Log monitoring enabled

   ## Vulnerability Management
   - [ ] Regular security scans
   - [ ] Patch management process
   - [ ] Incident response plan
   ```

9. **Conduct security review**:

   If possible, have security team review:
   - Architecture
   - Code
   - Configuration
   - Access controls

**Success Criteria**:

- ✅ Secrets management implemented
- ✅ Authentication and authorization in place
- ✅ Encryption configured
- ✅ Audit logging enabled
- ✅ Security scans passed
- ✅ Security checklist completed
