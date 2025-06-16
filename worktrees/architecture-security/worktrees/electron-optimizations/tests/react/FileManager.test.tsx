import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileManager from '../../src/frontend/react/components/FileManager/FileManager';
import { ApiContext } from '../../src/frontend/react/contexts/ApiContext';

// Mock API context
const mockApiContext = {
  apiUrl: 'http://localhost:8001',
  isConnected: true,
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
};

describe('FileManager Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithContext = (component: React.ReactElement) => {
    return render(
      <ApiContext.Provider value={mockApiContext}>
        {component}
      </ApiContext.Provider>
    );
  };

  test('renders file manager interface', () => {
    renderWithContext(<FileManager />);
    
    expect(screen.getByText(/file manager/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /new folder/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
  });

  test('displays file tree when loaded', async () => {
    const mockFileTree = {
      name: 'root',
      type: 'directory',
      children: [
        { name: 'documents', type: 'directory', children: [] },
        { name: 'test.txt', type: 'file', size: 1024 }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockFileTree });

    renderWithContext(<FileManager />);

    await waitFor(() => {
      expect(screen.getByText('documents')).toBeInTheDocument();
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });
  });

  test('handles folder creation', async () => {
    mockApiContext.post.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<FileManager />);

    const newFolderButton = screen.getByRole('button', { name: /new folder/i });
    fireEvent.click(newFolderButton);

    const folderNameInput = await screen.findByPlaceholderText(/folder name/i);
    fireEvent.change(folderNameInput, { target: { value: 'New Folder' } });

    const createButton = screen.getByRole('button', { name: /create/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/files/folder',
        expect.objectContaining({ name: 'New Folder' })
      );
    });
  });

  test('handles file deletion with confirmation', async () => {
    const mockFileTree = {
      name: 'root',
      type: 'directory',
      children: [
        { name: 'test.txt', type: 'file', size: 1024, path: '/test.txt' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockFileTree });
    mockApiContext.delete.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<FileManager />);

    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument();
    });

    // Find and click delete button
    const deleteButton = screen.getByTestId('delete-file-/test.txt');
    fireEvent.click(deleteButton);

    // Confirm deletion
    const confirmButton = await screen.findByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockApiContext.delete).toHaveBeenCalledWith('/api/files/delete?path=/test.txt');
    });
  });

  test('handles file search', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        results: [
          { name: 'search-result.txt', path: '/docs/search-result.txt' }
        ]
      }
    });

    renderWithContext(<FileManager />);

    const searchInput = screen.getByPlaceholderText(/search files/i);
    fireEvent.change(searchInput, { target: { value: 'search' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 13 });

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/files/search?query=search');
      expect(screen.getByText('search-result.txt')).toBeInTheDocument();
    });
  });

  test('handles file upload', async () => {
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    mockApiContext.post.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<FileManager />);

    const uploadInput = screen.getByTestId('file-upload-input');
    fireEvent.change(uploadInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/files/upload',
        expect.any(FormData)
      );
    });
  });

  test('displays error message on API failure', async () => {
    mockApiContext.get.mockRejectedValueOnce(new Error('Network error'));

    renderWithContext(<FileManager />);

    await waitFor(() => {
      expect(screen.getByText(/error loading files/i)).toBeInTheDocument();
    });
  });

  test('handles file/folder renaming', async () => {
    const mockFileTree = {
      name: 'root',
      type: 'directory',
      children: [
        { name: 'old-name.txt', type: 'file', path: '/old-name.txt' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockFileTree });
    mockApiContext.post.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<FileManager />);

    await waitFor(() => {
      expect(screen.getByText('old-name.txt')).toBeInTheDocument();
    });

    const renameButton = screen.getByTestId('rename-file-/old-name.txt');
    fireEvent.click(renameButton);

    const renameInput = await screen.findByDisplayValue('old-name.txt');
    fireEvent.change(renameInput, { target: { value: 'new-name.txt' } });
    fireEvent.keyPress(renameInput, { key: 'Enter', code: 13 });

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/files/rename',
        expect.objectContaining({
          oldPath: '/old-name.txt',
          newName: 'new-name.txt'
        })
      );
    });
  });

  test('handles drag and drop for file moving', async () => {
    const mockFileTree = {
      name: 'root',
      type: 'directory',
      children: [
        { name: 'folder', type: 'directory', path: '/folder', children: [] },
        { name: 'file.txt', type: 'file', path: '/file.txt' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockFileTree });
    mockApiContext.post.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<FileManager />);

    await waitFor(() => {
      expect(screen.getByText('file.txt')).toBeInTheDocument();
      expect(screen.getByText('folder')).toBeInTheDocument();
    });

    const file = screen.getByText('file.txt');
    const folder = screen.getByText('folder');

    // Simulate drag and drop
    fireEvent.dragStart(file);
    fireEvent.dragOver(folder);
    fireEvent.drop(folder);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/files/move',
        expect.objectContaining({
          source: '/file.txt',
          destination: '/folder/file.txt'
        })
      );
    });
  });
});