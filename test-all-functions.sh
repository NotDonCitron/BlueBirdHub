#!/bin/bash
# Comprehensive Function Testing Script
# Automatically test every function in your codebase

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Show banner
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Comprehensive Function Testing Workflow               ║${NC}"
echo -e "${BLUE}║  Automatically discover, test, and validate every function   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check dependencies
check_deps() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    
    # Check pytest
    if ! python3 -c "import pytest" 2>/dev/null; then
        echo -e "${YELLOW}Installing pytest...${NC}"
        pip install pytest pytest-cov pytest-json-report
    fi
    
    # Check rich
    if ! python3 -c "import rich" 2>/dev/null; then
        echo -e "${YELLOW}Installing rich...${NC}"
        pip install rich
    fi
    
    echo -e "${GREEN}✅ Dependencies ready${NC}"
}

# Main function
run_tests() {
    local mode=$1
    
    case "$mode" in
        "full")
            echo -e "${BLUE}Running full comprehensive testing...${NC}"
            python3 src/backend/services/comprehensive_test_orchestrator.py
            ;;
        "generate")
            echo -e "${BLUE}Generating tests only...${NC}"
            python3 src/backend/services/comprehensive_test_orchestrator.py --generate-only
            ;;
        "execute")
            echo -e "${BLUE}Executing tests only...${NC}"
            python3 src/backend/services/comprehensive_test_orchestrator.py --execute-only
            ;;
        "report")
            echo -e "${BLUE}Generating report only...${NC}"
            python3 src/backend/services/comprehensive_test_orchestrator.py --report-only
            ;;
        "target")
            echo -e "${BLUE}Testing specific target: $2${NC}"
            python3 src/backend/services/comprehensive_test_orchestrator.py --target "$2"
            ;;
        *)
            show_help
            ;;
    esac
}

# Show help
show_help() {
    echo "Usage: ./test-all-functions.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  full       - Run complete testing workflow (default)"
    echo "  generate   - Only generate missing tests"
    echo "  execute    - Only execute existing tests"
    echo "  report     - Only generate coverage report"
    echo "  target     - Test specific file/directory"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./test-all-functions.sh"
    echo "  ./test-all-functions.sh generate"
    echo "  ./test-all-functions.sh target src/backend/services"
    echo ""
    echo "The workflow will:"
    echo "  1. Discover all functions in your codebase"
    echo "  2. Generate tests for untested functions"
    echo "  3. Execute all tests and collect results"
    echo "  4. Generate comprehensive coverage report"
}

# Show stats
show_stats() {
    if [ -f "test_coverage_report.json" ]; then
        echo -e "\n${BLUE}📊 Current Test Coverage:${NC}"
        python3 -c "
import json
with open('test_coverage_report.json') as f:
    data = json.load(f)
    summary = data.get('summary', {})
    print(f'  Total Functions: {summary.get(\"total_functions\", 0)}')
    print(f'  Functions with Tests: {summary.get(\"functions_with_tests\", 0)}')
    print(f'  Coverage: {summary.get(\"test_coverage\", 0):.1f}%')
    print(f'  High Risk Functions: {len(data.get(\"high_risk_functions\", []))}')
"
    fi
}

# Main execution
if [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_help
    exit 0
fi

# Check dependencies
check_deps

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
fi

# Run the testing workflow
if [ -z "$1" ]; then
    run_tests "full"
else
    run_tests "$1" "$2"
fi

# Show final stats
show_stats

echo -e "\n${GREEN}✅ Testing workflow complete!${NC}"
echo -e "Check ${BLUE}test_coverage_report.json${NC} for detailed results"
