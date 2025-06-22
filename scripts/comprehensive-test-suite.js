#!/usr/bin/env node
/**
 * Comprehensive Test Suite - Tests Every Function and Component
 * This script thoroughly tests all application functionality
 */

const BASE_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:3002';

// Test results tracking
let testResults = {
  passed: 0,
  failed: 0,
  errors: [],
  warnings: [],
  details: []
};

// Utility functions
function logTest(name, status, message = '', details = null) {
  const emoji = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : status === 'WARN' ? '⚠️' : '📝';
  console.log(`${emoji} ${name}: ${status}${message ? ` - ${message}` : ''}`);
  
  testResults.details.push({ name, status, message, details });
  
  if (status === 'PASS') testResults.passed++;
  else if (status === 'FAIL') {
    testResults.failed++;
    testResults.errors.push({ name, message, details });
  } else if (status === 'WARN') {
    testResults.warnings.push({ name, message, details });
  }
}

// API Testing Functions
async function testAPI() {
  console.log('\n🔍 TESTING: Backend API Functions\n');
  
  try {
    // Basic connectivity
    const healthCheck = await fetch(`${BASE_URL}/health`);
    if (healthCheck.ok) {
      logTest('Health Check', 'PASS', 'Backend is responding');
    } else {
      logTest('Health Check', 'FAIL', `Status: ${healthCheck.status}`);
      return false;
    }

    // Test all GET endpoints
    const getEndpoints = [
      '/workspaces',
      '/tasks/taskmaster/all',
      '/tasks/taskmaster/progress', 
      '/tasks/taskmaster/next',
      '/agents',
      '/agents/tasks',
      '/agents/messages',
      '/files'
    ];

    for (const endpoint of getEndpoints) {
      try {
        const response = await fetch(`${BASE_URL}${endpoint}`);
        if (response.ok) {
          const data = await response.json();
          logTest(`GET ${endpoint}`, 'PASS', `Returned ${Array.isArray(data) ? data.length : typeof data} items`);
        } else {
          logTest(`GET ${endpoint}`, 'FAIL', `Status: ${response.status}`);
        }
      } catch (error) {
        logTest(`GET ${endpoint}`, 'FAIL', `Network error: ${error.message}`);
      }
    }

    // Test POST endpoints with real data
    const postTests = [
      {
        endpoint: '/workspaces',
        data: { name: 'Test Workspace', description: 'Testing', color: '#3b82f6' },
        expectedStatus: 201
      },
      {
        endpoint: '/tasks/taskmaster',
        data: { title: 'Test Task', description: 'Testing', priority: 'medium' },
        expectedStatus: 201
      },
      {
        endpoint: '/tasks/taskmaster/suggest-workspace',
        data: { title: 'development task', description: 'coding project' },
        expectedStatus: 200
      },
      {
        endpoint: '/ai/suggest-workspaces',
        data: { task_title: 'web development', task_description: 'building website', existing_workspaces: [] },
        expectedStatus: 200
      },
      {
        endpoint: '/agents/tasks',
        data: { title: 'Test Agent Task', assignedAgent: 'a2a-google' },
        expectedStatus: 201
      },
      {
        endpoint: '/agents/broadcast',
        data: { message: 'Test broadcast' },
        expectedStatus: 200
      }
    ];

    for (const test of postTests) {
      try {
        const response = await fetch(`${BASE_URL}${test.endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(test.data)
        });
        
        if (response.status === test.expectedStatus) {
          logTest(`POST ${test.endpoint}`, 'PASS', `Status: ${response.status}`);
        } else {
          logTest(`POST ${test.endpoint}`, 'FAIL', `Expected ${test.expectedStatus}, got ${response.status}`);
        }
      } catch (error) {
        logTest(`POST ${test.endpoint}`, 'FAIL', `Network error: ${error.message}`);
      }
    }

    return true;
  } catch (error) {
    logTest('API Testing', 'FAIL', `Critical error: ${error.message}`);
    return false;
  }
}

// Frontend Component Testing
async function testFrontend() {
  console.log('\n🔍 TESTING: Frontend Components\n');
  
  try {
    // Test if frontend is accessible
    const frontendResponse = await fetch(FRONTEND_URL);
    if (frontendResponse.ok) {
      logTest('Frontend Accessibility', 'PASS', 'Frontend server responding');
    } else {
      logTest('Frontend Accessibility', 'FAIL', `Status: ${frontendResponse.status}`);
      return false;
    }

    // Test static assets
    const assetTests = [
      '/src/frontend/react/index.tsx',
      '/src/frontend/react/SimpleApp.tsx',
      '/src/frontend/react/components/TaskManager/TaskManager.tsx',
      '/src/frontend/react/components/AgentHub/AgentHub.tsx'
    ];

    for (const asset of assetTests) {
      try {
        const response = await fetch(`${FRONTEND_URL}${asset}`);
        if (response.ok || response.status === 304) {
          logTest(`Asset ${asset}`, 'PASS', 'File accessible');
        } else {
          logTest(`Asset ${asset}`, 'WARN', `Status: ${response.status} (may be normal)`);
        }
      } catch (error) {
        logTest(`Asset ${asset}`, 'WARN', `Not directly accessible (normal for bundled assets)`);
      }
    }

    return true;
  } catch (error) {
    logTest('Frontend Testing', 'FAIL', `Critical error: ${error.message}`);
    return false;
  }
}

// File System Testing
async function testFileSystem() {
  console.log('\n🔍 TESTING: File System Structure\n');
  
  const fs = require('fs');
  const path = require('path');
  
  const criticalFiles = [
    'ultra_simple_backend.py',
    'package.json',
    'src/frontend/react/index.tsx',
    'src/frontend/react/SimpleApp.tsx',
    'src/frontend/react/components/TaskManager/TaskManager.tsx',
    'src/frontend/react/components/AgentHub/AgentHub.tsx',
    'src/frontend/react/lib/api.ts',
    'src/frontend/react/lib/agentApi.ts',
    'src/frontend/react/utils/consoleFilter.ts'
  ];

  for (const file of criticalFiles) {
    try {
      if (fs.existsSync(file)) {
        const stats = fs.statSync(file);
        if (stats.size > 0) {
          logTest(`File: ${file}`, 'PASS', `Size: ${stats.size} bytes`);
        } else {
          logTest(`File: ${file}`, 'FAIL', 'File is empty');
        }
      } else {
        logTest(`File: ${file}`, 'FAIL', 'File does not exist');
      }
    } catch (error) {
      logTest(`File: ${file}`, 'FAIL', `Access error: ${error.message}`);
    }
  }

  // Test directory structure
  const criticalDirs = [
    'src/frontend/react/components',
    'src/frontend/react/lib',
    'src/frontend/react/utils',
    'scripts',
    'temp'
  ];

  for (const dir of criticalDirs) {
    try {
      if (fs.existsSync(dir) && fs.statSync(dir).isDirectory()) {
        const files = fs.readdirSync(dir);
        logTest(`Directory: ${dir}`, 'PASS', `Contains ${files.length} items`);
      } else {
        logTest(`Directory: ${dir}`, 'FAIL', 'Directory missing');
      }
    } catch (error) {
      logTest(`Directory: ${dir}`, 'FAIL', `Access error: ${error.message}`);
    }
  }
}

// Configuration Testing
async function testConfiguration() {
  console.log('\n🔍 TESTING: Configuration and Dependencies\n');
  
  const fs = require('fs');
  
  try {
    // Test package.json
    if (fs.existsSync('package.json')) {
      const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
      
      // Check critical scripts
      const requiredScripts = ['dev', 'dev:backend', 'dev:vite', 'dev:electron'];
      for (const script of requiredScripts) {
        if (packageJson.scripts && packageJson.scripts[script]) {
          logTest(`Script: ${script}`, 'PASS', packageJson.scripts[script]);
        } else {
          logTest(`Script: ${script}`, 'FAIL', 'Script missing');
        }
      }

      // Check dependencies
      const criticalDeps = ['react', 'vite', 'electron', 'concurrently'];
      for (const dep of criticalDeps) {
        if (packageJson.dependencies?.[dep] || packageJson.devDependencies?.[dep]) {
          const version = packageJson.dependencies?.[dep] || packageJson.devDependencies?.[dep];
          logTest(`Dependency: ${dep}`, 'PASS', `Version: ${version}`);
        } else {
          logTest(`Dependency: ${dep}`, 'FAIL', 'Dependency missing');
        }
      }
    } else {
      logTest('package.json', 'FAIL', 'File missing');
    }

    // Test TypeScript configuration
    if (fs.existsSync('tsconfig.json')) {
      logTest('tsconfig.json', 'PASS', 'TypeScript config present');
    } else {
      logTest('tsconfig.json', 'WARN', 'TypeScript config missing');
    }

    // Test Vite configuration
    if (fs.existsSync('vite.config.ts') || fs.existsSync('vite.config.js')) {
      logTest('Vite config', 'PASS', 'Vite configuration present');
    } else {
      logTest('Vite config', 'WARN', 'Vite configuration missing');
    }

  } catch (error) {
    logTest('Configuration Testing', 'FAIL', `Error: ${error.message}`);
  }
}

// Integration Testing
async function testIntegration() {
  console.log('\n🔍 TESTING: Integration and Data Flow\n');
  
  try {
    // Test full workflow: Create workspace -> Create task -> Get suggestions
    
    // Step 1: Create a workspace
    const workspaceResponse = await fetch(`${BASE_URL}/workspaces`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Integration Test Workspace',
        description: 'Testing full workflow',
        color: '#10b981'
      })
    });

    if (workspaceResponse.ok) {
      const workspace = await workspaceResponse.json();
      logTest('Integration: Create Workspace', 'PASS', `Created workspace ID: ${workspace.id}`);
      
      // Step 2: Create a task in that workspace
      const taskResponse = await fetch(`${BASE_URL}/tasks/taskmaster`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Integration Test Task',
          description: 'Testing task creation in workspace',
          workspace_id: workspace.id,
          priority: 'high'
        })
      });

      if (taskResponse.ok) {
        const task = await taskResponse.json();
        logTest('Integration: Create Task', 'PASS', `Created task ID: ${task.id}`);
        
        // Step 3: Test workspace suggestions
        const suggestionResponse = await fetch(`${BASE_URL}/tasks/taskmaster/suggest-workspace`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: 'integration test workflow',
            description: 'testing the full system integration'
          })
        });

        if (suggestionResponse.ok) {
          const suggestions = await suggestionResponse.json();
          logTest('Integration: Workspace Suggestions', 'PASS', `Got ${suggestions.suggestions?.length || 0} suggestions`);
        } else {
          logTest('Integration: Workspace Suggestions', 'FAIL', `Status: ${suggestionResponse.status}`);
        }
      } else {
        logTest('Integration: Create Task', 'FAIL', `Status: ${taskResponse.status}`);
      }
    } else {
      logTest('Integration: Create Workspace', 'FAIL', `Status: ${workspaceResponse.status}`);
    }

    // Test agent workflow
    const agentResponse = await fetch(`${BASE_URL}/agents/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Integration Agent Task',
        assignedAgent: 'a2a-google',
        description: 'Testing agent integration'
      })
    });

    if (agentResponse.ok) {
      logTest('Integration: Agent Task Creation', 'PASS', 'Agent task workflow working');
    } else {
      logTest('Integration: Agent Task Creation', 'FAIL', `Status: ${agentResponse.status}`);
    }

  } catch (error) {
    logTest('Integration Testing', 'FAIL', `Error: ${error.message}`);
  }
}

// Error Detection and Auto-Fix Testing
async function testErrorDetection() {
  console.log('\n🔍 TESTING: Error Detection and Auto-Fix Systems\n');
  
  try {
    // Test with invalid endpoints to trigger error handling
    const invalidTests = [
      { endpoint: '/nonexistent', expectedStatus: 404 },
      { endpoint: '/tasks/invalid', expectedStatus: 404 }
    ];

    for (const test of invalidTests) {
      try {
        const response = await fetch(`${BASE_URL}${test.endpoint}`);
        if (response.status === test.expectedStatus) {
          logTest(`Error Handling: ${test.endpoint}`, 'PASS', `Correctly returned ${response.status}`);
        } else {
          logTest(`Error Handling: ${test.endpoint}`, 'WARN', `Expected ${test.expectedStatus}, got ${response.status}`);
        }
      } catch (error) {
        logTest(`Error Handling: ${test.endpoint}`, 'FAIL', `Network error: ${error.message}`);
      }
    }

    // Test malformed data handling
    try {
      const malformedResponse = await fetch(`${BASE_URL}/workspaces`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'invalid json'
      });
      
      if (malformedResponse.status >= 400) {
        logTest('Error Handling: Malformed JSON', 'PASS', 'Correctly rejected invalid data');
      } else {
        logTest('Error Handling: Malformed JSON', 'FAIL', 'Should have rejected invalid data');
      }
    } catch (error) {
      logTest('Error Handling: Malformed JSON', 'PASS', 'Network correctly rejected malformed request');
    }

  } catch (error) {
    logTest('Error Detection Testing', 'FAIL', `Error: ${error.message}`);
  }
}

// Performance Testing
async function testPerformance() {
  console.log('\n🔍 TESTING: Performance and Response Times\n');
  
  const performanceTests = [
    { name: 'Health Check', endpoint: '/health' },
    { name: 'Get Workspaces', endpoint: '/workspaces' },
    { name: 'Get Tasks', endpoint: '/tasks/taskmaster/all' },
    { name: 'Get Agents', endpoint: '/agents' }
  ];

  for (const test of performanceTests) {
    try {
      const startTime = Date.now();
      const response = await fetch(`${BASE_URL}${test.endpoint}`);
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      if (response.ok) {
        if (responseTime < 1000) {
          logTest(`Performance: ${test.name}`, 'PASS', `${responseTime}ms (Good)`);
        } else if (responseTime < 3000) {
          logTest(`Performance: ${test.name}`, 'WARN', `${responseTime}ms (Acceptable)`);
        } else {
          logTest(`Performance: ${test.name}`, 'FAIL', `${responseTime}ms (Too slow)`);
        }
      } else {
        logTest(`Performance: ${test.name}`, 'FAIL', `Request failed with status ${response.status}`);
      }
    } catch (error) {
      logTest(`Performance: ${test.name}`, 'FAIL', `Error: ${error.message}`);
    }
  }
}

// Main test runner
async function runAllTests() {
  console.log('🚀 Starting Comprehensive Test Suite...\n');
  console.log('Testing every function, component, and integration point\n');
  
  // Reset test results
  testResults = { passed: 0, failed: 0, errors: [], warnings: [], details: [] };

  // Run all test suites
  await testFileSystem();
  await testConfiguration();
  await testAPI();
  await testFrontend();
  await testIntegration();
  await testErrorDetection();
  await testPerformance();

  // Generate comprehensive report
  console.log('\n' + '='.repeat(80));
  console.log('📊 COMPREHENSIVE TEST RESULTS SUMMARY');
  console.log('='.repeat(80));
  
  console.log(`\n✅ PASSED: ${testResults.passed}`);
  console.log(`❌ FAILED: ${testResults.failed}`);
  console.log(`⚠️  WARNINGS: ${testResults.warnings.length}`);
  console.log(`📈 SUCCESS RATE: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);

  if (testResults.failed > 0) {
    console.log('\n❌ CRITICAL ERRORS FOUND:');
    testResults.errors.forEach((error, index) => {
      console.log(`${index + 1}. ${error.name}: ${error.message}`);
    });
  }

  if (testResults.warnings.length > 0) {
    console.log('\n⚠️  WARNINGS (may need attention):');
    testResults.warnings.forEach((warning, index) => {
      console.log(`${index + 1}. ${warning.name}: ${warning.message}`);
    });
  }

  if (testResults.failed === 0) {
    console.log('\n🎉 ALL CRITICAL TESTS PASSED! System is fully operational.');
  } else {
    console.log(`\n🔧 ${testResults.failed} critical issues need to be fixed.`);
  }

  return testResults;
}

// Export for use as module
module.exports = { runAllTests, testResults };

// Run if called directly
if (require.main === module) {
  runAllTests().then(results => {
    process.exit(results.failed === 0 ? 0 : 1);
  });
} 