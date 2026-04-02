---
inclusion: always
---

# Data Privacy and Security

**CRITICAL**: Handle data responsibly throughout the boot camp.

## Data Privacy Considerations

- **PII Protection**: Customer data contains Personally Identifiable Information (names, addresses, SSNs, etc.)
- **Sample Data**: Use anonymized or synthetic data for testing when possible
- **Access Control**: Limit who can access raw data files
- **Compliance**: Consider GDPR, CCPA, HIPAA, or other regulations applicable to your data

## Security Best Practices

### 1. Never Commit Sensitive Data to Git

- Use `.gitignore` for data files
- Store credentials in `.env` (not in git)
- Use `.env.example` as a template

### 2. Anonymize Test Data

- Replace real names with fake names
- Use fake addresses and phone numbers
- Mask or remove SSNs and other identifiers
- Keep data structure but change values

### 3. Secure Credentials

- Use environment variables for API keys
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate credentials regularly
- Never hardcode passwords in source code

### 4. Database Security

- Use strong passwords
- Enable encryption at rest
- Use SSL/TLS for connections
- Regular backups with encryption

### 5. Access Logging

- Log who accesses data and when
- Monitor for unusual access patterns
- Audit trail for compliance

## Security Compliance Documentation

Create `docs/security_compliance.md`:

```markdown
# Security and Compliance Notes

## Data Classification
- **Data Source 1**: Contains PII (names, addresses, SSNs)
- **Data Source 2**: Contains business data (no PII)

## Compliance Requirements
- GDPR: Right to be forgotten, data portability
- CCPA: Consumer privacy rights
- [Add your specific requirements]

## Data Handling Procedures
1. All PII must be encrypted at rest
2. Access requires authentication
3. Audit logs retained for 90 days
4. Data retention: [specify period]

## Anonymization Strategy
- Test data: Use a synthetic data generation library for your language (e.g., Faker for Python/Java, Bogus for C#, fake-rs for Rust, @faker-js/faker for TypeScript)
- Sample data: Mask last 4 digits of SSN, use fake addresses

## Incident Response
- Contact: [security team email]
- Procedure: [link to incident response plan]
```
