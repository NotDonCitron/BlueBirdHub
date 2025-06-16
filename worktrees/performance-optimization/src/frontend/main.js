const { app, BrowserWindow, ipcMain, powerMonitor } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');

let mainWindow;
let pythonProcess = null;

// Performance optimization flags
app.commandLine.appendSwitch('--enable-features', 'VaapiVideoDecoder');
app.commandLine.appendSwitch('--disable-background-timer-throttling');
app.commandLine.appendSwitch('--disable-renderer-backgrounding');
app.commandLine.appendSwitch('--disable-backgrounding-occluded-windows');

// Memory management
let memoryUsageInterval = null;
const MEMORY_WARNING_THRESHOLD = 200 * 1024 * 1024; // 200MB
const MEMORY_CRITICAL_THRESHOLD = 350 * 1024 * 1024; // 350MB

// Function to start Python backend with optimizations
function startPythonBackend() {
  const pythonExecutable = 'python3';
  const backendDir = path.join(__dirname, '..', 'backend');
  const projectRoot = path.join(__dirname, '..', '..');
  
  pythonProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'main:app', '--port', '8001'], {
    cwd: backendDir,
    env: { 
      ...process.env, 
      PYTHONPATH: projectRoot,
      PYTHONOPTIMIZE: '1', // Enable Python optimizations
      PYTHONDONTWRITEBYTECODE: '1' // Reduce disk I/O
    },
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python Backend: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Backend Error: ${data}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python Backend exited with code ${code}`);
  });

  // Restart backend if it crashes
  pythonProcess.on('error', (error) => {
    console.error('Python Backend crashed:', error);
    setTimeout(() => {
      console.log('Restarting Python Backend...');
      startPythonBackend();
    }, 5000);
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
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'OrdnungsHub',
    icon: path.join(__dirname, '..', '..', 'resources', 'icon.png')
  });

  // Load React app in development or built HTML in production
  if (process.argv.includes('--dev')) {
    mainWindow.loadURL('http://localhost:3001');
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', '..', 'dist', 'index.html'));
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
app.whenReady().then(() => {
  // Start Python backend first
  startPythonBackend();
  
  // Wait a bit for backend to start, then create window
  setTimeout(createWindow, 2000);
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

// IPC handlers for frontend-backend communication
ipcMain.handle('api-request', async (event, endpoint, method = 'GET', data = null) => {
  try {
    const url = `http://127.0.0.1:8001${endpoint}`;
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      }
    };
    
    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    return await response.json();
  } catch (error) {
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
      await fs.writeFile(result.filePath, JSON.stringify(data, null, 2));
      return true;
    } catch (error) {
      console.error('File save failed:', error);
      return false;
    }
  }
  return false;
});