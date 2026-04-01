---
inclusion: manual
---

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_10_SECURITY_HARDENING.md`.

# Module 10: Security Hardening

## Workflow: Security Hardening End-to-End (Module 10)

Implement production-grade security measures for your Senzing entity resolution system. This module covers secrets management, authentication, authorization, encryption, audit logging, input validation, network security, and Senzing-specific security concerns.

**Time**: Varies significantly by compliance requirements (2-8 hrs). Simple setups with environment variables and basic TLS may take 2 hours. Full compliance implementations (HIPAA, PCI-DSS) with vault integration, field-level encryption, and comprehensive audit logging can take a full day or more.

**Language**: Use the bootcamper's chosen programming language (`<chosen_language>`) from the language selection step. All code generation, scaffold calls, and examples in this module must use that language.

**Prerequisites**:

- ✅ Module 9 complete (performance validated)
- ✅ Security requirements identified (or will be identified in Step 1)
- ✅ Compliance needs documented (or will be documented in Step 1)
- ✅ Working Senzing deployment to harden

**Before starting**: Call `search_docs(query='security best practices', version='current')` to retrieve the latest Senzing security guidance. Review the results and incorporate any platform-specific recommendations into the workflow below.

## Step 1: Assess Security and Compliance Requirements

Ask: "What are your security and compliance requirements? For example: SOC 2, ISO 27001, GDPR, CCPA, HIPAA, PCI-DSS, FedRAMP, or industry-specific regulations. If you're unsure, tell me about your industry and the type of data you're processing, and I'll help identify what applies."

WAIT for response before proceeding.

Based on the user's response, categorize the compliance posture:

- **Minimal**: No specific regulatory requirements. Focus on general best practices (secrets management, TLS, basic access control).
- **Standard**: SOC 2, ISO 27001, or similar. Requires documented controls, audit logging, encryption at rest and in transit, access reviews.
- **Strict**: GDPR, CCPA, HIPAA, PCI-DSS, or similar. Requires field-level encryption for PII, comprehensive audit trails, data retention policies, right-to-erasure support, breach notification procedures.

Document the compliance posture in `docs/security_compliance.md` (created during Module 2 if the security-privacy steering was followed, otherwise create it now).

Ask: "Who are the stakeholders for security sign-off? Is there a security team or compliance officer who needs to review the implementation?"

WAIT for response.

Record the answer in `docs/security_compliance.md` under a "Stakeholders" section.

## Step 2: Secrets Management

Never hard-code credentials. This is the single most common security failure in entity resolution deployments.

Ask: "How do you currently manage secrets and credentials? Options include: environment variables (minimum viable), AWS Secrets Manager, Azure Key Vault, Google Secret Manager, HashiCorp Vault, or another secrets manager."

WAIT for response.

### 2a: Environment Variables (Minimum Viable)

For development and simple deployments, use environment variables with a `.env` file that is never committed to version control.

Create `src/security/secrets_manager.<ext>`:

```text
// Secrets manager abstraction layer
// Supports environment variables as the default backend
// Can be extended to support vault integrations

function get_secret(secret_name):
    // First, try the configured secrets backend
    value = read_from_secrets_backend(secret_name)
    if value is not null:
        return value

    // Fall back to environment variable
    value = get_environment_variable(secret_name)
    if value is not null:
        return value

    // No secret found — fail loudly, never silently
    raise error "Secret '{secret_name}' not found in any configured backend"

function get_database_credentials():
    return {
        host:     get_secret("SENZING_DB_HOST"),
        port:     get_secret("SENZING_DB_PORT"),
        database: get_secret("SENZING_DB_NAME"),
        username: get_secret("SENZING_DB_USER"),
        password: get_secret("SENZING_DB_PASSWORD")
    }

function get_engine_configuration():
    // CRITICAL: Never expose SENZING_ENGINE_CONFIGURATION_JSON in logs or API responses
    config_json = get_secret("SENZING_ENGINE_CONFIGURATION_JSON")
    if config_json is null:
        raise error "Engine configuration not found — set SENZING_ENGINE_CONFIGURATION_JSON"
    return parse_json(config_json)
```

Create `.env.example` (committed to git as a template):

```text
# Senzing Database Credentials
SENZING_DB_HOST=localhost
SENZING_DB_PORT=5432
SENZING_DB_NAME=G2
SENZING_DB_USER=senzing
SENZING_DB_PASSWORD=CHANGE_ME

# Senzing Engine Configuration
# CRITICAL: This contains database credentials — never log or expose this value
SENZING_ENGINE_CONFIGURATION_JSON=CHANGE_ME

# Senzing License (if applicable)
SENZING_LICENSE_BASE64=CHANGE_ME

# API Authentication
API_JWT_SECRET=CHANGE_ME
API_KEY_SALT=CHANGE_ME
```

Verify `.env` is in `.gitignore`:

```bash
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

### 2b: Vault Integration (Production)

For production deployments, integrate with a secrets vault. The abstraction layer in `src/security/secrets_manager.<ext>` should support swapping backends without changing application code.

```text
// Extended secrets manager with vault backend support

function initialize_secrets_backend(backend_type, config):
    if backend_type == "aws_secrets_manager":
        initialize AWS Secrets Manager client with config.region
    else if backend_type == "azure_key_vault":
        initialize Azure Key Vault client with config.vault_url
    else if backend_type == "hashicorp_vault":
        initialize HashiCorp Vault client with config.vault_addr, config.vault_token
    else if backend_type == "environment":
        // No initialization needed for environment variables
        pass
    else:
        raise error "Unknown secrets backend: {backend_type}"

function read_from_secrets_backend(secret_name):
    // Implementation depends on the configured backend
    // Each backend translates the secret_name to its own path convention
    // e.g., AWS: "prod/senzing/{secret_name}"
    // e.g., Vault: "secret/data/senzing/{secret_name}"
    return backend.get_secret(secret_name)
```

### 2c: Secret Rotation

Create `src/security/secret_rotation.<ext>`:

```text
function rotate_database_password():
    // 1. Generate new password
    new_password = generate_secure_random_string(length=32)

    // 2. Update password in the database server
    update_database_user_password("senzing", new_password)

    // 3. Update password in the secrets backend
    store_secret("SENZING_DB_PASSWORD", new_password)

    // 4. Update SENZING_ENGINE_CONFIGURATION_JSON with new password
    config = get_engine_configuration()
    config.SQL.CONNECTION = rebuild_connection_string(config, new_password)
    store_secret("SENZING_ENGINE_CONFIGURATION_JSON", serialize_json(config))

    // 5. Log the rotation event (never log the actual password)
    audit_log("SECRET_ROTATED", {
        secret_name: "SENZING_DB_PASSWORD",
        rotated_by: current_user(),
        timestamp: now()
    })

function schedule_rotation():
    // Rotate database password every 90 days (adjust per compliance requirements)
    schedule_recurring_task(rotate_database_password, interval_days=90)
```

**Validation gate**: Before proceeding, verify:

- ✅ No hard-coded credentials in any source file
- ✅ `.env` is in `.gitignore`
- ✅ Secrets manager abstraction created
- ✅ Application can retrieve credentials at runtime

## Step 3: Authentication

Ask: "How will users and services authenticate to your entity resolution system? Common patterns: JWT tokens for web APIs, OAuth 2.0 for third-party integrations, API keys for service-to-service calls, or mutual TLS for internal microservices."

WAIT for response.

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')` to get the current SDK initialization pattern. Wrap it with the authentication layer below. Do not hand-code SDK method names.

Create `src/security/auth.<ext>`:

```text
// Authentication middleware for Senzing API access
// Supports JWT, API key, and OAuth 2.0 token validation

function authenticate_request(request):
    // Check for Bearer token (JWT or OAuth)
    auth_header = request.get_header("Authorization")
    if auth_header starts with "Bearer ":
        token = auth_header.remove_prefix("Bearer ")
        return validate_jwt_token(token)

    // Check for API key
    api_key = request.get_header("X-API-Key")
    if api_key is not null:
        return validate_api_key(api_key)

    // No credentials provided
    raise AuthenticationError("Missing authentication credentials", status=401)

function validate_jwt_token(token):
    try:
        jwt_secret = get_secret("API_JWT_SECRET")
        payload = decode_jwt(token, secret=jwt_secret, algorithms=["HS256"])

        // Validate standard claims
        if payload.exp < now():
            raise AuthenticationError("Token expired", status=401)
        if payload.iss != "senzing-er-system":
            raise AuthenticationError("Invalid token issuer", status=401)

        return {
            user_id:  payload.sub,
            roles:    payload.roles,
            exp:      payload.exp
        }
    catch JWTDecodeError:
        raise AuthenticationError("Invalid token", status=401)

function validate_api_key(api_key):
    // Hash the API key and compare against stored hashes
    // NEVER store API keys in plaintext
    api_key_hash = hash_with_salt(api_key, get_secret("API_KEY_SALT"))
    stored_key = lookup_api_key_hash(api_key_hash)

    if stored_key is null:
        raise AuthenticationError("Invalid API key", status=401)
    if stored_key.is_revoked:
        raise AuthenticationError("API key has been revoked", status=401)
    if stored_key.expires_at < now():
        raise AuthenticationError("API key expired", status=401)

    return {
        user_id:  stored_key.owner_id,
        roles:    stored_key.roles,
        exp:      stored_key.expires_at
    }

function generate_jwt_token(user_id, roles):
    jwt_secret = get_secret("API_JWT_SECRET")
    payload = {
        sub:   user_id,
        roles: roles,
        iss:   "senzing-er-system",
        iat:   now(),
        exp:   now() + hours(8)    // Token lifetime — adjust per security policy
    }
    return encode_jwt(payload, secret=jwt_secret, algorithm="HS256")

function generate_api_key(owner_id, roles, expires_in_days=365):
    raw_key = generate_secure_random_string(length=48)
    api_key_hash = hash_with_salt(raw_key, get_secret("API_KEY_SALT"))

    store_api_key({
        hash:       api_key_hash,
        owner_id:   owner_id,
        roles:      roles,
        created_at: now(),
        expires_at: now() + days(expires_in_days),
        is_revoked: false
    })

    // Return the raw key ONCE — it cannot be retrieved again
    return raw_key
```

### Multi-Factor Authentication (MFA)

For strict compliance environments (HIPAA, PCI-DSS), recommend MFA for administrative access:

```text
function authenticate_with_mfa(username, password, mfa_code):
    // Step 1: Validate primary credentials
    user = validate_credentials(username, password)
    if user is null:
        raise AuthenticationError("Invalid credentials")

    // Step 2: Validate MFA code (TOTP-based)
    if not validate_totp(user.mfa_secret, mfa_code):
        raise AuthenticationError("Invalid MFA code")

    // Step 3: Issue token with elevated privileges
    return generate_jwt_token(user.id, user.roles)
```

**Validation gate**: Before proceeding, verify:

- ✅ Authentication middleware created
- ✅ Token validation handles expiration and revocation
- ✅ API keys are hashed, never stored in plaintext
- ✅ MFA considered for administrative access (if strict compliance)

## Step 4: Authorization (RBAC)

Entity resolution systems handle sensitive data. Role-based access control ensures users can only perform actions appropriate to their role.

Ask: "What roles do you need for your entity resolution system? Common roles for ER systems include: Admin (full access, configuration changes), Analyst (read-only entity queries, export), Operator (load data, run redo), Auditor (read audit logs, compliance reports), and Service Account (API-only, specific operations). Which of these apply, or do you have custom roles?"

WAIT for response.

Create `src/security/rbac.<ext>`:

```text
// Role-Based Access Control for Senzing Entity Resolution
// Defines permissions for each role across all ER operations

PERMISSIONS = {
    "admin": {
        // Full system access
        "engine.initialize":     true,
        "engine.configure":      true,
        "engine.destroy":        true,
        "record.add":            true,
        "record.delete":         true,
        "record.reevaluate":     true,
        "entity.get":            true,
        "entity.search":         true,
        "entity.export":         true,
        "entity.why":            true,
        "entity.how":            true,
        "redo.process":          true,
        "config.modify":         true,
        "config.export":         true,
        "config.import":         true,
        "audit.read":            true,
        "audit.export":          true,
        "user.manage":           true,
        "datasource.add":        true,
        "datasource.delete":     true
    },
    "analyst": {
        // Read-only access to entity data — no modifications
        "entity.get":            true,
        "entity.search":         true,
        "entity.export":         true,
        "entity.why":            true,
        "entity.how":            true,
        "config.export":         true,
        "audit.read":            true
    },
    "operator": {
        // Data loading and maintenance — no configuration changes
        "record.add":            true,
        "record.delete":         true,
        "record.reevaluate":     true,
        "entity.get":            true,
        "entity.search":         true,
        "redo.process":          true,
        "datasource.add":        true
    },
    "auditor": {
        // Compliance and audit access only
        "audit.read":            true,
        "audit.export":          true,
        "entity.get":            true,
        "config.export":         true
    },
    "service": {
        // Automated service account — scoped to specific operations
        "record.add":            true,
        "record.delete":         true,
        "entity.get":            true,
        "entity.search":         true,
        "redo.process":          true
    }
}

function check_permission(user_context, permission):
    role = user_context.roles[0]    // Primary role
    if role not in PERMISSIONS:
        raise AuthorizationError("Unknown role: {role}", status=403)

    if permission not in PERMISSIONS[role] or PERMISSIONS[role][permission] != true:
        audit_log("PERMISSION_DENIED", {
            user_id:    user_context.user_id,
            role:       role,
            permission: permission,
            timestamp:  now()
        })
        raise AuthorizationError(
            "Role '{role}' does not have permission '{permission}'", status=403
        )

    return true

function require_permission(permission):
    // Decorator/middleware pattern — wrap around route handlers
    return function(request, ...args):
        user_context = authenticate_request(request)
        check_permission(user_context, permission)
        return handle_request(request, ...args)

// Usage examples:
// GET  /entities/{id}     → require_permission("entity.get")
// POST /records           → require_permission("record.add")
// GET  /audit/logs        → require_permission("audit.read")
// POST /config/datasource → require_permission("datasource.add")
```

### Row-Level Security for Multi-Tenant Deployments

If the system serves multiple tenants or departments, add data-source-level access control:

```text
function check_datasource_access(user_context, data_source):
    // Users can only access entities from data sources they're authorized for
    allowed_sources = user_context.allowed_data_sources
    if allowed_sources is not null and data_source not in allowed_sources:
        audit_log("DATASOURCE_ACCESS_DENIED", {
            user_id:     user_context.user_id,
            data_source: data_source,
            timestamp:   now()
        })
        raise AuthorizationError(
            "Not authorized to access data source '{data_source}'", status=403
        )
    return true
```

**Validation gate**: Before proceeding, verify:

- ✅ RBAC roles defined and documented
- ✅ Permissions mapped to all Senzing operations
- ✅ Authorization checks integrated into API routes
- ✅ Denied access attempts are logged

## Step 5: Encryption

Entity resolution systems process PII by definition — names, addresses, identifiers, contact information. Encryption is not optional.

> **Agent instruction:** Call `search_docs(query='encryption', version='current')` to retrieve the latest Senzing encryption guidance before recommending specific approaches.

> **Agent instruction:** Call `search_docs(query='PII protection', category='concepts', version='current')` to retrieve Senzing-specific PII protection guidance.

Ask: "What encryption requirements do you have? Let's cover three layers: (1) data at rest — is your database encrypted? (2) data in transit — are all connections using TLS? (3) field-level encryption — do specific PII fields need application-level encryption beyond database encryption?"

WAIT for response.

### 5a: Encryption at Rest

Database-level encryption protects data if storage media is compromised.

```text
// Database encryption verification
// Run these checks against your Senzing database

function verify_database_encryption():
    if database_type == "postgresql":
        // Check if PostgreSQL data directory is on encrypted storage
        // Check if pgcrypto extension is available for field-level encryption
        result = execute_sql("SELECT * FROM pg_available_extensions WHERE name = 'pgcrypto'")
        if result is empty:
            warn "pgcrypto extension not available — field-level encryption will need application layer"

        // Check SSL mode in connection string
        if connection_string does not contain "sslmode=verify-full":
            warn "Database connection is not using SSL — add sslmode=verify-full"

    else if database_type == "sqlite":
        // SQLite does not support native encryption
        // For production with SQLite, use SQLCipher or move to PostgreSQL
        warn "SQLite does not support encryption at rest — acceptable for development only"

    log "Database encryption check complete"
```

### 5b: Encryption in Transit (TLS)

All network connections must use TLS 1.2 or higher.

```text
// TLS configuration for Senzing API server

function configure_tls(server):
    tls_cert_path = get_secret("TLS_CERT_PATH")
    tls_key_path  = get_secret("TLS_KEY_PATH")

    server.configure_tls({
        certificate:       read_file(tls_cert_path),
        private_key:       read_file(tls_key_path),
        minimum_version:   "TLS_1_2",
        cipher_suites: [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256"
        ],
        // Disable older protocols
        disable_ssl_v2:    true,
        disable_ssl_v3:    true,
        disable_tls_1_0:   true,
        disable_tls_1_1:   true
    })

    // Enable HSTS if serving over HTTPS
    server.add_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    log "TLS configured with minimum version TLS 1.2"
```

### 5c: Field-Level Encryption for PII

For strict compliance (HIPAA, PCI-DSS), encrypt specific PII fields at the application layer before they reach the database. This protects data even from database administrators.

Create `src/security/encryption.<ext>`:

```text
// Field-level encryption for PII in entity resolution records
// Uses AES-256-GCM for authenticated encryption

// Fields that contain PII and should be encrypted at the application layer
PII_FIELDS = [
    "SSN_NUMBER",
    "PASSPORT_NUMBER",
    "DRIVERS_LICENSE_NUMBER",
    "NATIONAL_ID_NUMBER",
    "DATE_OF_BIRTH",
    "BANK_ACCOUNT_NUMBER",
    "CREDIT_CARD_NUMBER"
]

// Fields that Senzing needs in cleartext for matching — do NOT encrypt these
// Senzing must be able to read these to perform entity resolution
MATCHING_FIELDS = [
    "NAME_FULL", "NAME_FIRST", "NAME_LAST", "NAME_ORG",
    "ADDR_FULL", "ADDR_LINE1", "ADDR_CITY", "ADDR_STATE", "ADDR_POSTAL_CODE",
    "PHONE_NUMBER", "EMAIL_ADDRESS"
]

function encrypt_pii_fields(record):
    encryption_key = get_secret("PII_ENCRYPTION_KEY")
    encrypted_record = copy(record)

    for each field in PII_FIELDS:
        if field in encrypted_record and encrypted_record[field] is not null:
            plaintext = encrypted_record[field]
            // Generate a unique IV for each encryption operation
            iv = generate_random_bytes(12)
            ciphertext = aes_256_gcm_encrypt(plaintext, encryption_key, iv)
            // Store as base64-encoded string with IV prefix
            encrypted_record[field] = base64_encode(iv + ciphertext)
            // Add a marker so we know this field is encrypted
            encrypted_record[field + "_ENCRYPTED"] = true

    return encrypted_record

function decrypt_pii_fields(record):
    encryption_key = get_secret("PII_ENCRYPTION_KEY")
    decrypted_record = copy(record)

    for each field in PII_FIELDS:
        if field + "_ENCRYPTED" in decrypted_record and decrypted_record[field + "_ENCRYPTED"] == true:
            encoded = decrypted_record[field]
            raw = base64_decode(encoded)
            iv = raw[0:12]
            ciphertext = raw[12:]
            decrypted_record[field] = aes_256_gcm_decrypt(ciphertext, encryption_key, iv)
            remove decrypted_record[field + "_ENCRYPTED"]

    return decrypted_record

// IMPORTANT: Encrypt BEFORE loading into Senzing, decrypt AFTER retrieving
// Senzing will store the encrypted values but cannot match on them
// Only encrypt fields that are NOT used for matching
```

**Validation gate**: Before proceeding, verify:

- ✅ Database encryption at rest confirmed (or documented as development-only for SQLite)
- ✅ All connections use TLS 1.2+
- ✅ PII fields identified and encryption strategy documented
- ✅ Matching fields are NOT encrypted (Senzing needs cleartext for resolution)
- ✅ Encryption keys stored in secrets manager, not in code

## Step 6: Audit Logging

Audit logging is required for every compliance framework. Entity resolution systems are especially sensitive because they process and correlate PII across data sources.

Ask: "What are your audit log retention requirements? Common policies: 90 days for general access logs, 1 year for compliance (SOC 2), 6 years for financial regulations (SOX), 7 years for healthcare (HIPAA). Also, where should audit logs be stored — local files, centralized logging (ELK, Splunk, CloudWatch), or a database?"

WAIT for response.

Create `src/security/audit_log.<ext>`:

```text
// Comprehensive audit logging for entity resolution operations
// Covers GDPR, CCPA, HIPAA, and SOC 2 requirements

// Log levels for different event types
LOG_LEVELS = {
    "ACCESS":          "INFO",      // Normal data access
    "MODIFICATION":    "WARN",      // Data changes
    "AUTHENTICATION":  "INFO",      // Login/logout events
    "AUTHORIZATION":   "WARN",      // Permission checks (especially denials)
    "SECURITY":        "ERROR",     // Security events (failed logins, suspicious activity)
    "COMPLIANCE":      "INFO",      // Compliance-related events (data export, deletion)
    "CONFIGURATION":   "WARN"       // System configuration changes
}

function audit_log(event_type, details):
    entry = {
        timestamp:    now_utc_iso8601(),
        event_id:     generate_uuid(),
        event_type:   event_type,
        level:        LOG_LEVELS.get(event_type, "INFO"),

        // WHO
        user_id:      details.user_id or current_user_id(),
        user_role:    details.user_role or current_user_role(),
        source_ip:    details.source_ip or current_request_ip(),
        user_agent:   details.user_agent or current_request_user_agent(),

        // WHAT
        action:       details.action,
        resource:     details.resource,
        resource_id:  details.resource_id,

        // OUTCOME
        outcome:      details.outcome or "SUCCESS",
        reason:       details.reason or null,

        // CONTEXT
        data_source:  details.data_source or null,
        entity_id:    details.entity_id or null,
        record_id:    details.record_id or null,

        // COMPLIANCE
        pii_accessed: details.pii_accessed or false,
        consent_ref:  details.consent_ref or null
    }

    // Write to configured log destination
    write_to_audit_log(entry)

    // For security events, also trigger alerts
    if entry.level == "ERROR":
        send_security_alert(entry)

    return entry.event_id

// ─── What to Log for Each Compliance Framework ───

// GDPR Requirements:
//   - All access to personal data (who, when, what)
//   - Data subject access requests (DSAR)
//   - Right-to-erasure requests and execution
//   - Data portability exports
//   - Consent changes
//   - Cross-border data transfers
//   - Data breach detection and notification

// CCPA Requirements:
//   - Consumer data access requests
//   - Data deletion requests and execution
//   - Opt-out requests
//   - Data sale/sharing disclosures
//   - Verification of consumer identity for requests

// HIPAA Requirements:
//   - All access to Protected Health Information (PHI)
//   - Minimum necessary access verification
//   - Disclosure tracking (who received PHI and why)
//   - Breach notification within 60 days
//   - Business Associate Agreement (BAA) compliance

// SOC 2 Requirements:
//   - System access and authentication events
//   - Configuration changes
//   - Data processing activities
//   - Incident detection and response
//   - Availability monitoring

// ─── Specific Audit Events for Entity Resolution ───

function log_record_added(user_context, data_source, record_id):
    audit_log("MODIFICATION", {
        action:      "RECORD_ADD",
        resource:    "record",
        resource_id: record_id,
        data_source: data_source,
        user_id:     user_context.user_id,
        user_role:   user_context.roles[0]
    })

function log_record_deleted(user_context, data_source, record_id, reason):
    audit_log("COMPLIANCE", {
        action:      "RECORD_DELETE",
        resource:    "record",
        resource_id: record_id,
        data_source: data_source,
        reason:      reason,    // e.g., "GDPR right-to-erasure request #12345"
        user_id:     user_context.user_id,
        user_role:   user_context.roles[0]
    })

function log_entity_accessed(user_context, entity_id, pii_fields_returned):
    audit_log("ACCESS", {
        action:       "ENTITY_GET",
        resource:     "entity",
        resource_id:  entity_id,
        pii_accessed: length(pii_fields_returned) > 0,
        user_id:      user_context.user_id,
        user_role:    user_context.roles[0]
    })

function log_entity_search(user_context, search_criteria, result_count):
    audit_log("ACCESS", {
        action:       "ENTITY_SEARCH",
        resource:     "entity",
        resource_id:  "search:" + hash(search_criteria),
        // NEVER log the actual search criteria if it contains PII
        // Log a hash or sanitized version instead
        reason:       "Search returned {result_count} results",
        pii_accessed: true,
        user_id:      user_context.user_id,
        user_role:    user_context.roles[0]
    })

function log_entity_export(user_context, export_format, record_count, reason):
    audit_log("COMPLIANCE", {
        action:       "ENTITY_EXPORT",
        resource:     "entity",
        resource_id:  "export:" + generate_uuid(),
        reason:       reason,    // e.g., "DSAR fulfillment", "Quarterly compliance report"
        pii_accessed: true,
        user_id:      user_context.user_id,
        user_role:    user_context.roles[0]
    })

function log_config_change(user_context, config_section, old_value_hash, new_value_hash):
    audit_log("CONFIGURATION", {
        action:       "CONFIG_MODIFY",
        resource:     "configuration",
        resource_id:  config_section,
        reason:       "Config changed from hash:{old_value_hash} to hash:{new_value_hash}",
        user_id:      user_context.user_id,
        user_role:    user_context.roles[0]
    })

function log_failed_login(username, source_ip, reason):
    audit_log("SECURITY", {
        action:    "LOGIN_FAILED",
        resource:  "authentication",
        outcome:   "FAILURE",
        reason:    reason,
        source_ip: source_ip,
        user_id:   username    // Use the attempted username, not a resolved user ID
    })
```

**Validation gate**: Before proceeding, verify:

- ✅ Audit log captures who, what, when, where, and outcome
- ✅ PII is never logged in cleartext (use hashes or markers)
- ✅ Security events trigger alerts
- ✅ Log retention policy matches compliance requirements
- ✅ Audit logs are tamper-resistant (append-only, or shipped to centralized logging)

## Step 7: Input Validation and Injection Prevention

Entity resolution systems accept search queries that include names, addresses, and identifiers. Without proper validation, these inputs can be vectors for injection attacks.

Create `src/security/input_validation.<ext>`:

```text
// Input validation for entity resolution search queries and record ingestion
// Prevents SQL injection, NoSQL injection, and log injection

// Maximum lengths for common fields (adjust per your data model)
FIELD_MAX_LENGTHS = {
    "NAME_FULL":          200,
    "NAME_FIRST":         100,
    "NAME_LAST":          100,
    "NAME_ORG":           300,
    "ADDR_FULL":          500,
    "ADDR_LINE1":         200,
    "ADDR_CITY":          100,
    "ADDR_STATE":         100,
    "ADDR_POSTAL_CODE":   20,
    "PHONE_NUMBER":       30,
    "EMAIL_ADDRESS":      254,
    "SSN_NUMBER":         11,
    "PASSPORT_NUMBER":    20,
    "DRIVERS_LICENSE_NUMBER": 20,
    "DATE_OF_BIRTH":      10,
    "RECORD_ID":          100,
    "DATA_SOURCE":        50
}

// Characters that should never appear in entity resolution fields
DANGEROUS_PATTERNS = [
    "'; DROP",           // SQL injection
    "1=1",               // SQL injection
    "OR 1=1",            // SQL injection
    "<script",           // XSS
    "javascript:",       // XSS
    "${",                // Template injection
    "{{",                // Template injection
    "\x00",              // Null byte injection
    "\n",                // Log injection (in single-line fields)
    "\r"                 // Log injection
]

function validate_record(record):
    errors = []

    // Required fields
    if "DATA_SOURCE" not in record or record["DATA_SOURCE"] is empty:
        errors.append("DATA_SOURCE is required")
    if "RECORD_ID" not in record or record["RECORD_ID"] is empty:
        errors.append("RECORD_ID is required")

    // Validate each field
    for each (field_name, field_value) in record:
        if field_value is null:
            continue

        // Type check — all Senzing fields should be strings
        if field_value is not a string:
            errors.append("{field_name}: expected string, got {type(field_value)}")
            continue

        // Length check
        max_length = FIELD_MAX_LENGTHS.get(field_name, 1000)
        if length(field_value) > max_length:
            errors.append("{field_name}: exceeds maximum length of {max_length}")

        // Dangerous pattern check
        for each pattern in DANGEROUS_PATTERNS:
            if pattern in field_value (case-insensitive):
                errors.append("{field_name}: contains potentially dangerous content")
                audit_log("SECURITY", {
                    action:      "INPUT_VALIDATION_FAILED",
                    resource:    "record",
                    resource_id: record.get("RECORD_ID", "unknown"),
                    reason:      "Dangerous pattern detected in field {field_name}"
                })
                break

    if length(errors) > 0:
        raise ValidationError("Record validation failed", errors=errors)

    return true

function validate_search_query(search_attributes):
    // Search queries are especially sensitive because they're often user-provided
    validate_record(search_attributes)

    // Additional search-specific validation
    // Prevent wildcard-only searches that could return all records
    non_empty_fields = count fields in search_attributes where value is not empty
    if non_empty_fields == 0:
        raise ValidationError("Search query must contain at least one non-empty attribute")

    // Rate limiting for search queries (prevent enumeration attacks)
    if rate_limit_exceeded(current_user_id(), "entity.search", max=100, window_seconds=60):
        raise RateLimitError("Search rate limit exceeded — max 100 queries per minute")

    return true

function sanitize_for_logging(value):
    // Remove newlines and control characters to prevent log injection
    sanitized = replace_all(value, "\n", "\\n")
    sanitized = replace_all(sanitized, "\r", "\\r")
    sanitized = replace_all(sanitized, "\x00", "")
    // Truncate long values
    if length(sanitized) > 100:
        sanitized = sanitized[0:100] + "...[truncated]"
    return sanitized
```

**Validation gate**: Before proceeding, verify:

- ✅ All record inputs validated before loading into Senzing
- ✅ Search queries validated and rate-limited
- ✅ Dangerous patterns detected and logged
- ✅ Log injection prevented via sanitization

## Step 8: Network Security

Ask: "What is your network architecture? Is the Senzing system deployed in a private network (VPC), on-premises, or publicly accessible? Are there existing firewall rules or network policies?"

WAIT for response.

> **Agent instruction:** Call `search_docs(query='deployment security', category='anti_patterns', version='current')` to check for known deployment security pitfalls before recommending network architecture.

### 8a: TLS for All Connections

```text
// Network security checklist — verify all connections use TLS

function verify_network_security():
    checks = []

    // 1. API server TLS
    if api_server.is_tls_enabled():
        checks.append("✅ API server uses TLS")
    else:
        checks.append("❌ API server is NOT using TLS — configure immediately")

    // 2. Database connection TLS
    db_connection_string = get_secret("SENZING_ENGINE_CONFIGURATION_JSON")
    if "sslmode=verify-full" in db_connection_string or "sslmode=require" in db_connection_string:
        checks.append("✅ Database connection uses SSL")
    else:
        checks.append("❌ Database connection is NOT using SSL")

    // 3. Inter-service communication
    // If using microservices, verify all internal calls use TLS or mTLS
    checks.append("⚠️  Verify inter-service communication uses TLS or mutual TLS")

    // 4. External API calls (if any)
    checks.append("⚠️  Verify all external API calls use HTTPS")

    return checks
```

### 8b: Firewall Rules

```text
// Recommended firewall rules for a Senzing deployment

FIREWALL_RULES = {
    // Senzing API server — only accessible from trusted networks
    "api_server": {
        inbound: [
            { port: 443,  protocol: "TCP", source: "application_subnet",  description: "HTTPS API access" },
            { port: 443,  protocol: "TCP", source: "load_balancer",       description: "HTTPS via load balancer" }
        ],
        outbound: [
            { port: 5432, protocol: "TCP", destination: "database_subnet", description: "PostgreSQL" },
            { port: 443,  protocol: "TCP", destination: "secrets_manager", description: "Secrets retrieval" }
        ],
        deny_all_other: true
    },

    // Database server — only accessible from application tier
    "database": {
        inbound: [
            { port: 5432, protocol: "TCP", source: "application_subnet",  description: "PostgreSQL from app" }
        ],
        outbound: [],
        deny_all_other: true
    },

    // NEVER expose these ports to the public internet:
    // - 5432 (PostgreSQL)
    // - 8250, 8251 (Senzing API server default ports)
    // - 9999 (Senzing debug/admin ports)
}
```

### 8c: VPN and Private Network Access

For production deployments, the Senzing system should not be directly accessible from the public internet.

```text
// Network architecture recommendations

RECOMMENDED_ARCHITECTURE = {
    "public_tier": [
        "Load balancer with TLS termination",
        "WAF (Web Application Firewall) for API protection",
        "DDoS protection"
    ],
    "application_tier": [
        "Senzing API server (private subnet)",
        "Authentication/authorization service",
        "Audit log aggregator"
    ],
    "data_tier": [
        "PostgreSQL database (private subnet, no public IP)",
        "Encrypted backups in object storage",
        "Senzing configuration files (restricted access)"
    ],
    "management_tier": [
        "VPN or bastion host for administrative access",
        "Monitoring and alerting (Module 11)",
        "Log aggregation (ELK, Splunk, CloudWatch)"
    ]
}
```

**Validation gate**: Before proceeding, verify:

- ✅ All connections use TLS 1.2+
- ✅ Database not exposed to public internet
- ✅ Firewall rules restrict access to necessary ports only
- ✅ Administrative access requires VPN or bastion host
- ✅ Network architecture documented

## Step 9: Senzing-Specific Security

Entity resolution with Senzing introduces unique security concerns beyond general application security. This section covers Senzing-specific attack surfaces and mitigations.

### 9a: Engine Configuration Security

`SENZING_ENGINE_CONFIGURATION_JSON` contains database credentials, file paths, and system configuration. It is the single most sensitive artifact in a Senzing deployment.

```text
// SENZING_ENGINE_CONFIGURATION_JSON security rules

// ❌ NEVER do these:
//   - Log SENZING_ENGINE_CONFIGURATION_JSON (it contains database passwords)
//   - Return it in API responses
//   - Store it in version control
//   - Pass it as a command-line argument (visible in process listings)
//   - Include it in error messages or stack traces

// ✅ ALWAYS do these:
//   - Store in a secrets manager or environment variable
//   - Restrict file permissions if stored on disk (chmod 600)
//   - Rotate the database password it contains on a schedule
//   - Audit access to the secret

function safe_log_engine_config(config_json):
    // If you need to log configuration for debugging, redact sensitive fields
    config = parse_json(config_json)

    if "SQL" in config and "CONNECTION" in config["SQL"]:
        config["SQL"]["CONNECTION"] = "[REDACTED]"
    if "HYBRID" in config:
        for each key in config["HYBRID"]:
            if "CONNECTION" in key:
                config["HYBRID"][key] = "[REDACTED]"

    return serialize_json(config)
```

### 9b: Database Credential Protection

```text
// Database credential security for Senzing deployments

// The Senzing database contains ALL entity resolution data — every record,
// every resolved entity, every relationship. Compromising the database
// means compromising ALL PII across ALL data sources.

CREDENTIAL_SECURITY_CHECKLIST = [
    "Database user has minimum necessary privileges (not superuser/admin)",
    "Separate database users for application vs. admin operations",
    "Database password meets complexity requirements (32+ chars, random)",
    "Password stored in secrets manager, not in config files",
    "Connection uses SSL/TLS with certificate verification",
    "Database audit logging enabled for the Senzing user",
    "Failed login attempts trigger alerts",
    "Database user cannot create or drop databases (only tables within its database)"
]

function create_least_privilege_db_user():
    // Create a Senzing-specific database user with minimum privileges
    // This user can read/write Senzing tables but cannot:
    //   - Create or drop databases
    //   - Create or drop users
    //   - Access other databases
    //   - Modify database configuration

    execute_sql("CREATE USER senzing_app WITH PASSWORD '[from_secrets_manager]'")
    execute_sql("GRANT CONNECT ON DATABASE senzing TO senzing_app")
    execute_sql("GRANT USAGE ON SCHEMA public TO senzing_app")
    execute_sql("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO senzing_app")
    execute_sql("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO senzing_app")

    // For admin operations (schema changes, configuration), use a separate user
    execute_sql("CREATE USER senzing_admin WITH PASSWORD '[from_secrets_manager]'")
    execute_sql("GRANT ALL PRIVILEGES ON DATABASE senzing TO senzing_admin")
```

### 9c: License File Security

```text
// Senzing license file security

// The Senzing license file (if applicable) should be treated as a secret:
//   - Do not commit to version control
//   - Store in secrets manager or encrypted storage
//   - Restrict file permissions (chmod 600)
//   - Monitor for unauthorized access

// Add to .gitignore:
//   g2.lic
//   *.lic
//   SENZING_LICENSE_BASE64
```

### 9d: PII in Entity Resolution Results

Entity resolution results contain correlated PII from multiple data sources. A single resolved entity may combine PII from CRM, support tickets, financial records, and more. This makes entity resolution results MORE sensitive than any individual data source.

```text
// PII protection in entity resolution results

function sanitize_entity_response(entity, user_context):
    // Apply role-based field filtering
    // Analysts may see names and addresses but not SSNs
    // Auditors may see metadata but not PII

    role = user_context.roles[0]

    FIELD_VISIBILITY = {
        "admin":   ["*"],                    // All fields
        "analyst": ["NAME_*", "ADDR_*", "PHONE_*", "EMAIL_*", "ENTITY_ID", "RECORD_ID", "DATA_SOURCE"],
        "operator": ["ENTITY_ID", "RECORD_ID", "DATA_SOURCE", "MATCH_KEY"],
        "auditor": ["ENTITY_ID", "RECORD_ID", "DATA_SOURCE", "MATCH_KEY", "MATCH_SCORE"]
    }

    allowed_patterns = FIELD_VISIBILITY.get(role, [])

    if "*" in allowed_patterns:
        return entity    // Admin sees everything

    filtered_entity = {}
    for each (field, value) in entity:
        if field_matches_any_pattern(field, allowed_patterns):
            filtered_entity[field] = value
        else:
            filtered_entity[field] = "[REDACTED]"

    return filtered_entity

// GDPR Right-to-Erasure support
function handle_erasure_request(data_source, record_id, request_reference):
    // 1. Log the erasure request
    audit_log("COMPLIANCE", {
        action:      "ERASURE_REQUEST",
        resource:    "record",
        resource_id: record_id,
        data_source: data_source,
        reason:      "GDPR erasure request: {request_reference}"
    })

    // 2. Delete the record from Senzing
    // This triggers re-evaluation of affected entities
    senzing_engine.delete_record(data_source, record_id)

    // 3. Process any redo records generated by the deletion
    process_redo_records()

    // 4. Log completion
    audit_log("COMPLIANCE", {
        action:      "ERASURE_COMPLETED",
        resource:    "record",
        resource_id: record_id,
        data_source: data_source,
        reason:      "GDPR erasure request: {request_reference}"
    })

    // 5. Verify the record is no longer in any entity
    // Search for the record to confirm deletion
    verify_record_deleted(data_source, record_id)
```

**Validation gate**: Before proceeding, verify:

- ✅ `SENZING_ENGINE_CONFIGURATION_JSON` is never logged or exposed
- ✅ Database user has least-privilege access
- ✅ License file is not in version control
- ✅ Entity resolution results are filtered by role
- ✅ GDPR erasure workflow implemented (if applicable)

## Step 10: Vulnerability Scanning

Run security scanning tools appropriate for `<chosen_language>`:

```bash
# Dependency audit — use your language's tool
# Python:     pip-audit
# Java:       mvn dependency-check:check
# C#:         dotnet list package --vulnerable
# Rust:       cargo audit
# TypeScript: npm audit

# Static analysis — use your language's tool
# Python:     bandit -r src/
# Java:       spotbugs (via Maven/Gradle plugin)
# C#:         dotnet format --verify-no-changes
# Rust:       cargo clippy -- -D warnings
# TypeScript: eslint --ext .ts src/ (with security plugin)

# Container scanning (if using Docker)
# trivy image your-senzing-image:latest

# Secret scanning — check for accidentally committed secrets
# git-secrets --scan
# trufflehog git file://. --only-verified
```

Ask: "Have you run the dependency audit and static analysis for `<chosen_language>`? Any findings we should address?"

WAIT for response.

Address any findings before proceeding.

## Step 11: Create Security Checklist

Document the complete security posture in `docs/security_checklist.md`:

```markdown
# Security Checklist

**Project**: [Project name]
**Date**: [Current date]
**Compliance posture**: [Minimal / Standard / Strict]
**Reviewed by**: [Name/role]

## Secrets Management
- [ ] No hard-coded credentials in source code
- [ ] Secrets stored in vault/manager (not just .env)
- [ ] .env file in .gitignore
- [ ] Secret rotation schedule defined
- [ ] SENZING_ENGINE_CONFIGURATION_JSON protected

## Authentication
- [ ] Authentication required for all API endpoints
- [ ] JWT tokens with expiration
- [ ] API keys hashed (never stored in plaintext)
- [ ] MFA enabled for administrative access
- [ ] Session timeout configured

## Authorization
- [ ] RBAC roles defined and documented
- [ ] Least privilege principle applied
- [ ] Permission checks on all operations
- [ ] Denied access attempts logged
- [ ] Regular access reviews scheduled

## Encryption
- [ ] TLS 1.2+ for all connections
- [ ] Database encryption at rest enabled
- [ ] PII fields encrypted at application layer (if required)
- [ ] Encryption keys in secrets manager
- [ ] Certificate rotation schedule defined

## Audit Logging
- [ ] All data access logged (who, what, when)
- [ ] PII never logged in cleartext
- [ ] Security events trigger alerts
- [ ] Log retention meets compliance requirements
- [ ] Logs are tamper-resistant

## Input Validation
- [ ] All record inputs validated before loading
- [ ] Search queries validated and rate-limited
- [ ] Injection patterns detected and blocked
- [ ] Log injection prevented

## Network Security
- [ ] Database not exposed to public internet
- [ ] Firewall rules restrict access to necessary ports
- [ ] Administrative access via VPN/bastion only
- [ ] Network architecture documented

## Senzing-Specific
- [ ] SENZING_ENGINE_CONFIGURATION_JSON never logged
- [ ] Database user has least-privilege access
- [ ] License file not in version control
- [ ] Entity results filtered by user role
- [ ] GDPR erasure workflow implemented (if applicable)

## Vulnerability Management
- [ ] Dependency audit passed
- [ ] Static analysis passed
- [ ] Container scan passed (if applicable)
- [ ] Secret scan passed
- [ ] Remediation plan for any findings
```

## Step 12: Security Review

Ask: "Do you have a security team or external auditor who should review this implementation? If so, I can prepare a security review package with architecture diagrams, control descriptions, and test evidence."

WAIT for response.

If a security review is needed, prepare `docs/security_review_package.md`:

```text
// Security review package contents:
// 1. Architecture diagram showing network tiers and data flows
// 2. Control matrix mapping compliance requirements to implementations
// 3. Secrets management approach and rotation schedule
// 4. Authentication and authorization model
// 5. Encryption strategy (at rest, in transit, field-level)
// 6. Audit logging configuration and retention policy
// 7. Vulnerability scan results
// 8. Incident response procedures
// 9. Data classification and handling procedures
// 10. Access control matrix (roles × permissions)
```

## Success Criteria

- ✅ Secrets management implemented (no hard-coded credentials anywhere)
- ✅ Authentication middleware created and tested
- ✅ RBAC authorization with Senzing-specific permissions
- ✅ Encryption configured (at rest, in transit, field-level if required)
- ✅ Comprehensive audit logging with compliance-specific events
- ✅ Input validation and injection prevention on all inputs
- ✅ Network security hardened (TLS, firewall, private network)
- ✅ Senzing-specific security concerns addressed
- ✅ Vulnerability scans passed
- ✅ Security checklist completed and documented
- ✅ Security review package prepared (if applicable)

## Transition

Once security hardening is complete, proceed to:

- **Module 11** (Monitoring and Observability) — monitor the secured system for anomalies, performance, and compliance
- If security review is pending, you can proceed to Module 11 in parallel while awaiting review feedback

"Module 10 is complete. Your entity resolution system now has production-grade security controls.

**Module 10 Complete ✅**

- ✅ Secrets management — credentials protected
- ✅ Authentication — access controlled
- ✅ Authorization — roles enforced
- ✅ Encryption — data protected at rest and in transit
- ✅ Audit logging — compliance trail established
- ✅ Input validation — injection attacks prevented
- ✅ Network security — attack surface minimized
- ✅ Senzing-specific — engine config, database, license, PII protected

**Common Issues to Watch For**:

- If secrets rotation breaks the application, check that `SENZING_ENGINE_CONFIGURATION_JSON` is updated when database passwords change
- If audit logs grow too large, configure log rotation and archival before they fill the disk
- If field-level encryption breaks entity resolution matching, verify you're only encrypting non-matching fields (SSN, passport) and NOT matching fields (name, address, phone)

Ready to move to Module 11 and set up monitoring and observability?"

## Troubleshooting

- **Senzing fails to initialize after adding secrets management**: Verify `SENZING_ENGINE_CONFIGURATION_JSON` is correctly retrieved from the secrets backend. Use `safe_log_engine_config()` to log a redacted version for debugging.
- **Authentication tokens rejected**: Check token expiration, issuer claim, and that the JWT secret matches between token generation and validation.
- **RBAC denying legitimate access**: Review the permissions matrix. Use audit logs to see which specific permission was denied. Ensure the user's role is correctly assigned in the token.
- **Field-level encryption breaks entity resolution**: You encrypted a matching field. Senzing needs cleartext for names, addresses, phone numbers, and email addresses to perform resolution. Only encrypt identifier fields (SSN, passport, driver's license) that are used for exact-match only.
- **Audit logs missing events**: Verify the audit logging middleware is applied to all routes, not just some. Check that async log writes are not being dropped.
- **TLS certificate errors**: Verify certificate chain is complete, certificate is not expired, and the hostname matches the certificate's Subject Alternative Name (SAN).
- **Database connection fails after enabling SSL**: Ensure the PostgreSQL server has SSL enabled (`ssl = on` in `postgresql.conf`), the client certificate is trusted, and the connection string includes `sslmode=verify-full` with the correct `sslrootcert` path.
- **Vulnerability scan finds issues in Senzing dependencies**: Check `search_docs(query='known vulnerabilities', version='current')` for Senzing-specific guidance. Some findings may be false positives or already mitigated.

## Agent Behavior

- Always call `search_docs` for the latest security guidance before recommending approaches
- Use `generate_scaffold` for any SDK code patterns — never hand-code Senzing method names
- NEVER log or display `SENZING_ENGINE_CONFIGURATION_JSON` in cleartext
- NEVER include real credentials, API keys, or secrets in code examples — always use placeholders
- Adapt all code examples to `<chosen_language>`
- For strict compliance (HIPAA, PCI-DSS), recommend vault integration over environment variables
- For minimal compliance, environment variables with `.env` files are acceptable
- Always recommend TLS 1.2+ — never suggest disabling TLS for convenience
- When discussing encryption, clearly distinguish between fields Senzing needs for matching (must be cleartext) and fields that can be encrypted
- Log security events but NEVER log PII in cleartext
- If the user is unsure about compliance requirements, help them identify applicable regulations based on their industry and data types
- Be thorough but not alarmist — security is about risk management, not perfection

### Important Rules for Security Hardening

- NEVER hard-code credentials — use `get_secret()` abstraction for all sensitive values
- NEVER log `SENZING_ENGINE_CONFIGURATION_JSON` — it contains database passwords
- NEVER encrypt fields that Senzing needs for matching (names, addresses, phone numbers, emails)
- NEVER store API keys in plaintext — always hash them
- NEVER expose the database to the public internet
- ALWAYS validate inputs before passing to Senzing SDK methods
- ALWAYS use TLS for all network connections
- ALWAYS log access to PII (but never log the PII itself)
- ALWAYS use `search_docs` and `generate_scaffold` for current Senzing patterns
