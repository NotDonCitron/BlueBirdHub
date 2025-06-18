const { ZenClient } = require('zen-mcp');

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8080';

class McpClient {
  constructor() {
    this.client = new ZenClient(MCP_SERVER_URL);
  }

  async call(service, method, params) {
    return this.client.request(service, method, params);
  }

  // File service shortcuts
  async listDirectory(path) {
    return this.call('fileManagement', 'listDirectory', { path });
  }

  // System monitor shortcuts
  async getSystemStats() {
    return this.call('systemMonitor', 'getSystemStats', {});
  }
}

export default new McpClient();
