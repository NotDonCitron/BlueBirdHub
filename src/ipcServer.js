const { ipcMain } = require('electron');
const fs = require('fs').promises;
const os = require('os');
const https = require('http');

module.exports = {
  init() {
    // API request handler
    ipcMain.handle('api-request', async (_, endpoint, method = 'GET', data = null) => {
      return new Promise((resolve, reject) => {
        const options = {
          hostname: '127.0.0.1',
          port: 8000,
          path: endpoint,
          method: method.toUpperCase(),
          headers: {
            'Content-Type': 'application/json',
          }
        };

        const req = https.request(options, (res) => {
          let responseData = '';
          
          res.on('data', (chunk) => {
            responseData += chunk;
          });
          
          res.on('end', () => {
            try {
              const parsed = JSON.parse(responseData);
              resolve(parsed);
            } catch (error) {
              resolve(responseData);
            }
          });
        });

        req.on('error', (error) => {
          console.error('API request error:', error);
          reject(error);
        });

        if (data && method.toUpperCase() !== 'GET') {
          req.write(JSON.stringify(data));
        }
        
        req.end();
      });
    });

    // File listing service
    ipcMain.handle('file:listDirectory', async (_, path) => {
      try {
        const files = await fs.readdir(path);
        const stats = await Promise.all(
          files.map(file => fs.stat(`${path}/${file}`))
        );
        
        return files.map((file, i) => ({
          name: file,
          isDirectory: stats[i].isDirectory(),
          size: stats[i].size,
          modified: stats[i].mtime
        }));
      } catch (error) {
        console.error(`Error listing directory: ${path}`, error);
        throw new Error(`Could not list directory: ${error.message}`);
      }
    }),
    
    // System stats service
    ipcMain.handle('system:getStats', async () => ({
      freemem: os.freemem(),
      totalmem: os.totalmem(),
      loadavg: os.loadavg(),
      cpus: os.cpus().length
    }))
  }
};
