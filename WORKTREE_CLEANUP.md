# Worktree Cleanup and Consolidation Guide

## Current Worktree Analysis

### Active Worktrees (9 total):
1. `ai-enhancement` - AI features development
2. `api-optimizations` - Backend API improvements  
3. `architecture-security` - Security and architecture updates
4. `electron-optimizations` - Desktop app optimizations
5. `file-operations` - File management features
6. `new-feature` - General new feature development
7. `performance-optimization` - Performance improvements
8. `zen-mcp-integration` - MCP (Model Context Protocol) integration
9. `data` - Database/data-related changes

## Recommended Consolidation Strategy

### Phase 1: Immediate Cleanup (Complete Features)
```bash
# 1. Review completed features and merge to main
git worktree list
cd worktrees/[completed-feature]
git status
git log --oneline -10

# 2. Merge completed work
git checkout main
git merge worktrees/[completed-feature]
git worktree remove worktrees/[completed-feature]
```

### Phase 2: Reorganize Active Development
Keep only 3-4 active worktrees:
- `feature/current-sprint` - Current sprint work
- `hotfix/urgent-fixes` - Critical bug fixes
- `experiment/research` - R&D and experimental features
- `release/staging` - Release preparation

### Phase 3: New Branching Strategy

#### Branch Naming Convention:
- `feature/description` - New features
- `bugfix/issue-number` - Bug fixes
- `hotfix/critical-issue` - Critical production fixes
- `experiment/research-topic` - Experimental work
- `release/version-number` - Release branches

#### Worktree Rules:
1. Maximum 4 active worktrees
2. Regular cleanup every 2 weeks
3. Completed features merged within 1 week
4. Abandoned experiments removed immediately

## Migration Commands

### Safe Worktree Removal:
```bash
# 1. Backup current state
git branch backup-[worktree-name] [worktree-name]

# 2. Merge valuable changes to main
git checkout main
git merge [worktree-name]

# 3. Remove worktree
git worktree remove worktrees/[worktree-name]
git branch -d [worktree-name]
```

### Create New Organized Worktrees:
```bash
# Create new feature branch
git checkout -b feature/current-sprint
git worktree add worktrees/current-sprint feature/current-sprint

# Create hotfix branch  
git checkout main
git checkout -b hotfix/urgent-fixes
git worktree add worktrees/urgent-fixes hotfix/urgent-fixes
```

## Automation Script

Create `scripts/cleanup-worktrees.sh`:
```bash
#!/bin/bash
# Auto-cleanup abandoned worktrees older than 30 days
# Check for unmerged changes before cleanup
# Send notification of cleanup actions
```

## Benefits of Consolidation

1. **Reduced Complexity**: Fewer directories to manage
2. **Faster Development**: Less context switching
3. **Cleaner Git History**: More organized commits
4. **Easier Maintenance**: Simplified CI/CD processes
5. **Better Collaboration**: Clear feature boundaries

## Next Steps

1. ✅ Review each worktree for completeness
2. ⏳ Merge completed features to main
3. ⏳ Remove obsolete worktrees
4. ⏳ Implement new branching strategy
5. ⏳ Create automation scripts