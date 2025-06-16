#\!/bin/bash

echo "=== Running OrdnungsHub Test Suite ==="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall test status
ALL_TESTS_PASSED=true

# Function to run tests and report status
run_test_suite() {
    local suite_name=$1
    local command=$2
    
    echo -e "${YELLOW}Running $suite_name...${NC}"
    
    if eval $command; then
        echo -e "${GREEN}✓ $suite_name passed${NC}"
        echo
    else
        echo -e "${RED}✗ $suite_name failed${NC}"
        echo
        ALL_TESTS_PASSED=false
    fi
}

# Change to project directory
cd "$(dirname "$0")"

# 1. Run Python backend tests
echo "=== Backend Tests (Python) ==="
if [ -d "venv" ]; then
    source venv/bin/activate
    
    # Fix TestClient import issues
    pip install -U httpx fastapi pytest pytest-asyncio pytest-cov > /dev/null 2>&1
    
    run_test_suite "Python Unit Tests" "python -m pytest tests/unit/test_*.py -v --tb=short"
else
    echo -e "${RED}Virtual environment not found. Please create it first.${NC}"
    ALL_TESTS_PASSED=false
fi

# 2. Run JavaScript/TypeScript tests
echo
echo "=== Frontend Tests (JavaScript/React) ==="

# Fix missing dependencies
echo "Installing test dependencies..."
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom ts-jest > /dev/null 2>&1

# Run general JavaScript tests
run_test_suite "JavaScript Unit Tests" "npm test -- --testPathPattern='tests/unit/.*\\.js$' --passWithNoTests"

# Run React component tests
run_test_suite "React Component Tests" "npm run test:react -- --passWithNoTests"

# 3. Run integration tests
echo
echo "=== Integration Tests ==="
run_test_suite "Integration Tests" "npm test -- --testPathPattern='tests/integration/.*\\.js$' --passWithNoTests"

# 4. Run linting checks
echo
echo "=== Code Quality Checks ==="
run_test_suite "ESLint" "npm run lint -- --quiet"

# 5. Run TypeScript type checking
run_test_suite "TypeScript Check" "npx tsc --noEmit"

# Summary
echo
echo "=== Test Summary ==="
if [ "$ALL_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✓ All tests passed\!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
EOF < /dev/null