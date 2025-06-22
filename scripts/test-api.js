#!/usr/bin/env node

const API_BASE = 'http://localhost:8000';

const endpoints = [
  { method: 'GET', path: '/health', description: 'Health check' },
  { method: 'POST', path: '/auth/login', body: { username: 'admin', password: 'admin123' }, description: 'Admin login' },
  { method: 'POST', path: '/auth/login', body: { username: 'user', password: 'user123' }, description: 'User login' },
  { method: 'GET', path: '/workspaces', description: 'Get workspaces' },
  { method: 'GET', path: '/tasks/taskmaster/all', description: 'Get all tasks' },
  { method: 'GET', path: '/tasks/taskmaster/progress', description: 'Get task progress' },
  { method: 'GET', path: '/tasks/taskmaster/next', description: 'Get next task' }
];

async function testEndpoint(endpoint) {
  const url = `${API_BASE}${endpoint.path}`;
  
  const options = {
    method: endpoint.method,
    headers: { 'Content-Type': 'application/json' }
  };

  if (endpoint.body) {
    options.body = JSON.stringify(endpoint.body);
  }

  try {
    console.log(`\n🧪 Testing: ${endpoint.method} ${endpoint.path}`);
    console.log(`📝 Description: ${endpoint.description}`);
    
    const startTime = Date.now();
    const response = await fetch(url, options);
    const endTime = Date.now();
    
    const data = await response.json();
    
    const status = response.ok ? '✅' : '❌';
    console.log(`${status} Status: ${response.status} (${endTime - startTime}ms)`);
    
    if (response.ok) {
      console.log(`📄 Response:`, JSON.stringify(data, null, 2).substring(0, 200) + '...');
    } else {
      console.log(`❌ Error:`, data.error || 'Unknown error');
    }
    
    return { success: response.ok, status: response.status, data };
  } catch (error) {
    console.log(`💥 Network Error: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function testAllEndpoints() {
  console.log(`🚀 Testing BlueBirdHub API at ${API_BASE}`);
  console.log(`📅 ${new Date().toISOString()}`);
  console.log('='.repeat(60));

  const results = [];
  
  for (const endpoint of endpoints) {
    const result = await testEndpoint(endpoint);
    results.push({ ...endpoint, result });
    
    // Small delay between requests
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log('\n📊 SUMMARY');
  console.log('='.repeat(60));
  
  const successful = results.filter(r => r.result.success).length;
  const total = results.length;
  
  console.log(`✅ Successful: ${successful}/${total}`);
  console.log(`❌ Failed: ${total - successful}/${total}`);
  
  if (successful < total) {
    console.log('\n🔍 Failed Endpoints:');
    results
      .filter(r => !r.result.success)
      .forEach(r => {
        console.log(`  • ${r.method} ${r.path} - ${r.result.error || `Status ${r.result.status}`}`);
      });
  }

  console.log('\n💡 Tips:');
  console.log('  • Make sure the backend is running: python ultra_simple_backend.py');
  console.log('  • Check if port 8000 is available');
  console.log('  • Verify demo accounts exist: admin/admin123, user/user123');
}

// Run if called directly
if (require.main === module) {
  testAllEndpoints().catch(console.error);
}

module.exports = { testEndpoint, testAllEndpoints }; 