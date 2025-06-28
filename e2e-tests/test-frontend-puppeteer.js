const puppeteer = require('puppeteer');

class OrdnungsHubTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.testResults = [];
    this.baseUrl = 'http://localhost:5173';
    this.backendUrl = 'http://localhost:8000';
  }

  async init() {
    console.log('🚀 Starting OrdnungsHub Frontend Tests...');
    this.browser = await puppeteer.launch({
      headless: process.argv.includes('--headless'),
      slowMo: 100, // Slow down actions to be more human-like
      defaultViewport: { width: 1920, height: 1080 },
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Set up request interception to monitor API calls
    await this.page.setRequestInterception(true);
    this.page.on('request', (request) => {
      if (request.url().includes('localhost:8000')) {
        console.log(`📡 ${request.method()} ${request.url()}`);
      }
      request.continue();
    });
    
    // Monitor console messages and network errors
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log(`❌ Console Error: ${msg.text()}`);
      }
    });

    this.page.on('response', (response) => {
      if (!response.ok() && response.url().includes('localhost')) {
        console.log(`❌ HTTP Error: ${response.status()} ${response.url()}`);
      }
    });
  }

  async humanWait(min = 500, max = 1500) {
    const delay = Math.random() * (max - min) + min;
    await this.page.waitForTimeout(delay);
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
    try {
      await this.page.waitForSelector(selector, { visible: true, timeout: 5000 });
      await this.humanWait(200, 800);
      await this.page.click(selector);
      await this.humanWait(300, 1000);
      return true;
    } catch (error) {
      console.log(`⚠️ Click failed: ${description || selector} - ${error.message}`);
      return false;
    }
  }

  async waitForPageLoad() {
    try {
      await this.page.waitForSelector('body', { timeout: 10000 });
      await this.humanWait(500, 1000);
    } catch (error) {
      console.log(`⚠️ Page load timeout: ${error.message}`);
    }
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
      await this.logTest('Backend Health Check', false, `Error: ${error.message}`);
      return false;
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
        const usernameInput = await this.page.$('input[type="text"], input[name="username"]');
        const passwordInput = await this.page.$('input[type="password"], input[name="password"]');
        
        if (usernameInput && passwordInput) {
          const usernameValue = await this.page.evaluate(el => el.value, usernameInput);
          const passwordValue = await this.page.evaluate(el => el.value, passwordInput);
          
          await this.logTest('Credentials Pre-filled', 
            usernameValue === 'admin' && passwordValue === 'admin123',
            `Username: ${usernameValue}, Password: ${passwordValue ? '***' : 'empty'}`);

          // Submit login
          const submitButton = await this.page.$('button[type="submit"]');
          if (submitButton) {
            await this.humanClick('button[type="submit"]', 'Login Button');
            
            // Wait for redirect or page change
            await this.page.waitForTimeout(3000);
            
            const currentUrl = this.page.url();
            const isAuthenticated = !currentUrl.includes('login') && 
                                   (currentUrl.includes('/dashboard') || currentUrl === `${this.baseUrl}/`);
            await this.logTest('Login Successful', isAuthenticated, `Current URL: ${currentUrl}`);
            
            return isAuthenticated;
          }
        }
      } else {
        // Maybe already logged in?
        const currentUrl = this.page.url();
        if (currentUrl.includes('/dashboard') || await this.page.$('.dashboard')) {
          await this.logTest('Already Authenticated', true, `Current URL: ${currentUrl}`);
          return true;
        }
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
      const statElements = await this.page.$$('.stat-card, .dashboard-stat, [class*="stat"]');
      await this.logTest('Statistics Elements Present', statElements.length >= 1, `Found ${statElements.length} stat elements`);

      // Test action buttons/cards
      const actionElements = await this.page.$$('.action-card, button[class*="action"], [class*="dashboard-action"]');
      await this.logTest('Action Elements Present', actionElements.length >= 1, `Found ${actionElements.length} action elements`);

      // Test clicking action elements
      if (actionElements.length > 0) {
        for (let i = 0; i < Math.min(actionElements.length, 4); i++) {
          try {
            const beforeUrl = this.page.url();
            await actionElements[i].click();
            await this.humanWait(1000, 2000);
            
            const afterUrl = this.page.url();
            const hasNavigation = beforeUrl !== afterUrl;
            await this.logTest(`Action Element ${i + 1} Click`, true, 
              hasNavigation ? `Navigated to: ${afterUrl}` : 'No navigation detected');
            
            // Navigate back to dashboard if we moved
            if (hasNavigation && !afterUrl.includes('dashboard')) {
              await this.page.goto(`${this.baseUrl}/dashboard`);
              await this.waitForPageLoad();
            }
          } catch (error) {
            await this.logTest(`Action Element ${i + 1} Click`, false, `Error: ${error.message}`);
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
      const searchInputs = await this.page.$$('input[placeholder*="Search"], input[placeholder*="search"], [class*="search"] input');
      if (searchInputs.length > 0) {
        await this.humanType('input[placeholder*="Search"], input[placeholder*="search"], [class*="search"] input', 'test search query');
        await this.page.keyboard.press('Enter');
        await this.humanWait(1000, 2000);
        
        const currentUrl = this.page.url();
        await this.logTest('Search Navigation', 
          currentUrl.includes('/search') || currentUrl.includes('q='), 
          `URL: ${currentUrl}`);
      }

      // Test header action buttons
      const headerButtons = await this.page.$$('.header-action-btn, button[title], [class*="header"] button');
      await this.logTest('Header Buttons Present', headerButtons.length >= 1, `Found ${headerButtons.length} header buttons`);

      for (let i = 0; i < Math.min(headerButtons.length, 3); i++) {
        try {
          await headerButtons[i].click();
          await this.humanWait(500, 1000);
          await this.logTest(`Header Button ${i + 1} Click`, true);
        } catch (error) {
          await this.logTest(`Header Button ${i + 1} Click`, false, `Error: ${error.message}`);
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
        
        // Check for page-specific content
        await this.humanWait(500, 1000);
        const pageContent = await this.page.$('main, .page-content, .container, [class*="page"]');
        await this.logTest(`${route.name} Content Loaded`, !!pageContent);
        
      } catch (error) {
        await this.logTest(`Navigate to ${route.name}`, false, `Error: ${error.message}`);
      }
    }

    return true;
  }

  // Test 6: Button and Interaction Testing
  async testAllInteractions() {
    console.log('\n🖱️ Testing All Interactive Elements...');
    
    const routes = ['/dashboard', '/tasks', '/workspaces'];
    
    for (const route of routes) {
      try {
        await this.page.goto(`${this.baseUrl}${route}`);
        await this.waitForPageLoad();
        
        // Find all interactive elements
        const buttons = await this.page.$$('button:not([disabled])');
        const links = await this.page.$$('a[href]');
        const inputs = await this.page.$$('input, textarea, select');
        
        await this.logTest(`${route} - Interactive Elements Found`, 
          buttons.length + links.length + inputs.length > 0, 
          `${buttons.length} buttons, ${links.length} links, ${inputs.length} inputs`);
        
        // Test first few buttons on each page
        for (let i = 0; i < Math.min(buttons.length, 3); i++) {
          try {
            const buttonText = await this.page.evaluate(el => el.textContent || el.title || el.getAttribute('aria-label'), buttons[i]);
            await buttons[i].click();
            await this.humanWait(500, 1000);
            await this.logTest(`${route} - Button "${buttonText}" Click`, true);
          } catch (error) {
            await this.logTest(`${route} - Button ${i + 1} Click`, false, `Error: ${error.message}`);
          }
        }
        
      } catch (error) {
        await this.logTest(`${route} - Interaction Test`, false, `Error: ${error.message}`);
      }
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
        () => this.testAllInteractions()
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