const { ipcRenderer } = require('electron');

export default {
  async listDirectory(path) {
    return await ipcRenderer.invoke('file:listDirectory', path);
  },
  
  async getSystemStats() {
    return await ipcRenderer.invoke('system:getStats');
  }
};
