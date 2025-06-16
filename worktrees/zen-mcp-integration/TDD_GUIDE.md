# Test-Driven Development (TDD) Guide

## Overview
This document outlines the Test-Driven Development (TDD) workflow and quality standards for our project. All new features and bug fixes should follow this process.

## TDD Workflow

### 1. Red Phase - Write a Failing Test
- Write a test for the smallest unit of functionality
- The test should fail initially (red)
- Run the test to verify it fails as expected

### 2. Green Phase - Make the Test Pass
- Write the minimal code needed to make the test pass
- Don't worry about code quality yet
- Run the test to verify it passes (green)

### 3. Refactor Phase - Improve the Code
- Refactor the code while keeping tests passing
- Improve readability and maintainability
- Ensure all tests still pass after refactoring

## Quality Standards

### Test Coverage Requirements
- Minimum 80% line coverage
- Minimum 80% branch coverage
- All public APIs must have tests
- Edge cases must be tested

### Test Naming Conventions
- Test files: `*.test.js` or `*.spec.js`
- Test directories: `__tests__`
- Test names should be descriptive and follow the pattern: `should [expected behavior] when [state/condition]`

### Test Structure
Use the AAA pattern (Arrange-Act-Assert):

```javascript
describe('Component/Module Name', () => {
  describe('methodName', () => {
    it('should do something when some condition', () => {
      // Arrange
      const input = {...};
      const expected = {...};
      
      // Act
      const result = methodUnderTest(input);
      
      // Assert
      expect(result).toEqual(expected);
    });
  });
});
```

## Running Tests

### Development (Watch Mode)
```bash
npm test -- --watch
```

### Run Specific Test File
```bash
npm test -- path/to/test.file.js
```

### Run with Coverage
```bash
npm test -- --coverage
```

### CI/CD Pipeline
- Tests must pass in CI before merging to main
- Coverage thresholds are enforced
- Build fails if coverage is below minimum requirements

## Best Practices
1. Write tests first (Red-Green-Refactor)
2. Keep tests small and focused
3. Test one thing per test case
4. Use descriptive test names
5. Avoid test interdependencies
6. Mock external dependencies
7. Keep test data close to tests
8. Regularly refactor test code

## Code Review Checklist
- [ ] Tests exist for new functionality
- [ ] Tests follow naming conventions
- [ ] Tests are readable and maintainable
- [ ] Edge cases are tested
- [ ] Test coverage meets requirements
- [ ] Mocks are used appropriately
- [ ] Test data is properly set up and cleaned up
