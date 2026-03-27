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

4. **Create Dockerfile** (if using containers):

   Create `docker/Dockerfile`:

   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .

   CMD ["python", "src/load/orchestrator.py"]
   ```

   Create `docker/docker-compose.yml`:

   ```yaml
   version: '3.8'
   services:
     senzing-api:
       build:
         context: ..
         dockerfile: docker/Dockerfile
       ports:
         - "8080:8080"
       environment:
         - CONFIG_FILE=/app/config/prod/senzing_config.json
   ```

5. **Create deployment scripts**:

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

6. **Create CI/CD pipeline**:

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

7. **Create disaster recovery plan**:

   Document in `docs/operations/disaster_recovery.md`:
   - Backup procedures
   - Recovery procedures
   - RTO/RPO targets
   - Failover process

8. **Deploy to staging**:

   ```bash
   ./deployment/scripts/deploy.sh staging 1.0.0
   ```

   Test in staging:
   - Run smoke tests
   - Verify monitoring
   - Check performance

9. **Deploy to production**:

   ```bash
   ./deployment/scripts/deploy.sh prod 1.0.0
   ```

   Monitor closely:
   - Watch dashboards
   - Check error rates
   - Verify functionality

10. **Create operations documentation**:

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
