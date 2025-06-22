import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiProvider, useApi } from '../ApiContext';
import { getApiUrl } from '../../config/api';

// Mock the API config
jest.mock('../../config/api', () => ({
  API_CONFIG: {
    BASE_URL: 'http://localhost:8000',
    TIMEOUT: 10000,
  },
  getApiUrl: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

const mockGetApiUrl = getApiUrl as jest.MockedFunction<typeof getApiUrl>;

// Test component that uses the API context
const TestComponent: React.FC = () => {
  const { apiStatus, setApiStatus, retryConnection, makeApiRequest } = useApi();

  const handleRetry = () => {
    retryConnection();
  };

  const handleApiRequest = async () => {
    try {
      const result = await makeApiRequest('/test', 'GET');
      console.log('API result:', result);
    } catch (error) {
      console.error('API error:', error);
    }
  };

  const handleSetStatus = (status: 'connected' | 'disconnected' | 'checking') => {
    setApiStatus(status);
  };

  return (
    <div>
      <div data-testid="api-status">{apiStatus}</div>
      <button onClick={handleRetry}>Retry Connection</button>
      <button onClick={handleApiRequest}>Make API Request</button>
      <button onClick={() => handleSetStatus('connected')}>Set Connected</button>
      <button onClick={() => handleSetStatus('disconnected')}>Set Disconnected</button>
      <button onClick={() => handleSetStatus('checking')}>Set Checking</button>
    </div>
  );
};

describe('ApiContext', () => {
  const mockOnRetryConnection = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    (global.fetch as jest.Mock).mockClear();
    mockGetApiUrl.mockReturnValue('http://localhost:8000/test');
    delete (window as any).electronAPI;
  });

  afterEach(() => {
    delete (window as any).electronAPI;
  });

  describe('Provider Initialization', () => {
    it('initializes with provided API status', () => {
      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      expect(screen.getByTestId('api-status')).toHaveTextContent('connected');
    });

    it('initializes with disconnected status', () => {
      render(
        <ApiProvider 
          apiStatus="disconnected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      expect(screen.getByTestId('api-status')).toHaveTextContent('disconnected');
    });

    it('initializes with checking status', () => {
      render(
        <ApiProvider 
          apiStatus="checking" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      expect(screen.getByTestId('api-status')).toHaveTextContent('checking');
    });
  });

  describe('Status Management', () => {
    it('updates API status when setApiStatus is called', async () => {
      const user = userEvent.setup();
      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      expect(screen.getByTestId('api-status')).toHaveTextContent('connected');

      await user.click(screen.getByText('Set Disconnected'));

      expect(screen.getByTestId('api-status')).toHaveTextContent('disconnected');
    });

    it('handles retry connection correctly', async () => {
      const user = userEvent.setup();
      render(
        <ApiProvider 
          apiStatus="disconnected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Retry Connection'));

      expect(screen.getByTestId('api-status')).toHaveTextContent('checking');
      expect(mockOnRetryConnection).toHaveBeenCalledTimes(1);
    });
  });

  describe('API Requests - Browser Mode', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'test-token');
    });

    it('makes successful GET request with auth token', async () => {
      const user = userEvent.setup();
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      expect(mockGetApiUrl).toHaveBeenCalledWith('/test');
      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
      });
    });

    it('makes POST request with data', async () => {
      const mockResponse = { success: true };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      const { makeApiRequest } = useApi();
      const testData = { name: 'test' };

      await act(async () => {
        await makeApiRequest('/test', 'POST', testData);
      });

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
        body: JSON.stringify(testData),
      });
    });

    it('makes request without auth token when not available', async () => {
      localStorage.removeItem('auth_token');
      const user = userEvent.setup();
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('includes custom headers in request', async () => {
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      const { makeApiRequest } = useApi();
      const customHeaders = { 'X-Custom-Header': 'custom-value' };

      await act(async () => {
        await makeApiRequest('/test', 'GET', null, customHeaders);
      });

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
          'X-Custom-Header': 'custom-value',
        },
      });
    });

    it('handles failed requests and sets status to disconnected', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      await waitFor(() => {
        expect(screen.getByTestId('api-status')).toHaveTextContent('disconnected');
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'API request failed:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('handles network errors and sets status to disconnected', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      await waitFor(() => {
        expect(screen.getByTestId('api-status')).toHaveTextContent('disconnected');
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'API request failed:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('does not include body for GET requests', async () => {
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      const { makeApiRequest } = useApi();
      const testData = { name: 'test' };

      await act(async () => {
        await makeApiRequest('/test', 'GET', testData);
      });

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
      });
    });
  });

  describe('API Requests - Electron Mode', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'test-token');
      (window as any).electronAPI = {
        apiRequest: jest.fn(),
      };
    });

    it('uses electronAPI when available', async () => {
      const user = userEvent.setup();
      const mockResponse = { data: 'electron-data' };
      (window as any).electronAPI.apiRequest.mockResolvedValueOnce(mockResponse);

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      expect((window as any).electronAPI.apiRequest).toHaveBeenCalledWith(
        '/test',
        'GET',
        undefined,
        {
          'Authorization': 'Bearer test-token',
        }
      );
      expect(fetch).not.toHaveBeenCalled();
    });

    it('passes custom headers to electronAPI', async () => {
      const mockResponse = { data: 'electron-data' };
      (window as any).electronAPI.apiRequest.mockResolvedValueOnce(mockResponse);

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      const { makeApiRequest } = useApi();
      const customHeaders = { 'X-Custom-Header': 'custom-value' };

      await act(async () => {
        await makeApiRequest('/test', 'POST', { data: 'test' }, customHeaders);
      });

      expect((window as any).electronAPI.apiRequest).toHaveBeenCalledWith(
        '/test',
        'POST',
        { data: 'test' },
        {
          'Authorization': 'Bearer test-token',
          'X-Custom-Header': 'custom-value',
        }
      );
    });

    it('handles electronAPI errors and sets status to disconnected', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (window as any).electronAPI.apiRequest.mockRejectedValueOnce(new Error('Electron error'));

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      await waitFor(() => {
        expect(screen.getByTestId('api-status')).toHaveTextContent('disconnected');
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'API request failed:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Context Hook', () => {
    it('throws error when used outside provider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useApi must be used within an ApiProvider');

      consoleSpy.mockRestore();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined data in POST request', async () => {
      const mockResponse = { success: true };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      const { makeApiRequest } = useApi();

      await act(async () => {
        await makeApiRequest('/test', 'POST', undefined);
      });

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
        body: JSON.stringify(undefined),
      });
    });

    it('handles null auth token', async () => {
      localStorage.removeItem('auth_token');
      const user = userEvent.setup();
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('handles empty auth token', async () => {
      localStorage.setItem('auth_token', '');
      const user = userEvent.setup();
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('handles non-JSON response errors gracefully', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      await user.click(screen.getByText('Make API Request'));

      await waitFor(() => {
        expect(screen.getByTestId('api-status')).toHaveTextContent('disconnected');
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Method Defaults', () => {
    it('uses GET method by default', async () => {
      const mockResponse = { data: 'test-data' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      render(
        <ApiProvider 
          apiStatus="connected" 
          onRetryConnection={mockOnRetryConnection}
        >
          <TestComponent />
        </ApiProvider>
      );

      const { makeApiRequest } = useApi();

      await act(async () => {
        await makeApiRequest('/test');
      });

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
      });
    });
  });
});