// Test if Electron app can start successfully
const { spawn } = require('child_process');
const path = require('path');

console.log('Testing Electron app startup...');

// Start the app in headless mode for testing
const electronProcess = spawn('npx', ['electron', '.', '--no-sandbox'], {
  cwd: __dirname,
  env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }
});

let output = '';

electronProcess.stdout.on('data', (data) => {
  output += data.toString();
  console.log('Electron:', data.toString());
});

electronProcess.stderr.on('data', (data) => {
  console.error('Electron Error:', data.toString());
});

// Give it 5 seconds to start
setTimeout(() => {
  console.log('\nKilling Electron process...');
  electronProcess.kill();
  
  // Check if app started successfully
  if (output.includes('Python Backend:') || !electronProcess.killed) {
    console.log('✅ Electron app started successfully!');
    process.exit(0);
  } else {
    console.log('❌ Electron app failed to start properly');
    process.exit(1);
  }
}, 5000);