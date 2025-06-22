# Project Diagnosis and Systematic Repair - Context

**Task**: Complete diagnosis and systematic repair of OrdnungsHub application
**Repo path**: /mnt/c/Users/pasca/BlueBirdHub
**Desired parallelism**: 3 specialists (Backend Issues, Dependencies, Configuration)
**Target Score**: 90

## Current Situation
The OrdnungsHub application was broken after Cursor made changes. While basic backend functionality has been restored, multiple critical issues remain that require systematic analysis and repair.

## Critical Issues Identified
1. **SQLAlchemy Relationship Errors**: TeamMembership.user foreign key relationships causing database seeding failures
2. **Missing Dependencies**: AI features disabled due to missing packages (numpy, sentence-transformers, sklearn)
3. **Disabled Features**: MCP integration disabled due to missing aiohttp
4. **Redis Connectivity**: Redis unavailable, using in-memory fallback
5. **Complex Project Structure**: Multiple worktrees with potential conflicts

## Current Status
- **Backend**: Running on port 8001 with minimal functionality
- **Frontend**: Running on port 3002 with Vite
- **Database**: Operational but seeding fails
- **AI Services**: Disabled
- **Tests**: Not verified

## Project Structure
```
BlueBirdHub/
├── src/
│   ├── backend/          # Python FastAPI backend
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic (AI, file management)
│   │   ├── models/      # SQLAlchemy models (ISSUES HERE)
│   │   └── database/    # Database configuration
│   ├── frontend/        # Electron + React frontend
│   └── core/           # Shared utilities
├── worktrees/          # Multiple worktree branches (POTENTIAL CONFLICTS)
├── requirements.txt    # Python dependencies (CONFLICTS)
├── requirements-minimal.txt # Minimal working deps
└── package.json       # Node.js dependencies
```

## Technology Stack
- **Backend**: Python FastAPI with SQLAlchemy 2.0.29
- **Frontend**: React 19.1.0 + Electron + Vite
- **Database**: SQLite with performance optimizations
- **AI**: sentence-transformers, scikit-learn (disabled)
- **Testing**: Jest (frontend), pytest (backend)

## Key Files to Examine
1. `src/backend/models/` - SQLAlchemy relationship issues
2. `requirements.txt` vs `requirements-minimal.txt` - dependency conflicts
3. `src/backend/main.py` - disabled imports and features
4. `src/backend/services/smart_file_organizer.py` - AI dependencies
5. `src/backend/api/mcp_integration.py` - disabled MCP features
6. `worktrees/` - redundant project structures

## Success Criteria
- All SQLAlchemy relationships working correctly
- Database seeding successful
- AI features fully operational
- MCP integration restored
- All tests passing
- Frontend-backend integration verified
- Clean project structure
- Complete feature functionality

## Constraints
- Must maintain backward compatibility
- Must not break existing working components
- Must follow security best practices
- Must maintain performance standards

## Expected Deliverables
1. **Complete Issue Analysis**: Detailed technical report of all problems
2. **Systematic Repair Plan**: Step-by-step fix sequence
3. **Implementation**: All fixes applied and tested
4. **Verification**: Full functionality testing
5. **Documentation**: Updated setup and troubleshooting guides