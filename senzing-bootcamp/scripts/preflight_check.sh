#!/bin/bash
# Senzing Boot Camp Pre-flight Check

echo "=================================="
echo "SENZING BOOT CAMP PRE-FLIGHT CHECK"
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
    echo "You're ready to start the Senzing Boot Camp."
    exit 0
else
    echo "❌ PRE-FLIGHT CHECK FAILED"
    echo "Please fix the errors above before starting."
    exit 1
fi
