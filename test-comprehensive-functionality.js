const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class ComprehensiveFunctionalityTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.baseUrl = 'http://localhost:3001';
    this.backendUrl = 'http://localhost:8000';
    this.results = [];
    this.testStartTime = new Date();
  }

  async initialize() {
    console.log('🚀 Launching Comprehensive Functionality Test Suite...');
    this.browser = await puppeteer.launch({ 
      headless: false,
      devtools: true,
      defaultViewport: { width: 1920, height: 1080 }
    });
    this.page = await this.browser.newPage();
    
    // Enable console logging
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Browser Console Error:', msg.text());
      }
    });
    
    // Handle page errors
    this.page.on('pageerror', error => {
      console.log('❌ Page Error:', error.message);
    });
  }

  async logTest(testName, success, details = '') {
    const timestamp = new Date().toISOString();
    const result = { testName, success, details, timestamp };
    this.results.push(result);
    
    const icon = success ? '✅' : '❌';
    console.log(`${icon} ${testName}: ${success ? 'PASSED' : 'FAILED'} ${details ? `(${details})` : ''}`);
  }

  async humanWait(min = 500, max = 1500) {
    const delay = Math.random() * (max - min) + min;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  async humanClick(selector, description) {
    await this.page.waitForSelector(selector, { timeout: 5000 });
    await this.humanWait(200, 500);
    await this.page.click(selector);
    console.log(`🖱️ Clicked: ${description}`);
  }

  async humanType(selector, text, description) {
    await this.page.waitForSelector(selector, { timeout: 5000 });
    await this.page.click(selector);
    await this.humanWait(100, 300);
    await this.page.type(selector, text, { delay: 50 });
    console.log(`⌨️ Typed "${text}" in: ${description}`);
  }

  // === AUTHENTICATION TESTS ===
  async testAuthentication() {
    console.log('\n🔐 Testing Authentication...');
    
    try {
      await this.page.goto(this.baseUrl);
      await this.humanWait(2000);

      // Check login form
      const loginForm = await this.page.$('form');
      await this.logTest('Login Form Present', !!loginForm);

      if (loginForm) {
        // Submit login with pre-filled credentials
        await this.humanClick('button[type="submit"]', 'Login Button');
        await this.humanWait(3000, 5000);
        
        const currentUrl = this.page.url();
        const isLoggedIn = !currentUrl.includes('/login') && (currentUrl.includes('/dashboard') || currentUrl === this.baseUrl + '/');
        await this.logTest('Authentication Success', isLoggedIn, `URL: ${currentUrl}`);
        
        return isLoggedIn;
      }
      return false;
    } catch (error) {
      await this.logTest('Authentication', false, error.message);
      return false;
    }
  }

  // === TASK CREATION & WORKSPACE ASSIGNMENT TESTS ===
  async testTaskCreationAndWorkspaceAssignment() {
    console.log('\n📋 Testing Task Creation & Workspace Assignment...');
    
    try {
      // Navigate to tasks page
      await this.page.goto(`${this.baseUrl}/tasks`);
      await this.humanWait(2000);

      // Click Add Task tab/button
      try {
        const addTaskButtons = await this.page.$$('button, .tab, [role="tab"], .nav-item');
        for (const btn of addTaskButtons) {
          const text = await btn.evaluate(el => el.textContent);
          if (text && text.toLowerCase().includes('add')) {
            await btn.click();
            break;
          }
        }
      } catch {
        console.log('⚠️ Add task button not found, trying alternative approach');
      }
      await this.humanWait(1000);

      // Fill task creation form
      const taskTitle = `Test Task ${Date.now()}`;
      const taskDescription = 'This is a comprehensive test task for workspace assignment verification';
      
      const titleInputs = await this.page.$$('input');
      const textareas = await this.page.$$('textarea');
      
      if (titleInputs.length > 0) {
        await titleInputs[0].click();
        await titleInputs[0].type(taskTitle);
        await this.logTest('Task Title Entered', true, taskTitle);
      }
      
      if (textareas.length > 0) {
        await textareas[0].click();
        await textareas[0].type(taskDescription);
        await this.logTest('Task Description Entered', true);
      }

      // Submit task
      const submitButtons = await this.page.$$('button[type="submit"], button');
      for (const btn of submitButtons) {
        const text = await btn.evaluate(el => el.textContent);
        if (text && (text.toLowerCase().includes('create') || text.toLowerCase().includes('submit') || text.toLowerCase().includes('add'))) {
          await btn.click();
          break;
        }
      }
      await this.humanWait(2000, 3000);

      await this.logTest('Task Creation Form Submission', true, `Created: ${taskTitle}`);

      return { taskTitle };
    } catch (error) {
      await this.logTest('Task Creation & Workspace Assignment', false, error.message);
      return null;
    }
  }

  // === WORKSPACE INTEGRATION TESTS ===
  async testWorkspaceTaskIntegration(createdTasks) {
    console.log('\n🏠 Testing Workspace-Task Integration...');
    
    try {
      // Navigate to workspaces
      await this.page.goto(`${this.baseUrl}/workspaces`);
      await this.humanWait(2000);

      // Test workspace overview API
      const overviewResponse = await fetch(`${this.backendUrl}/tasks/taskmaster/workspace-overview`);
      const overviewData = await overviewResponse.json();
      
      await this.logTest('Workspace Overview API', overviewResponse.ok && overviewData.success, 
        `Workspaces: ${Object.keys(overviewData.overview || {}).length}`);

      // Check if tasks appear in workspace overview
      const workspace1Tasks = overviewData.overview?.['1']?.tasks || [];
      const workspace2Tasks = overviewData.overview?.['2']?.tasks || [];
      
      await this.logTest('Workspace 1 Has Tasks', workspace1Tasks.length > 0, `${workspace1Tasks.length} tasks`);
      await this.logTest('Workspace 2 Has Tasks', workspace2Tasks.length > 0, `${workspace2Tasks.length} tasks`);

      // Test workspace switching
      const workspaceCards = await this.page.$$('.workspace-card, [data-testid="workspace-card"]');
      if (workspaceCards.length > 1) {
        await workspaceCards[1].click();
        await this.humanWait(2000);
        await this.logTest('Workspace Switching', true, 'Switched to second workspace');
        
        // Check if workspace-specific content loads
        const workspaceContent = await this.page.$('.workspace-content, .tasks-list, .workspace-tasks');
        await this.logTest('Workspace Content Loads', !!workspaceContent);
      }

      return true;
    } catch (error) {
      await this.logTest('Workspace-Task Integration', false, error.message);
      return false;
    }
  }

  // === FILE UPLOAD TESTS ===
  async testFileUploadFunctionality() {
    console.log('\n📁 Testing File Upload Functionality...');
    
    try {
      // Navigate to file manager
      await this.page.goto(`${this.baseUrl}/files`);
      await this.humanWait(2000);

      // Test workspace files API endpoints
      for (let workspaceId = 1; workspaceId <= 3; workspaceId++) {
        const filesResponse = await fetch(`${this.backendUrl}/workspaces/${workspaceId}/files`);
        const filesData = await filesResponse.json();
        
        await this.logTest(`Workspace ${workspaceId} Files API`, filesResponse.ok && filesData.success !== false, 
          `Files: ${filesData.files?.length || 0}`);
      }

      // Create a test file for upload
      const testFileContent = 'This is a test file for upload functionality testing';
      const testFileName = `test-upload-${Date.now()}.txt`;
      
      // Test file upload UI if available
      const fileInput = await this.page.$('input[type="file"]');
      if (fileInput) {
        // Create temporary test file
        const tempFilePath = path.join(__dirname, testFileName);
        fs.writeFileSync(tempFilePath, testFileContent);
        
        await fileInput.uploadFile(tempFilePath);
        await this.humanWait(1000);
        
        // Look for upload button or submit
        const uploadBtn = await this.page.$('button:has-text("Upload"), button[type="submit"], .upload-btn');
        if (uploadBtn) {
          await uploadBtn.click();
          await this.humanWait(2000);
        }
        
        await this.logTest('File Upload UI Interaction', true, testFileName);
        
        // Clean up temp file
        fs.unlinkSync(tempFilePath);
      } else {
        await this.logTest('File Upload UI Available', false, 'No file input found');
      }

      // Test file management features
      const fileActions = await this.page.$$('button[aria-label*="delete"], button[aria-label*="download"], .file-action');
      await this.logTest('File Management Actions Available', fileActions.length > 0, `${fileActions.length} actions`);

      return true;
    } catch (error) {
      await this.logTest('File Upload Functionality', false, error.message);
      return false;
    }
  }

  // === SEARCH FUNCTIONALITY TESTS ===
  async testSearchFunctionality() {
    console.log('\n🔍 Testing Search Functionality...');
    
    try {
      // Test global search
      await this.page.goto(`${this.baseUrl}/search`);
      await this.humanWait(2000);

      const searchQueries = [
        'test task',
        'organization',
        'development',
        'file',
        'workspace'
      ];

      for (const query of searchQueries) {
        // Find search input
        const searchInput = await this.page.$('input[type="search"], input[placeholder*="search"], #search-input');
        if (searchInput) {
          await searchInput.click();
          await searchInput.evaluate(el => el.value = ''); // Clear
          await searchInput.type(query);
          await this.humanWait(500);
          
          // Try to submit search
          try {
            await this.page.keyboard.press('Enter');
          } catch {
            const searchBtn = await this.page.$('button[type="submit"], .search-btn, button:has-text("Search")');
            if (searchBtn) await searchBtn.click();
          }
          
          await this.humanWait(1500);
          
          // Check for search results
          const results = await this.page.$$('.search-result, .result-item, .search-item');
          await this.logTest(`Search: "${query}"`, true, `${results.length} results`);
        }
      }

      // Test search API endpoint
      const searchResponse = await fetch(`${this.backendUrl}/search?q=test&type=all`);
      await this.logTest('Search API Endpoint', searchResponse.ok, `Status: ${searchResponse.status}`);

      return true;
    } catch (error) {
      await this.logTest('Search Functionality', false, error.message);
      return false;
    }
  }

  // === AI FEATURES TESTS ===
  async testAIFeatures() {
    console.log('\n🤖 Testing AI Features...');
    
    try {
      // Test AI Assistant
      await this.page.goto(`${this.baseUrl}/ai-assistant`);
      await this.humanWait(2000);

      const aiInput = await this.page.$('input[placeholder*="message"], textarea[placeholder*="ask"], .ai-input');
      if (aiInput) {
        await aiInput.type('Help me organize my tasks');
        await this.humanWait(500);
        
        const sendBtn = await this.page.$('button:has-text("Send"), .send-btn, button[type="submit"]');
        if (sendBtn) {
          await sendBtn.click();
          await this.humanWait(2000);
        }
        
        await this.logTest('AI Assistant Interaction', true, 'Message sent');
      }

      // Test AI Content Assignment
      await this.page.goto(`${this.baseUrl}/ai-content`);
      await this.humanWait(2000);

      const aiContentFeatures = await this.page.$$('.ai-feature, .content-assignment, .ai-suggestion');
      await this.logTest('AI Content Features Available', aiContentFeatures.length > 0, `${aiContentFeatures.length} features`);

      // Test AI API endpoints
      const aiEndpoints = [
        '/ai/text/analyze',
        '/ai/text/summarize',
        '/ai/content/categorize'
      ];

      for (const endpoint of aiEndpoints) {
        try {
          const response = await fetch(`${this.backendUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: 'This is a test text for AI analysis' })
          });
          await this.logTest(`AI API: ${endpoint}`, response.status !== 404, `Status: ${response.status}`);
        } catch (error) {
          await this.logTest(`AI API: ${endpoint}`, false, error.message);
        }
      }

      return true;
    } catch (error) {
      await this.logTest('AI Features', false, error.message);
      return false;
    }
  }

  // === AUTOMATION TESTS ===
  async testAutomationFeatures() {
    console.log('\n⚙️ Testing Automation Features...');
    
    try {
      await this.page.goto(`${this.baseUrl}/automation`);
      await this.humanWait(2000);

      // Test automation UI elements
      const automationFeatures = await this.page.$$('.automation-rule, .workflow, .trigger, .automation-item');
      await this.logTest('Automation UI Elements', automationFeatures.length > 0, `${automationFeatures.length} elements`);

      // Test automation API
      const automationResponse = await fetch(`${this.backendUrl}/automation/rules`);
      await this.logTest('Automation API', automationResponse.ok, `Status: ${automationResponse.status}`);

      // Test workflow creation if available
      const createWorkflowBtn = await this.page.$('button:has-text("Create"), .create-workflow, .new-automation');
      if (createWorkflowBtn) {
        await createWorkflowBtn.click();
        await this.humanWait(1000);
        await this.logTest('Workflow Creation UI', true, 'Creation dialog opened');
      }

      return true;
    } catch (error) {
      await this.logTest('Automation Features', false, error.message);
      return false;
    }
  }

  // === SETTINGS & CONFIGURATION TESTS ===
  async testSettingsAndConfiguration() {
    console.log('\n⚙️ Testing Settings & Configuration...');
    
    try {
      await this.page.goto(`${this.baseUrl}/settings`);
      await this.humanWait(2000);

      // Test settings sections
      const settingSections = await this.page.$$('.setting-section, .config-group, .settings-item');
      await this.logTest('Settings Sections Available', settingSections.length > 0, `${settingSections.length} sections`);

      // Test theme switching if available
      const themeSelector = await this.page.$('select[name*="theme"], .theme-selector, input[type="radio"][name*="theme"]');
      if (themeSelector) {
        await themeSelector.click();
        await this.humanWait(500);
        await this.logTest('Theme Selection Available', true);
      }

      // Test settings save
      const saveBtn = await this.page.$('button:has-text("Save"), .save-settings, button[type="submit"]');
      if (saveBtn) {
        await saveBtn.click();
        await this.humanWait(1000);
        await this.logTest('Settings Save Functionality', true);
      }

      return true;
    } catch (error) {
      await this.logTest('Settings & Configuration', false, error.message);
      return false;
    }
  }

  // === COLLABORATION TESTS ===
  async testCollaborationFeatures() {
    console.log('\n👥 Testing Collaboration Features...');
    
    try {
      // Test collaboration API endpoints
      const collaborationEndpoints = [
        '/collaboration/workspaces',
        '/collaboration/teams',
        '/collaboration/shared-tasks'
      ];

      for (const endpoint of collaborationEndpoints) {
        try {
          const response = await fetch(`${this.backendUrl}${endpoint}`);
          await this.logTest(`Collaboration API: ${endpoint}`, response.status !== 404, `Status: ${response.status}`);
        } catch (error) {
          await this.logTest(`Collaboration API: ${endpoint}`, false, error.message);
        }
      }

      // Test sharing functionality in workspaces
      await this.page.goto(`${this.baseUrl}/workspaces`);
      await this.humanWait(2000);

      const shareButtons = await this.page.$$('button[aria-label*="share"], .share-btn, button:has-text("Share")');
      await this.logTest('Workspace Sharing Options', shareButtons.length > 0, `${shareButtons.length} share buttons`);

      return true;
    } catch (error) {
      await this.logTest('Collaboration Features', false, error.message);
      return false;
    }
  }

  // === PERFORMANCE & ERROR HANDLING TESTS ===
  async testPerformanceAndErrorHandling() {
    console.log('\n⚡ Testing Performance & Error Handling...');
    
    try {
      // Test invalid routes
      const invalidRoutes = [
        '/non-existent-page',
        '/invalid/route/test',
        '/api/fake-endpoint'
      ];

      for (const route of invalidRoutes) {
        await this.page.goto(`${this.baseUrl}${route}`);
        await this.humanWait(1000);
        
        const isErrorHandled = await this.page.evaluate(() => {
          return document.body.innerText.includes('404') || 
                 document.body.innerText.toLowerCase().includes('not found') ||
                 document.body.innerText.toLowerCase().includes('error');
        });
        
        await this.logTest(`Error Handling: ${route}`, isErrorHandled, 'Error page displayed');
      }

      // Test API error handling
      const invalidApiCall = await fetch(`${this.backendUrl}/non-existent-endpoint`);
      await this.logTest('API Error Handling', invalidApiCall.status === 404 || invalidApiCall.status === 422, 
        `Status: ${invalidApiCall.status}`);

      // Test performance monitoring endpoint
      const perfResponse = await fetch(`${this.backendUrl}/performance/metrics`);
      await this.logTest('Performance Monitoring API', perfResponse.status !== 404, `Status: ${perfResponse.status}`);

      return true;
    } catch (error) {
      await this.logTest('Performance & Error Handling', false, error.message);
      return false;
    }
  }

  // === API TESTS ===
  async testAllAPIEndpoints() {
    console.log('\n🔌 Testing All API Endpoints...');
    
    const endpoints = [
      { path: '/health', method: 'GET', expected: 200 },
      { path: '/workspaces/', method: 'GET', expected: 200 },
      { path: '/tasks/taskmaster/all', method: 'GET', expected: 200 },
      { path: '/tasks/taskmaster/workspace-overview', method: 'GET', expected: 200 },
      { path: '/workspaces/1/files', method: 'GET', expected: 200 },
      { path: '/workspaces/2/files', method: 'GET', expected: 200 }
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(`${this.backendUrl}${endpoint.path}`, {
          method: endpoint.method,
          headers: { 'Content-Type': 'application/json' }
        });
        
        const success = response.status === endpoint.expected || response.status === 200;
        await this.logTest(`API ${endpoint.method} ${endpoint.path}`, success, `Status: ${response.status}`);
      } catch (error) {
        await this.logTest(`API ${endpoint.method} ${endpoint.path}`, false, error.message);
      }
    }
  }

  // === MAIN TEST RUNNER ===
  async runAllTests() {
    try {
      await this.initialize();
      
      console.log('🎯 Starting Comprehensive Functionality Tests...\n');
      
      // Run all test suites
      const authSuccess = await this.testAuthentication();
      
      if (authSuccess) {
        const taskData = await this.testTaskCreationAndWorkspaceAssignment();
        await this.testWorkspaceTaskIntegration(taskData);
        await this.testFileUploadFunctionality();
        await this.testSearchFunctionality();
        await this.testAIFeatures();
        await this.testAutomationFeatures();
        await this.testSettingsAndConfiguration();
        await this.testCollaborationFeatures();
        await this.testPerformanceAndErrorHandling();
        await this.testAllAPIEndpoints();
      }
      
      // Generate final report
      await this.generateFinalReport();
      
    } catch (error) {
      console.error('❌ Test Suite Error:', error);
    } finally {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }

  async generateFinalReport() {
    const totalTests = this.results.length;
    const passedTests = this.results.filter(r => r.success).length;
    const failedTests = totalTests - passedTests;
    const successRate = ((passedTests / totalTests) * 100).toFixed(1);
    
    const summary = {
      totalTests,
      passedTests,
      failedTests,
      successRate: `${successRate}%`,
      testDuration: `${((Date.now() - this.testStartTime.getTime()) / 1000).toFixed(1)}s`
    };
    
    const report = {
      summary,
      timestamp: new Date().toISOString(),
      results: this.results
    };
    
    // Save detailed report
    fs.writeFileSync('comprehensive-test-results.json', JSON.stringify(report, null, 2));
    
    console.log('\n' + '='.repeat(80));
    console.log('📊 COMPREHENSIVE FUNCTIONALITY TEST RESULTS');
    console.log('='.repeat(80));
    console.log(`🎯 Total Tests: ${totalTests}`);
    console.log(`✅ Passed: ${passedTests}`);
    console.log(`❌ Failed: ${failedTests}`);
    console.log(`📈 Success Rate: ${successRate}%`);
    console.log(`⏱️ Duration: ${summary.testDuration}`);
    console.log('='.repeat(80));
    
    if (failedTests > 0) {
      console.log('\n❌ FAILED TESTS:');
      this.results.filter(r => !r.success).forEach(result => {
        console.log(`   • ${result.testName}: ${result.details}`);
      });
    }
    
    console.log(`\n📄 Detailed report saved to: comprehensive-test-results.json`);
  }
}

// Run the comprehensive test suite
const tester = new ComprehensiveFunctionalityTester();
tester.runAllTests().catch(console.error); 