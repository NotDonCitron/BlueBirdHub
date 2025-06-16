import { test, expect, _electron as electron } from '@playwright/test';
import { ElectronApplication, Page } from 'playwright';
import path from 'path';

let electronApp: ElectronApplication;
let page: Page;

test.beforeAll(async () => {
  // Launch Electron app
  electronApp = await electron.launch({
    args: [
      path.join(__dirname, '../../dist/main/main.js'),
      '--dev'
    ],
  });

  // Get the first window that the app opens
  page = await electronApp.firstWindow();
});

test.afterAll(async () => {
  // Close the app
  await electronApp.close();
});

test.describe('OrdnungsHub Desktop App', () => {
  test('should launch the application', async () => {
    // Check window title
    const title = await page.title();
    expect(title).toBe('OrdnungsHub');
  });

  test('should load the React app', async () => {
    // Wait for the app to load
    await page.waitForSelector('.app', { timeout: 10000 });
    
    // Check if main layout is present
    const appElement = await page.$('.app');
    expect(appElement).toBeTruthy();
  });

  test('should have working window controls', async () => {
    const window = await electronApp.browserWindow(page);
    
    // Test minimize
    await window.minimize();
    const isMinimized = await window.evaluate((win) => win.isMinimized());
    expect(isMinimized).toBe(true);
    
    // Restore window
    await window.restore();
    const isRestored = await window.evaluate((win) => !win.isMinimized());
    expect(isRestored).toBe(true);
  });

  test('should expose electronAPI to renderer', async () => {
    // Check if electronAPI is available
    const hasElectronAPI = await page.evaluate(() => {
      return typeof window.electronAPI !== 'undefined';
    });
    expect(hasElectronAPI).toBe(true);

    // Check API methods
    const apiMethods = await page.evaluate(() => {
      return Object.keys(window.electronAPI);
    });
    expect(apiMethods).toContain('apiRequest');
    expect(apiMethods).toContain('platform');
    expect(apiMethods).toContain('openFile');
    expect(apiMethods).toContain('saveFile');
  });

  test('should handle API requests through IPC', async () => {
    // Test API request
    const response = await page.evaluate(async () => {
      return await window.electronAPI.apiRequest('/', 'GET');
    });
    
    expect(response).toBeDefined();
  });

  test('should display sidebar navigation', async () => {
    // Check for sidebar
    await page.waitForSelector('.sidebar', { timeout: 5000 });
    
    // Check navigation items
    const navItems = await page.$$eval('.sidebar-item', items => 
      items.map(item => item.textContent)
    );
    
    expect(navItems).toContain('Dashboard');
    expect(navItems).toContain('Tasks');
    expect(navItems).toContain('Files');
    expect(navItems).toContain('Workspaces');
  });

  test('should navigate between views', async () => {
    // Click on Tasks navigation
    await page.click('text=Tasks');
    await page.waitForURL('**/tasks');
    
    // Verify we're on tasks page
    const url = page.url();
    expect(url).toContain('/tasks');
  });

  test('should handle connection status', async () => {
    // Check for API status in header
    const headerElement = await page.waitForSelector('.header', { timeout: 5000 });
    expect(headerElement).toBeTruthy();
    
    // Should show connection status
    const statusText = await page.textContent('.api-status');
    expect(['Connected', 'Disconnected', 'Checking']).toContain(statusText);
  });
});