#!/bin/bash
# Senzing Boot Camp - Hook Installer
# Installs all recommended hooks with one command

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
POWER_HOOKS_DIR="$PROJECT_ROOT/senzing-bootcamp/hooks"
USER_HOOKS_DIR="$PROJECT_ROOT/.kiro/hooks"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  Senzing Boot Camp - Hook Installer                       ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if power hooks directory exists
if [ ! -d "$POWER_HOOKS_DIR" ]; then
    echo -e "${YELLOW}⚠ Power hooks directory not found: $POWER_HOOKS_DIR${NC}"
    echo "Make sure you're running this from a Senzing Boot Camp project."
    exit 1
fi

# Create user hooks directory if it doesn't exist
if [ ! -d "$USER_HOOKS_DIR" ]; then
    echo "Creating hooks directory: $USER_HOOKS_DIR"
    mkdir -p "$USER_HOOKS_DIR"
    echo -e "${GREEN}✓${NC} Created $USER_HOOKS_DIR"
    echo ""
fi

# List available hooks
echo -e "${CYAN}Available Hooks:${NC}"
echo ""

HOOKS=(
    "pep8-check.hook:PEP-8 Compliance Check:Ensures Python code follows PEP-8 standards"
    "data-quality-check.kiro.hook:Data Quality Check:Validates quality when transformations change"
    "backup-before-load.kiro.hook:Backup Before Load:Reminds to backup before loading"
    "validate-senzing-json.kiro.hook:Validate Senzing JSON:Validates output format against SGES"
    "backup-project-on-request.kiro.hook:Backup on Request:Auto-backup when user requests it"
)

for hook_info in "${HOOKS[@]}"; do
    IFS=':' read -r filename name description <<< "$hook_info"
    if [ -f "$POWER_HOOKS_DIR/$filename" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
        echo -e "    ${CYAN}→${NC} $description"
    else
        echo -e "  ${YELLOW}⚠${NC} $name (file not found)"
    fi
done

echo ""
echo -e "${CYAN}Installation Options:${NC}"
echo ""
echo "  A) Install all hooks (recommended)"
echo "  B) Install essential hooks only (PEP-8, backup)"
echo "  C) Select hooks individually"
echo "  Q) Quit"
echo ""
read -p "Choose an option (A/B/C/Q): " -n 1 -r
echo ""
echo ""

case $REPLY in
    [Aa])
        echo -e "${CYAN}Installing all hooks...${NC}"
        echo ""
        INSTALLED=0
        SKIPPED=0
        for hook_info in "${HOOKS[@]}"; do
            IFS=':' read -r filename name description <<< "$hook_info"
            if [ -f "$POWER_HOOKS_DIR/$filename" ]; then
                if [ -f "$USER_HOOKS_DIR/$filename" ]; then
                    echo -e "${YELLOW}⚠${NC} $name: already installed (skipping)"
                    ((SKIPPED++))
                else
                    cp "$POWER_HOOKS_DIR/$filename" "$USER_HOOKS_DIR/"
                    echo -e "${GREEN}✓${NC} $name: installed"
                    ((INSTALLED++))
                fi
            fi
        done
        echo ""
        echo -e "${GREEN}Installation complete!${NC}"
        echo "  Installed: $INSTALLED hooks"
        echo "  Skipped: $SKIPPED hooks (already installed)"
        ;;
    
    [Bb])
        echo -e "${CYAN}Installing essential hooks...${NC}"
        echo ""
        ESSENTIAL=("pep8-check.hook" "backup-before-load.kiro.hook" "backup-project-on-request.kiro.hook")
        INSTALLED=0
        for filename in "${ESSENTIAL[@]}"; do
            if [ -f "$POWER_HOOKS_DIR/$filename" ]; then
                if [ -f "$USER_HOOKS_DIR/$filename" ]; then
                    echo -e "${YELLOW}⚠${NC} $filename: already installed (skipping)"
                else
                    cp "$POWER_HOOKS_DIR/$filename" "$USER_HOOKS_DIR/"
                    echo -e "${GREEN}✓${NC} $filename: installed"
                    ((INSTALLED++))
                fi
            fi
        done
        echo ""
        echo -e "${GREEN}Installation complete!${NC}"
        echo "  Installed: $INSTALLED essential hooks"
        ;;
    
    [Cc])
        echo -e "${CYAN}Select hooks to install:${NC}"
        echo ""
        for hook_info in "${HOOKS[@]}"; do
            IFS=':' read -r filename name description <<< "$hook_info"
            if [ -f "$POWER_HOOKS_DIR/$filename" ]; then
                if [ -f "$USER_HOOKS_DIR/$filename" ]; then
                    echo -e "${YELLOW}⚠${NC} $name: already installed (skipping)"
                else
                    read -p "Install $name? (y/N): " -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        cp "$POWER_HOOKS_DIR/$filename" "$USER_HOOKS_DIR/"
                        echo -e "${GREEN}✓${NC} $name: installed"
                    else
                        echo -e "  $name: skipped"
                    fi
                fi
            fi
        done
        echo ""
        echo -e "${GREEN}Installation complete!${NC}"
        ;;
    
    [Qq])
        echo "Installation cancelled."
        exit 0
        ;;
    
    *)
        echo "Invalid option. Installation cancelled."
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Hooks are now active in your project"
echo "  2. View installed hooks: ls -la .kiro/hooks/"
echo "  3. Disable a hook: edit the .hook file and set 'enabled: false'"
echo "  4. Remove a hook: rm .kiro/hooks/<hook-name>.hook"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
