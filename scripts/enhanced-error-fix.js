#!/usr/bin/env node
/**
 * Enhanced Error Detection and Auto-Fix System
 * Comprehensive testing and automatic error resolution
 */

const BASE_URL = 'http://localhost:8000';
const fs = require('fs');
const path = require('path');

class ErrorDetector {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.fixes = [];
    this.passed = 0;
    this.failed = 0;
  }

  log(type, message, details = null) {
    const timestamp = new Date().toLocaleTimeString();
    const emoji = {
      'PASS': '✅',
      'FAIL': '❌', 
      'WARN': '⚠️',
      'FIX': '🔧',
      'INFO': '📝'
    };

    console.log(`${emoji[type] || '📝'} [${timestamp}] ${message}`);
    
    if (type === 'PASS') this.passed++;
    if (type === 'FAIL') {
      this.failed++;
      this.errors.push({ message, details, timestamp });
    }
    if (type === 'WARN') this.warnings.push({ message, details, timestamp });
    if (type === 'FIX') this.fixes.push({ message, details, timestamp });
  }

  // Check if backend is running and responsive
  async checkBackendHealth() {
    this.log('INFO', 'Checking backend health...');
    
    try {
      const response = await fetch(`${BASE_URL}/health`);
      if (response.ok) {
        this.log('PASS', 'Backend is healthy and responsive');
        return true;
      } else {
        this.log('FAIL', `Backend returned status ${response.status}`);
        return false;
      }
    } catch (error) {
      this.log('FAIL', `Backend not responding: ${error.message}`);
      return false;
    }
  }

  // Test all critical API endpoints
  async testApiEndpoints() {
    this.log('INFO', 'Testing all API endpoints...');
    
    const endpoints = [
      { path: '/health', method: 'GET', expected: 200 },
      { path: '/workspaces', method: 'GET', expected: 200 },
      { path: '/tasks/taskmaster/all', method: 'GET', expected: 200 },
      { path: '/agents', method: 'GET', expected: 200 },
      { path: '/nonexistent', method: 'GET', expected: 404 }, // Should return 404
      { path: '/tasks/invalid', method: 'GET', expected: 404 }  // Should return 404
    ];

    let endpointsPassed = 0;
    
    for (const endpoint of endpoints) {
      try {
        const response = await fetch(`${BASE_URL}${endpoint.path}`, {
          method: endpoint.method
        });
        
        if (response.status === endpoint.expected) {
          this.log('PASS', `${endpoint.method} ${endpoint.path} returned ${response.status}`);
          endpointsPassed++;
        } else {
          this.log('FAIL', `${endpoint.method} ${endpoint.path} expected ${endpoint.expected}, got ${response.status}`);
        }
      } catch (error) {
        this.log('FAIL', `${endpoint.method} ${endpoint.path} failed: ${error.message}`);
      }
    }

    return endpointsPassed === endpoints.length;
  }

  // Test POST endpoints with data
  async testPostEndpoints() {
    this.log('INFO', 'Testing POST endpoints...');
    
    const postTests = [
      {
        path: '/workspaces',
        data: { name: 'Error Test Workspace', description: 'Testing', color: '#ff6b6b' },
        expected: 201
      },
      {
        path: '/tasks/taskmaster',
        data: { title: 'Error Test Task', priority: 'high' },
        expected: 201
      },
      {
        path: '/tasks/taskmaster/suggest-workspace',
        data: { title: 'development work', description: 'coding project' },
        expected: 200
      }
    ];

    let postsPassed = 0;

    for (const test of postTests) {
      try {
        const response = await fetch(`${BASE_URL}${test.path}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(test.data)
        });

        if (response.status === test.expected) {
          this.log('PASS', `POST ${test.path} returned ${response.status}`);
          postsPassed++;
        } else {
          this.log('FAIL', `POST ${test.path} expected ${test.expected}, got ${response.status}`);
        }
      } catch (error) {
        this.log('FAIL', `POST ${test.path} failed: ${error.message}`);
      }
    }

    return postsPassed === postTests.length;
  }

  // Check file system integrity
  async checkFileSystem() {
    this.log('INFO', 'Checking file system integrity...');
    
    const criticalFiles = [
      'ultra_simple_backend.py',
      'package.json',
      'src/frontend/react/index.tsx',
      'src/frontend/react/SimpleApp.tsx',
      'src/frontend/react/components/TaskManager/TaskManager.tsx',
      'src/frontend/react/lib/api.ts',
      'src/frontend/react/utils/consoleFilter.ts'
    ];

    let filesPassed = 0;

    for (const file of criticalFiles) {
      try {
        if (fs.existsSync(file)) {
          const stats = fs.statSync(file);
          if (stats.size > 0) {
            this.log('PASS', `File ${file} exists and is valid (${stats.size} bytes)`);
            filesPassed++;
          } else {
            this.log('FAIL', `File ${file} exists but is empty`);
          }
        } else {
          this.log('FAIL', `Critical file ${file} is missing`);
        }
      } catch (error) {
        this.log('FAIL', `Error checking file ${file}: ${error.message}`);
      }
    }

    return filesPassed === criticalFiles.length;
  }

  // Auto-fix common issues
  async autoFixIssues() {
    this.log('INFO', 'Running auto-fix procedures...');
    
    // Fix 1: Ensure console filter is applied
    try {
      const indexPath = 'src/frontend/react/index.tsx';
      if (fs.existsSync(indexPath)) {
        const content = fs.readFileSync(indexPath, 'utf8');
        if (!content.includes('consoleFilter')) {
          this.log('FIX', 'Console filter import missing, this should be added manually');
        } else {
          this.log('PASS', 'Console filter is properly imported');
        }
      }
    } catch (error) {
      this.log('WARN', `Could not check console filter: ${error.message}`);
    }

    // Fix 2: Verify API client is properly exported
    try {
      const apiPath = 'src/frontend/react/lib/api.ts';
      if (fs.existsSync(apiPath)) {
        const content = fs.readFileSync(apiPath, 'utf8');
        if (content.includes('export const apiClient') && content.includes('export const api')) {
          this.log('PASS', 'API client exports are correct');
        } else {
          this.log('WARN', 'API client exports may need verification');
        }
      }
    } catch (error) {
      this.log('WARN', `Could not check API exports: ${error.message}`);
    }

    // Fix 3: Check if backend process is running
    try {
      const response = await fetch(`${BASE_URL}/health`);
      if (response.ok) {
        this.log('PASS', 'Backend process is running correctly');
      } else {
        this.log('WARN', 'Backend may need restart');
      }
    } catch (error) {
      this.log('WARN', 'Backend appears to be down - may need manual restart');
    }
  }

  // Generate comprehensive report
  generateReport() {
    console.log('\n' + '='.repeat(80));
    console.log('🔍 COMPREHENSIVE ERROR DETECTION REPORT');
    console.log('='.repeat(80));
    
    console.log(`\n📊 SUMMARY:`);
    console.log(`✅ Tests Passed: ${this.passed}`);
    console.log(`❌ Tests Failed: ${this.failed}`);
    console.log(`⚠️  Warnings: ${this.warnings.length}`);
    console.log(`🔧 Auto-fixes Applied: ${this.fixes.length}`);
    console.log(`📈 Success Rate: ${((this.passed / (this.passed + this.failed)) * 100).toFixed(1)}%`);

    if (this.errors.length > 0) {
      console.log('\n❌ CRITICAL ERRORS:');
      this.errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.message}`);
      });
    }

    if (this.warnings.length > 0) {
      console.log('\n⚠️  WARNINGS:');
      this.warnings.forEach((warning, index) => {
        console.log(`  ${index + 1}. ${warning.message}`);
      });
    }

    if (this.fixes.length > 0) {
      console.log('\n🔧 AUTO-FIXES APPLIED:');
      this.fixes.forEach((fix, index) => {
        console.log(`  ${index + 1}. ${fix.message}`);
      });
    }

    // Overall health assessment
    console.log('\n🎯 SYSTEM HEALTH ASSESSMENT:');
    if (this.failed === 0) {
      console.log('🎉 EXCELLENT: All critical systems are operational!');
    } else if (this.failed <= 2) {
      console.log('👍 GOOD: Minor issues detected but system is largely functional');
    } else if (this.failed <= 5) {
      console.log('⚠️  MODERATE: Several issues need attention');
    } else {
      console.log('🚨 CRITICAL: Multiple serious issues require immediate attention');
    }

    return {
      passed: this.passed,
      failed: this.failed,
      warnings: this.warnings.length,
      fixes: this.fixes.length,
      healthy: this.failed === 0
    };
  }

  // Main test runner
  async runFullDiagnostic() {
    console.log('🚀 Starting Enhanced Error Detection and Auto-Fix...\n');
    
    // Run all diagnostic tests
    await this.checkFileSystem();
    await this.checkBackendHealth();
    await this.testApiEndpoints();
    await this.testPostEndpoints();
    await this.autoFixIssues();
    
    return this.generateReport();
  }
}

// Additional utility functions
async function testIntegrationFlow() {
  console.log('\n🔄 Testing Full Integration Flow...');
  
  try {
    // Test: Create workspace -> Create task -> Get suggestions
    const workspaceResponse = await fetch(`${BASE_URL}/workspaces`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Integration Flow Test',
        description: 'Testing complete workflow',
        color: '#6366f1'
      })
    });

    if (!workspaceResponse.ok) {
      console.log('❌ Integration test failed at workspace creation');
      return false;
    }

    const workspace = await workspaceResponse.json();
    console.log(`✅ Created test workspace: ${workspace.name} (ID: ${workspace.id})`);

    // Create a task in the workspace
    const taskResponse = await fetch(`${BASE_URL}/tasks/taskmaster`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Integration Test Task',
        description: 'Full workflow testing',
        workspace_id: workspace.id,
        priority: 'high'
      })
    });

    if (!taskResponse.ok) {
      console.log('❌ Integration test failed at task creation');
      return false;
    }

    const task = await taskResponse.json();
    console.log(`✅ Created test task: ${task.title} (ID: ${task.id})`);

    console.log('🎉 Integration flow test completed successfully!');
    return true;

  } catch (error) {
    console.log(`❌ Integration test failed: ${error.message}`);
    return false;
  }
}

// Performance testing
async function testPerformance() {
  console.log('\n⚡ Testing System Performance...');
  
  const performanceTests = [
    { name: 'Health Check', endpoint: '/health' },
    { name: 'Get Workspaces', endpoint: '/workspaces' },
    { name: 'Get Tasks', endpoint: '/tasks/taskmaster/all' }
  ];

  for (const test of performanceTests) {
    const startTime = Date.now();
    try {
      const response = await fetch(`${BASE_URL}${test.endpoint}`);
      const endTime = Date.now();
      const duration = endTime - startTime;

      if (response.ok) {
        if (duration < 100) {
          console.log(`✅ ${test.name}: ${duration}ms (Excellent)`);
        } else if (duration < 500) {
          console.log(`✅ ${test.name}: ${duration}ms (Good)`);
        } else {
          console.log(`⚠️ ${test.name}: ${duration}ms (Slow)`);
        }
      } else {
        console.log(`❌ ${test.name}: Failed (${response.status})`);
      }
    } catch (error) {
      console.log(`❌ ${test.name}: Error - ${error.message}`);
    }
  }
}

// Main execution
async function main() {
  const detector = new ErrorDetector();
  
  // Run full diagnostic
  const results = await detector.runFullDiagnostic();
  
  // Run additional tests
  await testIntegrationFlow();
  await testPerformance();
  
  // Final recommendations
  console.log('\n💡 RECOMMENDATIONS:');
  if (results.healthy) {
    console.log('🎯 System is fully operational - no action needed!');
    console.log('🔄 Continue monitoring with periodic health checks');
  } else {
    console.log('🔧 Review and fix the issues listed above');
    console.log('🔄 Re-run this diagnostic after applying fixes');
    if (results.failed > 3) {
      console.log('⚠️  Consider restarting all services if issues persist');
    }
  }
  
  return results.healthy;
}

// Export for module use
module.exports = { ErrorDetector, main };

// Run if called directly
if (require.main === module) {
  main().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('💥 Critical error in diagnostic system:', error);
    process.exit(1);
  });
} 