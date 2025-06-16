import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AIContentAssignment from '../../src/frontend/react/components/AIContentAssignment/AIContentAssignment';
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

describe('AIContentAssignment Component', () => {
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

  test('renders AI content assignment interface', () => {
    renderWithContext(<AIContentAssignment />);
    
    expect(screen.getByText(/ai content assignment/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze content/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /auto-organize/i })).toBeInTheDocument();
  });

  test('analyzes folder content with AI', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        analysis: {
          total_files: 50,
          categories: {
            'Documents': 20,
            'Images': 15,
            'Code': 10,
            'Other': 5
          },
          suggestions: [
            {
              action: 'move',
              files: ['doc1.pdf', 'doc2.docx'],
              destination: '/Documents/Work',
              reason: 'Work-related documents'
            }
          ]
        }
      }
    });

    renderWithContext(<AIContentAssignment />);

    const folderInput = screen.getByPlaceholderText(/folder path/i);
    fireEvent.change(folderInput, { target: { value: '/downloads' } });

    const analyzeButton = screen.getByRole('button', { name: /analyze content/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/analyze-folder',
        expect.objectContaining({ path: '/downloads' })
      );
      expect(screen.getByText(/50 files/i)).toBeInTheDocument();
      expect(screen.getByText(/documents: 20/i)).toBeInTheDocument();
      expect(screen.getByText(/work-related documents/i)).toBeInTheDocument();
    });
  });

  test('displays file categorization preview', async () => {
    const mockAnalysis = {
      analysis: {
        total_files: 10,
        categorized_files: [
          {
            file: 'report.pdf',
            current_path: '/downloads/report.pdf',
            suggested_category: 'Work Documents',
            suggested_path: '/Documents/Work/report.pdf',
            confidence: 0.92
          },
          {
            file: 'vacation.jpg',
            current_path: '/downloads/vacation.jpg',
            suggested_category: 'Personal Photos',
            suggested_path: '/Pictures/Personal/vacation.jpg',
            confidence: 0.88
          }
        ]
      }
    };

    mockApiContext.post.mockResolvedValueOnce({ data: mockAnalysis });

    renderWithContext(<AIContentAssignment />);

    const analyzeButton = screen.getByRole('button', { name: /analyze content/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('report.pdf')).toBeInTheDocument();
      expect(screen.getByText('Work Documents')).toBeInTheDocument();
      expect(screen.getByText(/92%/)).toBeInTheDocument();
      expect(screen.getByText('vacation.jpg')).toBeInTheDocument();
      expect(screen.getByText('Personal Photos')).toBeInTheDocument();
    });
  });

  test('applies AI organization suggestions', async () => {
    // First mock the analysis
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        analysis: {
          suggestions: [
            { action: 'move', files: ['file1.txt'], destination: '/Documents' }
          ]
        }
      }
    });

    // Then mock the apply action
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        success: true,
        moved_files: 1,
        errors: []
      }
    });

    renderWithContext(<AIContentAssignment />);

    // Analyze first
    const analyzeButton = screen.getByRole('button', { name: /analyze content/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('file1.txt')).toBeInTheDocument();
    });

    // Apply suggestions
    const applyButton = screen.getByRole('button', { name: /apply suggestions/i });
    fireEvent.click(applyButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/apply-organization',
        expect.objectContaining({ suggestions: expect.any(Array) })
      );
      expect(screen.getByText(/moved 1 file/i)).toBeInTheDocument();
    });
  });

  test('handles selective file organization', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        analysis: {
          categorized_files: [
            { file: 'file1.txt', suggested_path: '/Documents/file1.txt' },
            { file: 'file2.txt', suggested_path: '/Documents/file2.txt' }
          ]
        }
      }
    });

    renderWithContext(<AIContentAssignment />);

    const analyzeButton = screen.getByRole('button', { name: /analyze content/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('file1.txt')).toBeInTheDocument();
      expect(screen.getByText('file2.txt')).toBeInTheDocument();
    });

    // Deselect one file
    const checkbox1 = screen.getByTestId('select-file-file1.txt');
    fireEvent.click(checkbox1);

    // Apply only selected files
    mockApiContext.post.mockResolvedValueOnce({
      data: { success: true, moved_files: 1 }
    });

    const applySelectedButton = screen.getByRole('button', { name: /apply selected/i });
    fireEvent.click(applySelectedButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenLastCalledWith(
        '/api/ai/apply-organization',
        expect.objectContaining({
          suggestions: expect.arrayContaining([
            expect.objectContaining({ file: 'file2.txt' })
          ])
        })
      );
    });
  });

  test('creates custom organization rules', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        rule_id: 1,
        message: 'Rule created successfully'
      }
    });

    renderWithContext(<AIContentAssignment />);

    const rulesButton = screen.getByRole('button', { name: /create rule/i });
    fireEvent.click(rulesButton);

    // Fill rule form
    const patternInput = await screen.findByPlaceholderText(/file pattern/i);
    const categoryInput = screen.getByPlaceholderText(/category/i);
    const destinationInput = screen.getByPlaceholderText(/destination folder/i);

    fireEvent.change(patternInput, { target: { value: '*.pdf' } });
    fireEvent.change(categoryInput, { target: { value: 'Documents' } });
    fireEvent.change(destinationInput, { target: { value: '/Documents/PDFs' } });

    const saveRuleButton = screen.getByRole('button', { name: /save rule/i });
    fireEvent.click(saveRuleButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/organization-rules',
        expect.objectContaining({
          pattern: '*.pdf',
          category: 'Documents',
          destination: '/Documents/PDFs'
        })
      );
      expect(screen.getByText(/rule created successfully/i)).toBeInTheDocument();
    });
  });

  test('displays organization history', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        history: [
          {
            id: 1,
            timestamp: '2024-01-01T10:00:00',
            action: 'auto-organize',
            files_moved: 25,
            source: '/downloads',
            status: 'completed'
          },
          {
            id: 2,
            timestamp: '2024-01-01T09:00:00',
            action: 'manual-organize',
            files_moved: 10,
            source: '/desktop',
            status: 'completed'
          }
        ]
      }
    });

    renderWithContext(<AIContentAssignment />);

    const historyButton = screen.getByRole('button', { name: /view history/i });
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/ai/organization-history');
      expect(screen.getByText(/25 files moved/i)).toBeInTheDocument();
      expect(screen.getByText(/from \/downloads/i)).toBeInTheDocument();
    });
  });

  test('handles undo organization action', async () => {
    // First show history
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        history: [{
          id: 1,
          timestamp: '2024-01-01T10:00:00',
          files_moved: 5,
          can_undo: true
        }]
      }
    });

    renderWithContext(<AIContentAssignment />);

    const historyButton = screen.getByRole('button', { name: /view history/i });
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(screen.getByText(/5 files moved/i)).toBeInTheDocument();
    });

    // Undo the action
    mockApiContext.post.mockResolvedValueOnce({
      data: { success: true, files_restored: 5 }
    });

    const undoButton = screen.getByRole('button', { name: /undo/i });
    fireEvent.click(undoButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/undo-organization',
        expect.objectContaining({ history_id: 1 })
      );
      expect(screen.getByText(/5 files restored/i)).toBeInTheDocument();
    });
  });

  test('trains AI with user feedback', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        analysis: {
          categorized_files: [{
            file: 'document.txt',
            suggested_category: 'Work',
            file_id: 'doc123'
          }]
        }
      }
    });

    renderWithContext(<AIContentAssignment />);

    const analyzeButton = screen.getByRole('button', { name: /analyze content/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('document.txt')).toBeInTheDocument();
    });

    // Provide feedback
    const wrongCategoryButton = screen.getByTestId('wrong-category-doc123');
    fireEvent.click(wrongCategoryButton);

    const correctCategorySelect = await screen.findByLabelText(/correct category/i);
    fireEvent.change(correctCategorySelect, { target: { value: 'Personal' } });

    mockApiContext.post.mockResolvedValueOnce({
      data: { success: true, message: 'Feedback recorded' }
    });

    const submitFeedbackButton = screen.getByRole('button', { name: /submit feedback/i });
    fireEvent.click(submitFeedbackButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/feedback',
        expect.objectContaining({
          file_id: 'doc123',
          original_category: 'Work',
          correct_category: 'Personal'
        })
      );
    });
  });

  test('displays confidence threshold settings', async () => {
    renderWithContext(<AIContentAssignment />);

    const settingsButton = screen.getByRole('button', { name: /settings/i });
    fireEvent.click(settingsButton);

    const thresholdSlider = await screen.findByLabelText(/confidence threshold/i);
    expect(thresholdSlider).toHaveValue('80'); // Default value

    fireEvent.change(thresholdSlider, { target: { value: '90' } });

    expect(screen.getByText(/only organize files with 90% confidence/i)).toBeInTheDocument();
  });

  test('handles batch folder analysis', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        batch_id: 'batch123',
        folders_queued: 3,
        estimated_time: 120
      }
    });

    renderWithContext(<AIContentAssignment />);

    const batchButton = screen.getByRole('button', { name: /batch analyze/i });
    fireEvent.click(batchButton);

    // Add multiple folders
    const folderInput1 = await screen.findByPlaceholderText(/folder 1/i);
    const folderInput2 = screen.getByPlaceholderText(/folder 2/i);
    const folderInput3 = screen.getByPlaceholderText(/folder 3/i);

    fireEvent.change(folderInput1, { target: { value: '/downloads' } });
    fireEvent.change(folderInput2, { target: { value: '/desktop' } });
    fireEvent.change(folderInput3, { target: { value: '/documents' } });

    const startBatchButton = screen.getByRole('button', { name: /start batch/i });
    fireEvent.click(startBatchButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/batch-analyze',
        expect.objectContaining({
          folders: ['/downloads', '/desktop', '/documents']
        })
      );
      expect(screen.getByText(/3 folders queued/i)).toBeInTheDocument();
      expect(screen.getByText(/estimated time: 2 minutes/i)).toBeInTheDocument();
    });
  });
});