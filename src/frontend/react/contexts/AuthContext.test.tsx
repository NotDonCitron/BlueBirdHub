import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';

// Mock fetch
global.fetch = jest.fn();

// Test component that uses the auth context
const TestComponent = () => {
  const { user, isAuthenticated, isLoading, token, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="token">{token || 'no-token'}</div>
      <div data-testid="user">{user ? user.username : 'no-user'}</div>
      <button onClick={() => login('test-token')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    (global.fetch as jest.Mock).mockClear();
  });

  it('initializes with loading state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('loading')).toHaveTextContent('loading');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
  });

  it('loads existing token from localStorage', async () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true
    };

    localStorage.setItem('auth_token', 'existing-token');
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('token')).toHaveTextContent('existing-token');
    expect(screen.getByTestId('user')).toHaveTextContent('testuser');

    expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/auth/me', {
      headers: { 'Authorization': 'Bearer existing-token' }
    });
  });

  it('uses electronAPI when available', async () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true
    };

    const mockApiRequest = jest.fn().mockResolvedValue(mockUser);
    (window as any).electronAPI = { apiRequest: mockApiRequest };

    localStorage.setItem('auth_token', 'existing-token');

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(mockApiRequest).toHaveBeenCalledWith('/auth/me', 'GET', null, {
      'Authorization': 'Bearer existing-token'
    });
  });

  it('clears token on failed user fetch', async () => {
    localStorage.setItem('auth_token', 'invalid-token');
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Unauthorized'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('handles login successfully', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: 1,
      username: 'newuser',
      email: 'new@example.com',
      is_active: true
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial loading to complete
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    await act(async () => {
      await user.click(screen.getByText('Login'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('token')).toHaveTextContent('test-token');
    expect(screen.getByTestId('user')).toHaveTextContent('newuser');
    expect(localStorage.getItem('auth_token')).toBe('test-token');
  });

  it('handles logout', async () => {
    const user = userEvent.setup();
    
    // Start with authenticated state
    localStorage.setItem('auth_token', 'test-token');
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true
      })
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial auth state to load
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });

    await act(async () => {
      await user.click(screen.getByText('Logout'));
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('starts without loading when no token exists', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(fetch).not.toHaveBeenCalled();
  });

  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    console.error = originalError;
  });

  it('handles failed login attempt gracefully', async () => {
    const user = userEvent.setup();
    
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Login failed'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial loading to complete
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    await act(async () => {
      await user.click(screen.getByText('Login'));
    });

    // Should remain unauthenticated
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('token')).toHaveTextContent('no-token');
    expect(localStorage.getItem('auth_token')).toBeNull();
  });
});