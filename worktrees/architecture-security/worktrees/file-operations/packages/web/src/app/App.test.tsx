import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import App from './App';

// Mock fetch for API tests
global.fetch = vi.fn();

describe('App Component - Simplified', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset electronAPI mock
    (window.electronAPI.apiRequest as any).mockResolvedValue({ status: 'running' });
  });

  it('should render the application', async () => {
    await act(async () => {
      render(<App />);
    });

    // The app should render something
    const appElement = screen.getByRole('main') || screen.getByText(/OrdnungsHub/i);
    expect(appElement).toBeInTheDocument();
  });

  it('should call electronAPI on mount', async () => {
    const mockResponse = { status: 'running' };
    (window.electronAPI.apiRequest as any).mockResolvedValueOnce(mockResponse);

    await act(async () => {
      render(<App />);
    });

    // Wait for the API call
    await waitFor(() => {
      expect(window.electronAPI.apiRequest).toHaveBeenCalled();
    });
  });

  it('should handle connection failure gracefully', async () => {
    (window.electronAPI.apiRequest as any).mockRejectedValueOnce(new Error('Connection failed'));

    await act(async () => {
      render(<App />);
    });

    // App should still render even if connection fails
    await waitFor(() => {
      const appContent = screen.getByRole('main') || document.querySelector('.app');
      expect(appContent).toBeInTheDocument();
    });
  });

  it('should work with fetch fallback', async () => {
    // Remove electronAPI temporarily
    const originalElectronAPI = window.electronAPI;
    delete (window as any).electronAPI;

    (fetch as any).mockResolvedValueOnce({
      json: async () => ({ status: 'running' }),
    });

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/');
    });

    // Restore electronAPI
    (window as any).electronAPI = originalElectronAPI;
  });
});