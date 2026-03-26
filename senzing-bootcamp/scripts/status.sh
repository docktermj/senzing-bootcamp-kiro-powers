#!/bin/bash
# Senzing Boot Camp - Status Command
# Shows current module, progress, and next steps

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${CYAN}Senzing Boot Camp - Project Status${NC}                     ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if progress tracker exists
PROGRESS_FILE="docs/guides/PROGRESS_TRACKER.md"
if [ ! -f "$PROGRESS_FILE" ]; then
    echo -e "${YELLOW}⚠ Progress tracker not found${NC}"
    echo "Run: cp senzing-bootcamp/docs/guides/PROGRESS_TRACKER.md docs/guides/"
    echo ""
    exit 1
fi

# Parse progress tracker to find current module
CURRENT_MODULE=""
COMPLETED_MODULES=()
IN_PROGRESS_MODULE=""

while IFS= read -r line; do
    if [[ $line =~ \[x\].*Module\ ([0-9]+) ]]; then
        COMPLETED_MODULES+=("${BASH_REMATCH[1]}")
    elif [[ $line =~ \[\ \].*Module\ ([0-9]+) ]] && [ -z "$IN_PROGRESS_MODULE" ]; then
        IN_PROGRESS_MODULE="${BASH_REMATCH[1]}"
    fi
done < "$PROGRESS_FILE"

# Determine current status
if [ ${#COMPLETED_MODULES[@]} -eq 0 ]; then
    CURRENT_MODULE="0"
    STATUS="Not Started"
elif [ -n "$IN_PROGRESS_MODULE" ]; then
    CURRENT_MODULE="$IN_PROGRESS_MODULE"
    STATUS="In Progress"
else
    LAST_COMPLETED="${COMPLETED_MODULES[-1]}"
    CURRENT_MODULE=$((LAST_COMPLETED + 1))
    if [ $CURRENT_MODULE -gt 12 ]; then
        STATUS="Complete"
        CURRENT_MODULE="12"
    else
        STATUS="Ready to Start"
    fi
fi

# Calculate progress percentage
TOTAL_MODULES=13
COMPLETED_COUNT=${#COMPLETED_MODULES[@]}
PROGRESS_PCT=$((COMPLETED_COUNT * 100 / TOTAL_MODULES))

# Display current status
echo -e "${GREEN}Current Module:${NC} Module $CURRENT_MODULE"
echo -e "${GREEN}Status:${NC} $STATUS"
echo -e "${GREEN}Progress:${NC} $COMPLETED_COUNT/$TOTAL_MODULES modules ($PROGRESS_PCT%)"
echo ""

# Progress bar
BAR_WIDTH=50
FILLED=$((PROGRESS_PCT * BAR_WIDTH / 100))
EMPTY=$((BAR_WIDTH - FILLED))
printf "${GREEN}["
printf "%${FILLED}s" | tr ' ' '█'
printf "%${EMPTY}s" | tr ' ' '░'
printf "]${NC} ${PROGRESS_PCT}%%\n"
echo ""

# Show completed modules
if [ ${#COMPLETED_MODULES[@]} -gt 0 ]; then
    echo -e "${GREEN}✓ Completed Modules:${NC}"
    for mod in "${COMPLETED_MODULES[@]}"; do
        case $mod in
            0) echo "  ✓ Module 0: Quick Demo" ;;
            1) echo "  ✓ Module 1: Business Problem" ;;
            2) echo "  ✓ Module 2: Data Collection" ;;
            3) echo "  ✓ Module 3: Data Quality" ;;
            4) echo "  ✓ Module 4: Data Mapping" ;;
            5) echo "  ✓ Module 5: SDK Setup" ;;
            6) echo "  ✓ Module 6: Single Source Loading" ;;
            7) echo "  ✓ Module 7: Multi-Source Orchestration" ;;
            8) echo "  ✓ Module 8: Query & Validation" ;;
            9) echo "  ✓ Module 9: Performance Testing" ;;
            10) echo "  ✓ Module 10: Security Hardening" ;;
            11) echo "  ✓ Module 11: Monitoring" ;;
            12) echo "  ✓ Module 12: Deployment" ;;
        esac
    done
    echo ""
fi

# Show next steps
if [ $CURRENT_MODULE -le 12 ]; then
    echo -e "${CYAN}→ Next Steps:${NC}"
    case $CURRENT_MODULE in
        0)
            echo "  1. Start Module 0: Quick Demo (10-15 min)"
            echo "  2. See entity resolution in action with sample data"
            echo "  3. Command: Tell agent 'Start Module 0'"
            ;;
        1)
            echo "  1. Start Module 1: Business Problem (20-30 min)"
            echo "  2. Define your problem and identify data sources"
            echo "  3. Command: Tell agent 'Start Module 1'"
            ;;
        2)
            echo "  1. Start Module 2: Data Collection (10-15 min per source)"
            echo "  2. Upload or link to data source files"
            echo "  3. Command: Tell agent 'Start Module 2'"
            ;;
        3)
            echo "  1. Start Module 3: Data Quality (15-20 min per source)"
            echo "  2. Evaluate data quality with automated scoring"
            echo "  3. Command: Tell agent 'Start Module 3'"
            ;;
        4)
            echo "  1. Start Module 4: Data Mapping (1-2 hrs per source)"
            echo "  2. Create transformation programs"
            echo "  3. Command: Tell agent 'Start Module 4'"
            ;;
        5)
            echo "  1. Start Module 5: SDK Setup (30 min - 1 hr)"
            echo "  2. Install and configure Senzing SDK"
            echo "  3. Command: Tell agent 'Start Module 5'"
            ;;
        6)
            echo "  1. Start Module 6: Single Source Loading (30 min per source)"
            echo "  2. Load your first data source"
            echo "  3. Command: Tell agent 'Start Module 6'"
            ;;
        7)
            echo "  1. Start Module 7: Multi-Source Orchestration (1-2 hrs)"
            echo "  2. Manage dependencies between sources"
            echo "  3. Command: Tell agent 'Start Module 7'"
            ;;
        8)
            echo "  1. Start Module 8: Query & Validation (1-2 hrs)"
            echo "  2. Create query programs and validate results"
            echo "  3. Command: Tell agent 'Start Module 8'"
            ;;
        9)
            echo "  1. Start Module 9: Performance Testing (1-2 hrs)"
            echo "  2. Benchmark and optimize performance"
            echo "  3. Command: Tell agent 'Start Module 9'"
            ;;
        10)
            echo "  1. Start Module 10: Security Hardening (1-2 hrs)"
            echo "  2. Implement security best practices"
            echo "  3. Command: Tell agent 'Start Module 10'"
            ;;
        11)
            echo "  1. Start Module 11: Monitoring (1-2 hrs)"
            echo "  2. Set up monitoring and observability"
            echo "  3. Command: Tell agent 'Start Module 11'"
            ;;
        12)
            echo "  1. Start Module 12: Deployment (2-3 hrs)"
            echo "  2. Package and deploy to production"
            echo "  3. Command: Tell agent 'Start Module 12'"
            ;;
    esac
    echo ""
else
    echo -e "${GREEN}🎉 Boot Camp Complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy to production"
    echo "  2. Monitor performance"
    echo "  3. Share feedback: docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"
    echo ""
fi

# Show project health
echo -e "${CYAN}Project Health:${NC}"

# Check for key directories
HEALTH_SCORE=0
TOTAL_CHECKS=8

[ -d "data/raw" ] && echo "  ✓ Data directory exists" && ((HEALTH_SCORE++)) || echo "  ✗ Data directory missing"
[ -d "database" ] && echo "  ✓ Database directory exists" && ((HEALTH_SCORE++)) || echo "  ✗ Database directory missing"
[ -d "src" ] && echo "  ✓ Source directory exists" && ((HEALTH_SCORE++)) || echo "  ✗ Source directory missing"
[ -d "scripts" ] && echo "  ✓ Scripts directory exists" && ((HEALTH_SCORE++)) || echo "  ✗ Scripts directory missing"
[ -f ".gitignore" ] && echo "  ✓ .gitignore exists" && ((HEALTH_SCORE++)) || echo "  ✗ .gitignore missing"
[ -f ".env.example" ] && echo "  ✓ .env.example exists" && ((HEALTH_SCORE++)) || echo "  ✗ .env.example missing"
[ -f "README.md" ] && echo "  ✓ README.md exists" && ((HEALTH_SCORE++)) || echo "  ✗ README.md missing"
[ -d "backups" ] && echo "  ✓ Backups directory exists" && ((HEALTH_SCORE++)) || echo "  ✗ Backups directory missing"

HEALTH_PCT=$((HEALTH_SCORE * 100 / TOTAL_CHECKS))
echo ""
echo -e "${GREEN}Health Score:${NC} $HEALTH_SCORE/$TOTAL_CHECKS ($HEALTH_PCT%)"
echo ""

# Quick commands
echo -e "${CYAN}Quick Commands:${NC}"
echo "  status          - Show this status (./scripts/status.sh)"
echo "  backup          - Backup project (./scripts/backup_project.sh)"
echo "  resume          - Resume bootcamp (tell agent 'resume bootcamp')"
echo "  help            - Show help (tell agent 'bootcamp help')"
echo ""
