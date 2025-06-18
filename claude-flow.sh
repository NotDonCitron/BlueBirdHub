#!/bin/bash
# Claude Code Flow - Quick Start Script
# Usage: ./claude-flow.sh [command] [description]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Function to display help
show_help() {
    echo -e "${BLUE}Claude Code Flow - Autonomous Development System${NC}"
    echo ""
    echo "Usage: ./claude-flow.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  feature <description>    - Develop a new feature"
    echo "  fix <description>       - Fix a bug"
    echo "  refactor <description>  - Refactor existing code"
    echo "  test <description>      - Add or improve tests"
    echo "  setup                   - Initial setup and configuration"
    echo "  status                  - Show current workflow status"
    echo ""
    echo "Options:"
    echo "  --auto                  - Auto-approve human checkpoints (dev only)"
    echo "  --verbose               - Show detailed output"
    echo "  --dry-run              - Preview changes without applying"
    echo ""
    echo "Examples:"
    echo "  ./claude-flow.sh feature 'Add user authentication with JWT'"
    echo "  ./claude-flow.sh fix 'File upload fails on large files'"
    echo "  ./claude-flow.sh refactor 'Optimize database queries in file scanner'"
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js is not installed${NC}"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    
    # Install Python dependencies
    if ! python -c "import rich" 2>/dev/null; then
        echo -e "${YELLOW}Installing Python dependencies...${NC}"
        pip install rich asyncio
    fi
    
    echo -e "${GREEN}✓ Dependencies checked${NC}"
}

# Function to run the orchestrator
run_orchestrator() {
    local command=$1
    local description=$2
    shift 2
    local extra_args=$@
    
    echo -e "${BLUE}Starting Claude Code Flow...${NC}"
    echo -e "${YELLOW}Task: ${command} - ${description}${NC}"
    echo ""
    
    # Activate virtual environment
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    
    # Run the orchestrator
    python src/backend/services/claude_code_orchestrator.py "$command" "$description" $extra_args
}

# Function to setup the environment
setup_environment() {
    echo -e "${BLUE}Setting up Claude Code Flow environment...${NC}"
    
    check_dependencies
    
    # Create necessary directories
    mkdir -p .claude/workflows
    mkdir -p .claude/commands
    mkdir -p logs/claude-flow
    
    # Check if configuration exists
    if [ ! -f ".claude/workflows/claude-code-flow.json" ]; then
        echo -e "${RED}Error: Configuration file not found${NC}"
        echo "Please ensure .claude/workflows/claude-code-flow.json exists"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Environment setup complete${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}Claude Code Flow Status${NC}"
    echo "========================"
    
    # Check configuration
    if [ -f ".claude/workflows/claude-code-flow.json" ]; then
        echo -e "${GREEN}✓ Configuration found${NC}"
    else
        echo -e "${RED}✗ Configuration missing${NC}"
    fi
    
    # Check virtual environment
    if [ -d ".venv" ]; then
        echo -e "${GREEN}✓ Virtual environment exists${NC}"
    else
        echo -e "${RED}✗ Virtual environment missing${NC}"
    fi
    
    # Check recent logs
    if [ -d "logs/claude-flow" ]; then
        log_count=$(find logs/claude-flow -name "*.log" -mtime -7 | wc -l)
        echo -e "${BLUE}Recent logs: ${log_count} (last 7 days)${NC}"
    fi
    
    # Show test coverage if available
    if [ -f "coverage/lcov-report/index.html" ]; then
        echo -e "${BLUE}Latest test coverage report available${NC}"
    fi
}

# Main script logic
case "$1" in
    feature|fix|refactor|test)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Description required${NC}"
            echo "Usage: ./claude-flow.sh $1 <description>"
            exit 1
        fi
        check_dependencies
        run_orchestrator "$1" "$2" "${@:3}"
        ;;
    setup)
        setup_environment
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
