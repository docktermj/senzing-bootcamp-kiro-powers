#!/bin/bash
# Senzing Boot Camp - Prerequisites Checker
# Validates environment before starting modules

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  Senzing Boot Camp - Prerequisites Check                  ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# Function to check command
check_command() {
    local cmd=$1
    local name=$2
    local required=$3
    local install_hint=$4
    
    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -n1 || echo "unknown")
        echo -e "${GREEN}✓${NC} $name: ${GREEN}installed${NC} ($version)"
        ((PASSED++))
        return 0
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}✗${NC} $name: ${RED}NOT FOUND${NC} (required)"
            echo -e "  ${YELLOW}Install:${NC} $install_hint"
            ((FAILED++))
        else
            echo -e "${YELLOW}⚠${NC} $name: ${YELLOW}NOT FOUND${NC} (optional)"
            echo -e "  ${YELLOW}Install:${NC} $install_hint"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Function to check Python package
check_python_package() {
    local package=$1
    local name=$2
    local required=$3
    
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Python package '$name': ${GREEN}installed${NC}"
        ((PASSED++))
        return 0
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}✗${NC} Python package '$name': ${RED}NOT FOUND${NC} (required)"
            echo -e "  ${YELLOW}Install:${NC} pip install $package"
            ((FAILED++))
        else
            echo -e "${YELLOW}⚠${NC} Python package '$name': ${YELLOW}NOT FOUND${NC} (optional)"
            echo -e "  ${YELLOW}Install:${NC} pip install $package"
            ((WARNINGS++))
        fi
        return 1
    fi
}

echo -e "${BLUE}Core Requirements:${NC}"
echo ""

# Check Python
check_command "python3" "Python 3" "required" "sudo apt install python3 (Ubuntu) or brew install python3 (macOS)"

# Check pip
check_command "pip3" "pip" "required" "sudo apt install python3-pip (Ubuntu) or brew install python3 (macOS)"

# Check git
check_command "git" "Git" "required" "sudo apt install git (Ubuntu) or brew install git (macOS)"

# Check curl
check_command "curl" "curl" "required" "sudo apt install curl (Ubuntu) or brew install curl (macOS)"

# Check zip/unzip
check_command "zip" "zip" "required" "sudo apt install zip (Ubuntu) or brew install zip (macOS)"
check_command "unzip" "unzip" "required" "sudo apt install unzip (Ubuntu) or brew install unzip (macOS)"

echo ""
echo -e "${BLUE}Optional Tools:${NC}"
echo ""

# Check Docker
check_command "docker" "Docker" "optional" "https://docs.docker.com/get-docker/"

# Check PostgreSQL client
check_command "psql" "PostgreSQL client" "optional" "sudo apt install postgresql-client (Ubuntu) or brew install postgresql (macOS)"

# Check jq (for JSON processing)
check_command "jq" "jq (JSON processor)" "optional" "sudo apt install jq (Ubuntu) or brew install jq (macOS)"

echo ""
echo -e "${BLUE}Python Packages:${NC}"
echo ""

# Check if Python is available before checking packages
if command -v python3 &> /dev/null; then
    check_python_package "json" "json" "required"
    check_python_package "csv" "csv" "required"
    check_python_package "requests" "requests" "optional"
else
    echo -e "${YELLOW}⚠${NC} Skipping Python package checks (Python not found)"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}Directory Structure:${NC}"
echo ""

# Check for required directories
DIRS=("data/raw" "data/transformed" "database" "src" "scripts" "docs" "backups" "licenses")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} Directory '$dir': ${GREEN}exists${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Directory '$dir': ${YELLOW}missing${NC}"
        echo -e "  ${YELLOW}Create:${NC} mkdir -p $dir"
        ((WARNINGS++))
    fi
done

echo ""
echo -e "${BLUE}Configuration Files:${NC}"
echo ""

# Check for configuration files
if [ -f ".gitignore" ]; then
    echo -e "${GREEN}✓${NC} .gitignore: ${GREEN}exists${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} .gitignore: ${YELLOW}missing${NC}"
    ((WARNINGS++))
fi

if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓${NC} .env.example: ${GREEN}exists${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} .env.example: ${YELLOW}missing${NC}"
    ((WARNINGS++))
fi

if [ -f "README.md" ]; then
    echo -e "${GREEN}✓${NC} README.md: ${GREEN}exists${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} README.md: ${YELLOW}missing${NC}"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Summary
TOTAL=$((PASSED + FAILED + WARNINGS))
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

# Overall status
if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All prerequisites met! Ready to start the boot camp.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Some optional prerequisites missing, but you can proceed.${NC}"
        echo -e "${YELLOW}  Install optional tools for the best experience.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Missing required prerequisites. Please install them before starting.${NC}"
    exit 1
fi
