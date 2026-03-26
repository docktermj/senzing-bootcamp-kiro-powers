#!/bin/bash
# Senzing Boot Camp Project Restore Script
# Restores a project from a backup ZIP file

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${GREEN}Senzing Boot Camp - Project Restore${NC}"
echo "======================================"
echo ""

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-file.zip> [restore-directory]"
    echo ""
    echo "Examples:"
    echo "  $0 backups/senzing-bootcamp-backup_20260326_143022.zip"
    echo "  $0 backups/senzing-bootcamp-backup_20260326_143022.zip ~/new-project"
    echo ""
    echo "Available backups:"
    if ls "$PROJECT_ROOT"/backups/*.zip 1> /dev/null 2>&1; then
        ls -lh "$PROJECT_ROOT"/backups/*.zip | awk '{print "  " $9 " (" $5 ")"}'
    else
        echo "  No backups found in backups/ directory"
    fi
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="${2:-.}"  # Default to current directory if not specified

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Check if unzip is installed
if ! command -v unzip &> /dev/null; then
    echo -e "${RED}Error: 'unzip' command not found${NC}"
    echo "Please install unzip:"
    echo "  Ubuntu/Debian: sudo apt-get install unzip"
    echo "  macOS: brew install unzip (or use built-in)"
    echo "  Windows: Install from https://www.7-zip.org/"
    exit 1
fi

# Get absolute paths
BACKUP_FILE=$(cd "$(dirname "$BACKUP_FILE")" && pwd)/$(basename "$BACKUP_FILE")
RESTORE_DIR=$(mkdir -p "$RESTORE_DIR" && cd "$RESTORE_DIR" && pwd)

echo "Restore details:"
echo "  Backup file: $BACKUP_FILE"
echo "  Restore to: $RESTORE_DIR"
echo ""

# Check if restore directory is empty (if not current directory)
if [ "$RESTORE_DIR" != "$PROJECT_ROOT" ] && [ "$(ls -A "$RESTORE_DIR" 2>/dev/null)" ]; then
    echo -e "${YELLOW}Warning: Restore directory is not empty${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi
fi

# If restoring to current project, warn about overwriting
if [ "$RESTORE_DIR" = "$PROJECT_ROOT" ]; then
    echo -e "${YELLOW}Warning: This will overwrite files in the current project${NC}"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi
fi

# List contents of backup
echo "Backup contains:"
unzip -l "$BACKUP_FILE" | head -20
echo ""

# Extract the backup
echo "Extracting backup..."
cd "$RESTORE_DIR"
if unzip -o "$BACKUP_FILE" -q; then
    echo ""
    echo -e "${GREEN}✓ Restore completed successfully!${NC}"
    echo ""
    echo "Restored to: $RESTORE_DIR"
    echo ""

    # Check what was restored
    echo "Restored items:"
    for item in database data licenses config src scripts docs; do
        if [ -e "$RESTORE_DIR/$item" ]; then
            echo "  ✓ $item"
        fi
    done
    echo ""

    # Provide next steps
    echo "Next steps:"
    if [ "$RESTORE_DIR" != "$PROJECT_ROOT" ]; then
        echo "  1. cd $RESTORE_DIR"
        echo "  2. Review restored files"
        echo "  3. Update .env file with your environment variables"
        echo "  4. Test your Senzing installation"
    else
        echo "  1. Review restored files"
        echo "  2. Verify database integrity"
        echo "  3. Test your Senzing installation"
    fi
    echo ""
else
    echo -e "${RED}✗ Restore failed${NC}"
    exit 1
fi

echo -e "${GREEN}Restore complete!${NC}"
