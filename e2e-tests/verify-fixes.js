const fetch = require('node-fetch');

class FixVerificationTester {
  constructor() {
    this.baseUrl = 'http://localhost:5173';
    this.backendUrl = 'http://localhost:8000';
    this.results = [];
  }

  async log(testName, success, details = '') {
    const status = success ? '✅' : '❌';
    const result = { testName, success, details };
    this.results.push(result);
    console.log(`${status} ${testName}${details ? `: ${details}` : ''}`);
  }

  async testSearchEndpoints() {
    console.log('\n🔍 Testing Search API Fixes...');
    
    // Test /search/tags endpoint
    try {
      const tagsResponse = await fetch(`${this.backendUrl}/search/tags`);
      if (tagsResponse.ok) {
        const data = await tagsResponse.json();
        await this.log('Search Tags Endpoint', true, `Status: ${tagsResponse.status}, Format: ${data.success ? 'New' : 'Old'}`);
      } else {
        await this.log('Search Tags Endpoint', false, `Status: ${tagsResponse.status}`);
      }
    } catch (error) {
      await this.log('Search Tags Endpoint', false, `Error: ${error.message}`);
    }

    // Test /search/categories endpoint
    try {
      const categoriesResponse = await fetch(`${this.backendUrl}/search/categories`);
      if (categoriesResponse.ok) {
        const data = await categoriesResponse.json();
        await this.log('Search Categories Endpoint', true, `Status: ${categoriesResponse.status}, Format: ${data.success ? 'New' : 'Old'}`);
      } else {
        await this.log('Search Categories Endpoint', false, `Status: ${categoriesResponse.status}`);
      }
    } catch (error) {
      await this.log('Search Categories Endpoint', false, `Error: ${error.message}`);
    }

    // Test /search/categories with user_id
    try {
      const categoriesWithUserResponse = await fetch(`${this.backendUrl}/search/categories?user_id=1`);
      if (categoriesWithUserResponse.ok) {
        const data = await categoriesWithUserResponse.json();
        await this.log('Search Categories with user_id', true, `Status: ${categoriesWithUserResponse.status}`);
      } else {
        await this.log('Search Categories with user_id', false, `Status: ${categoriesWithUserResponse.status}`);
      }
    } catch (error) {
      await this.log('Search Categories with user_id', false, `Error: ${error.message}`);
    }

    // Test /search/files endpoint
    try {
      const filesResponse = await fetch(`${this.backendUrl}/search/files?user_id=1&q=test`);
      if (filesResponse.ok) {
        const data = await filesResponse.json();
        await this.log('Search Files Endpoint', true, `Status: ${filesResponse.status}`);
      } else {
        await this.log('Search Files Endpoint', false, `Status: ${filesResponse.status}`);
      }
    } catch (error) {
      await this.log('Search Files Endpoint', false, `Error: ${error.message}`);
    }
  }

  async testWorkspaceAuth() {
    console.log('\n🔐 Testing Workspace Authentication...');
    
    // Test workspace endpoint without auth
    try {
      const workspaceResponse = await fetch(`${this.backendUrl}/workspaces/`);
      if (workspaceResponse.status === 401) {
        await this.log('Workspace Auth Check', true, 'Correctly requires authentication');
      } else {
        await this.log('Workspace Auth Check', false, `Unexpected status: ${workspaceResponse.status}`);
      }
    } catch (error) {
      await this.log('Workspace Auth Check', false, `Error: ${error.message}`);
    }

    // Test with auth token (if available)
    try {
      const loginResponse = await fetch(`${this.backendUrl}/auth/login-json`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        const token = loginData.access_token;

        const authWorkspaceResponse = await fetch(`${this.backendUrl}/workspaces/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (authWorkspaceResponse.ok) {
          await this.log('Workspace with Auth Token', true, `Status: ${authWorkspaceResponse.status}`);
        } else {
          await this.log('Workspace with Auth Token', false, `Status: ${authWorkspaceResponse.status}`);
        }
      } else {
        await this.log('Admin Login', false, `Status: ${loginResponse.status}`);
      }
    } catch (error) {
      await this.log('Auth Token Test', false, `Error: ${error.message}`);
    }
  }

  async testFrontendIntegration() {
    console.log('\n🌐 Testing Frontend Integration...');
    
    try {
      const frontendResponse = await fetch(this.baseUrl);
      if (frontendResponse.ok) {
        await this.log('Frontend Accessibility', true, `Status: ${frontendResponse.status}`);
      } else {
        await this.log('Frontend Accessibility', false, `Status: ${frontendResponse.status}`);
      }
    } catch (error) {
      await this.log('Frontend Accessibility', false, `Error: ${error.message}`);
    }
  }

  async generateReport() {
    console.log('\n📊 VERIFICATION RESULTS SUMMARY');
    console.log('==============================');
    
    const totalTests = this.results.length;
    const passedTests = this.results.filter(test => test.success).length;
    const failedTests = totalTests - passedTests;
    const successRate = ((passedTests / totalTests) * 100).toFixed(1);

    console.log(`Total Tests: ${totalTests}`);
    console.log(`Passed: ${passedTests} ✅`);
    console.log(`Failed: ${failedTests} ❌`);
    console.log(`Success Rate: ${successRate}%`);
    
    if (failedTests > 0) {
      console.log('\n🔧 Failed Tests:');
      this.results.filter(test => !test.success).forEach(test => {
        console.log(`❌ ${test.testName}${test.details ? ` - ${test.details}` : ''}`);
      });
    }

    return { totalTests, passedTests, failedTests, successRate };
  }

  async runAllTests() {
    console.log('🔧 Starting Fix Verification Tests...\n');

    try {
      await this.testSearchEndpoints();
      await this.testWorkspaceAuth();
      await this.testFrontendIntegration();

      const summary = await this.generateReport();
      
      if (summary.failedTests === 0) {
        console.log('\n🎉 All fixes verified successfully!');
      } else {
        console.log('\n⚠️ Some issues still need attention. Please restart the backend if search endpoints are failing.');
      }

    } catch (error) {
      console.error(`🔥 Verification failed: ${error.message}`);
    }
  }
}

// Run the tests
if (require.main === module) {
  const tester = new FixVerificationTester();
  tester.runAllTests().catch(console.error);
}

module.exports = FixVerificationTester; 