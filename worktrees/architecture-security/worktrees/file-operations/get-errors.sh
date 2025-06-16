#!/bin/bash

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API base URL
API_BASE="http://localhost:8001/api/logs"

# Function to display help
show_help() {
    echo -e "${GREEN}Console Error Retrieval Tool${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  recent      Show recent errors (default)"
    echo "  all         Show all errors"
    echo "  stats       Show error statistics"
    echo "  summary     Show comprehensive error summary"
    echo "  patterns    Show common error patterns"
    echo "  resolve ID  Mark error as resolved"
    echo "  cleanup     Delete old errors"
    echo ""
    echo "Options:"
    echo "  --limit N     Limit number of results (default: 10)"
    echo "  --source S    Filter by error source"
    echo "  --severity S  Filter by severity (error, warning, info)"
    echo "  --unresolved  Show only unresolved errors"
    echo "  --help, -h    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 recent --limit 5"
    echo "  $0 all --source 'JavaScript Error' --unresolved"
    echo "  $0 stats"
    echo "  $0 resolve 123"
}

# Function to make API request
api_request() {
    local endpoint="$1"
    local params="$2"
    
    if [ -n "$params" ]; then
        curl -s "${API_BASE}${endpoint}?${params}" 2>/dev/null
    else
        curl -s "${API_BASE}${endpoint}" 2>/dev/null
    fi
}

# Function to format timestamp
format_time() {
    local timestamp="$1"
    if command -v date >/dev/null 2>&1; then
        date -d "$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$timestamp"
    else
        echo "$timestamp"
    fi
}

# Function to format error output
format_error() {
    local json="$1"
    
    echo "$json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for error in data:
            print(f\"\\n{'='*60}\")
            print(f\"ID: {error.get('id', 'N/A')}\")
            print(f\"Time: {error.get('timestamp', 'N/A')}\")
            print(f\"Source: {error.get('source', 'N/A')}\")
            print(f\"Severity: {error.get('severity', 'N/A')}\")
            print(f\"Message: {error.get('message', 'N/A')}\")
            if error.get('url'):
                print(f\"URL: {error.get('url')}\")
            if error.get('stack'):
                print(f\"Stack: {error.get('stack')[:200]}...\")
            print(f\"Resolved: {'Yes' if error.get('resolved') else 'No'}\")
    else:
        print(json.dumps(data, indent=2))
except:
    print('Error parsing JSON response')
" 2>/dev/null || echo "$json"
}

# Function to format stats
format_stats() {
    local json="$1"
    
    echo "$json" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f\"\\n${GREEN}Error Statistics${NC}\")
    print(f\"{'='*40}\")
    print(f\"Total Errors: {data.get('total_errors', 0)}\")
    print(f\"Unresolved: {data.get('unresolved_errors', 0)}\")
    print(f\"Recent (24h): {data.get('recent_errors_count', 0)}\")
    
    severity = data.get('errors_by_severity', {})
    if severity:
        print(f\"\\nBy Severity:\")
        for sev, count in severity.items():
            print(f\"  {sev}: {count}\")
    
    sources = data.get('errors_by_source', {})
    if sources:
        print(f\"\\nBy Source:\")
        for src, count in sources.items():
            print(f\"  {src}: {count}\")
except Exception as e:
    print(f'Error parsing stats: {e}')
    print(sys.stdin.read())
" 2>/dev/null || echo "$json"
}

# Parse command line arguments
COMMAND="recent"
LIMIT="10"
SOURCE=""
SEVERITY=""
UNRESOLVED=""
ERROR_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        recent|all|stats|summary|patterns|cleanup)
            COMMAND="$1"
            shift
            ;;
        resolve)
            COMMAND="resolve"
            ERROR_ID="$2"
            shift 2
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --severity)
            SEVERITY="$2"
            shift 2
            ;;
        --unresolved)
            UNRESOLVED="0"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if backend is running
if ! curl -s "$API_BASE/../.." >/dev/null 2>&1; then
    echo -e "${RED}Error: Backend API is not running on http://localhost:8001${NC}"
    echo "Please start the backend first with: npm run dev:backend"
    exit 1
fi

# Build query parameters
PARAMS=""
if [ -n "$LIMIT" ]; then
    PARAMS="${PARAMS}limit=$LIMIT&"
fi
if [ -n "$SOURCE" ]; then
    PARAMS="${PARAMS}source=$SOURCE&"
fi
if [ -n "$SEVERITY" ]; then
    PARAMS="${PARAMS}severity=$SEVERITY&"
fi
if [ -n "$UNRESOLVED" ]; then
    PARAMS="${PARAMS}resolved=$UNRESOLVED&"
fi
PARAMS="${PARAMS%&}"  # Remove trailing &

# Execute command
case $COMMAND in
    recent)
        echo -e "${BLUE}Fetching recent errors...${NC}"
        response=$(api_request "/recent-errors" "limit=$LIMIT")
        format_error "$response"
        ;;
    all)
        echo -e "${BLUE}Fetching all errors...${NC}"
        response=$(api_request "/frontend-errors" "$PARAMS")
        format_error "$response"
        ;;
    stats)
        echo -e "${BLUE}Fetching error statistics...${NC}"
        response=$(api_request "/error-stats" "")
        format_stats "$response"
        ;;
    summary)
        echo -e "${BLUE}Fetching error summary...${NC}"
        response=$(api_request "/error-summary" "")
        echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    stats = data.get('stats', {})
    print(f\"\\n${GREEN}Error Summary${NC}\")
    print(f\"{'='*40}\")
    print(f\"Total: {stats.get('total_errors', 0)}\")
    print(f\"Unresolved: {stats.get('unresolved_errors', 0)}\")
    print(f\"Recent: {stats.get('recent_errors_count', 0)}\")
    
    recent = data.get('recent_errors', [])
    if recent:
        print(f\"\\n${YELLOW}Recent Errors:${NC}\")
        for error in recent[:3]:
            print(f\"  [{error.get('severity', 'N/A')}] {error.get('message', 'N/A')[:80]}\")
    
    patterns = data.get('common_patterns', [])
    if patterns:
        print(f\"\\n${YELLOW}Common Patterns:${NC}\")
        for pattern in patterns[:3]:
            print(f\"  {pattern.get('count', 0)}x: {pattern.get('message', 'N/A')[:60]}\")
except:
    print('Error parsing summary')
" 2>/dev/null
        ;;
    patterns)
        echo -e "${BLUE}Fetching error patterns...${NC}"
        response=$(api_request "/patterns" "limit=$LIMIT")
        echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f\"\\n${YELLOW}Common Error Patterns${NC}\")
    print(f\"{'='*50}\")
    for pattern in data:
        print(f\"\\nCount: {pattern.get('count', 0)}\")
        print(f\"Source: {pattern.get('source', 'N/A')}\")
        print(f\"Message: {pattern.get('message', 'N/A')}\")
        print(f\"Last Seen: {pattern.get('last_seen', 'N/A')}\")
        print('-' * 30)
except:
    print('Error parsing patterns')
" 2>/dev/null
        ;;
    resolve)
        if [ -z "$ERROR_ID" ]; then
            echo -e "${RED}Error: Please provide an error ID to resolve${NC}"
            exit 1
        fi
        echo -e "${BLUE}Resolving error $ERROR_ID...${NC}"
        response=$(curl -s -X PUT "${API_BASE}/resolve-error/$ERROR_ID" 2>/dev/null)
        echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'success':
        print(f\"${GREEN}✓ {data.get('message', 'Error resolved')}${NC}\")
    else:
        print(f\"${RED}✗ Failed to resolve error${NC}\")
except:
    print(f\"${RED}✗ Error resolving error $ERROR_ID${NC}\")
" 2>/dev/null
        ;;
    cleanup)
        echo -e "${YELLOW}Cleaning up old errors...${NC}"
        response=$(curl -s -X DELETE "${API_BASE}/cleanup-errors?days=30" 2>/dev/null)
        echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    count = data.get('deleted_count', 0)
    print(f\"${GREEN}✓ Deleted {count} old errors${NC}\")
except:
    print(f\"${RED}✗ Error during cleanup${NC}\")
" 2>/dev/null
        ;;
esac