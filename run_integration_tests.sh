#!/bin/bash
#
# Integration Test Runner for TPRM-Frameworks MCP
#
# Usage:
#   ./run_integration_tests.sh          # Run all tests
#   ./run_integration_tests.sh fast     # Run fast tests only (exclude slow)
#   ./run_integration_tests.sh scenario # Run only end-to-end scenario tests
#   ./run_integration_tests.sh coverage # Run with coverage report
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           TPRM-Frameworks MCP Server - Integration Test Suite               ║
║                        Phase 0 Deployment Validation                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing dependencies...${NC}"
    pip install -e ".[dev]"
fi

# Determine test mode
MODE="${1:-all}"

case "$MODE" in
    fast)
        echo -e "${GREEN}Running fast tests only (excluding slow tests)...${NC}\n"
        pytest tests/ -v -m "not slow" --tb=short
        ;;
    scenario)
        echo -e "${GREEN}Running end-to-end scenario tests only...${NC}\n"
        pytest tests/ -v -m scenario --tb=short
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}\n"
        if ! command -v pytest-cov &> /dev/null; then
            echo -e "${YELLOW}Installing pytest-cov...${NC}"
            pip install pytest-cov
        fi
        pytest tests/ -v --cov=tprm_frameworks_mcp --cov-report=html --cov-report=term-missing --tb=short
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    integration)
        echo -e "${GREEN}Running integration tests only...${NC}\n"
        pytest tests/ -v -m integration --tb=short
        ;;
    *)
        echo -e "${GREEN}Running all integration tests...${NC}\n"
        pytest tests/ -v --tb=short
        ;;
esac

# Print summary
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Integration tests complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "Next steps:"
echo -e "  • Review test results above"
echo -e "  • Check coverage report: ${BLUE}open htmlcov/index.html${NC}"
echo -e "  • Run specific tests: ${BLUE}pytest tests/integration_test.py::TestClass::test_method -v${NC}"
echo -e "  • See test documentation: ${BLUE}cat tests/README.md${NC}\n"
