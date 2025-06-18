# 🧪 Comprehensive Function Testing Workflow

## Overview

This workflow automatically discovers EVERY function in your codebase and ensures it has comprehensive tests. No function is left untested!

## Quick Start

```bash
# Windows
test-all-functions.bat

# Linux/Mac  
./test-all-functions.sh

# Or use Claude Code Flow
claude-flow.bat test "Generate comprehensive tests for all functions"
```

## What It Does

### 1. **Function Discovery** 🔍
- Scans all Python files (`.py`)
- Scans all JavaScript/TypeScript files (`.js`, `.ts`, `.jsx`, `.tsx`)
- Identifies:
  - Regular functions
  - Async functions
  - Class methods
  - Arrow functions
  - Exported functions
  - React components
  - API endpoints

### 2. **Test Analysis** 📊
For each function, analyzes:
- Current test coverage
- Cyclomatic complexity
- Dependencies
- Parameters and return types
- Error handling needs
- Async behavior

### 3. **Test Generation** 🔨
Automatically generates tests covering:
- **Happy Path**: Expected behavior with valid inputs
- **Edge Cases**: Empty arrays, null values, boundary conditions
- **Error Cases**: Invalid inputs, exceptions, timeouts
- **Type Safety**: Wrong types, undefined handling
- **Async Behavior**: Promise resolution/rejection
- **Performance**: Execution time limits

### 4. **Test Execution** 🚀
- Runs all tests (existing + generated)
- Collects coverage metrics
- Identifies failures
- Categorizes errors
- Detects flaky tests

### 5. **Report Generation** 📈
Creates detailed report showing:
- Total functions discovered
- Test coverage percentage
- High-risk untested functions
- Performance bottlenecks
- Actionable recommendations

## Usage Examples

### Full Workflow (Recommended)
```bash
# Discover, generate, execute, and report
test-all-functions.bat
```

### Generate Tests Only
```bash
# Only create missing tests
test-all-functions.bat generate
```

### Execute Tests Only
```bash
# Run existing tests
test-all-functions.bat execute
```

### Target Specific Directory
```bash
# Test only backend services
test-all-functions.bat target src/backend/services
```

### Generate Report
```bash
# Create coverage report from existing data
test-all-functions.bat report
```

## Output Files

### Generated Tests
```
tests/generated/
├── test_enhanced_ai_service_categorize_file.py
├── test_file_scanner_scan_directory.py
├── test_api_endpoints_upload_file.py
└── ... (one file per untested function)
```

### Coverage Report
```json
// test_coverage_report.json
{
  "summary": {
    "total_functions": 157,
    "functions_with_tests": 134,
    "test_coverage": 85.4,
    "complex_functions": 23,
    "async_functions": 42
  },
  "untested_functions": [...],
  "high_risk_functions": [...],
  "recommendations": [...]
}
```

## Test Template Example

For each function, generates comprehensive tests like:

```python
class TestCategorizeFile:
    """Comprehensive test suite for categorize_file"""
    
    def test_categorize_file_happy_path(self):
        """Test normal operation"""
        result = categorize_file("document.pdf")
        assert result == "documents"
    
    def test_categorize_file_edge_cases(self):
        """Test edge cases"""
        assert categorize_file("") == "uncategorized"
        assert categorize_file(None) raises TypeError
        
    def test_categorize_file_error_handling(self):
        """Test error scenarios"""
        with pytest.raises(FileNotFoundError):
            categorize_file("nonexistent.txt")
    
    @pytest.mark.parametrize("filename,expected", [
        ("image.jpg", "images"),
        ("video.mp4", "videos"),
        ("archive.zip", "archives"),
    ])
    def test_categorize_file_parameterized(self, filename, expected):
        """Test multiple file types"""
        assert categorize_file(filename) == expected
```

## Integration with Claude Code Flow

Use within Claude Code workflow:

```bash
# As part of feature development
claude-flow.bat feature "Add file monitoring" --with-comprehensive-tests

# Standalone test improvement
claude-flow.bat test "Improve test coverage to 100%"
```

## Configuration

Edit `.claude/workflows/comprehensive-testing.json`:

```json
{
  "testPatterns": {
    "python": {
      "frameworks": ["pytest"],
      "coverage_target": 100
    },
    "javascript": {
      "frameworks": ["jest"],
      "coverage_target": 95
    }
  },
  "qualityGates": {
    "functions": 100,  // Every function must have tests
    "lines": 95,       // Line coverage target
    "branches": 90     // Branch coverage target
  }
}
```

## Best Practices

1. **Run regularly**: Make it part of your CI/CD pipeline
2. **Review generated tests**: AI generates good starting points, but review for accuracy
3. **Add custom assertions**: Enhance generated tests with domain-specific checks
4. **Monitor trends**: Track coverage over time
5. **Fix high-risk functions first**: Focus on complex, untested code

## Troubleshooting

### "No functions found"
- Check excluded patterns in orchestrator
- Ensure correct file extensions
- Verify project structure

### "Tests failing"
- Check import paths in generated tests
- Ensure test dependencies installed
- Review function signatures

### "Low coverage"
- Some functions may be test files themselves
- Check if functions are actually being called
- Review branch coverage vs line coverage

## Success Metrics

After running this workflow, you should see:
- ✅ 100% function coverage (every function has at least one test)
- ✅ 90%+ line coverage
- ✅ All edge cases covered
- ✅ Error handling validated
- ✅ No untested high-complexity functions

## Next Steps

1. **Run the workflow**: `test-all-functions.bat`
2. **Review the report**: Open `test_coverage_report.json`
3. **Fix high-risk functions**: Add tests for complex untested code
4. **Integrate with CI/CD**: Run on every pull request
5. **Maintain coverage**: Keep it above 90%

Remember: **Every function deserves a test!** 🎯
