#!/bin/bash
# Test runner script for Jarvis CD
# Usage: ./run_tests.sh [all|shell|util|core|parallel] [additional pytest args]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print usage
usage() {
    echo "Usage: $0 [TEST_SUITE] [PYTEST_ARGS]"
    echo ""
    echo "TEST_SUITE options:"
    echo "  all       - Run all tests (default)"
    echo "  shell     - Run only shell module tests"
    echo "  util      - Run only util module tests"
    echo "  core      - Run only core module tests"
    echo "  parallel  - Run all tests in parallel"
    echo ""
    echo "Examples:"
    echo "  $0 all"
    echo "  $0 shell -v"
    echo "  $0 parallel -n 4"
    echo "  $0 core --tb=short"
    exit 1
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        echo "Please install Docker Compose"
        exit 1
    fi
}

# Determine docker-compose command
get_compose_cmd() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Main execution
main() {
    local test_suite="${1:-all}"
    shift || true
    local pytest_args="$@"

    # Check for help flag
    if [[ "$test_suite" == "-h" || "$test_suite" == "--help" ]]; then
        usage
    fi

    echo -e "${GREEN}=== Jarvis CD Test Runner ===${NC}"
    echo "Test Suite: $test_suite"
    echo "Additional Args: $pytest_args"
    echo ""

    # Check Docker
    check_docker

    # Get docker-compose command
    COMPOSE_CMD=$(get_compose_cmd)

    cd "$SCRIPT_DIR"

    # Set service name based on test suite
    case "$test_suite" in
        all)
            SERVICE="test"
            ;;
        shell)
            SERVICE="test-shell"
            ;;
        util)
            SERVICE="test-util"
            ;;
        core)
            SERVICE="test-core"
            ;;
        parallel)
            SERVICE="test-parallel"
            ;;
        *)
            echo -e "${RED}Error: Unknown test suite '$test_suite'${NC}"
            usage
            ;;
    esac

    echo -e "${YELLOW}Building Docker image...${NC}"
    $COMPOSE_CMD build $SERVICE

    echo -e "${YELLOW}Running tests...${NC}"
    if [ -n "$pytest_args" ]; then
        PYTEST_ARGS="$pytest_args" $COMPOSE_CMD run --rm $SERVICE
    else
        $COMPOSE_CMD run --rm $SERVICE
    fi

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Tests passed!${NC}"
    else
        echo -e "${RED}✗ Tests failed with exit code $EXIT_CODE${NC}"
    fi

    # Copy coverage report if it exists
    if [ -d "$PROJECT_ROOT/htmlcov" ]; then
        echo -e "${YELLOW}Coverage report available at: $PROJECT_ROOT/htmlcov/index.html${NC}"
    fi

    exit $EXIT_CODE
}

main "$@"
