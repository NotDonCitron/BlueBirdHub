#!/usr/bin/env node

const API_BASE = 'http://localhost:8000';

// Test configuration
const testConfig = {
  timeout: 5000,
  verbose: true
};

// Test cases for agent endpoints
const agentTests = [
  {
    name: 'GET /agents',
    description: 'Get all agents',
    method: 'GET',
    endpoint: '/agents',
    expectedStatus: 200
  },
  {
    name: 'GET /agents/system',
    description: 'Get agent system status',
    method: 'GET',
    endpoint: '/agents/system',
    expectedStatus: 200
  },
  {
    name: 'POST /agents/tasks',
    description: 'Create agent task',
    method: 'POST',
    endpoint: '/agents/tasks',
    body: {
      title: 'Test AI Analysis Task',
      description: 'Analyze code quality using AI agents',
      assignedAgent: 'serena-coder',
      priority: 'high'
    },
    expectedStatus: 201
  },
  {
    name: 'POST /agents/anubis/init',
    description: 'Initialize Anubis workflow',
    method: 'POST',
    endpoint: '/agents/anubis/init',
    body: {
      projectName: 'BlueBirdHub Agent Integration'
    },
    expectedStatus: 201
  },
  {
    name: 'POST /agents/broadcast',
    description: 'Broadcast message to agents',
    method: 'POST',
    endpoint: '/agents/broadcast',
    body: {
      message: 'System initialization complete',
      targetAgents: ['a2a-google', 'anubis-workflow', 'serena-coder']
    },
    expectedStatus: 200
  },
  {
    name: 'POST /agents/a2a/a2a-google/message',
    description: 'Send A2A message',
    method: 'POST',
    endpoint: '/agents/a2a/a2a-google/message',
    body: {
      message: 'Hello from BlueBirdHub! Testing A2A protocol communication.'
    },
    expectedStatus: 201
  },
  {
    name: 'POST /agents/serena/activate',
    description: 'Activate Serena project',
    method: 'POST',
    endpoint: '/agents/serena/activate',
    body: {
      projectPath: 'C:\\Users\\pasca\\BlueBirdHub'
    },
    expectedStatus: 200
  },
  {
    name: 'GET /agents/messages',
    description: 'Get agent messages',
    method: 'GET',
    endpoint: '/agents/messages',
    expectedStatus: 200
  }
];

// Helper function to make HTTP requests
async function makeRequest(method, endpoint, body = null) {
  const url = `${API_BASE}${endpoint}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), testConfig.timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const responseText = await response.text();
    let responseData;
    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = responseText;
    }

    return {
      status: response.status,
      data: responseData,
      headers: response.headers
    };
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}

// Test runner
async function runAgentTests() {
  console.log('🧠 Testing BlueBirdHub AI Agent System');
  console.log('=' .repeat(60));
  console.log('');

  let passed = 0;
  let failed = 0;

  for (const test of agentTests) {
    const startTime = Date.now();
    
    try {
      console.log(`🧪 Testing: ${test.name}`);
      console.log(`📝 Description: ${test.description}`);

      const result = await makeRequest(test.method, test.endpoint, test.body);
      const duration = Date.now() - startTime;

      if (result.status === test.expectedStatus) {
        console.log(`✅ Status: ${result.status} (${duration}ms)`);
        
        if (testConfig.verbose && result.data) {
          const dataStr = typeof result.data === 'string' 
            ? result.data 
            : JSON.stringify(result.data, null, 2);
          const truncated = dataStr.length > 200 
            ? dataStr.substring(0, 200) + '...' 
            : dataStr;
          console.log(`📄 Response: ${truncated}`);
        }
        
        passed++;
      } else {
        console.log(`❌ Status: ${result.status} (expected ${test.expectedStatus})`);
        console.log(`📄 Response: ${JSON.stringify(result.data, null, 2)}`);
        failed++;
      }
    } catch (error) {
      const duration = Date.now() - startTime;
      console.log(`❌ Error: ${error.message} (${duration}ms)`);
      failed++;
    }

    console.log('');
  }

  // Summary
  console.log('📊 AGENT SYSTEM TEST SUMMARY');
  console.log('=' .repeat(60));
  console.log(`✅ Successful: ${passed}/${agentTests.length}`);
  console.log(`❌ Failed: ${failed}/${agentTests.length}`);
  console.log('');

  if (failed === 0) {
    console.log('🎉 All agent tests passed! The AI agent system is ready.');
    console.log('');
    console.log('🚀 Available Agents:');
    console.log('  • Google A2A Agent - Agent-to-Agent communication');
    console.log('  • Anubis Workflow Manager - Intelligent workflow guidance');
    console.log('  • Serena Code Assistant - Semantic code analysis');
    console.log('');
    console.log('💡 You can now:');
    console.log('  • Create intelligent workflows with Anubis');
    console.log('  • Communicate between agents using A2A protocol');
    console.log('  • Analyze code semantically with Serena');
    console.log('  • Delegate tasks to specialized AI agents');
  } else {
    console.log('⚠️  Some agent tests failed. Check the backend and try again.');
    console.log('');
    console.log('💡 Tips:');
    console.log('  • Make sure the backend is running: python ultra_simple_backend.py');
    console.log('  • Verify agent endpoints are properly implemented');
    console.log('  • Check agent system initialization');
  }

  return failed === 0;
}

// Run tests
if (require.main === module) {
  runAgentTests()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Test runner failed:', error);
      process.exit(1);
    });
}

module.exports = { runAgentTests }; 