const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;

// Function to start Python backend with proper error handling
function startPythonBackend() {
  return new Promise((resolve, reject) => {
    const pythonExecutable = 'python3';
    const backendDir = path.join(__dirname, '..', '..', '..', 'backend', 'src');
    const projectRoot = path.join(__dirname, '..', '..', '..');
    
    pythonProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'main_simple:app', '--port', '8000'], {
      cwd: backendDir,
      env: { ...process.env, PYTHONPATH: projectRoot }
    });
    
    let resolved = false;
    const timeout = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        console.warn('Backend startup timeout - proceeding with window creation');
        resolve();
      }
    }, 5000); // 5 second timeout instead of blocking
    
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(`Python Backend: ${output}`);
      
      // Check for startup completion indicators
      if ((output.includes('Uvicorn running') || output.includes('Application startup complete')) && !resolved) {
        resolved = true;
        clearTimeout(timeout);
        console.log('Backend startup detected - creating window');
        resolve();
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python Backend Error: ${data}`);
    });
    
    pythonProcess.on('error', (error) => {
      if (!resolved) {
        resolved = true;
        clearTimeout(timeout);
        console.error('Failed to start Python backend:', error);
        reject(error);
      }
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`Python Backend exited with code ${code}`);
      if (!resolved) {
        resolved = true;
        clearTimeout(timeout);
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Backend exited with code ${code}`));
        }
      }
    });
  });
}

// Function to create the main application window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '..', 'preload', 'preload.js')
    },
    title: 'OrdnungsHub',
    icon: path.join(__dirname, '..', '..', 'resources', 'icon.png')
  });

  // Load React app in development or built HTML in production
  if (process.argv.includes('--dev')) {
    mainWindow.loadURL('http://localhost:3001');
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', '..', '..', 'dist', 'web', 'index.html'));
  }

  // Open DevTools in development mode
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App event handlers
app.whenReady().then(async () => {
  try {
    // Start Python backend with smart timeout handling
    await startPythonBackend();
    
    // Create window immediately when backend is ready (or timeout reached)
    createWindow();
  } catch (error) {
    console.error('Backend startup failed:', error);
    // Create window anyway - frontend can handle offline state
    createWindow();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  // Kill Python process when app quits
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// IPC handlers for frontend-backend communication with timeout protection
ipcMain.handle('api-request', async (event, endpoint, method = 'GET', data = null) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
  
  try {
    const url = `http://127.0.0.1:8000${endpoint}`;
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal
    };
    
    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    clearTimeout(timeoutId);
    return result;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Request timeout after 15 seconds');
    }
    
    console.error('API request failed:', error);
    throw error;
  }
});

// Window control handlers
ipcMain.on('window:minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window:maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('window:close', () => {
  if (mainWindow) mainWindow.close();
});

// File operation handlers
const { dialog } = require('electron');

ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle('dialog:saveFile', async (event, data) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: [
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  
  if (!result.canceled && result.filePath) {
    const fs = require('fs').promises;
    try {
      // Use streaming for large files to prevent main thread blocking
      const content = JSON.stringify(data, null, 2);
      if (content.length > 1024 * 1024) { // > 1MB
        console.log('Large file detected - using streaming write');
        const stream = require('fs').createWriteStream(result.filePath);
        await new Promise((resolve, reject) => {
          stream.write(content, (error) => {
            if (error) reject(error);
            else {
              stream.end();
              resolve();
            }
          });
        });
      } else {
        await fs.writeFile(result.filePath, content);
      }
      return true;
    } catch (error) {
      console.error('File save failed:', error);
      return false;
    }
  }
  return false;
});