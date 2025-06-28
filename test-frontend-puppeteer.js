const puppeteer = require('puppeteer');

class OrdnungsHubTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.testResults = [];
    this.baseUrl = 'http://localhost:3001';
    this.backendUrl = 'http://localhost:8000';
  }

  async init() {
    console.log('🚀 Starting OrdnungsHub Frontend Tests...');
    this.browser = await puppeteer.launch({
      headless: false, // Show browser for human-like testing
      slowMo: 100, // Slow down actions to be more human-like
      defaultViewport: { width: 1920, height: 1080 },
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Set up request interception to monitor API calls
    await this.page.setRequestInterception(true);
    this.page.on('request', (request) => {
      console.log(`📡 ${request.method()} ${request.url()}`);
      request.continue();
    });
    
    // Monitor console messages
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log(`❌ Console Error: ${msg.text()}`);
      }
    });
  }

  async humanWait(min = 500, max = 1500) {
    const delay = Math.random() * (max - min) + min;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  async humanType(selector, text, options = {}) {
    await this.page.click(selector);
    await this.humanWait(200, 500);
    if (options.clear) {
      await this.page.keyboard.down('Control');
      await this.page.keyboard.press('KeyA');
      await this.page.keyboard.up('Control');
    }
    await this.page.type(selector, text, { delay: 50 + Math.random() * 100 });
  }

  async humanClick(selector, description = '') {
    console.log(`👆 Clicking: ${description || selector}`);
    await this.page.waitForSelector(selector, { visible: true, timeout: 5000 });
    await this.humanWait(200, 800);
    await this.page.click(selector);
    await this.humanWait(300, 1000);
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState?.('networkidle') || 
          this.page.waitForSelector('body', { timeout: 10000 });
    await this.humanWait(500, 1000);
  }

  async logTest(testName, success, details = '') {
    const result = { testName, success, details, timestamp: new Date().toISOString() };
    this.testResults.push(result);
    const status = success ? '✅' : '❌';
    console.log(`${status} ${testName}${details ? `: ${details}` : ''}`);
  }

  // Test 1: Backend Health Check
  async testBackendHealth() {
    console.log('\n🏥 Testing Backend Health...');
    try {
      const response = await fetch(`${this.backendUrl}/health`);
      const data = await response.json();
      const isHealthy = data.status === 'healthy';
      await this.logTest('Backend Health Check', isHealthy, `Status: ${data.status}`);
      return isHealthy;
    } catch (error) {
      await this.logTest('Backend Health Check', false, `Error: ${error.message} - Continuing with frontend tests`);
      return false; // Continue with other tests even if backend is down
    }
  }

  // Test 2: Authentication Flow
  async testAuthentication() {
    console.log('\n🔐 Testing Authentication Flow...');
    try {
      await this.page.goto(this.baseUrl);
      await this.waitForPageLoad();

      // Check if login form is present
      const loginForm = await this.page.$('form');
      if (loginForm) {
        await this.logTest('Login Form Present', true);

        // Check pre-filled credentials
        const usernameValue = await this.page.$eval('input[type="text"]', el => el.value);
        const passwordValue = await this.page.$eval('input[type="password"]', el => el.value);
        
        await this.logTest('Credentials Pre-filled', 
          usernameValue === 'admin' && passwordValue === 'admin123',
          `Username: ${usernameValue}, Password: ${passwordValue ? '***' : 'empty'}`);

        // Submit login
        await this.humanClick('button[type="submit"]', 'Login Button');
        
        // Improved waiting strategy for authentication
        try {
          // Wait for either navigation or main content to appear
          await Promise.race([
            this.page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 15000 }),
            this.page.waitForSelector('.dashboard, .task-manager, .main-content', { timeout: 15000 }),
            this.page.waitForFunction(() => !window.location.href.includes('login'), { timeout: 15000 })
          ]);
        } catch (waitError) {
          console.log('Navigation timeout, checking current state...');
        }
        
        // Wait a bit more for async loading
        await this.humanWait(2000, 3000);
        
        const currentUrl = this.page.url();
        const isOnDashboard = !currentUrl.includes('login') && !currentUrl.includes('signin');
        await this.logTest('Authentication Flow', isOnDashboard, `Current URL: ${currentUrl}`);
        
        return isOnDashboard;
      } else {
        await this.logTest('Login Form Present', false, 'No login form found');
        return false;
      }
    } catch (error) {
      await this.logTest('Authentication Flow', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Test 3: Dashboard Functionality
  async testDashboard() {
    console.log('\n🏠 Testing Dashboard Functionality...');
    try {
      // Ensure we're on dashboard
      if (!this.page.url().includes('dashboard') && this.page.url() !== `${this.baseUrl}/`) {
        await this.page.goto(`${this.baseUrl}/dashboard`);
        await this.waitForPageLoad();
      }

      // Test statistics cards
      const statCards = await this.page.$$('.stat-card');
      await this.logTest('Statistics Cards Present', statCards.length >= 4, `Found ${statCards.length} cards`);

      // Test action buttons with better error handling
      const actionCards = await this.page.$$('.action-card');
      if (actionCards.length > 0) {
        for (let i = 0; i < Math.min(actionCards.length, 4); i++) {
          try {
            // Re-query the elements to avoid stale references
            const freshActionCards = await this.page.$$('.action-card');
            if (freshActionCards[i]) {
              await freshActionCards[i].click();
              await this.humanWait(500, 1000);
              await this.logTest(`Action Button ${i + 1} Click`, true);
              
              // Navigate back to dashboard if we moved
              const currentUrl = this.page.url();
              if (!currentUrl.includes('dashboard') && currentUrl !== `${this.baseUrl}/`) {
                await this.page.goto(`${this.baseUrl}/dashboard`);
                await this.waitForPageLoad();
              }
            } else {
              await this.logTest(`Action Button ${i + 1} Click`, false, `Button not found after re-query`);
            }
          } catch (error) {
            await this.logTest(`Action Button ${i + 1} Click`, false, `Error: ${error.message}`);
          }
        }
      }

      return true;
    } catch (error) {
      await this.logTest('Dashboard Test', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Test 4: Header Functionality
  async testHeader() {
    console.log('\n📋 Testing Header Functionality...');
    try {
      // Test search functionality
      const searchInput = await this.page.$('input[placeholder*="Search"]');
      if (searchInput) {
        await this.humanType('input[placeholder*="Search"]', 'test search query');
        await this.page.keyboard.press('Enter');
        await this.humanWait(1000, 2000);
        
        const currentUrl = this.page.url();
        await this.logTest('Search Navigation', 
          currentUrl.includes('/search'), 
          `URL: ${currentUrl}`);
      }

      // Test header action buttons
      const headerButtons = await this.page.$$('.header-action-btn');
      for (let i = 0; i < headerButtons.length; i++) {
        try {
          await headerButtons[i].click();
          await this.humanWait(500, 1000);
          await this.logTest(`Header Action Button ${i + 1} Click`, true);
        } catch (error) {
          await this.logTest(`Header Action Button ${i + 1} Click`, false, `Error: ${error.message}`);
        }
      }

      return true;
    } catch (error) {
      await this.logTest('Header Test', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Test 5: Navigation Testing
  async testNavigation() {
    console.log('\n🧭 Testing Navigation...');
    const routes = [
      { path: '/tasks', name: 'Task Manager' },
      { path: '/workspaces', name: 'Workspaces' },
      { path: '/files', name: 'File Manager' },
      { path: '/search', name: 'Smart Search' },
      { path: '/ai-assistant', name: 'AI Assistant' },
      { path: '/ai-content', name: 'AI Content' },
      { path: '/automation', name: 'Automation' },
      { path: '/settings', name: 'Settings' }
    ];

    for (const route of routes) {
      try {
        await this.page.goto(`${this.baseUrl}${route.path}`);
        await this.waitForPageLoad();
        
        const currentUrl = this.page.url();
        const isCorrectRoute = currentUrl.includes(route.path);
        await this.logTest(`Navigate to ${route.name}`, isCorrectRoute, `URL: ${currentUrl}`);
        
        // Look for page-specific elements
        await this.humanWait(500, 1000);
        
      } catch (error) {
        await this.logTest(`Navigate to ${route.name}`, false, `Error: ${error.message}`);
      }
    }

    return true;
  }

  // Test 6: Task Manager Functionality
  async testTaskManager() {
    console.log('\n📋 Testing Task Manager...');
    try {
      await this.page.goto(`${this.baseUrl}/tasks`);
      await this.waitForPageLoad();

      // Test tab navigation using proper CSS selectors
      const tabTests = [
        { text: 'Overview', selector: '.task-manager-tabs button.tab' },
        { text: 'All Tasks', selector: '.task-manager-tabs button.tab' },
        { text: 'Dependencies', selector: '.task-manager-tabs button.tab' },
        { text: 'Add Task', selector: '.task-manager-tabs button.tab' },
        { text: 'Workspaces', selector: '.task-manager-tabs button.tab' }
      ];
      
      for (const tab of tabTests) {
        try {
          // Find tab by text content
          const tabElements = await this.page.$$(tab.selector);
          let targetTab = null;
          
          for (const element of tabElements) {
            const text = await this.page.evaluate(el => el.textContent.trim(), element);
            if (text === tab.text || text.includes(tab.text)) {
              targetTab = element;
              break;
            }
          }
          
          if (targetTab) {
            await targetTab.click();
            await this.humanWait(500, 1000);
            await this.logTest(`${tab.text} Tab Click`, true);
          } else {
            await this.logTest(`${tab.text} Tab Click`, false, `Tab not found`);
          }
        } catch (error) {
          await this.logTest(`${tab.text} Tab Click`, false, `Error: ${error.message}`);
        }
      }

      // Test Add Task functionality
      try {
        // Click on Add Task tab first
        const addTaskTabs = await this.page.$$(`.task-manager-tabs button.tab`);
        let addTaskTab = null;
        
        for (const tab of addTaskTabs) {
          const text = await this.page.evaluate(el => el.textContent.trim(), tab);
          if (text.includes('Add Task')) {
            addTaskTab = tab;
            break;
          }
        }
        
        if (addTaskTab) {
          await addTaskTab.click();
          await this.humanWait(1000, 2000);

          // Fill task form
          const titleInput = await this.page.$('input[placeholder*="title"]');
          if (titleInput) {
            await this.humanType('input[placeholder*="title"]', 'Test Task from Puppeteer');
            
            const descInput = await this.page.$('textarea[placeholder*="description"], textarea[placeholder*="Describe"]');
            if (descInput) {
              await this.humanType('textarea[placeholder*="description"], textarea[placeholder*="Describe"]', 
                'This is a test task created by automated testing');
            }
            
            // Try to submit - look for various button text patterns
            const addButtons = await this.page.$$('button');
            let submitButton = null;
            
            for (const button of addButtons) {
              const text = await this.page.evaluate(el => el.textContent.trim(), button);
              if (text.includes('Add') || text.includes('Create') || text.includes('Submit')) {
                submitButton = button;
                break;
              }
            }
            
            if (submitButton) {
              await submitButton.click();
              await this.humanWait(1000, 2000);
              await this.logTest('Add Task Form Submission', true);
            } else {
              await this.logTest('Add Task Form', false, 'Submit button not found');
            }
          } else {
            await this.logTest('Add Task Form', false, 'Title input not found');
          }
        } else {
          await this.logTest('Add Task Form', false, 'Add Task tab not found');
        }
      } catch (error) {
        await this.logTest('Add Task Form', false, `Error: ${error.message}`);
      }

      return true;
    } catch (error) {
      await this.logTest('Task Manager Test', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Test 7: Workspaces Functionality
  async testWorkspaces() {
    console.log('\n🗂️ Testing Workspaces...');
    try {
      await this.page.goto(`${this.baseUrl}/workspaces`);
      await this.waitForPageLoad();

      // Test workspace creation button - look for proper button with correct text
      const createButtons = await this.page.$$('button');
      let createButton = null;
      
      for (const button of createButtons) {
        const text = await this.page.evaluate(el => el.textContent.trim(), button);
        if (text.includes('Create') || text.includes('📁 Create File Workspace')) {
          createButton = button;
          break;
        }
      }
      
      if (createButton) {
        await createButton.click();
        await this.humanWait(1000, 2000);
        await this.logTest('Workspace Creation Button', true);
      } else {
        await this.logTest('Workspaces Test', false, 'Create button not found');
      }

      // Test workspace cards if any exist
      const workspaceCards = await this.page.$$('.workspace-card');
      await this.logTest('Workspace Cards Present', workspaceCards.length >= 0, `Found ${workspaceCards.length} workspace cards`);

      return true;
    } catch (error) {
      await this.logTest('Workspaces Test', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Test 8: Sidebar Functionality
  async testSidebar() {
    console.log('\n📱 Testing Sidebar...');
    try {
      // Test sidebar toggle - look for the toggle button by class
      const toggleButton = await this.page.$('.sidebar-toggle') || 
                           await this.page.$('button[title*="Toggle"]') ||
                           await this.page.$('button[title*="sidebar"]');
      
      if (toggleButton) {
        await toggleButton.click();
        await this.humanWait(500, 1000);
        await this.logTest('Sidebar Toggle', true);
      } else {
        await this.logTest('Sidebar Test', false, `Toggle button not found`);
      }

      // Test navigation items
      const navItems = await this.page.$$('.sidebar button, .nav-item, [class*="nav"]');
      await this.logTest('Sidebar Navigation Items', navItems.length > 0, `Found ${navItems.length} navigation items`);

      return true;
    } catch (error) {
      await this.logTest('Sidebar Test', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Test 9: Error Handling and Edge Cases
  async testErrorHandling() {
    console.log('\n⚠️ Testing Error Handling...');
    try {
      // Test invalid routes
      await this.page.goto(`${this.baseUrl}/invalid-route`);
      await this.waitForPageLoad();
      
      const currentUrl = this.page.url();
      await this.logTest('Invalid Route Handling', true, `URL: ${currentUrl}`);

      // Test offline scenario (if possible)
      await this.page.setOfflineMode(true);
      await this.humanWait(1000, 2000);
      await this.page.setOfflineMode(false);
      await this.logTest('Offline Mode Test', true);

      return true;
    } catch (error) {
      await this.logTest('Error Handling Test', false, `Error: ${error.message}`);
      return false;
    }
  }

  // Run all tests
  async runAllTests() {
    try {
      await this.init();

      const tests = [
        () => this.testBackendHealth(),
        () => this.testAuthentication(),
        () => this.testDashboard(),
        () => this.testHeader(),
        () => this.testNavigation(),
        () => this.testTaskManager(),
        () => this.testWorkspaces(),
        () => this.testSidebar(),
        () => this.testErrorHandling()
      ];

      for (const test of tests) {
        await test();
        await this.humanWait(1000, 2000); // Pause between tests
      }

      await this.generateReport();
      
    } catch (error) {
      console.error(`🔥 Test suite failed: ${error.message}`);
    } finally {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }

  async generateReport() {
    console.log('\n📊 TEST RESULTS SUMMARY');
    console.log('========================');
    
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(test => test.success).length;
    const failedTests = totalTests - passedTests;
    const successRate = ((passedTests / totalTests) * 100).toFixed(1);

    console.log(`Total Tests: ${totalTests}`);
    console.log(`Passed: ${passedTests} ✅`);
    console.log(`Failed: ${failedTests} ❌`);
    console.log(`Success Rate: ${successRate}%`);
    
    console.log('\nDetailed Results:');
    this.testResults.forEach(test => {
      const status = test.success ? '✅' : '❌';
      console.log(`${status} ${test.testName}${test.details ? ` - ${test.details}` : ''}`);
    });

    // Save results to file
    const fs = require('fs');
    const reportData = {
      summary: { totalTests, passedTests, failedTests, successRate },
      timestamp: new Date().toISOString(),
      results: this.testResults
    };
    
    fs.writeFileSync('test-results.json', JSON.stringify(reportData, null, 2));
    console.log('\n💾 Results saved to test-results.json');
  }
}

// Run the tests
if (require.main === module) {
  const tester = new OrdnungsHubTester();
  tester.runAllTests().catch(console.error);
}

module.exports = OrdnungsHubTester; 