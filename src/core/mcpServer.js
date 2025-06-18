const { ZenServer } = require('zen-mcp');
const logger = require('../utils/logger');

const services = {
  fileManagement: require('./services/fileService'),
  systemMonitor: require('./services/systemMonitorService')
};

const server = new ZenServer({
  logger: logger.child({ module: 'mcp-server' })
});

// Register all services
Object.entries(services).forEach(([name, service]) => {
  server.registerService(name, service);
});

module.exports = {
  start: (port = 8080) => {
    server.start(port);
    logger.info(`MCP server started on port ${port}`);
    return server;
  },
  stop: () => {
    server.stop();
    logger.info('MCP server stopped');
  }
};
