// Type definitions for Electron API
declare global {
  interface Window {
    electronAPI?: {
      apiRequest: (url: string, method: string, data?: any) => Promise<any>;
      openFile: () => Promise<string | null>;
      saveFile: (content: string) => Promise<boolean>;
      showMessageBox: (options: any) => Promise<any>;
    };
  }
}

export {};
EOF < /dev/null