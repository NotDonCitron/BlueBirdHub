const { app, BrowserWindow, ipcMain, dialog, shell, session, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const crypto = require('crypto');

// Security Configuration
const SECURITY_CONFIG = {
  csp: {
    defaultSrc: "'self'",
    scriptSrc: "'self' 'unsafe-eval'", // Required for React Dev Tools in development
    styleSrc: "'self' 'unsafe-inline'",
    imgSrc: "'self' data: https:",
    connectSrc: "'self' http://localhost:* ws://localhost:*",
    fontSrc: "'self'",
    objectSrc: "'none'",
    mediaSrc: "'self'",
    frameSrc: "'none'"
  },
  permissions: {
    allowedOrigins: ['http://localhost:3001', 'http://127.0.0.1:3001'],
    blockedPermissions: ['camera', 'microphone', 'geolocation', 'notifications']
  }
};

let mainWindow;
let pythonProcess = null;
const sessionNonce = crypto.randomBytes(16).toString('hex');
const isDevelopment = process.argv.includes('--dev');

// Function to start Python backend
function startPythonBackend() {
  const pythonExecutable = 'python3';
  const backendDir = path.join(__dirname, '..', 'backend');
  const projectRoot = path.join(__dirname, '..', '..');
  
  pythonProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'main:app', '--port', '8001'], {
    cwd: backendDir,
    env: { ...process.env, PYTHONPATH: projectRoot }
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
}

// Setup secure session
function setupSecureSession() {
  const ses = session.defaultSession;
  
  // Set Content Security Policy
  const cspString = Object.entries(SECURITY_CONFIG.csp)
    .map(([directive, value]) => `${camelToKebab(directive)} ${value}`)
    .join('; ');
  
  ses.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [cspString],
        'X-Frame-Options': ['DENY'],
        'X-Content-Type-Options': ['nosniff'],
        'Referrer-Policy': ['strict-origin-when-cross-origin']
      }
    });
  });
  
  // Block unwanted permissions
  ses.setPermissionRequestHandler((webContents, permission, callback) => {
    const isBlocked = SECURITY_CONFIG.permissions.blockedPermissions.includes(permission);
    callback(!isBlocked);
  });
  
  console.log('🔒 Secure session configured');
}

// Function to create the main application window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      allowRunningInsecureContent: false,
      webSecurity: true,
      sandbox: !isDevelopment,
      preload: path.join(__dirname, 'preload.js'),
      additionalArguments: [`--session-nonce=${sessionNonce}`]
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

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('will-navigate', (navigationEvent, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    if (!SECURITY_CONFIG.permissions.allowedOrigins.includes(parsedUrl.origin)) {
      console.warn(`Blocked navigation to: ${navigationUrl}`);
      navigationEvent.preventDefault();
    }
  });
  
  contents.setWindowOpenHandler(({ url }) => {
    console.warn(`Blocked window.open to: ${url}`);
    if (url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });
});

// App event handlers
app.whenReady().then(() => {
  setupSecureSession();
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

// Security IPC handlers
ipcMain.handle('get-security-info', () => {
  return {
    sessionNonce,
    securityConfig: SECURITY_CONFIG,
    electronVersion: process.versions.electron
  };
});

// Memory management
ipcMain.handle('trigger-gc', () => {
  if (global.gc) {
    global.gc();
    return { success: true, memory: process.memoryUsage() };
  }
  return { success: false, reason: 'Garbage collection not available' };
});

// File operation handlers

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

// Utility function
function camelToKebab(str) {
  return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
}