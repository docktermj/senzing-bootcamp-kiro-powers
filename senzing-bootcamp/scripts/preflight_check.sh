#!/bin/bash
# Senzing Boot Camp Pre-flight Check
# Checks core system requirements (language-agnostic)

echo "=================================="
echo "SENZING BOOT CAMP PRE-FLIGHT CHECK"
echo "=================================="
echo ""

ERRORS=0
WARNINGS=0

# Check for at least one supported language runtime
echo "Checking language runtimes..."
LANG_FOUND=0
if command -v python3 &> /dev/null; then
    echo "✅ Python $(python3 --version 2>&1 | cut -d' ' -f2) installed"
    LANG_FOUND=1
fi
if command -v java &> /dev/null; then
    echo "✅ Java $(java --version 2>&1 | head -1) installed"
    LANG_FOUND=1
fi
if command -v dotnet &> /dev/null; then
    echo "✅ .NET $(dotnet --version 2>&1) installed"
    LANG_FOUND=1
fi
if command -v rustc &> /dev/null; then
    echo "✅ Rust $(rustc --version 2>&1 | cut -d' ' -f2) installed"
    LANG_FOUND=1
fi
if command -v node &> /dev/null; then
    echo "✅ Node.js $(node --version 2>&1) installed"
    LANG_FOUND=1
fi
if [ $LANG_FOUND -eq 0 ]; then
    echo "❌ No supported language runtime found"
    echo "   Install one of: Python 3.10+, Java 17+, .NET SDK, Rust, or Node.js"
    ((ERRORS++))
fi
echo ""

# Check disk space
echo "Checking disk space..."
AVAILABLE=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
if [ -n "$AVAILABLE" ] && [ "$AVAILABLE" -ge 10 ] 2>/dev/null; then
    echo "✅ ${AVAILABLE}GB available (10GB+ required)"
else
    echo "⚠️  Could not verify disk space (10GB+ recommended)"
    ((WARNINGS++))
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

# Check PostgreSQL
echo "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client installed"
else
    echo "ℹ️  PostgreSQL not found (optional — SQLite works for evaluation)"
fi
echo ""

# Check write permissions
echo "Checking permissions..."
if mkdir -p test_preflight 2>/dev/null && rmdir test_preflight 2>/dev/null; then
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
    echo "The agent will ask which language you'd like to use."
    exit 0
else
    echo "❌ PRE-FLIGHT CHECK FAILED"
    echo "Please fix the errors above before starting."
    exit 1
fi
