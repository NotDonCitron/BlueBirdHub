// TypeScript declarations for Electron API

export interface ElectronAPI {
  // API communication
  apiRequest: (endpoint: string, method: string, data?: any) => Promise<any>;
  
  // System information
  platform: string;
  
  // File operations
  openFile: () => Promise<string | null>;
  saveFile: (data: any) => Promise<boolean>;
  
  // Application controls
  minimize: () => void;
  maximize: () => void;
  close: () => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}