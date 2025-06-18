const { spawn } = require('child_process');
const args = process.argv.slice(2);

console.log(`Running 'task-master-ai ${args.join(' ')}'...`);

const child = spawn('npx', ['task-master-ai', ...args], {
  shell: true,
  // This is the important change. We are now controlling the I/O streams
  // to prevent the terminal from interfering with the tool.
  stdio: ['ignore', process.stdout, process.stderr]
});

child.on('close', (code) => {
  console.log(`\ntask-master-ai process exited with code ${code}`);
});

child.on('error', (err) => {
  console.error('Failed to start task-master-ai process:', err);
});