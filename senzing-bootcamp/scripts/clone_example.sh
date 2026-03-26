#!/bin/bash
# Senzing Boot Camp - Example Project Cloner
# Copies an example project to user's workspace

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXAMPLES_DIR="$PROJECT_ROOT/senzing-bootcamp/examples"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  Senzing Boot Camp - Example Project Cloner               ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if examples directory exists
if [ ! -d "$EXAMPLES_DIR" ]; then
    echo -e "${RED}✗ Examples directory not found: $EXAMPLES_DIR${NC}"
    exit 1
fi

# List available examples
echo -e "${CYAN}Available Example Projects:${NC}"
echo ""

EXAMPLES=(
    "simple-single-source:Simple Single Source:Basic customer deduplication (2-3 hours)"
    "multi-source-project:Multi-Source Project:Customer 360 with three sources (6-8 hours)"
    "production-deployment:Production Deployment:Complete production-ready system (12-15 hours)"
)

INDEX=1
for example_info in "${EXAMPLES[@]}"; do
    IFS=':' read -r dirname name description <<< "$example_info"
    if [ -d "$EXAMPLES_DIR/$dirname" ]; then
        echo -e "  ${GREEN}$INDEX)${NC} ${CYAN}$name${NC}"
        echo -e "     $description"
        echo ""
    fi
    ((INDEX++))
done

echo -e "${CYAN}Options:${NC}"
echo "  1-3) Clone an example project"
echo "  Q) Quit"
echo ""
read -p "Choose an option (1-3/Q): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        EXAMPLE_DIR="simple-single-source"
        EXAMPLE_NAME="Simple Single Source"
        ;;
    2)
        EXAMPLE_DIR="multi-source-project"
        EXAMPLE_NAME="Multi-Source Project"
        ;;
    3)
        EXAMPLE_DIR="production-deployment"
        EXAMPLE_NAME="Production Deployment"
        ;;
    [Qq])
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac

SOURCE_DIR="$EXAMPLES_DIR/$EXAMPLE_DIR"

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}✗ Example not found: $SOURCE_DIR${NC}"
    exit 1
fi

# Ask for destination
echo -e "${CYAN}Clone '$EXAMPLE_NAME' to:${NC}"
echo ""
echo "  A) Current project (merge with existing files)"
echo "  B) New directory (create separate copy)"
echo "  Q) Quit"
echo ""
read -p "Choose an option (A/B/Q): " -n 1 -r
echo ""
echo ""

case $REPLY in
    [Aa])
        DEST_DIR="$PROJECT_ROOT"
        echo -e "${YELLOW}⚠ Warning: This will merge files into your current project${NC}"
        read -p "Continue? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled."
            exit 0
        fi
        ;;
    
    [Bb])
        read -p "Enter directory name: " DIR_NAME
        DEST_DIR="$PROJECT_ROOT/$DIR_NAME"
        if [ -d "$DEST_DIR" ]; then
            echo -e "${RED}✗ Directory already exists: $DEST_DIR${NC}"
            exit 1
        fi
        mkdir -p "$DEST_DIR"
        echo -e "${GREEN}✓${NC} Created directory: $DEST_DIR"
        ;;
    
    [Qq])
        echo "Cancelled."
        exit 0
        ;;
    
    *)
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}Cloning example project...${NC}"
echo ""

# Copy files
COPIED=0
SKIPPED=0

# Copy directory structure
for item in "$SOURCE_DIR"/*; do
    basename_item=$(basename "$item")
    
    # Skip README if merging
    if [ "$DEST_DIR" = "$PROJECT_ROOT" ] && [ "$basename_item" = "README.md" ]; then
        echo -e "${YELLOW}⚠${NC} Skipping README.md (preserving your existing README)"
        ((SKIPPED++))
        continue
    fi
    
    if [ -d "$item" ]; then
        # Copy directory
        if [ -d "$DEST_DIR/$basename_item" ]; then
            echo -e "${YELLOW}⚠${NC} Merging directory: $basename_item"
            cp -r "$item"/* "$DEST_DIR/$basename_item/" 2>/dev/null || true
        else
            echo -e "${GREEN}✓${NC} Copying directory: $basename_item"
            cp -r "$item" "$DEST_DIR/"
        fi
        ((COPIED++))
    else
        # Copy file
        if [ -f "$DEST_DIR/$basename_item" ]; then
            echo -e "${YELLOW}⚠${NC} File exists (skipping): $basename_item"
            ((SKIPPED++))
        else
            echo -e "${GREEN}✓${NC} Copying file: $basename_item"
            cp "$item" "$DEST_DIR/"
            ((COPIED++))
        fi
    fi
done

echo ""
echo -e "${GREEN}✓ Clone complete!${NC}"
echo "  Copied: $COPIED items"
echo "  Skipped: $SKIPPED items (already exist)"
echo ""

# Show next steps
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Review the example files in: $DEST_DIR"
echo "  2. Read the example README: $DEST_DIR/README.md"
echo "  3. Customize for your use case"
echo "  4. Run the example code"
echo ""

if [ "$DEST_DIR" != "$PROJECT_ROOT" ]; then
    echo -e "${CYAN}To work with this example:${NC}"
    echo "  cd $DEST_DIR"
    echo ""
fi

echo -e "${GREEN}Happy coding!${NC}"
