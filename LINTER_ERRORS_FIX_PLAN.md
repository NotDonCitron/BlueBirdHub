# Linter Errors Fix Plan - BlueBirdHub Backend

## Summary
21 Python linter errors across 4 backend files + 1 TypeScript config error. Most errors are type-related and can be fixed with minimal changes.

---

## Error Categories

### 1. **SQLAlchemy Column Usage Errors** (5 errors)
- Using Column objects in boolean contexts
- Assigning values directly to Column attributes instead of instances

### 2. **Type Annotation Mismatches** (11 errors)
- Functions returning None when declared to return Dict[str, Any]
- Passing None to parameters expecting Dict/List types

### 3. **Missing Attributes/Methods** (2 errors)
- CRUD class missing expected methods
- Enum missing expected attributes

### 4. **Type Conversion Issues** (2 errors)
- Dict type mismatches in function arguments

### 5. **TypeScript Config** (1 error)
- Project reference configuration issue

---

## File-by-File Fix Plan

### 1. **src/backend/api/tasks.py** (5 errors)

#### Line 242: None assigned to Dict[str, Any] parameter
```python
# Current issue: Passing None to a function expecting Dict[str, Any]
# Fix: Use empty dict {} instead of None
# Change: func(param, None) → func(param, {})
```

#### Lines 375-376: Column[str] in boolean context
```python
# Current issue: if task.title or task.description
# Fix: Use actual values from the task instance
# Change: if task.title → if task.title is not None
```

#### Line 431: Assigning literal to Column[int]
```python
# Current issue: task.ai_suggested_priority = 90
# Fix: This should be set on the instance, not the class
# Change: Ensure we're working with task instance, not Task class
```

#### Line 437: TaskPriority.lower() doesn't exist
```python
# Current issue: priority.lower()
# Fix: Use .value.lower() for enum values
# Change: priority.lower() → priority.value.lower()
```

### 2. **src/backend/api/workspace_files.py** (3 errors)

#### Line 27: Missing get_by_workspace method
```python
# Current issue: crud_file.get_by_workspace() doesn't exist
# Fix: Add the method to CRUDFileMetadata or use existing method
# Alternative: Use filter query directly if method not needed elsewhere
```

#### Line 41: Column[datetime] in boolean context
```python
# Current issue: if f.last_accessed_at or f.file_modified_at
# Fix: Check actual values, not column definitions
# Change: Similar to tasks.py fix
```

#### Line 79: Dict type mismatch
```python
# Current issue: Passing dict to function expecting FileMetadataCreate
# Fix: Create proper FileMetadataCreate object
# Change: crud.create(db, obj_in=dict) → crud.create(db, obj_in=FileMetadataCreate(**dict))
```

### 3. **src/backend/database/seed.py** (2 errors)

#### Line 211: Assigning datetime to Column[datetime]
```python
# Current issue: workspace.last_accessed_at = datetime.now()
# Fix: This should work on instance, verify it's not a class reference
```

#### Line 221: Column[int] passed as int parameter
```python
# Current issue: get_by_user(db, User.id)
# Fix: Pass actual user id value
# Change: User.id → user.id or specific user_id value
```

### 4. **src/backend/services/taskmaster_integration.py** (10 errors)

#### Lines 28, 59: None assigned to Dict[str, Any]
```python
# Fix: Replace None with empty dict {}
```

#### Lines 226, 264: None assigned to List[str]
```python
# Fix: Replace None with empty list []
```

#### Lines 259, 261, 349, 367, 445, 458: Return type mismatches
```python
# Current issue: Functions returning None when declared to return Dict[str, Any]
# Fix: Return empty dict {} instead of None
# Pattern: return None → return {}
```

### 5. **tsconfig.json** (1 error)

#### Line 48: Referenced project may not disable emit
```python
# Fix: Check tsconfig.node.json and ensure "noEmit" is false or remove it
```

---

## Implementation Strategy

### Priority Order:
1. **High Priority**: Fix return type issues in taskmaster_integration.py (affects API responses)
2. **Medium Priority**: Fix SQLAlchemy column usage errors (affects queries)
3. **Low Priority**: Fix TypeScript config (doesn't affect runtime)

### Testing After Each Fix:
1. Run the comprehensive test suite after each file's fixes
2. Verify API endpoints still return expected data
3. Check that database operations still work

### Minimal Change Principles:
1. Use empty collections ({}, []) instead of None where appropriate
2. For SQLAlchemy columns, access instance attributes not class attributes
3. Add missing methods only if they're used in multiple places
4. Preserve existing logic flow and error handling

---

## Quick Fix Commands

```bash
# After making fixes, test each module
python -m pytest tests/unit/test_tasks_api.py -v
python -m pytest tests/unit/test_workspace_files_api.py -v
python -m pytest tests/unit/test_taskmaster_integration.py -v

# Run the comprehensive test to ensure nothing broke
node test-comprehensive-functionality.js
```

---

## Estimated Time: 30-45 minutes for all fixes
## Risk Level: Low (mostly type annotation fixes)
## Testing Required: High (API functionality must be preserved) 