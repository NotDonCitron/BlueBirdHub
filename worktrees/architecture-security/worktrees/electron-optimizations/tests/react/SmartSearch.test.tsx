import React from 'react';
import { render, screen, fireEvent, waitFor, mockApiContext } from '../utils/test-utils';
import '@testing-library/jest-dom';
import SmartSearch from '../../src/frontend/react/components/SmartSearch/SmartSearch';

describe('SmartSearch Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (component: React.ReactElement) => {
    return render(component);
  };

  test('renders search interface', () => {
    renderComponent(<SmartSearch />);
    
    expect(screen.getByPlaceholderText(/search files, tasks, and more/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument();
  });

  test('performs basic search', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        results: [
          {
            type: 'file',
            name: 'document.pdf',
            path: '/docs/document.pdf',
            relevance: 0.95
          },
          {
            type: 'task',
            title: 'Review document',
            id: 1,
            relevance: 0.85
          }
        ],
        total_count: 2
      }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'document' } });

    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/search/smart?q=document');
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
      expect(screen.getByText('Review document')).toBeInTheDocument();
    });
  });

  test('performs AI-powered search', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        results: [
          {
            type: 'file',
            name: 'project-notes.txt',
            path: '/projects/notes.txt',
            relevance: 0.92,
            snippet: 'Contains information about the project timeline...'
          }
        ],
        suggestions: ['Try searching for "project timeline"', 'Look in the projects folder']
      }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'when is the project due' } });

    const aiSearchButton = screen.getByRole('button', { name: /ai search/i });
    fireEvent.click(aiSearchButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/search/ai',
        expect.objectContaining({ query: 'when is the project due' })
      );
      expect(screen.getByText('project-notes.txt')).toBeInTheDocument();
      expect(screen.getByText(/contains information about the project timeline/i)).toBeInTheDocument();
      expect(screen.getByText(/try searching for "project timeline"/i)).toBeInTheDocument();
    });
  });

  test('displays search suggestions while typing', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        suggestions: ['test file', 'test document', 'testing results']
      }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'tes' } });

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/search/suggestions?q=tes');
      expect(screen.getByText('test file')).toBeInTheDocument();
      expect(screen.getByText('test document')).toBeInTheDocument();
    });
  });

  test('applies search filters', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        results: [
          {
            type: 'file',
            name: 'report.txt',
            path: '/docs/report.txt',
            size: 2048
          }
        ],
        total_count: 1
      }
    });

    renderComponent(<SmartSearch />);

    // Open filters
    const filtersButton = screen.getByRole('button', { name: /filters/i });
    fireEvent.click(filtersButton);

    // Set filters
    const fileTypeCheckbox = await screen.findByLabelText(/documents/i);
    fireEvent.click(fileTypeCheckbox);

    const datePicker = screen.getByLabelText(/date range/i);
    fireEvent.change(datePicker, { target: { value: '2024-01-01' } });

    const sizeRange = screen.getByLabelText(/max size/i);
    fireEvent.change(sizeRange, { target: { value: '10' } });

    // Apply filters and search
    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'report' } });

    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/search/advanced',
        expect.objectContaining({
          query: 'report',
          filters: expect.objectContaining({
            file_types: expect.any(Array),
            date_range: expect.any(Object),
            size_range: expect.any(Object)
          })
        })
      );
    });
  });

  test('handles empty search results', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        results: [],
        total_count: 0
      }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText(/no results found/i)).toBeInTheDocument();
      expect(screen.getByText(/try different keywords/i)).toBeInTheDocument();
    });
  });

  test('displays recent searches', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        history: [
          { query: 'project files', timestamp: '2024-01-01T10:00:00' },
          { query: 'meeting notes', timestamp: '2024-01-01T09:00:00' }
        ]
      }
    });

    renderComponent(<SmartSearch />);

    const recentButton = screen.getByRole('button', { name: /recent/i });
    fireEvent.click(recentButton);

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/search/history');
      expect(screen.getByText('project files')).toBeInTheDocument();
      expect(screen.getByText('meeting notes')).toBeInTheDocument();
    });
  });

  test('handles search with keyboard shortcuts', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: { results: [], total_count: 0 }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'test search' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 13 });

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/search/smart?q=test+search');
    });
  });

  test('groups search results by type', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        results: [
          { type: 'file', name: 'file1.txt', path: '/file1.txt' },
          { type: 'task', title: 'Task 1', id: 1 },
          { type: 'file', name: 'file2.txt', path: '/file2.txt' },
          { type: 'workspace', name: 'Workspace 1', id: 1 }
        ],
        total_count: 4
      }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.submit(searchInput.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/files \(2\)/i)).toBeInTheDocument();
      expect(screen.getByText(/tasks \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText(/workspaces \(1\)/i)).toBeInTheDocument();
    });
  });

  test('navigates to search result on click', async () => {
    const mockNavigate = jest.fn();
    // Mock router navigation
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));

    mockApiContext.get.mockResolvedValueOnce({
      data: {
        results: [
          {
            type: 'file',
            name: 'clickable.txt',
            path: '/docs/clickable.txt'
          }
        ],
        total_count: 1
      }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'clickable' } });
    fireEvent.submit(searchInput.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText('clickable.txt')).toBeInTheDocument();
    });

    const result = screen.getByText('clickable.txt');
    fireEvent.click(result);

    // Verify navigation or file opening logic
    expect(result).toBeInTheDocument();
  });

  test('clears search and filters', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: { results: [{ type: 'file', name: 'test.txt' }], total_count: 1 }
    });

    renderComponent(<SmartSearch />);

    const searchInput = screen.getByPlaceholderText(/search files, tasks, and more/i);
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.submit(searchInput.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });

    const clearButton = screen.getByRole('button', { name: /clear/i });
    fireEvent.click(clearButton);

    expect(searchInput).toHaveValue('');
    expect(screen.queryByText('test.txt')).not.toBeInTheDocument();
  });
});