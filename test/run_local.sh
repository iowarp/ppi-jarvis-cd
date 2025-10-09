#!/bin/bash
# Local test runner (non-containerized)
# Usage: ./run_local.sh [test-path] [pytest-args]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$PROJECT_ROOT"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Default test path
TEST_PATH="${1:-test/unit/}"
shift || true

echo -e "${GREEN}=== Jarvis CD Local Test Runner ===${NC}"
echo "Test Path: $TEST_PATH"
echo "Additional Args: $@"
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null && ! python3 -m pytest --version &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Compile test binaries if needed
if [ -f "test/unit/shell/test_env_checker.c" ] && [ ! -f "test/unit/shell/test_env_checker" ]; then
    echo -e "${YELLOW}Compiling test binaries...${NC}"
    gcc test/unit/shell/test_env_checker.c -o test/unit/shell/test_env_checker
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
python3 -m pytest "$TEST_PATH" -v "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed!${NC}"
else
    echo -e "${RED}✗ Tests failed with exit code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
