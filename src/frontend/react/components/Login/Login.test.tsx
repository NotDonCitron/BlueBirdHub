import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from './Login';

// Mock fetch for browser requests
global.fetch = jest.fn();

describe('Login Component', () => {
  const mockOnLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  it('renders login form by default', () => {
    render(<Login onLogin={mockOnLogin} />);
    
    expect(screen.getByText('OrdnungsHub')).toBeInTheDocument();
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
  });

  it('toggles to register mode', async () => {
    const user = userEvent.setup();
    render(<Login onLogin={mockOnLogin} />);
    
    const toggleButton = screen.getByRole('button', { name: 'Sign Up' });
    await user.click(toggleButton);
    
    expect(screen.getByText('Create a new account')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
    expect(screen.getByText('Already have an account?')).toBeInTheDocument();
  });

  it('submits login form with correct data', async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'test-token', token_type: 'bearer' })
    });

    render(<Login onLogin={mockOnLogin} />);
    
    await user.type(screen.getByLabelText('Username'), 'testuser');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: 'testuser',
          password: 'password123',
          grant_type: 'password'
        })
      });
    });

    expect(mockOnLogin).toHaveBeenCalledWith('test-token');
  });

  it('submits register form with correct data', async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'test-token', token_type: 'bearer' })
    });

    render(<Login onLogin={mockOnLogin} />);
    
    // Switch to register mode
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));
    
    await user.type(screen.getByLabelText('Username'), 'newuser');
    await user.type(screen.getByLabelText('Email'), 'new@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'newuser',
          email: 'new@example.com',
          password: 'password123'
        })
      });
    });

    expect(mockOnLogin).toHaveBeenCalledWith('test-token');
  });

  it('displays error message on failed login', async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' })
    });

    render(<Login onLogin={mockOnLogin} />);
    
    await user.type(screen.getByLabelText('Username'), 'wronguser');
    await user.type(screen.getByLabelText('Password'), 'wrongpass');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    expect(mockOnLogin).not.toHaveBeenCalled();
  });

  it('uses electronAPI when available', async () => {
    const user = userEvent.setup();
    const mockApiRequest = jest.fn().mockResolvedValue({
      access_token: 'electron-token',
      token_type: 'bearer'
    });

    (window as any).electronAPI = { apiRequest: mockApiRequest };

    render(<Login onLogin={mockOnLogin} />);
    
    await user.type(screen.getByLabelText('Username'), 'testuser');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/auth/login',
        'POST',
        new URLSearchParams({
          username: 'testuser',
          password: 'password123',
          grant_type: 'password'
        }),
        { 'Content-Type': 'application/x-www-form-urlencoded' }
      );
    });

    expect(mockOnLogin).toHaveBeenCalledWith('electron-token');
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    let resolvePromise: (value: any) => void;
    const delayedPromise = new Promise(resolve => {
      resolvePromise = resolve;
    });

    (global.fetch as jest.Mock).mockReturnValue(delayedPromise);

    render(<Login onLogin={mockOnLogin} />);
    
    await user.type(screen.getByLabelText('Username'), 'testuser');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Should show loading state
    expect(screen.getByRole('button', { name: 'Loading...' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Loading...' })).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      ok: true,
      json: async () => ({ access_token: 'test-token', token_type: 'bearer' })
    });

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    });
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    render(<Login onLogin={mockOnLogin} />);
    
    // Try to submit without filling fields
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    // Form should not submit (browser validation will prevent it)
    expect(fetch).not.toHaveBeenCalled();
    expect(mockOnLogin).not.toHaveBeenCalled();
  });

  it('clears error when switching modes', async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Login failed' })
    });

    render(<Login onLogin={mockOnLogin} />);
    
    // Cause an error
    await user.type(screen.getByLabelText('Username'), 'wronguser');
    await user.type(screen.getByLabelText('Password'), 'wrongpass');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument();
    });

    // Switch to register mode
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    // Error should be cleared
    expect(screen.queryByText('Login failed')).not.toBeInTheDocument();
  });

  it('handles network errors gracefully', async () => {
    const user = userEvent.setup();
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<Login onLogin={mockOnLogin} />);
    
    await user.type(screen.getByLabelText('Username'), 'testuser');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    expect(mockOnLogin).not.toHaveBeenCalled();
  });
});