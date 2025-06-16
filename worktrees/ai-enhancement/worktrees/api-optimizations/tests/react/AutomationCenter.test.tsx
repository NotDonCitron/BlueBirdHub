import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AutomationCenter from '../../src/frontend/react/components/AutomationCenter/AutomationCenter';
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

describe('AutomationCenter Component', () => {
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

  test('renders automation center interface', () => {
    renderWithContext(<AutomationCenter />);
    
    expect(screen.getByText(/automation center/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create automation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /browse templates/i })).toBeInTheDocument();
  });

  test('displays automations when loaded', async () => {
    const mockAutomations = {
      automations: [
        {
          id: 1,
          name: 'File Organizer',
          description: 'Organize downloads folder',
          enabled: true,
          trigger_type: 'schedule',
          schedule: '0 9 * * *',
          last_run: '2024-01-01T09:00:00'
        },
        {
          id: 2,
          name: 'Email Classifier',
          description: 'Classify incoming emails',
          enabled: false,
          trigger_type: 'event',
          event_type: 'new_email'
        }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockAutomations });

    renderWithContext(<AutomationCenter />);

    await waitFor(() => {
      expect(screen.getByText('File Organizer')).toBeInTheDocument();
      expect(screen.getByText('Email Classifier')).toBeInTheDocument();
      expect(screen.getByText('Organize downloads folder')).toBeInTheDocument();
    });
  });

  test('creates new automation', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        id: 3,
        name: 'New Automation',
        description: 'Test automation',
        enabled: true,
        trigger_type: 'manual'
      }
    });

    renderWithContext(<AutomationCenter />);

    const createButton = screen.getByRole('button', { name: /create automation/i });
    fireEvent.click(createButton);

    // Fill automation form
    const nameInput = await screen.findByPlaceholderText(/automation name/i);
    const descriptionInput = screen.getByPlaceholderText(/description/i);
    const triggerSelect = screen.getByLabelText(/trigger type/i);

    fireEvent.change(nameInput, { target: { value: 'New Automation' } });
    fireEvent.change(descriptionInput, { target: { value: 'Test automation' } });
    fireEvent.change(triggerSelect, { target: { value: 'manual' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/automations',
        expect.objectContaining({
          name: 'New Automation',
          description: 'Test automation',
          trigger_type: 'manual'
        })
      );
    });
  });

  test('toggles automation enabled state', async () => {
    const mockAutomations = {
      automations: [{
        id: 1,
        name: 'Test Automation',
        enabled: false
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockAutomations });
    mockApiContext.put.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<AutomationCenter />);

    await waitFor(() => {
      expect(screen.getByText('Test Automation')).toBeInTheDocument();
    });

    const toggleSwitch = screen.getByTestId('toggle-automation-1');
    fireEvent.click(toggleSwitch);

    await waitFor(() => {
      expect(mockApiContext.put).toHaveBeenCalledWith('/api/automations/1/toggle', {});
    });
  });

  test('executes automation manually', async () => {
    const mockAutomations = {
      automations: [{
        id: 1,
        name: 'Manual Automation',
        enabled: true,
        trigger_type: 'manual'
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockAutomations });
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        status: 'success',
        executed_actions: 5,
        duration: 2.5
      }
    });

    renderWithContext(<AutomationCenter />);

    await waitFor(() => {
      expect(screen.getByText('Manual Automation')).toBeInTheDocument();
    });

    const executeButton = screen.getByTestId('execute-automation-1');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith('/api/automations/1/execute', {});
      expect(screen.getByText(/executed successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/5 actions/i)).toBeInTheDocument();
    });
  });

  test('displays automation templates', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        templates: [
          {
            id: 'file-cleanup',
            name: 'File Cleanup',
            description: 'Clean up old temporary files',
            category: 'maintenance'
          },
          {
            id: 'backup-automation',
            name: 'Backup Automation',
            description: 'Regular backup of important files',
            category: 'backup'
          }
        ]
      }
    });

    renderWithContext(<AutomationCenter />);

    const templatesButton = screen.getByRole('button', { name: /browse templates/i });
    fireEvent.click(templatesButton);

    await waitFor(() => {
      expect(screen.getByText('File Cleanup')).toBeInTheDocument();
      expect(screen.getByText('Backup Automation')).toBeInTheDocument();
    });
  });

  test('creates automation from template', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        templates: [{
          id: 'file-cleanup',
          name: 'File Cleanup Template',
          actions: [{ type: 'scan', target: '/tmp' }]
        }]
      }
    });

    mockApiContext.post.mockResolvedValueOnce({
      data: { success: true, automation_id: 4 }
    });

    renderWithContext(<AutomationCenter />);

    const templatesButton = screen.getByRole('button', { name: /browse templates/i });
    fireEvent.click(templatesButton);

    await waitFor(() => {
      expect(screen.getByText('File Cleanup Template')).toBeInTheDocument();
    });

    const useTemplateButton = screen.getByTestId('use-template-file-cleanup');
    fireEvent.click(useTemplateButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/automations/from-template',
        expect.objectContaining({ template_id: 'file-cleanup' })
      );
    });
  });

  test('displays automation execution logs', async () => {
    const mockAutomations = {
      automations: [{
        id: 1,
        name: 'Logged Automation',
        enabled: true
      }]
    };

    const mockLogs = {
      logs: [
        {
          id: 1,
          automation_id: 1,
          timestamp: '2024-01-01T10:00:00',
          status: 'success',
          message: 'Automation completed successfully',
          actions_executed: 3
        },
        {
          id: 2,
          automation_id: 1,
          timestamp: '2024-01-01T09:00:00',
          status: 'error',
          message: 'Failed to process file',
          error: 'Permission denied'
        }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockAutomations });

    renderWithContext(<AutomationCenter />);

    await waitFor(() => {
      expect(screen.getByText('Logged Automation')).toBeInTheDocument();
    });

    const viewLogsButton = screen.getByTestId('view-logs-1');
    fireEvent.click(viewLogsButton);

    mockApiContext.get.mockResolvedValueOnce({ data: mockLogs });

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/automations/1/logs');
      expect(screen.getByText(/completed successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
  });

  test('performs dry run of automation', async () => {
    const mockAutomations = {
      automations: [{
        id: 1,
        name: 'Test Automation',
        enabled: true
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockAutomations });
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        simulated_actions: [
          { action: 'move_file', target: 'file1.txt', result: 'would be moved' },
          { action: 'delete_file', target: 'temp.txt', result: 'would be deleted' }
        ],
        would_affect: 2
      }
    });

    renderWithContext(<AutomationCenter />);

    await waitFor(() => {
      expect(screen.getByText('Test Automation')).toBeInTheDocument();
    });

    const dryRunButton = screen.getByTestId('dry-run-1');
    fireEvent.click(dryRunButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith('/api/automations/1/dry-run', {});
      expect(screen.getByText(/would be moved/i)).toBeInTheDocument();
      expect(screen.getByText(/would affect 2/i)).toBeInTheDocument();
    });
  });

  test('displays AI automation suggestions', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        suggestions: [
          {
            name: 'Smart File Organization',
            description: 'AI suggests organizing your documents folder',
            confidence: 0.89,
            trigger: 'weekly',
            actions: ['scan_documents', 'categorize_files', 'move_to_folders']
          }
        ]
      }
    });

    renderWithContext(<AutomationCenter />);

    const suggestionsButton = screen.getByRole('button', { name: /ai suggestions/i });
    fireEvent.click(suggestionsButton);

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/automations/suggestions');
      expect(screen.getByText('Smart File Organization')).toBeInTheDocument();
      expect(screen.getByText(/89%/i)).toBeInTheDocument();
    });
  });

  test('handles automation deletion with confirmation', async () => {
    const mockAutomations = {
      automations: [{
        id: 1,
        name: 'Delete Me',
        enabled: false
      }]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockAutomations });
    mockApiContext.delete.mockResolvedValueOnce({ data: { success: true } });

    renderWithContext(<AutomationCenter />);

    await waitFor(() => {
      expect(screen.getByText('Delete Me')).toBeInTheDocument();
    });

    const deleteButton = screen.getByTestId('delete-automation-1');
    fireEvent.click(deleteButton);

    const confirmButton = await screen.findByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockApiContext.delete).toHaveBeenCalledWith('/api/automations/1');
    });
  });
});