#!/bin/bash

# End-to-End Test Runner for Workspace Management
# This script runs the comprehensive E2E test suite with proper setup and reporting

set -e

echo "🧪 OrdnungsHub E2E Test Suite - Workspace Management"
echo "=================================================="
echo ""

# Check if backend is running
check_backend() {
    echo "🔍 Checking backend status..."
    if curl -s http://localhost:8001/docs > /dev/null; then
        echo "✅ Backend is running"
        return 0
    else
        echo "❌ Backend is not running"
        return 1
    fi
}

# Start backend if not running
start_backend() {
    echo "🚀 Starting backend server..."
    npm run dev:backend &
    BACKEND_PID=$!
    echo "⏳ Waiting for backend to start..."
    sleep 10
    
    if check_backend; then
        echo "✅ Backend started successfully"
        return 0
    else
        echo "❌ Failed to start backend"
        return 1
    fi
}

# Run tests with different configurations
run_tests() {
    local test_type=$1
    local extra_args=$2
    
    echo ""
    echo "🧪 Running $test_type tests..."
    echo "--------------------------------"
    
    npx playwright test $extra_args
}

# Generate test report
generate_report() {
    echo ""
    echo "📊 Generating test report..."
    npx playwright show-report
}

# Main execution
main() {
    # Parse arguments
    TEST_FILTER=""
    HEADED=""
    DEBUG=""
    REPORT_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --filter)
                TEST_FILTER="$2"
                shift 2
                ;;
            --headed)
                HEADED="--headed"
                shift
                ;;
            --debug)
                DEBUG="--debug"
                shift
                ;;
            --report)
                REPORT_ONLY=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--filter <test-name>] [--headed] [--debug] [--report]"
                exit 1
                ;;
        esac
    done
    
    if [ "$REPORT_ONLY" = true ]; then
        generate_report
        exit 0
    fi
    
    # Check and start backend if needed
    BACKEND_STARTED=false
    if ! check_backend; then
        if start_backend; then
            BACKEND_STARTED=true
        else
            echo "❌ Cannot proceed without backend"
            exit 1
        fi
    fi
    
    # Install Playwright browsers if needed
    echo "🔧 Ensuring Playwright browsers are installed..."
    npx playwright install
    
    # Clear previous test results
    echo "🧹 Cleaning previous test results..."
    rm -rf test-results/
    rm -rf playwright-report/
    
    # Run tests based on configuration
    if [ -n "$TEST_FILTER" ]; then
        echo "🎯 Running filtered tests: $TEST_FILTER"
        run_tests "filtered" "$TEST_FILTER $HEADED $DEBUG"
    else
        echo "🏃 Running all E2E tests"
        
        # Run different test suites
        echo ""
        echo "📝 Test Suite Overview:"
        echo "1. Workspace CRUD Operations"
        echo "2. Workspace State Management"
        echo "3. Templates and Themes"
        echo "4. AI-Powered Features"
        echo "5. Settings and Configurations"
        echo "6. End-to-End Scenarios"
        echo ""
        
        run_tests "all" "$HEADED $DEBUG"
    fi
    
    # Show test results
    echo ""
    echo "📊 Test Results Summary"
    echo "======================"
    
    # Check if tests passed
    if [ $? -eq 0 ]; then
        echo "✅ All tests passed!"
    else
        echo "❌ Some tests failed"
    fi
    
    # Cleanup
    if [ "$BACKEND_STARTED" = true ]; then
        echo ""
        echo "🧹 Stopping backend server..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Ask if user wants to view the report
    echo ""
    read -p "📊 Would you like to view the detailed test report? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        generate_report
    fi
}

# Run main function
main "$@"