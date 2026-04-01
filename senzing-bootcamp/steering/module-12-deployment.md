---
inclusion: manual
---

# Module 12: Package and Deploy

**Purpose**: Package code and deploy to production.

**Prerequisites**:

- ✅ Module 11 complete (monitoring configured)
- ✅ All tests passing
- ✅ Deployment target confirmed

**Agent Workflow**:

> **Agent instruction:** Before starting deployment, check for anti-patterns:
> `search_docs(query="deployment", category="anti_patterns", version="current")`.
> Key pitfalls include Docker base image issues, wrong paths, and initialization patterns.

1. **Refactor code into package**:

   Organize code:

   ```text
   senzing_mdm/
   ├── __init__.py
   ├── transform/
   │   ├── __init__.py
   │   └── transformers.py
   ├── load/
   │   ├── __init__.py
   │   └── loaders.py
   ├── query/
   │   ├── __init__.py
   │   └── queries.py
   └── utils/
       ├── __init__.py
       └── config.py
   ```

2. **Create setup.py**:

   ```python
   from setuptools import setup, find_packages

   setup(
       name='senzing-mdm',
       version='1.0.0',
       packages=find_packages(),
       install_requires=[
           'senzing>=4.0.0',
           'pandas>=1.5.0',
           # Add dependencies
       ]
   )
   ```

3. **Create multi-environment configs**:

   ```text
   config/
   ├── dev/
   │   ├── senzing_config.json
   │   └── app_config.yaml
   ├── staging/
   │   ├── senzing_config.json
   │   └── app_config.yaml
   └── prod/
       ├── senzing_config.json
       └── app_config.yaml
   ```

4. **Create deployment scripts**:

   Create `deployment/scripts/deploy.sh`:

   ```bash
   #!/bin/bash
   set -e

   ENVIRONMENT=$1
   VERSION=$2

   echo "Deploying version $VERSION to $ENVIRONMENT"

   # Run tests
   pytest tests/

   # Build package
   python setup.py sdist bdist_wheel

   # Deploy (customize for your platform)
   # ...

   echo "Deployment complete!"
   ```

5. **Create CI/CD pipeline**:

   Use `find_examples(query="dockerfile")` for container build patterns using the official senzingsdk-runtime base image.

   Create `.github/workflows/ci.yml`:

   ```yaml
   name: CI

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Run tests
           run: pytest tests/
         - name: Security scan
           run: bandit -r src/
   ```

6. **Create disaster recovery plan**:

   Document in `docs/operations/disaster_recovery.md`:
   - Backup procedures
   - Recovery procedures
   - RTO/RPO targets
   - Failover process

7. **Deploy to staging**:

   ```bash
   ./deployment/scripts/deploy.sh staging 1.0.0
   ```

   Test in staging:
   - Run smoke tests
   - Verify monitoring
   - Check performance

8. **Deploy to production**:

   ```bash
   ./deployment/scripts/deploy.sh prod 1.0.0
   ```

   Monitor closely:
   - Watch dashboards
   - Check error rates
   - Verify functionality

9. **Create operations documentation**:

    Document in `docs/operations/`:
    - `deployment_guide.md` - How to deploy
    - `monitoring_guide.md` - How to monitor
    - `troubleshooting_guide.md` - Common issues
    - `maintenance_procedures.md` - Regular maintenance

**Success Criteria**:

- ✅ Code packaged and organized
- ✅ Multi-environment configs created
- ✅ Deployment scripts working
- ✅ CI/CD pipeline configured
- ✅ Deployed to staging successfully
- ✅ Deployed to production successfully
- ✅ Operations documentation complete

## Boot Camp Completion

When Module 12 is complete, congratulate the user and remind them about feedback:

- "Congratulations on completing the Senzing Boot Camp!"
- "If you have any feedback about your experience, say 'power feedback' or 'bootcamp feedback' and I'll help you document it"
- "If you've already documented feedback in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`, please share that file with the power author"
