// Backend is running in Docker, this script just provides status
console.log('[Backend] Docker backend should be running on http://localhost:8000');
console.log('[Backend] Use "docker-compose up -d" to start the backend');
console.log('[Backend] Use "docker-compose ps" to check status');

// Keep the process alive
setInterval(() => {
  // Check if backend is responding
  fetch('http://localhost:8000/health')
    .then(res => res.json())
    .then(data => console.log('[Backend] Health check passed'))
    .catch(err => console.log('[Backend] Health check failed - ensure Docker backend is running'));
}, 30000);
