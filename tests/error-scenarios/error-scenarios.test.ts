import { test, expect } from '@playwright/test';

test.describe('Error Handling Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3000');
    
    // Wait for app to load
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
  });

  test('handles network failures gracefully', async ({ page }) => {
    // Block all network requests to simulate network failure
    await page.route('**/*', route => route.abort());
    
    // Try to perform an action that requires network
    await page.click('[data-testid="create-workspace-btn"]');
    
    // Should show error message instead of crashing
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Verbindungsfehler');
  });

  test('handles API timeout errors', async ({ page }) => {
    // Delay all API requests to simulate timeout
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 30000)); // 30 second delay
      route.continue();
    });
    
    // Try to load data that times out
    await page.click('[data-testid="load-workspaces-btn"]');
    
    // Should show timeout error
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
  });

  test('handles server errors (5xx)', async ({ page }) => {
    // Mock server error responses
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    // Try to perform an action
    await page.click('[data-testid="create-task-btn"]');
    
    // Should show server error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Serverfehler');
  });

  test('handles authentication errors (401)', async ({ page }) => {
    // Mock authentication error
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      });
    });
    
    // Try to access protected resource
    await page.click('[data-testid="dashboard-link"]');
    
    // Should redirect to login or show auth error
    await expect(page.locator('[data-testid="login-form"], [data-testid="auth-error"]')).toBeVisible();
  });

  test('handles validation errors (422)', async ({ page }) => {
    // Mock validation error
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Validation Error',
          details: [
            { field: 'name', message: 'Name is required' }
          ]
        })
      });
    });
    
    // Submit a form with invalid data
    await page.fill('[data-testid="workspace-name-input"]', '');
    await page.click('[data-testid="submit-workspace-form"]');
    
    // Should show validation errors
    await expect(page.locator('[data-testid="field-error-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="field-error-name"]')).toContainText('Name is required');
  });

  test('error boundary catches React component errors', async ({ page }) => {
    // Inject code that will cause a React error
    await page.evaluate(() => {
      // Trigger a React error by modifying component state incorrectly
      const reactRoot = document.querySelector('#root');
      if (reactRoot) {
        // Force a render error
        Object.defineProperty(window, 'triggerReactError', {
          value: () => {
            throw new Error('Test React Component Error');
          }
        });
      }
    });
    
    // Trigger the error
    await page.evaluate(() => (window as any).triggerReactError());
    
    // Error boundary should catch it and show fallback UI
    await expect(page.locator('[data-testid="error-boundary-fallback"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-boundary-fallback"]')).toContainText('Etwas ist schiefgelaufen');
  });

  test('error dashboard appears when errors occur', async ({ page }) => {
    // Generate some errors
    await page.route('**/api/workspaces', route => route.abort());
    await page.click('[data-testid="load-workspaces-btn"]');
    
    // Error dashboard button should appear
    await expect(page.locator('[data-testid="error-dashboard-toggle"]')).toBeVisible();
    
    // Click to open dashboard
    await page.click('[data-testid="error-dashboard-toggle"]');
    
    // Dashboard should be visible
    await expect(page.locator('[data-testid="error-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-count"]')).toContainText('1');
  });

  test('circuit breaker prevents cascade failures', async ({ page }) => {
    let requestCount = 0;
    
    // Mock failing API that fails multiple times
    await page.route('**/api/health', route => {
      requestCount++;
      if (requestCount <= 5) {
        route.fulfill({ status: 500 });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'healthy' })
        });
      }
    });
    
    // Make multiple requests that should trigger circuit breaker
    for (let i = 0; i < 3; i++) {
      await page.click('[data-testid="check-health-btn"]');
      await page.waitForTimeout(1000);
    }
    
    // Circuit breaker should be open
    await expect(page.locator('[data-testid="circuit-breaker-status"]')).toContainText('OPEN');
    
    // Further requests should be blocked
    await page.click('[data-testid="check-health-btn"]');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Service unavailable');
  });

  test('retry mechanism works for transient failures', async ({ page }) => {
    let attemptCount = 0;
    
    // Mock API that fails first two times then succeeds
    await page.route('**/api/tasks', route => {
      attemptCount++;
      if (attemptCount <= 2) {
        route.abort();
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ tasks: [] })
        });
      }
    });
    
    // Make request that should retry and eventually succeed
    await page.click('[data-testid="load-tasks-btn"]');
    
    // Should eventually show success
    await expect(page.locator('[data-testid="tasks-list"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible();
  });

  test('error export functionality works', async ({ page }) => {
    // Generate some errors
    await page.route('**/api/**', route => route.abort());
    await page.click('[data-testid="create-workspace-btn"]');
    
    // Open error dashboard
    await page.click('[data-testid="error-dashboard-toggle"]');
    
    // Start download when export is clicked
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="export-errors-btn"]');
    const download = await downloadPromise;
    
    // Verify download occurred
    expect(download.suggestedFilename()).toMatch(/error-report-\d+\.json/);
  });

  test('error clearing functionality works', async ({ page }) => {
    // Generate some errors
    await page.route('**/api/**', route => route.abort());
    await page.click('[data-testid="create-workspace-btn"]');
    
    // Open error dashboard
    await page.click('[data-testid="error-dashboard-toggle"]');
    
    // Verify errors exist
    await expect(page.locator('[data-testid="error-count"]')).not.toContainText('0');
    
    // Clear errors
    await page.click('[data-testid="clear-errors-btn"]');
    
    // Verify errors are cleared
    await expect(page.locator('[data-testid="error-count"]')).toContainText('0');
  });
});