---
inclusion: manual
---

# Module 12: Package and Deploy

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md`.

## Workflow: Package, Deploy, and Go Live (Module 12)

Take the entity resolution pipeline built throughout the bootcamp and prepare it for production deployment. This module covers containerization, database migration, configuration management, CI/CD pipelines, API layers, scaling, and operational readiness.

**Language**: Use the bootcamper's chosen programming language from the language selection step. All code generation, scaffold calls, and examples in this module must use `<chosen_language>`.

**Prerequisites**:

- ✅ Module 11 complete (monitoring and observability configured)
- ✅ All tests passing (unit, integration, performance)
- ✅ Security hardening applied (Module 10)
- ✅ Performance benchmarks documented (Module 9)
- ✅ All data sources mapped and loading successfully (Modules 5-7)

**Cloud-aware guidance**: Read `cloud_provider` from `config/bootcamp_preferences.yaml`. If the bootcamper chose AWS, tailor deployment guidance to AWS services — use ECS or EKS for container orchestration, ECR for container registry, RDS/Aurora for database, and CodePipeline or GitHub Actions with AWS deployment targets for CI/CD. Adapt examples and MCP tool calls accordingly.

**Before starting**: The agent MUST call the following to check for known deployment pitfalls:

> **Agent instruction:** Call `search_docs(query='deployment', category='anti_patterns', version='current')` before giving any deployment advice. Key pitfalls include Docker base image issues, wrong SDK paths, initialization race conditions, and database connection pooling mistakes. Review the results and keep them in context throughout this module.

---

## Step 1: Gather Deployment Requirements

Before any packaging or deployment work, understand the target environment.

Ask: "What is your deployment target? Options include Docker containers, bare metal servers, cloud services (AWS/Azure/GCP), or Kubernetes. You can also combine these — for example, Docker containers orchestrated by Kubernetes."

WAIT for response before proceeding.

Ask: "What database will you use in production? PostgreSQL is strongly recommended for production workloads. If you've been using SQLite during the bootcamp, we'll migrate to PostgreSQL in this module."

WAIT for response before proceeding.

Ask: "Do you need a REST API layer for entity resolution queries? This is common when other applications or teams need to query resolved entities programmatically."

WAIT for response before proceeding.

Document the answers in `docs/deployment_plan.md`:

```text
# Deployment Plan

## Target Environment
- Deployment type: [Docker / Bare Metal / Cloud / Kubernetes]
- Cloud provider: [AWS / Azure / GCP / On-Premise / N/A]
- Operating system: [Ubuntu 22.04 / RHEL 9 / etc.]

## Database
- Engine: [PostgreSQL / SQLite (dev only)]
- Host: [hostname or managed service URL]
- Connection pooling: [PgBouncer / built-in / etc.]
- Backup strategy: [automated snapshots / pg_dump / etc.]

## API Layer
- Required: [Yes / No]
- Framework: [Flask / FastAPI / Spring Boot / ASP.NET / Actix / Express / etc.]
- Authentication: [JWT / OAuth 2.0 / API Key / etc.]

## Scaling Requirements
- Expected record volume: [number]
- Expected concurrent users: [number]
- Throughput target: [records/sec]
- Query latency target: [milliseconds]
```

---

## Step 2: Refactor Code into a Deployable Package

Organize the code built throughout the bootcamp into a clean, deployable package structure.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='full_pipeline', version='current')` to get the current recommended project structure and deployment patterns. Use the scaffold output as the foundation — do not hand-code SDK initialization or method calls.

Create the package structure:

```text
senzing_mdm/
├── __init__.[ext]              # Package initialization (language-appropriate)
├── transform/
│   ├── __init__.[ext]
│   └── transformers.[ext]      # All data transformation logic from Module 5
├── load/
│   ├── __init__.[ext]
│   └── loaders.[ext]           # Record loading logic from Modules 6-7
├── query/
│   ├── __init__.[ext]
│   └── queries.[ext]           # Entity query logic from Module 8
├── monitor/
│   ├── __init__.[ext]
│   └── metrics.[ext]           # Monitoring from Module 11
├── security/
│   ├── __init__.[ext]
│   └── auth.[ext]              # Security from Module 10
└── utils/
    ├── __init__.[ext]
    ├── config.[ext]            # Configuration loader
    └── logging_config.[ext]    # Structured logging from Module 11
```

Create a package configuration file appropriate for `<chosen_language>`:

```text
Package configuration should specify:
  - Package name: "senzing-mdm" (or user's chosen name)
  - Version: "1.0.0"
  - Description: "Senzing entity resolution pipeline"
  - Dependencies:
      - senzing SDK (>= 4.0.0)
      - database driver (e.g., psycopg2, pg driver for chosen language)
      - monitoring library (from Module 11)
      - web framework (if API layer requested)
      - any data processing libraries used in transformation
  - Entry points or main module declaration
  - Minimum language runtime version
```

Save the package configuration to the project root using the appropriate filename for `<chosen_language>` (e.g., `setup.py`/`pyproject.toml`, `package.json`, `pom.xml`, `Cargo.toml`, `*.csproj`).

---

## Step 3: Create Multi-Environment Configuration

Create environment-specific configurations that separate dev, staging, and production settings. Secrets must NEVER be stored in configuration files.

```text
config/
├── dev/
│   ├── senzing_config.json       # SQLite database, verbose logging
│   └── app_config.yaml           # Local settings, debug mode on
├── staging/
│   ├── senzing_config.json       # PostgreSQL, moderate logging
│   └── app_config.yaml           # Staging endpoints, debug mode off
└── prod/
    ├── senzing_config.json       # PostgreSQL, minimal logging
    └── app_config.yaml           # Production endpoints, optimized settings
```

Each `senzing_config.json` should contain the engine configuration for that environment:

```text
The engine configuration JSON structure includes:
  PIPELINE > CONFIGPATH:    path to Senzing configuration files
  PIPELINE > RESOURCEPATH:  path to Senzing resource files
  PIPELINE > SUPPORTPATH:   path to Senzing support files
  SQL > CONNECTION:          database connection string for the environment

For dev:    use SQLite at database/G2C.db
For staging: use PostgreSQL at the staging database host
For prod:   use PostgreSQL at the production database host
```

> **Agent instruction:** Do NOT hand-code the engine configuration JSON. Use
> `sdk_guide(topic='configure', platform='<user_platform>', language='<chosen_language>', version='current')`
> to generate the correct configuration for each environment. The MCP server provides correct
> paths and catches anti-patterns like wrong CONFIGPATH or RESOURCEPATH values.

Create a configuration loader in `src/utils/config.[ext]`:

```text
function load_config(environment):
    # environment is one of: "dev", "staging", "prod"
    # Determine from SENZING_ENVIRONMENT env var if not passed

    config_dir = "config/" + environment
    senzing_config = read_json(config_dir + "/senzing_config.json")
    app_config = read_yaml(config_dir + "/app_config.yaml")

    # Override with environment variables (secrets injection)
    if env var "SENZING_DB_PASSWORD" is set:
        replace password placeholder in senzing_config connection string

    if env var "SENZING_API_KEY" is set:
        set app_config api_key from env var

    validate_config(senzing_config)
    validate_config(app_config)

    return senzing_config, app_config

function validate_config(config):
    # Check required fields are present
    # Check paths exist on disk
    # Check database connection string format
    # Raise clear error if validation fails
```

**Secrets injection pattern**: Production secrets come from environment variables, a secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault), or Kubernetes secrets — never from config files checked into source control.

---

## Step 4: Containerization

> **Agent instruction:** Call `search_docs(query='docker quickstart', version='current')` for container deployment guidance. Then call `find_examples(query='dockerfile')` for container build patterns using the official `senzingsdk-runtime` base image. Also call `sdk_guide(topic='install', platform='docker', language='<chosen_language>', version='current')` for Docker-specific SDK setup instructions.

### 4a: Create the Dockerfile

Use the official `senzing/senzingsdk-runtime` base image. This image includes the Senzing SDK libraries pre-installed with correct paths.

**CRITICAL**: Do NOT install the Senzing SDK manually inside the container. The `senzingsdk-runtime` base image already has it. Installing it again causes path conflicts and version mismatches — this is the #1 deployment anti-pattern.

Create a multi-stage Dockerfile:

```Dockerfile
# ============================================================
# Stage 1: Build stage
# ============================================================
# Use a language-appropriate build image for compiling/packaging
# For Python: python:3.11-slim
# For Java: maven:3.9-eclipse-temurin-21
# For C#: mcr.microsoft.com/dotnet/sdk:8.0
# For Rust: rust:1.75-slim
# For TypeScript: node:20-slim

FROM <build_base_image> AS builder

WORKDIR /app

# Copy dependency manifests first (for Docker layer caching)
COPY <package_manifest_file> .
# e.g., requirements.txt, pom.xml, Cargo.toml, package.json, *.csproj

# Install dependencies
# e.g., pip install -r requirements.txt
#        mvn dependency:resolve
#        cargo build --release --dependencies-only
#        npm ci
#        dotnet restore

# Copy application source code
COPY senzing_mdm/ ./senzing_mdm/
COPY config/ ./config/
COPY src/ ./src/

# Build/compile if needed (Java, C#, Rust, TypeScript)
# e.g., mvn package -DskipTests
#        dotnet publish -c Release -o /app/publish
#        cargo build --release

# ============================================================
# Stage 2: Runtime stage
# ============================================================
FROM senzing/senzingsdk-runtime:latest AS runtime

WORKDIR /app

# Copy built application from builder stage
# Adjust paths based on language build output
COPY --from=builder /app/ .

# Copy configuration templates (secrets injected at runtime)
COPY config/ ./config/

# Set environment variables
ENV SENZING_ENVIRONMENT=prod
# Do NOT set database passwords here — inject at runtime

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD <health_check_command>
# e.g., python -c "import senzing; print('ok')"
#        curl -f http://localhost:8080/health
#        dotnet MyApp.dll --health-check

# Expose port if running API layer
# EXPOSE 8080

# Entry point
# e.g., CMD ["python", "-m", "senzing_mdm.main"]
#        CMD ["java", "-jar", "target/senzing-mdm.jar"]
#        CMD ["dotnet", "SenzingMdm.dll"]
#        CMD ["./target/release/senzing-mdm"]
#        CMD ["node", "dist/main.js"]
CMD [<runtime_command>]
```

### 4b: Create .dockerignore

```text
.git
.gitignore
__pycache__
*.pyc
node_modules
target/debug
bin/Debug
.env
data/raw/*
data/samples/*
database/*.db
docs/
tests/
*.md
.github/
monitoring/
```

### 4c: Build and Test the Container

```bash
# Build the image
docker build -t senzing-mdm:1.0.0 .

# Run with environment variables for secrets
docker run -d \
    --name senzing-mdm \
    -e SENZING_ENVIRONMENT=prod \
    -e SENZING_DB_HOST=your-db-host \
    -e SENZING_DB_PASSWORD=your-db-password \
    -e SENZING_DB_NAME=senzing \
    -p 8080:8080 \
    senzing-mdm:1.0.0

# Verify the container is healthy
docker ps
docker logs senzing-mdm

# Run health check manually
docker exec senzing-mdm <health_check_command>
```

### 4d: Create Docker Compose for Local Development

Create `docker-compose.yml` for running the full stack locally:

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: senzing
      POSTGRES_USER: senzing
      POSTGRES_PASSWORD: ${DB_PASSWORD:-senzing_dev}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U senzing"]
      interval: 10s
      timeout: 5s
      retries: 5

  senzing-mdm:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      SENZING_ENVIRONMENT: dev
      SENZING_DB_HOST: postgres
      SENZING_DB_PORT: 5432
      SENZING_DB_NAME: senzing
      SENZING_DB_USER: senzing
      SENZING_DB_PASSWORD: ${DB_PASSWORD:-senzing_dev}
    ports:
      - "8080:8080"

volumes:
  pgdata:
```

**Validation gate**: The container must start, pass its health check, and connect to the database before proceeding.

---

## Step 5: Database Migration (SQLite → PostgreSQL)

If the user has been using SQLite during the bootcamp and is moving to PostgreSQL for production, guide them through the migration.

> **Agent instruction:** Call `search_docs(query='database setup', version='current')` for production database configuration guidance. Use the results to ensure correct schema creation and connection string format.

### 5a: Set Up PostgreSQL

```text
function setup_postgresql():
    # 1. Create the Senzing database
    connect to PostgreSQL as admin user
    execute: CREATE DATABASE senzing
    execute: CREATE USER senzing_user WITH PASSWORD '<from_secrets_manager>'
    execute: GRANT ALL PRIVILEGES ON DATABASE senzing TO senzing_user

    # 2. Initialize the Senzing schema
    # The Senzing SDK creates its schema on first initialization
    # Just point the engine config at the new PostgreSQL database
    # and initialize — the SDK handles schema creation automatically

    # 3. Verify the schema was created
    connect to senzing database as senzing_user
    query: SELECT COUNT(*) FROM information_schema.tables
           WHERE table_schema = 'public'
    # Should return multiple Senzing system tables
```

### 5b: Migrate Configuration

The Senzing engine configuration (custom entity types, features, rules) from your SQLite development database needs to be exported and imported into PostgreSQL.

```text
function migrate_configuration():
    # 1. Export configuration from SQLite
    initialize Senzing engine with SQLite config (config/dev/senzing_config.json)
    export_config = engine.export_config()
    save export_config to file "config/exported_config.json"
    close engine

    # 2. Import configuration into PostgreSQL
    initialize Senzing engine with PostgreSQL config (config/prod/senzing_config.json)
    engine.import_config(export_config)
    close engine

    # 3. Verify configuration
    re-initialize with PostgreSQL config
    current_config = engine.export_config()
    compare current_config with export_config
    print "Configuration migration verified" if they match
```

### 5c: Reload Data

After migrating the database, reload all data sources using the transformation programs built in Module 5:

```text
function reload_all_data():
    initialize Senzing engine with production config

    for each data_source in transformed_data_files:
        print "Loading {data_source}..."
        load records from data/transformed/{data_source}.jsonl
        track count of loaded records
        track count of errors

    print "Reload complete: {total_loaded} records, {total_errors} errors"

    # Run redo processing to ensure all cross-source matches are resolved
    process_redo_records()

    close engine
```

### 5d: Validate Migration

```text
function validate_migration():
    # Compare entity counts between SQLite and PostgreSQL
    sqlite_entity_count = count entities in SQLite database
    postgres_entity_count = count entities in PostgreSQL database

    if counts match (within acceptable tolerance):
        print "Migration validated: entity counts match"
    else:
        print "WARNING: Entity count mismatch"
        print "SQLite: {sqlite_entity_count}, PostgreSQL: {postgres_entity_count}"
        print "Investigate before proceeding"

    # Spot-check a few known entities
    for each test_entity in known_test_entities:
        result = search for test_entity in PostgreSQL
        verify result matches expected resolution
```

**Validation gate**: Entity counts must match between SQLite and PostgreSQL (within 1% tolerance for timing differences) before proceeding.

---

## Step 6: CI/CD Pipeline

Create automated build, test, and deployment pipelines. The examples below cover GitHub Actions, GitLab CI, and Jenkins — use whichever matches the user's infrastructure.

### 6a: GitHub Actions

Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/senzing-mdm

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up runtime
        # Language-specific setup step
        # e.g., uses: actions/setup-python@v5
        #        uses: actions/setup-java@v4
        #        uses: actions/setup-node@v4
        #        uses: actions/setup-dotnet@v4
        run: echo "Set up <chosen_language> runtime"

      - name: Install dependencies
        run: |
          # Language-specific dependency install
          # e.g., pip install -r requirements.txt
          #        mvn dependency:resolve
          #        npm ci

      - name: Run linter
        run: |
          # Language-specific linting
          # e.g., flake8 src/, eslint src/, mvn checkstyle:check

      - name: Run unit tests
        run: |
          # Language-specific test runner
          # e.g., pytest tests/unit/
          #        mvn test
          #        npm test
          #        dotnet test
          #        cargo test

      - name: Run security scan
        run: |
          # Language-specific security scanning
          # e.g., pip-audit, npm audit, mvn dependency-check:check
          #        cargo audit, dotnet list package --vulnerable

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to container registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment"
          # Replace with your deployment mechanism:
          # - kubectl set image deployment/senzing-mdm ...
          # - aws ecs update-service ...
          # - ssh deploy@staging ./deploy.sh ...

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production environment"
          # Same mechanism as staging, targeting production
```

### 6b: GitLab CI (Alternative)

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - build
  - deploy-staging
  - deploy-production

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE/senzing-mdm:$CI_COMMIT_SHA

test:
  stage: test
  script:
    - echo "Install dependencies for <chosen_language>"
    - echo "Run linter"
    - echo "Run unit tests"
    - echo "Run security scan"

build:
  stage: build
  only:
    - main
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG

deploy-staging:
  stage: deploy-staging
  only:
    - main
  environment:
    name: staging
  script:
    - echo "Deploy $IMAGE_TAG to staging"

deploy-production:
  stage: deploy-production
  only:
    - main
  environment:
    name: production
  when: manual
  script:
    - echo "Deploy $IMAGE_TAG to production"
```

### 6c: Jenkins (Alternative)

Create `Jenkinsfile`:

```text
pipeline:
    agent: any

    stages:
        stage "Test":
            steps:
                run language-specific test suite
                run security scanning
                publish test results

        stage "Build":
            when: branch is "main"
            steps:
                build Docker image with tag from build number
                push image to container registry

        stage "Deploy to Staging":
            when: branch is "main"
            steps:
                deploy image to staging environment
                run smoke tests against staging
                report staging deployment status

        stage "Deploy to Production":
            when: branch is "main" AND manual approval
            steps:
                request manual approval from authorized deployer
                deploy image to production environment
                run smoke tests against production
                report production deployment status
```

**Validation gate**: The CI pipeline must successfully build the Docker image and pass all tests before proceeding to deployment steps.

---

## Step 7: REST API Layer (If Requested)

If the user indicated they need a REST API layer in Step 1, build one using a web framework appropriate for `<chosen_language>`.

Ask: "Which web framework would you like to use for the API? Common choices include Flask/FastAPI (Python), Spring Boot (Java), ASP.NET (C#), Actix/Axum (Rust), or Express/Fastify (TypeScript)."

WAIT for response before proceeding.

### 7a: API Structure

```text
src/api/
├── __init__.[ext]
├── app.[ext]              # Application factory and middleware setup
├── routes/
│   ├── __init__.[ext]
│   ├── entities.[ext]     # Entity resolution query endpoints
│   ├── records.[ext]      # Record loading endpoints
│   └── health.[ext]       # Health check and status endpoints
├── middleware/
│   ├── __init__.[ext]
│   ├── auth.[ext]         # Authentication middleware (from Module 10)
│   └── rate_limit.[ext]   # Rate limiting
└── models/
    ├── __init__.[ext]
    └── schemas.[ext]      # Request/response schemas
```

### 7b: Core API Endpoints

```text
# Health check endpoint
GET /health
    response: { "status": "healthy", "database": "connected", "senzing": "ready" }

# Search for entities by attributes
POST /entities/search
    request body: {
        "name": "John Smith",
        "address": "123 Main St",
        "phone": "555-1234"
    }
    response: {
        "entities": [
            {
                "entity_id": 12345,
                "entity_name": "John Smith",
                "record_count": 3,
                "data_sources": ["CRM", "SUPPORT"],
                "match_score": 95
            }
        ]
    }

# Get entity details by ID
GET /entities/{entity_id}
    response: {
        "entity_id": 12345,
        "resolved_entity": { ... },
        "related_entities": [ ... ],
        "records": [ ... ]
    }

# Explain why records matched
GET /entities/{entity_id}/why
    response: {
        "entity_id": 12345,
        "why_results": { ... }
    }

# Load a single record
POST /records
    request body: {
        "DATA_SOURCE": "CRM",
        "RECORD_ID": "1001",
        "NAME_FULL": "John Smith",
        "ADDR_FULL": "123 Main St, Las Vegas, NV 89101"
    }
    response: { "status": "loaded", "entity_id": 12345 }

# Delete a record
DELETE /records/{data_source}/{record_id}
    response: { "status": "deleted" }

# Get engine statistics
GET /stats
    response: { ... engine statistics ... }
```

### 7c: API Implementation Pattern

```text
function create_app(config):
    initialize web framework application
    configure CORS, request logging, error handlers

    # Initialize Senzing engine (once, shared across requests)
    senzing_engine = initialize_senzing(config.senzing_config)

    # Register middleware
    register authentication_middleware (from Module 10 auth)
    register rate_limiting_middleware (e.g., 100 requests/minute per client)
    register request_logging_middleware (structured JSON logs from Module 11)

    # Register routes
    register entity_routes(senzing_engine)
    register record_routes(senzing_engine)
    register health_routes(senzing_engine)

    return application

function search_entities_handler(request):
    validate request body against schema
    if validation fails:
        return 400 error with details

    search_attributes = build_senzing_search_json(request.body)
    results = senzing_engine.search_by_attributes(search_attributes)
    parsed_results = parse_search_response(results)

    return 200 with parsed_results

function get_entity_handler(request):
    entity_id = request.path_params["entity_id"]
    try:
        result = senzing_engine.get_entity_by_entity_id(entity_id)
        return 200 with parsed result
    catch entity_not_found:
        return 404 with "Entity not found"
    catch error:
        log error
        return 500 with "Internal server error"
```

### 7d: API Rate Limiting and Connection Management

```text
# Connection pool configuration
SENZING_ENGINE_POOL_SIZE = 10          # Number of engine instances
API_RATE_LIMIT = 100                    # Requests per minute per client
API_BURST_LIMIT = 20                    # Max burst requests
REQUEST_TIMEOUT_SECONDS = 30            # Per-request timeout

function initialize_engine_pool(pool_size, config):
    pool = create thread-safe pool of size pool_size
    for i in range(pool_size):
        engine = initialize_senzing(config)
        pool.add(engine)
    return pool

function handle_request_with_pool(pool, handler_function, request):
    engine = pool.acquire(timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        result = handler_function(engine, request)
        return result
    finally:
        pool.release(engine)
```

**Validation gate**: The API must respond to health checks, return correct search results for known test entities, and handle error cases gracefully before proceeding.

---

## Step 8: Scaling Guidance

Provide scaling recommendations based on the user's volume and throughput requirements from Step 1.

### 8a: Horizontal Scaling

```text
Scaling Strategy by Record Volume:

< 1 million records:
    - Single instance is sufficient
    - SQLite acceptable for dev/test, PostgreSQL for production
    - No special scaling needed

1-10 million records:
    - PostgreSQL required
    - Connection pooling recommended (PgBouncer or built-in)
    - Consider separating loading and querying workloads
    - Single instance with adequate CPU/RAM (8+ cores, 16+ GB RAM)

10-100 million records:
    - PostgreSQL with connection pooling required
    - Multiple loader instances for parallel ingestion
    - Dedicated query instances behind a load balancer
    - Database on SSD storage with adequate IOPS
    - 16+ cores, 64+ GB RAM per instance

> 100 million records:
    - Contact Senzing for enterprise guidance
    - Distributed database configuration
    - Multiple engine instances with shared database
    - Dedicated infrastructure planning required
```

### 8b: Connection Pooling

```text
function configure_connection_pool():
    # Database connection pool settings
    pool_config = {
        "min_connections": 5,
        "max_connections": 20,
        "connection_timeout_seconds": 30,
        "idle_timeout_seconds": 300,
        "max_lifetime_seconds": 3600
    }

    # For PgBouncer (recommended for high-concurrency):
    # pgbouncer_config:
    #   pool_mode = transaction
    #   max_client_conn = 200
    #   default_pool_size = 20
    #   reserve_pool_size = 5

    return pool_config
```

### 8c: Thread Management

```text
function configure_threading():
    # Senzing engine thread count should match available CPU cores
    # Each thread can process one record at a time

    available_cores = get_cpu_count()

    # For loading: use most cores for throughput
    loader_threads = available_cores - 2  # Reserve 2 for OS and monitoring

    # For querying: balance between concurrent queries and per-query speed
    query_threads = min(available_cores, max_concurrent_users)

    # For mixed workloads: split between loading and querying
    if mixed_workload:
        loader_threads = available_cores // 2
        query_threads = available_cores // 2

    return loader_threads, query_threads
```

### 8d: Kubernetes Deployment (If Applicable)

If the user chose Kubernetes as their deployment target, create the manifests:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: senzing-mdm
  labels:
    app: senzing-mdm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: senzing-mdm
  template:
    metadata:
      labels:
        app: senzing-mdm
    spec:
      containers:
        - name: senzing-mdm
          image: ghcr.io/your-org/senzing-mdm:latest
          ports:
            - containerPort: 8080
          env:
            - name: SENZING_ENVIRONMENT
              value: "prod"
            - name: SENZING_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: senzing-secrets
                  key: db-password
          resources:
            requests:
              memory: "4Gi"
              cpu: "2"
            limits:
              memory: "8Gi"
              cpu: "4"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: senzing-mdm
spec:
  selector:
    app: senzing-mdm
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
---
# k8s/secret.yaml (template — actual values injected by secrets manager)
apiVersion: v1
kind: Secret
metadata:
  name: senzing-secrets
type: Opaque
data:
  db-password: <base64-encoded-password>
```

---

## Step 9: Deployment Scripts

Create deployment scripts that automate the build, test, and deploy cycle.

### 9a: Main Deployment Script

Create `deployment/scripts/deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:?"Usage: deploy.sh <environment> <version>"}
VERSION=${2:?"Usage: deploy.sh <environment> <version>"}
IMAGE_NAME="senzing-mdm"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/your-org}"

echo "============================================"
echo "Deploying ${IMAGE_NAME}:${VERSION} to ${ENVIRONMENT}"
echo "============================================"

# Step 1: Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "ERROR: Invalid environment '$ENVIRONMENT'. Must be dev, staging, or prod."
    exit 1
fi

# Step 2: Run tests
echo "Running test suite..."
# Replace with your language's test command:
# pytest tests/ --tb=short
# mvn test
# npm test
# dotnet test
# cargo test
echo "Tests passed."

# Step 3: Build Docker image
echo "Building Docker image..."
docker build -t "${REGISTRY}/${IMAGE_NAME}:${VERSION}" .
docker tag "${REGISTRY}/${IMAGE_NAME}:${VERSION}" "${REGISTRY}/${IMAGE_NAME}:latest"

# Step 4: Push to registry
echo "Pushing to registry..."
docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
docker push "${REGISTRY}/${IMAGE_NAME}:latest"

# Step 5: Deploy to target environment
echo "Deploying to ${ENVIRONMENT}..."
# Customize for your infrastructure:
# kubectl set image deployment/senzing-mdm senzing-mdm=${REGISTRY}/${IMAGE_NAME}:${VERSION}
# aws ecs update-service --cluster senzing --service senzing-mdm --force-new-deployment
# docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

# Step 6: Wait for health check
echo "Waiting for health check..."
HEALTH_URL="https://${ENVIRONMENT}.your-domain.com/health"
for i in $(seq 1 30); do
    if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Health check failed after 30 attempts. Rolling back."
        # Trigger rollback (see Step 11)
        ./deployment/scripts/rollback.sh "${ENVIRONMENT}"
        exit 1
    fi
    echo "  Attempt $i/30 - waiting 10s..."
    sleep 10
done

# Step 7: Run smoke tests
echo "Running smoke tests..."
./deployment/scripts/smoke_test.sh "${ENVIRONMENT}"

echo "============================================"
echo "Deployment complete: ${IMAGE_NAME}:${VERSION} → ${ENVIRONMENT}"
echo "============================================"
```

### 9b: Smoke Test Script

Create `deployment/scripts/smoke_test.sh`:

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:?"Usage: smoke_test.sh <environment>"}
BASE_URL="https://${ENVIRONMENT}.your-domain.com"
FAILURES=0

echo "Running smoke tests against ${BASE_URL}..."

# Test 1: Health check
echo -n "  Health check... "
if curl -sf "${BASE_URL}/health" | grep -q "healthy"; then
    echo "PASS"
else
    echo "FAIL"
    FAILURES=$((FAILURES + 1))
fi

# Test 2: Search endpoint responds
echo -n "  Search endpoint... "
RESPONSE=$(curl -sf -X POST "${BASE_URL}/entities/search" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Entity"}' \
    -w "%{http_code}" -o /dev/null)
if [ "$RESPONSE" -eq 200 ] || [ "$RESPONSE" -eq 404 ]; then
    echo "PASS (HTTP ${RESPONSE})"
else
    echo "FAIL (HTTP ${RESPONSE})"
    FAILURES=$((FAILURES + 1))
fi

# Test 3: Stats endpoint responds
echo -n "  Stats endpoint... "
if curl -sf "${BASE_URL}/stats" > /dev/null; then
    echo "PASS"
else
    echo "FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""
if [ "$FAILURES" -gt 0 ]; then
    echo "SMOKE TESTS FAILED: ${FAILURES} failure(s)"
    exit 1
else
    echo "ALL SMOKE TESTS PASSED"
fi
```

---

## Step 10: Pre-Deployment Checklist

Before deploying to any environment, walk through this checklist with the user. Create `docs/operations/pre_deployment_checklist.md`:

```text
# Pre-Deployment Checklist

## Code Quality
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Linter passes with no errors
- [ ] No hard-coded credentials, API keys, or passwords in source code
- [ ] Code reviewed by at least one other person (if team)
- [ ] No TODO/FIXME items blocking deployment

## Configuration
- [ ] Environment-specific configs created (config/dev, config/staging, config/prod)
- [ ] Secrets stored in secrets manager (not in config files or env files)
- [ ] Database connection strings verified for target environment
- [ ] Senzing engine configuration validated with sdk_guide
- [ ] SENZING_ENGINE_CONFIGURATION_JSON paths are correct for container/host

## Database
- [ ] PostgreSQL set up and accessible from deployment target
- [ ] Senzing schema initialized (first engine init creates it)
- [ ] Database backups configured and tested
- [ ] Connection pooling configured (PgBouncer or built-in)
- [ ] Database user has correct permissions (not superuser)

## Container
- [ ] Dockerfile builds successfully
- [ ] Container starts and passes health check
- [ ] Container uses senzingsdk-runtime base image (not manual SDK install)
- [ ] .dockerignore excludes sensitive files and unnecessary data
- [ ] Container image scanned for vulnerabilities

## Monitoring (from Module 11)
- [ ] Metrics collection configured and reporting
- [ ] Dashboards created and accessible
- [ ] Alerts configured for error rates, latency, resource usage
- [ ] Health check endpoint implemented and tested
- [ ] Structured logging enabled (JSON format)

## Security (from Module 10)
- [ ] Authentication enabled on all API endpoints
- [ ] Authorization / RBAC configured
- [ ] TLS/SSL enabled for all connections
- [ ] Audit logging enabled
- [ ] Security scan passed (dependency audit, static analysis)
- [ ] PII handling compliant with requirements

## Operations
- [ ] Deployment scripts tested
- [ ] Rollback procedure documented and tested
- [ ] Runbooks created for common issues (from Module 11)
- [ ] On-call or support contact identified
- [ ] Disaster recovery plan documented

## Performance (from Module 9)
- [ ] Performance benchmarks meet requirements
- [ ] Load testing completed at expected volume
- [ ] Resource limits set (CPU, memory) in container/orchestrator
- [ ] Connection pool sizes tuned for expected concurrency
```

**Validation gate**: Every item on the checklist must be checked (or explicitly marked N/A with justification) before deploying to production. Staging deployments may skip some items for testing purposes.

---

## Step 11: Rollback Plan

Create a documented rollback procedure. This is critical — deployments fail, and you need a fast, reliable way to revert.

Create `docs/operations/rollback_plan.md`:

```text
# Rollback Plan

## When to Rollback
- Health checks failing after deployment
- Error rate exceeds threshold (e.g., > 5% of requests)
- Critical functionality broken (entity resolution returning wrong results)
- Performance degradation beyond acceptable limits
- Data corruption detected

## Rollback Procedure

### Step 1: Confirm Rollback Decision
- Identify the issue and confirm rollback is the right action
- Notify stakeholders (team, on-call, management as appropriate)
- Record the decision and reason in incident log

### Step 2: Identify Previous Good Version
- Check deployment history for last known good version
- Verify the previous version's container image is still available in registry

### Step 3: Execute Rollback
- For Docker: redeploy the previous image tag
- For Kubernetes: kubectl rollout undo deployment/senzing-mdm
- For ECS: update service to previous task definition
- For bare metal: restore previous application version from backup

### Step 4: Verify Rollback
- Run health checks against the rolled-back version
- Run smoke tests to confirm functionality
- Check error rates are back to normal
- Verify entity resolution results are correct

### Step 5: Post-Rollback
- Investigate root cause of the failed deployment
- Document findings in incident report
- Fix the issue in a new version
- Re-test thoroughly before attempting deployment again

## Rollback Time Targets
- Detection to decision: < 5 minutes
- Decision to rollback complete: < 15 minutes
- Rollback to verified healthy: < 30 minutes
- Total incident time target: < 1 hour
```

Create `deployment/scripts/rollback.sh`:

```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:?"Usage: rollback.sh <environment>"}
IMAGE_NAME="senzing-mdm"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/your-org}"

echo "============================================"
echo "ROLLING BACK ${ENVIRONMENT}"
echo "============================================"

# Get the previous version tag from deployment history
# This depends on your deployment mechanism:
# - Kubernetes: kubectl rollout undo deployment/senzing-mdm
# - Docker: docker service update --rollback senzing-mdm
# - ECS: aws ecs update-service --task-definition <previous>

echo "Rolling back to previous version..."
# kubectl rollout undo deployment/senzing-mdm -n ${ENVIRONMENT}

echo "Waiting for rollback to complete..."
# kubectl rollout status deployment/senzing-mdm -n ${ENVIRONMENT} --timeout=300s

echo "Running health check..."
./deployment/scripts/smoke_test.sh "${ENVIRONMENT}"

echo "============================================"
echo "Rollback complete for ${ENVIRONMENT}"
echo "============================================"
```

---

## Step 12: Deploy to Staging

With all preparation complete, deploy to the staging environment first.

```text
Staging Deployment Sequence:

1. Run the pre-deployment checklist (Step 10) for staging
2. Execute deployment:
       ./deployment/scripts/deploy.sh staging 1.0.0
3. Verify health checks pass
4. Run smoke tests:
       ./deployment/scripts/smoke_test.sh staging
5. Run integration tests against staging
6. Load a representative data sample and verify entity resolution results
7. Check monitoring dashboards for anomalies
8. Verify logging is working (structured JSON logs appearing)
9. Test the rollback procedure:
       ./deployment/scripts/rollback.sh staging
       (then redeploy to confirm rollback works)
10. Get sign-off from stakeholders before proceeding to production
```

Ask: "Staging deployment is complete. Have you verified the results and are you ready to proceed to production deployment?"

WAIT for response before proceeding.

---

## Step 13: Deploy to Production

```text
Production Deployment Sequence:

1. Run the FULL pre-deployment checklist (Step 10) — no items skipped
2. Notify stakeholders that production deployment is starting
3. Confirm rollback procedure is ready and tested
4. Execute deployment:
       ./deployment/scripts/deploy.sh prod 1.0.0
5. Monitor closely for the first 30 minutes:
       - Watch error rate dashboards
       - Check query latency
       - Verify entity resolution results with known test cases
       - Monitor resource usage (CPU, memory, disk, network)
6. Run smoke tests:
       ./deployment/scripts/smoke_test.sh prod
7. Verify end-to-end functionality:
       - Load a test record and verify it resolves correctly
       - Search for a known entity and verify results
       - Check that monitoring alerts are not firing
8. Notify stakeholders that deployment is complete
9. Keep heightened monitoring for 24 hours after deployment
```

---

## Step 14: Operations Documentation

Create comprehensive operations documentation for the team that will maintain the system.

```text
docs/operations/
├── deployment_guide.md          # How to deploy (references deploy.sh)
├── rollback_plan.md             # How to rollback (created in Step 11)
├── monitoring_guide.md          # How to read dashboards, respond to alerts
├── troubleshooting_guide.md     # Common issues and resolutions
├── maintenance_procedures.md    # Regular maintenance tasks
├── disaster_recovery.md         # Backup/restore procedures
└── runbooks/                    # From Module 11
    ├── high_cpu.md
    ├── slow_queries.md
    ├── data_quality_issues.md
    └── system_outage.md
```

Create `docs/operations/maintenance_procedures.md`:

```text
# Maintenance Procedures

## Daily
- Review monitoring dashboards for anomalies
- Check error logs for new issues
- Verify backup completion

## Weekly
- Review entity resolution statistics (new entities, merges, splits)
- Check database disk usage and growth trends
- Review security audit logs
- Process any redo records that accumulated

## Monthly
- Rotate secrets and API keys
- Update dependencies (security patches)
- Review and update alert thresholds
- Performance benchmark comparison with baseline
- Database maintenance (VACUUM, ANALYZE for PostgreSQL)

## Quarterly
- Full disaster recovery test
- Security audit and penetration test
- Capacity planning review
- Documentation review and update
```

---

## Troubleshooting

Common deployment issues and resolutions:

```text
Problem: Container fails to start
  Cause: Wrong base image or SDK path conflicts
  Fix: Ensure using senzing/senzingsdk-runtime base image
       Do NOT install SDK manually inside the container
       Check search_docs(query='deployment', category='anti_patterns')

Problem: "SENZING_ENGINE_CONFIGURATION_JSON" errors
  Cause: Incorrect paths in engine configuration
  Fix: Use sdk_guide(topic='configure') to generate correct config
       Paths inside containers differ from host paths
       CONFIGPATH, RESOURCEPATH, SUPPORTPATH must match container layout

Problem: Database connection refused
  Cause: Network configuration, wrong credentials, or pool exhaustion
  Fix: Verify database is accessible from container network
       Check connection string format
       Verify credentials via secrets manager
       Check connection pool settings (max connections)

Problem: Engine initialization hangs
  Cause: Database schema not created, or concurrent init race condition
  Fix: Ensure first initialization runs single-threaded
       Check database has Senzing schema tables
       Verify database user has CREATE TABLE permissions

Problem: Slow query performance in production
  Cause: Missing indexes, connection pool too small, insufficient resources
  Fix: Review Module 9 performance benchmarks
       Increase connection pool size
       Add database indexes per Senzing recommendations
       Scale horizontally if single instance is saturated

Problem: Health check fails intermittently
  Cause: Engine initialization not complete, or resource pressure
  Fix: Increase health check start-period and interval
       Check memory limits (Senzing needs adequate RAM)
       Verify no OOM kills in container logs

Problem: Records load but entities don't resolve as expected
  Cause: Configuration not migrated, or different config between environments
  Fix: Export config from working environment and import to target
       Verify config/prod/senzing_config.json matches expectations
       Run why_entity to debug specific match failures
```

For any SENZ error codes encountered during deployment, use `explain_error_code` with the error code for specific resolution guidance.

---

## Success Criteria

- ✅ Code refactored into deployable package structure
- ✅ Multi-environment configurations created (dev, staging, prod)
- ✅ Secrets management configured (no hard-coded credentials)
- ✅ Dockerfile created using `senzingsdk-runtime` base image
- ✅ Docker image builds and passes health checks
- ✅ Database migrated from SQLite to PostgreSQL (if applicable)
- ✅ CI/CD pipeline configured and working
- ✅ REST API layer deployed (if requested)
- ✅ Deployment scripts created and tested
- ✅ Pre-deployment checklist completed
- ✅ Rollback plan documented and tested
- ✅ Deployed to staging successfully with smoke tests passing
- ✅ Deployed to production successfully with smoke tests passing
- ✅ Operations documentation complete
- ✅ Monitoring confirmed working in production (from Module 11)

---

## Agent Behavior

- Always call `search_docs(query='deployment', category='anti_patterns', version='current')` before giving deployment advice
- Use `sdk_guide` and `generate_scaffold` for all SDK-related code — never hand-code initialization or method calls
- Use `find_examples(query='dockerfile')` for container patterns — do not guess Dockerfile structure
- WAIT for user responses at each "Ask and WAIT" point — do not assume deployment targets or database choices
- Recommend PostgreSQL for production, but respect the user's choice
- Never put secrets in configuration files, Dockerfiles, or source code
- Always create and test the rollback procedure before deploying to production
- Run smoke tests after every deployment (staging and production)
- If any validation gate fails, stop and resolve the issue before proceeding
- Use `explain_error_code` for any SENZ error codes encountered during deployment
- Keep the user informed of progress — deployment is stressful, clear communication helps

---

## Bootcamp Completion

When Module 12 is complete and the production deployment is verified, celebrate the user's achievement:

🎉 **Congratulations on completing the Senzing Bootcamp!** 🎉

You've built a complete entity resolution pipeline from scratch:

- **Module 0**: Installed and configured the Senzing SDK
- **Module 1**: Saw entity resolution in action with a live demo
- **Module 2**: Defined your business problem and data sources
- **Module 3**: Collected and organized your data
- **Module 4**: Evaluated data quality and compliance
- **Module 5**: Mapped your data to the Senzing entity format
- **Modules 6-7**: Loaded single and multi-source data with resolution
- **Module 8**: Built queries to validate and explore resolved entities
- **Module 9**: Benchmarked and optimized performance
- **Module 10**: Hardened security for production
- **Module 11**: Set up monitoring and observability
- **Module 12**: Packaged, deployed, and went live!

Your entity resolution system is now running in production. 🚀

If you have any feedback about your bootcamp experience, say **"power feedback"** or **"bootcamp feedback"** and I'll help you document it. Your feedback helps improve the bootcamp for future users.

If you've already documented feedback in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`, please share that file with the power author.
