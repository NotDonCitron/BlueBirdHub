#!/bin/bash

# 🔄 OrdnungsHub Worktree Synchronization Script
# Synchronizes all development worktrees with main branch

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAIN_BRANCH="main"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREES_DIR="$PROJECT_ROOT/worktrees"

# Active worktrees
WORKTREES=(
    "ai-enhancement"
    "performance-optimization"
    "zen-mcp-integration"
    "architecture-security"
    "api-optimizations"
    "electron-optimizations"
    "file-operations"
    "new-feature"
)

echo -e "${BLUE}🚀 OrdnungsHub Worktree Sync Starting...${NC}"
echo -e "${BLUE}📁 Project Root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}🌳 Worktrees Dir: $WORKTREES_DIR${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to execute command with logging
execute_cmd() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${YELLOW}⚡ $description${NC}"
    echo -e "${YELLOW}   Command: $cmd${NC}"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ Success${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Function to check if worktree exists
worktree_exists() {
    local worktree_name="$1"
    [ -d "$WORKTREES_DIR/$worktree_name" ]
}

# Function to get current branch of worktree
get_worktree_branch() {
    local worktree_path="$1"
    cd "$worktree_path"
    git branch --show-current
}

# Function to sync single worktree
sync_worktree() {
    local worktree_name="$1"
    local worktree_path="$WORKTREES_DIR/$worktree_name"
    
    echo -e "\n${YELLOW}🔄 Syncing worktree: $worktree_name${NC}"
    
    if ! worktree_exists "$worktree_name"; then
        echo -e "${RED}❌ Worktree '$worktree_name' not found at $worktree_path${NC}"
        return 1
    fi
    
    cd "$worktree_path"
    
    # Get current branch
    local current_branch=$(get_worktree_branch "$worktree_path")
    echo -e "${BLUE}   Current branch: $current_branch${NC}"
    
    # Check for uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo -e "${YELLOW}⚠️  Uncommitted changes detected${NC}"
        echo -e "${YELLOW}   Stashing changes...${NC}"
        git stash push -m "Auto-stash before sync $(date)"
    fi
    
    # Fetch latest changes
    execute_cmd "git fetch origin" "Fetching latest changes"
    
    # Merge main branch
    if [ "$current_branch" != "$MAIN_BRANCH" ]; then
        execute_cmd "git merge origin/$MAIN_BRANCH" "Merging main branch into $current_branch"
    else
        execute_cmd "git merge origin/$MAIN_BRANCH" "Fast-forwarding main branch"
    fi
    
    # Pop stash if it exists
    if git stash list | grep -q "Auto-stash before sync"; then
        echo -e "${YELLOW}   Restoring stashed changes...${NC}"
        git stash pop
    fi
    
    echo -e "${GREEN}✅ Worktree '$worktree_name' synced successfully${NC}"
}

# Function to run integration tests
run_integration_tests() {
    print_section "Running Integration Tests"
    
    cd "$PROJECT_ROOT"
    
    # Check if all worktrees can build
    local failed_builds=()
    
    for worktree in "${WORKTREES[@]}"; do
        if worktree_exists "$worktree"; then
            echo -e "\n${YELLOW}🔨 Testing build for $worktree${NC}"
            cd "$WORKTREES_DIR/$worktree"
            
            if [ -f "package.json" ]; then
                if ! npm run build --if-present 2>/dev/null; then
                    failed_builds+=("$worktree")
                    echo -e "${RED}❌ Build failed for $worktree${NC}"
                else
                    echo -e "${GREEN}✅ Build successful for $worktree${NC}"
                fi
            else
                echo -e "${BLUE}ℹ️  No package.json found for $worktree, skipping build test${NC}"
            fi
        fi
    done
    
    if [ ${#failed_builds[@]} -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All worktree builds successful!${NC}"
        return 0
    else
        echo -e "\n${RED}❌ Build failures detected in: ${failed_builds[*]}${NC}"
        return 1
    fi
}

# Function to generate sync report
generate_sync_report() {
    print_section "Sync Report"
    
    local report_file="$PROJECT_ROOT/sync-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# 🔄 Worktree Sync Report

**Generated:** $(date)
**Project:** OrdnungsHub
**Main Branch:** $MAIN_BRANCH

## 📊 Worktree Status

| Worktree | Status | Current Branch | Last Commit |
|----------|--------|----------------|-------------|
EOF

    for worktree in "${WORKTREES[@]}"; do
        if worktree_exists "$worktree"; then
            cd "$WORKTREES_DIR/$worktree"
            local branch=$(git branch --show-current)
            local last_commit=$(git log -1 --format="%h - %s (%cr)")
            local status="✅ Active"
            
            echo "| $worktree | $status | $branch | $last_commit |" >> "$report_file"
        else
            echo "| $worktree | ❌ Missing | - | - |" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

## 🎯 Next Steps

1. Review failed builds if any
2. Run comprehensive tests: \`npm run test:all-worktrees\`
3. Check for merge conflicts
4. Update documentation if needed

## 🔧 Commands Used

\`\`\`bash
$0 $@
\`\`\`

---
*Generated by OrdnungsHub Sync Script*
EOF

    echo -e "${GREEN}📄 Sync report generated: $report_file${NC}"
}

# Main execution
main() {
    print_section "Pre-sync Checks"
    
    # Ensure we're in the project root
    cd "$PROJECT_ROOT"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}❌ Not in a git repository${NC}"
        exit 1
    fi
    
    # Check if worktrees directory exists
    if [ ! -d "$WORKTREES_DIR" ]; then
        echo -e "${RED}❌ Worktrees directory not found: $WORKTREES_DIR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Pre-sync checks passed${NC}"
    
    print_section "Syncing Main Branch"
    
    # Update main branch first
    execute_cmd "git fetch origin" "Fetching from origin"
    execute_cmd "git checkout $MAIN_BRANCH" "Switching to main branch"
    execute_cmd "git merge origin/$MAIN_BRANCH" "Updating main branch"
    
    print_section "Syncing Individual Worktrees"
    
    # Sync all worktrees
    local sync_failures=()
    
    for worktree in "${WORKTREES[@]}"; do
        if ! sync_worktree "$worktree"; then
            sync_failures+=("$worktree")
        fi
    done
    
    # Check for Node.js dependencies updates needed
    print_section "Checking Dependencies"
    
    for worktree in "${WORKTREES[@]}"; do
        if worktree_exists "$worktree" && [ -f "$WORKTREES_DIR/$worktree/package.json" ]; then
            cd "$WORKTREES_DIR/$worktree"
            echo -e "${YELLOW}📦 Checking dependencies for $worktree${NC}"
            
            if [ -f "package-lock.json" ] && ! npm ci --silent; then
                echo -e "${YELLOW}⚠️  Dependencies may need updating for $worktree${NC}"
            fi
        fi
    done
    
    # Run integration tests if requested
    if [ "$1" == "--with-tests" ]; then
        if ! run_integration_tests; then
            echo -e "${YELLOW}⚠️  Integration tests failed, but sync completed${NC}"
        fi
    fi
    
    # Generate report
    generate_sync_report
    
    # Final summary
    print_section "Sync Summary"
    
    if [ ${#sync_failures[@]} -eq 0 ]; then
        echo -e "${GREEN}🎉 All worktrees synced successfully!${NC}"
        echo -e "${GREEN}✅ Total worktrees processed: ${#WORKTREES[@]}${NC}"
        exit 0
    else
        echo -e "${RED}❌ Sync failures: ${sync_failures[*]}${NC}"
        echo -e "${YELLOW}⚠️  Check the output above for details${NC}"
        exit 1
    fi
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "🔄 OrdnungsHub Worktree Sync Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h           Show this help message"
        echo "  --with-tests         Run integration tests after sync"
        echo "  --list-worktrees     List all configured worktrees"
        echo ""
        echo "Examples:"
        echo "  $0                   Sync all worktrees"
        echo "  $0 --with-tests      Sync and run integration tests"
        echo ""
        ;;
    --list-worktrees)
        echo "📋 Configured Worktrees:"
        for worktree in "${WORKTREES[@]}"; do
            if worktree_exists "$worktree"; then
                echo -e "  ${GREEN}✅ $worktree${NC} (exists)"
            else
                echo -e "  ${RED}❌ $worktree${NC} (missing)"
            fi
        done
        ;;
    *)
        main "$@"
        ;;
esac