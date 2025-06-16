# OrdnungsHub Testing Guide

## Overview
This document describes the testing strategy and procedures for OrdnungsHub.

## Test Structure

```
tests/
├── unit/
│   ├── test_backend.py    # Python backend unit tests
│   └── test_renderer.js    # Frontend renderer tests
├── integration/
│   └── test_ipc.js        # Electron-Python IPC tests
└── test_app.py            # Full integration test
```

## Running Tests

### All Tests
```bash
./run_all_tests.sh
```

### Python Tests Only
```bash
source venv/bin/activate
pytest tests/unit/test_backend.py -v
```

### JavaScript Tests Only
```bash
npm test
```

### Integration Tests Only
```bash
source venv/bin/activate
python test_app.py
```

## Test Coverage

### Backend Tests (Python)
- ✅ API root endpoint functionality
- ✅ Health check endpoint
- ✅ FastAPI application startup
- ✅ CORS configuration

### Frontend Tests (JavaScript)
- ✅ IPC communication mocking
- ✅ API request handling
- ✅ Error handling
- ✅ DOM event listeners

### Integration Tests
- ✅ Project structure verification
- ✅ Backend startup and response
- ✅ API endpoint availability
- ✅ File system structure

## Test Development Guidelines

1. **Write tests first** - Follow TDD principles
2. **Test isolation** - Each test should be independent
3. **Mock external dependencies** - Use mocks for IPC, API calls
4. **Meaningful assertions** - Test behavior, not implementation
5. **Clear test names** - Describe what is being tested

## Continuous Testing

During development:
```bash
# Watch mode for Python tests
pytest --watch

# Watch mode for JavaScript tests
npm test -- --watch
```

## Adding New Tests

### Python Test Template
```python
def test_new_feature():
    """Test description"""
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.get("/new-endpoint")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"
```

### JavaScript Test Template
```javascript
test('should do something', () => {
  // Arrange
  const mockFunction = jest.fn();
  
  // Act
  mockFunction('test');
  
  // Assert
  expect(mockFunction).toHaveBeenCalledWith('test');
});
```