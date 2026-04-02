# Module 12: Package and Deploy

> **Agent workflow:** The agent follows `steering/module-12-deployment.md` for this module's step-by-step workflow.

## Overview

Module 12 is the final module that packages your production-ready code and deploys it to the target environment. After completing security hardening (Module 10) and monitoring setup (Module 11), you're ready for deployment.

## Purpose

After completing Modules 0-11, you have:

- Working transformation, loading, and query code from Modules 5, 6, and 8
- Performance tested and optimized
- Security hardened
- Monitoring and observability configured

Module 12 takes this production-ready code and:

1. Refactors it into a clean, maintainable package structure
2. Adds comprehensive test coverage
3. Applies language-specific packaging standards
4. Generates deployment documentation
5. Prepares for production database migration
6. Creates deployment artifacts

## Workflow

### Step 1: Choose Deployment Configuration

**Decisions to make:**

1. **Target Database**
   - SQLite (evaluation only, not for production)
   - PostgreSQL (recommended for production)
   - MySQL
   - MS SQL Server
   - Oracle

2. **Programming Language**
   - Python (most common, easiest)
   - Java (enterprise environments)
   - C# (.NET environments)
   - Rust (performance-critical)

3. **Deployment Environment**
   - On-premises servers
   - Cloud (AWS, Azure, GCP)
   - Kubernetes
   - Serverless (Lambda, Azure Functions)

4. **Integration Pattern** (from Module 7)
   - Batch processing
   - REST API
   - Streaming/event-driven
   - Database sync
   - Microservice

### Step 2: Refactor Code Structure

Transform the boot camp code into a proper package structure:

#### Python Package Structure

```text
my-senzing-project/
├── setup.py                    # Package configuration
├── pyproject.toml              # Modern Python packaging
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # Project documentation
├── LICENSE                     # License file
├── .gitignore                  # Git ignore rules
├── my_senzing_project/         # Main package
│   ├── __init__.py
│   ├── __version__.py
│   ├── config.py               # Configuration management
│   ├── transform/              # Transformation module
│   │   ├── __init__.py
│   │   ├── base.py             # Base transformer class
│   │   └── customers.py        # Customer transformer
│   ├── load/                   # Loading module
│   │   ├── __init__.py
│   │   ├── loader.py           # Base loader class
│   │   └── batch_loader.py     # Batch loading implementation
│   ├── query/                  # Query module
│   │   ├── __init__.py
│   │   ├── client.py           # Senzing client wrapper
│   │   └── queries.py          # Business queries
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── logging.py          # Logging configuration
│       ├── database.py         # Database utilities
│       └── validation.py       # Data validation
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration
│   ├── test_transform/
│   │   ├── __init__.py
│   │   └── test_customers.py
│   ├── test_load/
│   │   ├── __init__.py
│   │   └── test_loader.py
│   └── test_query/
│       ├── __init__.py
│       └── test_queries.py
├── scripts/                    # Deployment scripts
│   ├── deploy.sh
│   ├── migrate_db.sh
│   └── run_pipeline.sh
├── config/                     # Configuration files
│   ├── config.yaml
│   ├── config.dev.yaml
│   ├── config.prod.yaml
│   └── logging.yaml
├── docs/                       # Documentation
│   ├── deployment.md
│   ├── api.md
│   ├── configuration.md
│   └── troubleshooting.md
└── data/                       # Data directories
    ├── raw/
    ├── transformed/
    └── backups/
```

#### Java Package Structure

```text
my-senzing-project/
├── pom.xml                     # Maven configuration
├── README.md
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/company/senzing/
│   │   │       ├── transform/
│   │   │       │   ├── Transformer.java
│   │   │       │   └── CustomerTransformer.java
│   │   │       ├── load/
│   │   │       │   ├── Loader.java
│   │   │       │   └── BatchLoader.java
│   │   │       ├── query/
│   │   │       │   ├── SenzingClient.java
│   │   │       │   └── BusinessQueries.java
│   │   │       └── util/
│   │   │           ├── Config.java
│   │   │           └── DatabaseUtil.java
│   │   └── resources/
│   │       ├── application.properties
│   │       └── logback.xml
│   └── test/
│       └── java/
│           └── com/company/senzing/
│               ├── transform/
│               ├── load/
│               └── query/
├── scripts/
└── docs/
```

#### C# Package Structure

```text
MySenzingProject/
├── MySenzingProject.sln        # Solution file
├── README.md
├── src/
│   ├── MySenzingProject/
│   │   ├── MySenzingProject.csproj
│   │   ├── Program.cs
│   │   ├── Transform/
│   │   │   ├── ITransformer.cs
│   │   │   └── CustomerTransformer.cs
│   │   ├── Load/
│   │   │   ├── ILoader.cs
│   │   │   └── BatchLoader.cs
│   │   ├── Query/
│   │   │   ├── ISenzingClient.cs
│   │   │   └── BusinessQueries.cs
│   │   └── Utils/
│   │       ├── Config.cs
│   │       └── DatabaseUtil.cs
│   └── MySenzingProject.Tests/
│       ├── MySenzingProject.Tests.csproj
│       ├── Transform/
│       ├── Load/
│       └── Query/
├── scripts/
└── docs/
```

### Step 3: Create Comprehensive Test Suite

Add tests for all components:

#### Unit Tests

- Test individual transformation functions
- Test data validation logic
- Test configuration loading
- Test utility functions

#### Integration Tests

- Test end-to-end transformation pipeline
- Test loading to Senzing
- Test query operations
- Test database connectivity

#### Data Quality Tests

- Validate transformed data format
- Check attribute coverage
- Verify data completeness
- Test error handling

#### Example Test (pseudocode)

```text
Test: "Basic customer transformation"
    Create a CustomerTransformer instance

    input_data = {
        customer_id: "12345",
        first_name:  "John",
        last_name:   "Doe",
        email:       "john.doe@example.com"
    }

    result = transformer.transform(input_data)

    Assert result.DATA_SOURCE  == "CUSTOMERS"
    Assert result.RECORD_ID    == "12345"
    Assert result.NAME_FULL    == "John Doe"
    Assert result.EMAIL_ADDRESS == "john.doe@example.com"

Test: "Handling missing fields"
    Create a CustomerTransformer instance

    input_data = {
        customer_id: "12345",
        first_name:  "John"
        // last_name is missing
    }

    result = transformer.transform(input_data)

    Assert result.NAME_FULL == "John"
    Assert "last_name" not in result

Test: "Handling invalid email"
    Create a CustomerTransformer instance

    input_data = {
        customer_id: "12345",
        first_name:  "John",
        last_name:   "Doe",
        email:       "invalid-email"
    }

    result = transformer.transform(input_data)

    // Should skip invalid email
    Assert "EMAIL_ADDRESS" not in result
```

### Step 4: Apply Language-Specific Packaging

#### Python (pip/PyPI)

Create `setup.py`:

```text
Define package configuration:
    name:         "my-senzing-project"
    version:      "1.0.0"
    description:  "Entity resolution solution using Senzing"
    python:       requires >= 3.10

    dependencies:
        senzing          >= 4.0.0
        pandas           >= 2.0.0
        orjson           >= 3.9.0
        pyyaml           >= 6.0
        psycopg2-binary  >= 2.9.0

    dev dependencies:
        pytest      >= 7.4.0
        pytest-cov  >= 4.1.0
        black       >= 23.0.0
        flake8      >= 6.0.0
        mypy        >= 1.0.0

    console entry points:
        senzing-transform → my_senzing_project.transform.cli:main
        senzing-load      → my_senzing_project.load.cli:main
        senzing-query     → my_senzing_project.query.cli:main
```

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-senzing-project"
version = "1.0.0"
description = "Entity resolution solution using Senzing"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

dependencies = [
    "senzing>=4.0.0",
    "pandas>=2.0.0",
    "orjson>=3.9.0",
    "pyyaml>=6.0",
    "psycopg2-binary>=2.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

[project.scripts]
senzing-transform = "my_senzing_project.transform.cli:main"
senzing-load = "my_senzing_project.load.cli:main"
senzing-query = "my_senzing_project.query.cli:main"
```

#### Java (Maven)

Create `pom.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.company</groupId>
    <artifactId>my-senzing-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>My Senzing Project</name>
    <description>Entity resolution solution using Senzing</description>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <senzing.version>4.0.0</senzing.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>com.senzing</groupId>
            <artifactId>senzing-api</artifactId>
            <version>${senzing.version}</version>
        </dependency>

        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <version>42.6.0</version>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <version>3.3.0</version>
                <configuration>
                    <archive>
                        <manifest>
                            <mainClass>com.company.senzing.Main</mainClass>
                        </manifest>
                    </archive>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

#### C# (NuGet)

Create `.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net6.0</TargetFramework>
    <PackageId>MySenzingProject</PackageId>
    <Version>1.0.0</Version>
    <Authors>Your Name</Authors>
    <Company>Your Company</Company>
    <Description>Entity resolution solution using Senzing</Description>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Senzing" Version="4.0.0" />
    <PackageReference Include="Npgsql" Version="7.0.0" />
    <PackageReference Include="Microsoft.Extensions.Configuration" Version="7.0.0" />
    <PackageReference Include="Microsoft.Extensions.Logging" Version="7.0.0" />
  </ItemGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.4.2" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.4.5" />
  </ItemGroup>
</Project>
```

### Step 5: Generate Deployment Documentation

Create comprehensive deployment documentation:

#### docs/deployment.md

```markdown
# Deployment Guide

## Prerequisites

- Python 3.10+ (or Java 17+, .NET Standard 2.0+)
- PostgreSQL 15+ (or chosen database)
- Senzing SDK 4.0+
- 4GB RAM minimum
- 50GB disk space

## Installation

### 1. Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Configure Database

\`\`\`bash
# Create database
createdb senzing_prod

# Run migrations
python scripts/migrate_db.py
\`\`\`

### 3. Configure Application

Copy and edit configuration:

\`\`\`bash
cp config/config.example.yaml config/config.prod.yaml
# Edit config.prod.yaml with your settings
\`\`\`

### 4. Run Tests

\`\`\`bash
pytest tests/
\`\`\`

### 5. Deploy

\`\`\`bash
./scripts/deploy.sh production
\`\`\`

## Configuration

See [configuration.md](configuration.md) for detailed configuration options.

## Monitoring

See [monitoring.md](monitoring.md) for monitoring setup.

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues.
```

### Step 6: Create Deployment Artifacts

Generate deployment-ready artifacts:

## Agent Behavior

When a user is in Module 12, the agent should:

1. **Assess Current Code**
   - Review code from Modules 5, 6, and 8

2. **Guide Deployment Decisions**
   - Help choose target database
   - Recommend programming language (if multiple options)
   - Suggest deployment environment
   - Recommend integration pattern

3. **Refactor Code Structure**
   - Create proper package structure for chosen language
   - Extract common functionality into utilities
   - Apply design patterns (Factory, Strategy, etc.)
   - Add configuration management
   - Implement proper logging

4. **Create Test Suite**
   - Generate unit tests for transformers
   - Create integration tests for loading
   - Add data quality tests
   - Set up test fixtures and mocks
   - Configure test runner (pytest, JUnit, xUnit)

5. **Apply Packaging Standards**
   - Create setup.py/pyproject.toml (Python)
   - Create pom.xml (Java)
   - Create .csproj (C#)
   - Create Cargo.toml (Rust)
   - Update requirements.txt/dependencies

6. **Generate Documentation**
   - Create deployment guide
   - Document configuration options
   - Write API documentation
   - Create troubleshooting guide
   - Document monitoring setup

7. **Create Deployment Artifacts**
   - Write deployment scripts
   - Create CI/CD pipeline configuration
   - Generate Kubernetes manifests (if applicable)

8. **Validate Package**
   - Run all tests
   - Check code quality (linting)
   - Verify documentation completeness
   - Test deployment process
   - Validate configuration

## Validation Gates

Before completing Module 12, verify:

- [ ] Code refactored into proper package structure
- [ ] All components have unit tests (>80% coverage)
- [ ] Integration tests pass
- [ ] Language-specific packaging applied
- [ ] Deployment documentation complete
- [ ] Deployment scripts created
- [ ] Configuration management implemented
- [ ] Logging configured
- [ ] Error handling comprehensive
- [ ] Code quality checks pass (linting, type checking)
- [ ] Deployment tested in staging environment

## Success Indicators

Module 12 is complete when:

- Package can be installed via standard package manager
- All tests pass
- Deployment documentation is comprehensive
- Code follows language best practices
- Deployment artifacts are ready
- Configuration is externalized
- Monitoring and logging are configured
- Ready for production deployment

## Common Issues

### Issue: Test Coverage Too Low

**Solution:** Add tests for untested code paths, focus on critical business logic first

### Issue: Package Installation Fails

**Solution:** Verify all dependencies are listed, check version constraints

### Issue: Configuration Management Complex

**Solution**: Use environment variables for secrets, YAML for structure, provide examples

## Integration with Other Modules

- **From Module 5**: Refactor transformation code
- **From Module 6**: Refactor loading code
- **From Module 8**: Refactor query code
- **To Production**: Deploy packaged application

## Tools and Resources

### Python

- **Packaging:** setuptools, poetry, flit
- **Testing**: pytest, unittest, coverage.py
- **Linting**: flake8, pylint, black
- **Type checking**: mypy

### Java

- **Packaging:** Maven, Gradle
- **Testing**: JUnit, TestNG, Mockito
- **Build**: Maven Surefire, Gradle Test
- **Quality**: SonarQube, Checkstyle

### C sharp

- **Packaging:** NuGet
- **Testing**: xUnit, NUnit, MSTest
- **Build**: MSBuild, dotnet CLI
- **Quality**: SonarQube, StyleCop

## Related Documentation

- `POWER.md` - Module 12 overview
- `steering/module-12-deployment.md` - Module 12 workflow
- `steering/agent-instructions.md` - Agent behavior for Module 12
- Use MCP: `find_examples(query="API integration")` for deployment patterns
- `DEPENDENCY_MANAGEMENT_POLICY.md` - Dependency management

## Version History

- **v2.0.0** (2026-03-17): Module 12 added to boot camp structure
