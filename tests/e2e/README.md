# End-to-End Test Suite for Workspace Management

This directory contains comprehensive end-to-end tests for the workspace management functionality of OrdnungsHub.

## Test Structure

```
tests/e2e/
├── helpers/
│   ├── api-client.ts      # API client wrapper for workspace endpoints
│   └── test-data.ts       # Test data and constants
└── workspace-management/
    ├── workspace-crud.spec.ts       # CRUD operations tests
    ├── workspace-state.spec.ts      # State management tests
    ├── workspace-templates.spec.ts  # Templates and themes tests
    ├── workspace-ai-features.spec.ts # AI-powered features tests
    ├── workspace-settings.spec.ts   # Settings and configuration tests
    └── workspace-scenarios.spec.ts  # End-to-end scenario tests
```

## Prerequisites

1. Install dependencies:
```bash
npm install
```

2. Ensure the backend server is running:
```bash
npm run dev:backend
```

## Running Tests

### Run all E2E tests:
```bash
npm run test:e2e
```

### Run specific test suites:
```bash
# Run only CRUD tests
npx playwright test workspace-crud

# Run only AI feature tests
npx playwright test workspace-ai-features

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run tests in debug mode
npx playwright test --debug
```

### Run tests with specific configuration:
```bash
# Run tests against staging environment
BASE_URL=https://staging.ordnungshub.com npx playwright test

# Run tests in specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Coverage

### 1. Workspace CRUD Operations (`workspace-crud.spec.ts`)
- List all workspaces
- Create new workspace (with and without AI suggestions)
- Get workspace by ID
- Update workspace (full and partial)
- Delete workspace
- Error handling for invalid operations
- Validation testing

### 2. Workspace State Management (`workspace-state.spec.ts`)
- Switch between workspaces
- Update workspace state
- Retrieve workspace state
- Complex state preservation
- State persistence across switches
- Multiple workspace state management

### 3. Templates and Themes (`workspace-templates.spec.ts`)
- Get available templates
- Get available themes
- Create workspace from each template
- Verify template characteristics
- Theme compatibility validation

### 4. AI-Powered Features (`workspace-ai-features.spec.ts`)
- Content analysis and assignment
- Workspace compatibility scoring
- Alternative workspace suggestions
- AI-driven workspace suggestions
- Analytics with AI insights
- Contextual recommendations

### 5. Settings and Configurations (`workspace-settings.spec.ts`)
- Ambient sound management
- Theme updates
- Color customization
- Layout configuration
- Active/inactive status
- Default workspace setting
- Complex configuration updates

### 6. End-to-End Scenarios (`workspace-scenarios.spec.ts`)
- Complete workspace lifecycle
- Multi-workspace workflows
- Template coverage testing
- Content organization workflow
- Performance under load
- Workspace migration scenario

## Test Data

Test data is centralized in `helpers/test-data.ts` and includes:
- Sample workspace configurations
- State objects for testing
- Content samples for AI testing
- Available ambient sounds
- Template names

## Writing New Tests

1. Create a new spec file in the appropriate directory
2. Import the API client and test data:
```typescript
import { test, expect } from '@playwright/test';
import { WorkspaceAPIClient } from '../helpers/api-client';
import { testWorkspaces } from '../helpers/test-data';
```

3. Structure your tests with proper setup and cleanup:
```typescript
test.describe('Feature Name', () => {
  let apiClient: WorkspaceAPIClient;
  
  test.beforeEach(async ({ request }) => {
    apiClient = new WorkspaceAPIClient(request);
  });
  
  test('should do something', async () => {
    // Your test code
  });
});
```

## CI/CD Integration

The test suite is configured to run in CI environments with:
- JUnit XML reports for test results
- JSON reports for detailed analysis
- HTML reports for local debugging
- Retry logic for flaky tests
- Parallel execution control

## Debugging

1. **Visual debugging:**
```bash
npx playwright test --debug
```

2. **View test reports:**
```bash
npx playwright show-report
```

3. **Trace viewer for failed tests:**
```bash
npx playwright show-trace
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on state from other tests
2. **Cleanup**: Always clean up created resources in `afterEach` or `afterAll` hooks
3. **Descriptive Names**: Use clear, descriptive test names that explain what is being tested
4. **Error Handling**: Test both success and failure scenarios
5. **Assertions**: Use specific assertions rather than generic ones
6. **Performance**: Use parallel execution where possible, but be mindful of API rate limits

## Troubleshooting

### Common Issues:

1. **Backend not running**: Ensure the backend server is started before running tests
2. **Port conflicts**: Check that ports 8001 (backend) are available
3. **Database state**: Tests may fail if the database is in an inconsistent state
4. **Timeout errors**: Increase timeout in playwright.config.ts if needed

### Debug Output:

Enable debug logging:
```bash
DEBUG=pw:api npx playwright test
```

## Contributing

When adding new workspace features, ensure to:
1. Add corresponding E2E tests
2. Update test data if new configurations are added
3. Document any new test utilities or helpers
4. Ensure tests pass locally before submitting PR