#!/bin/bash
# Validate CommonMark compliance for all markdown files in the power
# This script checks for common CommonMark issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Validating CommonMark compliance..."

# Check if markdownlint is installed
if ! command -v markdownlint &> /dev/null; then
    echo -e "${YELLOW}⚠️  markdownlint-cli not found${NC}"
    echo "Installing markdownlint-cli..."
    npm install -g markdownlint-cli 2>&1 | grep -v "npm WARN" || true

    if ! command -v markdownlint &> /dev/null; then
        echo -e "${RED}❌ Failed to install markdownlint-cli${NC}"
        echo "Please install manually: npm install -g markdownlint-cli"
        exit 1
    fi
fi

# Create markdownlint config if it doesn't exist
if [ ! -f ".markdownlint.json" ]; then
    cat > .markdownlint.json << 'EOF'
{
  "default": true,
  "MD013": false,
  "MD033": false,
  "MD041": false,
  "line-length": false
}
EOF
    echo "✅ Created .markdownlint.json configuration"
fi

# Count total markdown files
TOTAL_FILES=$(find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.history/*" | wc -l)
echo "📄 Found $TOTAL_FILES markdown files"

# Run markdownlint
echo ""
echo "Running markdownlint..."
if markdownlint "**/*.md" --ignore node_modules --ignore .history 2>&1; then
    echo -e "${GREEN}✅ All markdown files are CommonMark compliant!${NC}"
    exit 0
else
    echo -e "${RED}❌ CommonMark compliance issues found${NC}"
    echo ""
    echo "Common issues and fixes:"
    echo "  MD022: Headings need blank lines before/after"
    echo "  MD032: Lists need blank lines before/after"
    echo "  MD040: Code blocks need language specified (e.g., \`\`\`bash)"
    echo ""
    echo "To fix automatically, run:"
    echo "  markdownlint --fix \"**/*.md\" --ignore node_modules --ignore .history"
    exit 1
fi
