#!/bin/bash
# Senzing Boot Camp Project Backup Script
# Creates a timestamped ZIP archive of all project data

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="senzing-bootcamp-backup_${TIMESTAMP}"
BACKUP_FILE="backups/${BACKUP_NAME}.zip"

echo -e "${GREEN}Senzing Boot Camp - Project Backup${NC}"
echo "======================================"
echo ""

# Create backups directory if it doesn't exist
if [ ! -d "backups" ]; then
    echo "Creating backups directory..."
    mkdir -p backups
fi

# Check if zip is installed
if ! command -v zip &> /dev/null; then
    echo -e "${RED}Error: 'zip' command not found${NC}"
    echo "Please install zip:"
    echo "  Ubuntu/Debian: sudo apt-get install zip"
    echo "  macOS: brew install zip (or use built-in)"
    echo "  Windows: Install from https://www.7-zip.org/"
    exit 1
fi

echo "Creating backup: ${BACKUP_FILE}"
echo ""

# List of directories/files to backup
BACKUP_ITEMS=(
    "database"
    "data"
    "licenses"
    "config"
    "src"
    "scripts"
    "docs"
    ".env.example"
    "README.md"
)

# Check what exists and will be backed up
echo "Backing up the following items:"
ITEMS_TO_BACKUP=()
for item in "${BACKUP_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        echo "  ✓ $item"
        ITEMS_TO_BACKUP+=("$item")
    else
        echo "  - $item (not found, skipping)"
    fi
done
echo ""

# Exclude patterns
EXCLUDE_PATTERNS=(
    "*.pyc"
    "__pycache__/*"
    "target/*"
    "bin/*"
    "obj/*"
    "node_modules/*"
    "dist/*"
    ".DS_Store"
    "*.swp"
    "*.swo"
    "*~"
    ".env"
    "data/temp/*"
    ".git/*"
    ".history/*"
    "backups/*"
    "node_modules/*"
    "venv/*"
    ".venv/*"
)

# Build exclude arguments for zip
EXCLUDE_ARGS=()
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS+=("-x" "$pattern")
done

# Create the backup
echo "Compressing files..."
if zip -r "$BACKUP_FILE" "${ITEMS_TO_BACKUP[@]}" "${EXCLUDE_ARGS[@]}" -q; then
    # Get backup file size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

    echo ""
    echo -e "${GREEN}✓ Backup created successfully!${NC}"
    echo ""
    echo "Backup details:"
    echo "  File: $BACKUP_FILE"
    echo "  Size: $BACKUP_SIZE"
    echo "  Timestamp: $TIMESTAMP"
    echo ""
    echo "To restore this backup:"
    echo "  unzip $BACKUP_FILE -d /path/to/restore/location"
    echo ""
    echo "Or use the restore script:"
    echo "  ./scripts/restore_project.sh $BACKUP_FILE"
    echo ""
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# List recent backups
echo "Recent backups:"
ls -lh backups/*.zip 2>/dev/null | tail -5 | awk '{print "  " $9 " (" $5 ")"}'
echo ""

# Warn if backups directory is getting large
BACKUP_COUNT=$(ls -1 backups/*.zip 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo -e "${YELLOW}Note: You have $BACKUP_COUNT backups. Consider cleaning up old backups.${NC}"
    echo ""
fi

echo -e "${GREEN}Backup complete!${NC}"
