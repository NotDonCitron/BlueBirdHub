#!/usr/bin/env node
/**
 * Test All API Endpoints - Comprehensive API Testing
 * Tests all backend endpoints to ensure they're working correctly
 */

const BASE_URL = 'http://localhost:8000';

async function testEndpoint(name, method, path, data = null) {
  try {
    console.log(`🔄 Testing ${name}: ${method} ${path}`);
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${BASE_URL}${path}`, options);
    const result = await response.json();
    
    if (response.ok) {
      console.log(`✅ ${name}: PASSED (${response.status})`);
      return true;
    } else {
      console.log(`❌ ${name}: FAILED (${response.status}) - ${result.error || 'Unknown error'}`);
      return false;
    }
  } catch (error) {
    console.log(`💥 ${name}: ERROR - ${error.message}`);
    return false;
  }
}

async function runAllTests() {
  console.log('🚀 Starting comprehensive API endpoint testing...\n');
  
  const tests = [
    // Core health check
    ['Health Check', 'GET', '/health'],
    
    // Workspace endpoints
    ['Get Workspaces', 'GET', '/workspaces'],
    ['Create Workspace', 'POST', '/workspaces', {
      name: 'Test Workspace',
      description: 'Created by test script',
      color: '#3b82f6'
    }],
    
    // Task endpoints
    ['Get All Tasks', 'GET', '/tasks/taskmaster/all'],
    ['Get Task Progress', 'GET', '/tasks/taskmaster/progress'],
    ['Get Next Task', 'GET', '/tasks/taskmaster/next'],
    ['Create Task', 'POST', '/tasks/taskmaster', {
      title: 'Test Task',
      description: 'Created by test script',
      priority: 'medium'
    }],
    
    // AI endpoints
    ['Workspace Suggestions', 'POST', '/tasks/taskmaster/suggest-workspace', {
      title: 'development project',
      description: 'coding and programming'
    }],
    ['AI Workspace Creation', 'POST', '/ai/suggest-workspaces', {
      task_title: 'web development',
      task_description: 'building a website',
      existing_workspaces: []
    }],
    
    // Agent endpoints
    ['Get Agents', 'GET', '/agents'],
    ['Get Agent Tasks', 'GET', '/agents/tasks'],
    ['Get Agent Messages', 'GET', '/agents/messages'],
    ['Create Agent Task', 'POST', '/agents/tasks', {
      title: 'Test Agent Task',
      assignedAgent: 'a2a-google'
    }],
    ['Agent Broadcast', 'POST', '/agents/broadcast', {
      message: 'Test broadcast message'
    }],
    
    // File system endpoints
    ['Get Files', 'GET', '/files'],
  ];
  
  let passed = 0;
  let failed = 0;
  
  for (const [name, method, path, data] of tests) {
    const success = await testEndpoint(name, method, path, data);
    if (success) {
      passed++;
    } else {
      failed++;
    }
    
    // Small delay between tests
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  console.log('\n📊 Test Results Summary:');
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);
  
  if (failed === 0) {
    console.log('\n🎉 All tests passed! API is fully operational.');
  } else {
    console.log(`\n⚠️  ${failed} test(s) failed. Please check the backend implementation.`);
  }
  
  return failed === 0;
}

// Run tests if called directly
if (require.main === module) {
  runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  });
}

module.exports = { runAllTests, testEndpoint }; 