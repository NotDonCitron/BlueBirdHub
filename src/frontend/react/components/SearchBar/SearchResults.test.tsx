import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import SearchResults from './SearchResults';

const mockResults = [
  { id: 'task-1', title: 'Test Task', type: 'task' as const },
  { id: 'ws-1', title: 'Test Workspace', type: 'workspace' as const },
  { id: 'file-1', title: 'Test File', type: 'file' as const },
];

describe('SearchResults', () => {
  const onClose = jest.fn();

  it('renders loading state correctly', () => {
    render(
      <Router>
        <SearchResults results={[]} isLoading={true} onClose={onClose} />
      </Router>
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders "no results" message when there are no results', () => {
    render(
      <Router>
        <SearchResults results={[]} isLoading={false} onClose={onClose} />
      </Router>
    );
    expect(screen.getByText('No results found.')).toBeInTheDocument();
  });

  it('renders and groups results correctly', () => {
    render(
      <Router>
        <SearchResults results={mockResults} isLoading={false} onClose={onClose} />
      </Router>
    );
    
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Workspaces')).toBeInTheDocument();
    expect(screen.getByText('Files')).toBeInTheDocument();
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('Test Workspace')).toBeInTheDocument();
    expect(screen.getByText('Test File')).toBeInTheDocument();
  });
}); 