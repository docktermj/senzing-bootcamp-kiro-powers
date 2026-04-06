# Pre-flight Checklist

Complete this checklist before starting the Senzing Bootcamp to ensure your environment is ready.

## Quick Check

Run the automated pre-flight check:

```bash
bash scripts/preflight_check.sh
```

Or manually verify each item below.

---

## System Requirements

### Operating System

- [ ] **Linux** (Ubuntu 20.04+, RHEL 8+, or similar)
- [ ] **macOS** (10.15+ for development only)
- [ ] **Windows** (WSL2 required)

**Check**:

```bash
uname -a
```

---

### Python Version

- [ ] **Python 3.8 or higher** installed
- [ ] **pip** package manager available

**Check**:

```bash
python --version  # Should be 3.8+
python3 --version
pip --version
```

**Fix if needed**:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# macOS
brew install python3

# Windows (WSL2)
sudo apt update
sudo apt install python3 python3-pip
```

---

### Disk Space

- [ ] **Minimum 10GB free** for development
- [ ] **50GB+ free** for production with large datasets

**Check**:

```bash
df -h .
```

**Recommended**:

- Development: 20GB
- Production: 100GB+

---

### Memory (RAM)

- [ ] **Minimum 4GB** for development
- [ ] **8GB+** for production

**Check**:

```bash
# Linux
free -h

# macOS
sysctl hw.memsize
```

**Recommended**:

- Development: 8GB
- Production: 16GB+

---

### CPU

- [ ] **Minimum 2 cores**
- [ ] **4+ cores** recommended

**Check**:

```bash
# Linux
nproc

# macOS
sysctl -n hw.ncpu
```

---

## Software Dependencies

### Git (Optional but Recommended)

- [ ] **Git** installed for version control

**Check**:

```bash
git --version
```

**Install if needed**:

```bash
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git

# Windows (WSL2)
sudo apt install git
```

---

### Docker (If Using Containers)

- [ ] **Docker** installed and running
- [ ] **Docker Compose** installed
- [ ] **User has Docker permissions**

**Check**:

```bash
docker --version
docker-compose --version
docker ps  # Should not require sudo
```

**Install if needed**:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# macOS
brew install --cask docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

### PostgreSQL (If Using PostgreSQL)

- [ ] **PostgreSQL 12+** installed (if not using Docker)
- [ ] **psycopg2** Python library available

**Check**:

```bash
psql --version
python -c "import psycopg2; print('psycopg2 available')"
```

**Install if needed**:

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
pip install psycopg2-binary

# macOS
brew install postgresql
pip install psycopg2-binary
```

---

## Network Access

### Internet Connectivity

- [ ] **Internet access** for downloading packages
- [ ] **No restrictive firewall** blocking package repositories

**Check**:

```bash
ping -c 3 google.com
curl -I https://pypi.org
```

---

### Port Availability

- [ ] **Port 5432** available (PostgreSQL)
- [ ] **Port 8080** available (if running API)

**Check**:

```bash
# Check if ports are in use
sudo lsof -i :5432
sudo lsof -i :8080

# Or
netstat -tuln | grep 5432
netstat -tuln | grep 8080
```

---

## Permissions

### File System Permissions

- [ ] **Write access** to working directory
- [ ] **Create directories** permission

**Check**:

```bash
mkdir test_dir && rmdir test_dir && echo "✅ Permissions OK"
```

---

### System Permissions

- [ ] **Can install packages** (sudo access or virtual environment)
- [ ] **Can run Docker** (if using containers)

**Check**:

```bash
# Test sudo (if needed)
sudo echo "✅ Sudo access OK"

# Test Docker (if using)
docker run hello-world
```

---

## Python Environment

### Virtual Environment (Recommended)

- [ ] **Can create virtual environments**

**Check**:

```bash
python -m venv test_venv
source test_venv/bin/activate
deactivate
rm -rf test_venv
echo "✅ Virtual environment OK"
```

---

### Required Python Packages

- [ ] **Can install Python packages**

**Check**:

```bash
pip install --dry-run senzing
```

**Note**: Don't actually install yet, just verify pip works.

---

## Data Preparation

### Data Access

- [ ] **Have access to data sources** identified in Module 1
- [ ] **Data is in accessible format** (CSV, JSON, database, API)
- [ ] **Have necessary credentials** for data access

---

### Data Privacy

- [ ] **Understand data privacy requirements**
- [ ] **Have permission to use data** for testing
- [ ] **Know if data contains PII** (Personally Identifiable Information)
- [ ] **Have anonymization plan** if needed

---

## Knowledge Prerequisites

### Senzing Concepts

- [ ] **Read POWER.md** overview
- [ ] **Understand entity resolution** basics
- [ ] **Reviewed Quick Start guide**

---

### Technical Skills

- [ ] **Basic command line** usage
- [ ] **Basic Python** (if writing custom code)
- [ ] **Basic SQL** (if using databases)
- [ ] **Basic Docker** (if using containers)

**Note**: Don't worry if you're not an expert. The bootcamp will guide you!

---

## Optional but Recommended

### Development Tools

- [ ] **Code editor** (VS Code, PyCharm, etc.)
- [ ] **Database client** (DBeaver, pgAdmin, etc.)
- [ ] **Git client** (command line or GUI)

---

### Documentation Access

- [ ] **Can access Senzing documentation** (online or offline)
- [ ] **Have MCP server access** for AI assistance

---

## Pre-flight Check Summary

### Critical (Must Have)

- ✅ Python 3.8+
- ✅ 10GB+ disk space
- ✅ 4GB+ RAM
- ✅ Internet access
- ✅ Write permissions

### Recommended (Should Have)

- ✅ Git installed
- ✅ Virtual environment capability
- ✅ 20GB+ disk space
- ✅ 8GB+ RAM
- ✅ Docker (if using containers)

### Optional (Nice to Have)

- ✅ Code editor
- ✅ Database client
- ✅ PostgreSQL installed

---

## Automated Pre-flight Check Script

Save this as `scripts/preflight_check.sh`:

```bash
#!/bin/bash
# Senzing Bootcamp Pre-flight Check

echo "=================================="
echo "SENZING BOOTCAMP PRE-FLIGHT CHECK "
echo "=================================="
echo ""

ERRORS=0
WARNINGS=0

# Check Python
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION installed"

    # Check version is 3.8+
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
        echo "❌ Python 3.8+ required (found $PYTHON_VERSION)"
        ((ERRORS++))
    fi
else
    echo "❌ Python not found"
    ((ERRORS++))
fi
echo ""

# Check pip
echo "Checking pip..."
if command -v pip3 &> /dev/null; then
    echo "✅ pip installed"
else
    echo "❌ pip not found"
    ((ERRORS++))
fi
echo ""

# Check disk space
echo "Checking disk space..."
AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE" -ge 10 ]; then
    echo "✅ ${AVAILABLE}GB available (10GB+ required)"
else
    echo "❌ Only ${AVAILABLE}GB available (10GB+ required)"
    ((ERRORS++))
fi
echo ""

# Check memory
echo "Checking memory..."
if command -v free &> /dev/null; then
    TOTAL_MEM=$(free -g | grep Mem | awk '{print $2}')
    if [ "$TOTAL_MEM" -ge 4 ]; then
        echo "✅ ${TOTAL_MEM}GB RAM (4GB+ required)"
    else
        echo "⚠️  Only ${TOTAL_MEM}GB RAM (4GB+ recommended)"
        ((WARNINGS++))
    fi
else
    echo "⚠️  Cannot check memory (Linux only)"
    ((WARNINGS++))
fi
echo ""

# Check Git
echo "Checking Git..."
if command -v git &> /dev/null; then
    echo "✅ Git installed"
else
    echo "⚠️  Git not found (recommended)"
    ((WARNINGS++))
fi
echo ""

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        echo "✅ Docker installed and running"
    else
        echo "⚠️  Docker installed but not running or no permissions"
        ((WARNINGS++))
    fi
else
    echo "ℹ️  Docker not found (optional)"
fi
echo ""

# Check PostgreSQL
echo "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client installed"
else
    echo "ℹ️  PostgreSQL not found (optional)"
fi
echo ""

# Check write permissions
echo "Checking permissions..."
if mkdir -p test_preflight && rmdir test_preflight; then
    echo "✅ Write permissions OK"
else
    echo "❌ Cannot write to current directory"
    ((ERRORS++))
fi
echo ""

# Summary
echo "=================================="
echo "SUMMARY"
echo "=================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ PRE-FLIGHT CHECK PASSED!"
    echo "You're ready to start the Senzing Bootcamp."
    exit 0
else
    echo "❌ PRE-FLIGHT CHECK FAILED"
    echo "Please fix the errors above before starting."
    exit 1
fi
```

Make it executable:

```bash
chmod +x scripts/preflight_check.sh
```

---

## What to Do If Checks Fail

### Python Issues

**Problem**: Python not found or wrong version

**Solution**:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3-pip

# macOS
brew install python@3.10

# Verify
python3 --version
```

---

### Disk Space Issues

**Problem**: Not enough disk space

**Solution**:

1. Clean up unnecessary files
2. Use external drive
3. Use cloud storage for data
4. Delete old Docker images: `docker system prune -a`

---

### Memory Issues

**Problem**: Not enough RAM

**Solution**:

1. Close unnecessary applications
2. Use smaller sample datasets
3. Upgrade RAM (if possible)
4. Use cloud instance with more memory

---

### Permission Issues

**Problem**: Cannot write files or install packages

**Solution**:

```bash
# Use virtual environment (no sudo needed)
python3 -m venv venv
source venv/bin/activate
pip install senzing

# Or fix directory permissions
sudo chown -R $USER:$USER .
```

---

### Docker Issues

**Problem**: Docker not running or permission denied

**Solution**:

```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in

# Verify
docker run hello-world
```

---

## Ready to Start

Once all critical checks pass:

1. ✅ Review [QUICK_START.md](QUICK_START.md)
2. ✅ Read [ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)
3. ✅ Start with Module 0 (Quick Demo) or Module 1 (Business Problem)

---

## Related Documentation

- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md) - Onboarding steps
- [POWER.md](../../POWER.md) - Bootcamp overview
- [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md) - SDK installation

## Version History

- **v1.0.0** (2026-03-17): Pre-flight checklist created
