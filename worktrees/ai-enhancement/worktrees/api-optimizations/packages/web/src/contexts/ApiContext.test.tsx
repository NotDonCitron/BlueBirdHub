import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, renderHook, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiProvider, useApi } from './ApiContext';

// Mock fetch
global.fetch = vi.fn();

describe('ApiContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset electronAPI mock
    (window.electronAPI.apiRequest as any).mockResolvedValue({ test: 'data' });
  });

  it('should provide API context to children', () => {
    const TestComponent = () => {
      const { apiStatus } = useApi();
      return <div>Status: {apiStatus}</div>;
    };

    render(
      <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
        <TestComponent />
      </ApiProvider>
    );

    expect(screen.getByText('Status: connected')).toBeInTheDocument();
  });

  it('should handle API request through context via electronAPI', async () => {
    const mockResponse = { test: 'data' };
    (window.electronAPI.apiRequest as any).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useApi(), {
      wrapper: ({ children }) => (
        <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
          {children}
        </ApiProvider>
      ),
    });

    let response;
    await act(async () => {
      response = await result.current.makeApiRequest('/test', 'GET');
    });

    expect(window.electronAPI.apiRequest).toHaveBeenCalledWith('/test', 'GET', undefined);
    expect(response).toEqual(mockResponse);
  });

  it('should provide retry connection function', async () => {
    const user = userEvent.setup();
    const mockRetry = vi.fn();
    
    const TestComponent = () => {
      const { retryConnection } = useApi();
      return <button onClick={retryConnection}>Retry</button>;
    };

    render(
      <ApiProvider apiStatus="disconnected" onRetryConnection={mockRetry}>
        <TestComponent />
      </ApiProvider>
    );

    const retryButton = screen.getByText('Retry');
    await user.click(retryButton);
    
    expect(mockRetry).toHaveBeenCalled();
  });

  it('should fallback to fetch when electronAPI is not available', async () => {
    // Temporarily remove electronAPI
    const originalElectronAPI = window.electronAPI;
    delete (window as any).electronAPI;

    const mockResponse = { test: 'data' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useApi(), {
      wrapper: ({ children }) => (
        <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
          {children}
        </ApiProvider>
      ),
    });

    let response;
    await act(async () => {
      response = await result.current.makeApiRequest('/test', 'GET');
    });
    
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/test',
      expect.objectContaining({
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
    );
    expect(response).toEqual(mockResponse);

    // Restore electronAPI
    (window as any).electronAPI = originalElectronAPI;
  });

  it('should handle POST requests with data', async () => {
    const mockResponse = { success: true };
    (window.electronAPI.apiRequest as any).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useApi(), {
      wrapper: ({ children }) => (
        <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
          {children}
        </ApiProvider>
      ),
    });

    const testData = { name: 'test' };
    let response;
    
    await act(async () => {
      response = await result.current.makeApiRequest('/test', 'POST', testData);
    });

    expect(window.electronAPI.apiRequest).toHaveBeenCalledWith('/test', 'POST', testData);
    expect(response).toEqual(mockResponse);
  });

  it('should handle API errors gracefully', async () => {
    const mockError = new Error('API Error');
    (window.electronAPI.apiRequest as any).mockRejectedValueOnce(mockError);

    const { result } = renderHook(() => useApi(), {
      wrapper: ({ children }) => (
        <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
          {children}
        </ApiProvider>
      ),
    });

    await act(async () => {
      try {
        await result.current.makeApiRequest('/test', 'GET');
      } catch (error) {
        expect(error).toBe(mockError);
      }
    });

    expect(window.electronAPI.apiRequest).toHaveBeenCalledWith('/test', 'GET', undefined);
  });
});