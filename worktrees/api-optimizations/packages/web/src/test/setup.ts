import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window.electronAPI for tests
global.window.electronAPI = {
  apiRequest: vi.fn().mockResolvedValue({ status: 'running' }),
  platform: 'test',
  openFile: vi.fn().mockResolvedValue('/test/file.txt'),
  saveFile: vi.fn().mockResolvedValue(true),
  minimize: vi.fn(),
  maximize: vi.fn(),
  close: vi.fn(),
};