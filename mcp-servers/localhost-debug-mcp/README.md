# Localhost Debug MCP Server

Auto-checking webview localhost debugging tool for OrdnungsHub development.

## Features

- 🔍 **Auto Health Checks** - Monitor frontend, backend, and API endpoints
- 📸 **Screenshot Capture** - Take screenshots of localhost pages and components
- 📝 **Console Log Monitoring** - Capture browser console logs and errors
- ⚡ **Performance Auditing** - Analyze page load times and metrics
- 🔄 **Real-time Monitoring** - Continuous health monitoring with WebSocket updates
- 🧪 **Component Testing** - Automated React component interaction testing

## Quick Start

```bash
# Install dependencies
cd mcp-servers/localhost-debug-mcp
npm install

# Start the debug server
npm start
```

## Endpoints

### Health Monitoring
```bash
# Check all services health
curl http://localhost:3004/health-check

# Start auto-monitoring (every 30 seconds)
curl -X POST http://localhost:3004/start-monitoring \
  -H "Content-Type: application/json" \
  -d '{"interval": 30000}'

# Stop auto-monitoring
curl -X POST http://localhost:3004/stop-monitoring
```

### Visual Debugging
```bash
# Take full page screenshot
curl -X POST http://localhost:3004/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:3002"}'

# Screenshot specific component
curl -X POST http://localhost:3004/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:3002", "selector": ".dashboard-container"}'
```

### Console Monitoring
```bash
# Capture console logs for 10 seconds
curl -X POST http://localhost:3004/capture-logs \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:3002", "duration": 10000}'
```

### Performance Analysis
```bash
# Run performance audit
curl -X POST http://localhost:3004/performance-audit \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:3002"}'
```

### Component Testing
```bash
# Click a button
curl -X POST http://localhost:3004/test-component \
  -H "Content-Type: application/json" \
  -d '{"selector": "#login-button", "action": "click"}'

# Type in input field
curl -X POST http://localhost:3004/test-component \
  -H "Content-Type: application/json" \
  -d '{"selector": "#username", "action": "type", "value": "demo"}'

# Get text content
curl -X POST http://localhost:3004/test-component \
  -H "Content-Type: application/json" \
  -d '{"selector": ".error-message", "action": "text"}'
```

## WebSocket Real-time Feed

Connect to `ws://localhost:3005` to receive real-time debugging updates:

```javascript
const ws = new WebSocket('ws://localhost:3005');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Debug update:', data);
  
  switch(data.type) {
    case 'health-check':
      console.log('Health status:', data.data);
      break;
    case 'screenshot':
      console.log('Screenshot taken:', data.data.url);
      break;
    case 'console-logs':
      console.log('Console logs:', data.data.logs);
      break;
    case 'performance-audit':
      console.log('Performance metrics:', data.data);
      break;
    case 'auto-monitor':
      console.log('Auto health check:', data.data.health);
      break;
  }
};
```

## Integration with OrdnungsHub

### 1. Add to package.json scripts:
```json
{
  "scripts": {
    "debug:start": "cd mcp-servers/localhost-debug-mcp && npm start",
    "debug:monitor": "curl -X POST http://localhost:3004/start-monitoring",
    "debug:health": "curl http://localhost:3004/health-check"
  }
}
```

### 2. Use in development workflow:
```bash
# Terminal 1: Start main app
npm run dev

# Terminal 2: Start debug server
npm run debug:start

# Terminal 3: Start monitoring
npm run debug:monitor
```

## Configuration

Environment variables (optional):
```bash
DEBUG_PORT=3004           # MCP server port
DEBUG_WS_PORT=3005        # WebSocket port
MONITOR_INTERVAL=30000    # Auto-monitor interval
SCREENSHOT_QUALITY=90     # Screenshot quality
```

## Troubleshooting

### Common Issues:

1. **Port conflicts**: Ensure ports 3004 and 3005 are available
2. **Puppeteer issues**: Install system dependencies for headless Chrome
3. **WebSocket connection fails**: Check firewall settings

### Debug Commands:
```bash
# Check if services are responding
curl http://localhost:3002   # Frontend
curl http://127.0.0.1:8001   # Backend
curl http://localhost:3004   # Debug MCP

# Test WebSocket connection
node -e "const ws = require('ws'); const client = new ws('ws://localhost:3005'); client.on('open', () => console.log('Connected')); client.on('error', console.error);"
```

## Advanced Usage

### Custom Health Checks
Add custom endpoints to monitor:
```javascript
const customTargets = [
  { name: 'Database', url: 'http://127.0.0.1:8001/api/health/db' },
  { name: 'AI Service', url: 'http://127.0.0.1:8001/api/health/ai' }
];
```

### Automated Testing Workflows
```bash
# Run complete debugging suite
curl -X POST http://localhost:3004/start-monitoring
sleep 5
curl -X POST http://localhost:3004/screenshot -d '{"url":"http://localhost:3002"}'
curl -X POST http://localhost:3004/capture-logs -d '{"duration":5000}'
curl -X POST http://localhost:3004/performance-audit
```

This MCP server provides comprehensive localhost debugging capabilities specifically designed for your OrdnungsHub development workflow.