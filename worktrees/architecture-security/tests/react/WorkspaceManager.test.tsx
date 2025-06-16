import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WorkspaceManager from '../../src/frontend/react/components/WorkspaceManager/WorkspaceManager';
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

describe('WorkspaceManager Component', () => {
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

  test('renders workspace manager interface', () => {
    renderWithContext(<WorkspaceManager />);
    
    expect(screen.getByText(/workspace manager/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create workspace/i })).toBeInTheDocument();
  });

  test('displays workspaces when loaded', async () => {
    const mockWorkspaces = {
      workspaces: [
        {
          id: 1,
          name: 'Development',
          description: 'Dev environment',
          active: true,
          settings: { theme: 'dark' }
        },
        {
          id: 2,
          name: 'Personal',
          description: 'Personal projects',
          active: false,
          settings: { theme: 'light' }
        }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Development')).toBeInTheDocument();
      expect(screen.getByText('Personal')).toBeInTheDocument();
      expect(screen.getByText('Dev environment')).toBeInTheDocument();
    });
  });

  test('creates new workspace', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        id: 3,
        name: 'New Workspace',
        description: 'Test workspace',
        active: false
      }
    });

    renderWithContext(<WorkspaceManager />);

    const createButton = screen.getByRole('button', { name: /create workspace/i });
    fireEvent.click(createButton);

    const nameInput = await screen.findByPlaceholderText(/workspace name/i);
    const descriptionInput = screen.getByPlaceholderText(/workspace description/i);

    fireEvent.change(nameInput, { target: { value: 'New Workspace' } });
    fireEvent.change(descriptionInput, { target: { value: 'Test workspace' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/workspaces',
        expect.objectContaining({
          name: 'New Workspace',
          description: 'Test workspace'
        })
      );
    });
  });

  test('switches active workspace', async () => {
    const mockWorkspaces = {
      workspaces: [
        { id: 1, name: 'Workspace 1', active: true },
        { id: 2, name: 'Workspace 2', active: false }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });
    mockApiContext.put.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Workspace 2')).toBeInTheDocument();
    });

    const activateButton = screen.getByTestId('activate-workspace-2');
    fireEvent.click(activateButton);

    await waitFor(() => {
      expect(mockApiContext.put).toHaveBeenCalledWith(
        '/api/workspaces/2/activate',
        {}
      );
    });
  });

  test('edits workspace settings', async () => {
    const mockWorkspaces = {
      workspaces: [{
        id: 1,
        name: 'Test Workspace',
        description: 'Original description',
        active: true,
        settings: { theme: 'light' }
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });
    mockApiContext.put.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Test Workspace')).toBeInTheDocument();
    });

    const editButton = screen.getByTestId('edit-workspace-1');
    fireEvent.click(editButton);

    const descriptionInput = await screen.findByDisplayValue('Original description');
    fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });

    const themeSelect = screen.getByLabelText(/theme/i);
    fireEvent.change(themeSelect, { target: { value: 'dark' } });

    const updateButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(mockApiContext.put).toHaveBeenCalledWith(
        '/api/workspaces/1',
        expect.objectContaining({
          description: 'Updated description',
          settings: expect.objectContaining({ theme: 'dark' })
        })
      );
    });
  });

  test('deletes workspace with confirmation', async () => {
    const mockWorkspaces = {
      workspaces: [
        { id: 1, name: 'Keep this', active: true },
        { id: 2, name: 'Delete this', active: false }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });
    mockApiContext.delete.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Delete this')).toBeInTheDocument();
    });

    const deleteButton = screen.getByTestId('delete-workspace-2');
    fireEvent.click(deleteButton);

    const confirmButton = await screen.findByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockApiContext.delete).toHaveBeenCalledWith('/api/workspaces/2');
    });
  });

  test('prevents deletion of active workspace', async () => {
    const mockWorkspaces = {
      workspaces: [{ id: 1, name: 'Active Workspace', active: true }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Active Workspace')).toBeInTheDocument();
    });

    const deleteButton = screen.getByTestId('delete-workspace-1');
    expect(deleteButton).toBeDisabled();
  });

  test('exports workspace configuration', async () => {
    const mockWorkspaces = {
      workspaces: [{
        id: 1,
        name: 'Export Me',
        settings: { theme: 'dark', layout: 'grid' }
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        workspace: mockWorkspaces.workspaces[0],
        export_date: '2024-01-01'
      }
    });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Export Me')).toBeInTheDocument();
    });

    const exportButton = screen.getByTestId('export-workspace-1');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/workspaces/1/export');
    });
  });

  test('imports workspace configuration', async () => {
    const importData = {
      name: 'Imported Workspace',
      settings: { theme: 'dark' }
    };

    mockApiContext.post.mockResolvedValueOnce({
      data: { success: true, workspace_id: 3 }
    });

    renderWithContext(<WorkspaceManager />);

    const importButton = screen.getByRole('button', { name: /import workspace/i });
    fireEvent.click(importButton);

    const fileInput = await screen.findByTestId('import-file-input');
    const file = new File([JSON.stringify(importData)], 'workspace.json', {
      type: 'application/json'
    });
    
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/workspaces/import',
        expect.any(FormData)
      );
    });
  });

  test('displays workspace statistics', async () => {
    const mockWorkspaces = {
      workspaces: [{
        id: 1,
        name: 'Stats Workspace',
        active: true,
        stats: {
          files_count: 150,
          tasks_count: 25,
          last_accessed: '2024-01-01T10:00:00'
        }
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockWorkspaces });

    renderWithContext(<WorkspaceManager />);

    await waitFor(() => {
      expect(screen.getByText('Stats Workspace')).toBeInTheDocument();
      expect(screen.getByText(/150 files/i)).toBeInTheDocument();
      expect(screen.getByText(/25 tasks/i)).toBeInTheDocument();
    });
  });
});