import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../../src/frontend/react/App';

// Mock the API request
const mockApiRequest = jest.fn();
window.electronAPI = {
  ...window.electronAPI,
  apiRequest: mockApiRequest,
};

describe('App Component', () => {
  beforeEach(() => {
    mockApiRequest.mockClear();
  });

  test('shows loading state initially', () => {
    render(<App />);
    expect(screen.getByText('Initializing OrdnungsHub...')).toBeInTheDocument();
  });

  test('shows app layout when API is connected', async () => {
    mockApiRequest.mockResolvedValue({ status: 'running' });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('OrdnungsHub')).toBeInTheDocument();
    });
  });

  test('handles API connection failure', async () => {
    mockApiRequest.mockRejectedValue(new Error('Connection failed'));
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Connection Lost')).toBeInTheDocument();
    });
  });
});