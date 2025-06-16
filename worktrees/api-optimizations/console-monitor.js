#!/usr/bin/env node

const puppeteer = require('puppeteer');
const chalk = require('chalk');

async function monitorConsole() {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ['--start-maximized']
  });

  const page = await browser.newPage();
  
  // Listen to console events
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    const timestamp = new Date().toLocaleTimeString();
    
    switch(type) {
      case 'error':
        console.log(chalk.red(`🚨 [${timestamp}] [ERROR] ${text}`));
        // Send to backend for analysis
        sendErrorToBackend('Console Error', text, page.url());
        break;
      case 'warning':
        console.log(chalk.yellow(`⚠️  [${timestamp}] [WARNING] ${text}`));
        sendErrorToBackend('Console Warning', text, page.url());
        break;
      case 'info':
        console.log(chalk.blue(`ℹ️  [${timestamp}] [INFO] ${text}`));
        break;
      case 'log':
        console.log(chalk.gray(`📝 [${timestamp}] [LOG] ${text}`));
        break;
      default:
        console.log(chalk.gray(`[${timestamp}] [${type.toUpperCase()}] ${text}`));
    }
  });

  // Listen to page errors
  page.on('pageerror', error => {
    const timestamp = new Date().toLocaleTimeString();
    console.log(chalk.red(`💥 [${timestamp}] [PAGE ERROR] ${error.message}`));
    sendErrorToBackend('Page Error', error.message, page.url(), error.stack);
  });

  // Listen to failed requests
  page.on('requestfailed', request => {
    console.log(chalk.red(`🌐 [REQUEST FAILED] ${request.url()} - ${request.failure().errorText}`));
  });

  // Listen to responses
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(chalk.red(`🔴 [HTTP ${response.status()}] ${response.url()}`));
    }
  });

  try {
    console.log(chalk.green('🚀 Opening frontend and monitoring console...'));
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle0' });
    
    console.log(chalk.green('✅ Page loaded successfully!'));
    console.log(chalk.cyan('📊 Monitoring console output... (Press Ctrl+C to stop)'));
    
    // Keep the script running
    process.on('SIGINT', async () => {
      console.log(chalk.yellow('\n🛑 Stopping console monitor...'));
      await browser.close();
      process.exit(0);
    });
    
    // Keep page alive
    await new Promise(() => {});
    
  } catch (error) {
    console.log(chalk.red(`❌ Error loading page: ${error.message}`));
    await browser.close();
  }
}

// Function to send errors to backend
async function sendErrorToBackend(source, message, url, stack = null) {
  try {
    const errorData = {
      message: message,
      stack: stack,
      source: source,
      timestamp: new Date().toISOString(),
      user_agent: 'Puppeteer Monitor',
      url: url,
      severity: source.toLowerCase().includes('warning') ? 'warning' : 'error'
    };

    const response = await fetch('http://localhost:8001/api/logs/frontend-error', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(errorData),
    });

    if (response.ok) {
      console.log(chalk.green(`✓ Error logged to backend`));
    }
  } catch (error) {
    // Silently fail if backend is not available
    console.log(chalk.gray(`⚠️  Could not log to backend: ${error.message}`));
  }
}

if (require.main === module) {
  monitorConsole().catch(console.error);
}

module.exports = { monitorConsole, sendErrorToBackend };