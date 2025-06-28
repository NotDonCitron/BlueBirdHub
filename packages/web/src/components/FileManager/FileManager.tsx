import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './FileManager.css';

interface FileOperation {
  type: 'move' | 'copy' | 'delete' | 'rename';
  source: string;
  destination?: string;
}

interface FileItem {
  id: string;
  name: string;
  type: string;
  size: string;
  modified: string;
  tags: string[];
  category: string;
  priority: string;
  workspace_id?: number;
  workspace_name?: string;
  folder?: string;
  thumbnail?: string;
}

interface FileFilter {
  search: string;
  type: string;
  category: string;
  workspace: string;
  tags: string[];
  dateRange: {
    start: string;
    end: string;
  };
  sizeRange: {
    min: number;
    max: number;
  };
}

interface StorageStats {
  total_files: number;
  total_size_gb: number;
  category_stats: Record<string, { count: number; size: number }>;
  insights: Array<{
    type: string;
    message: string;
    action: string;
  }>;
  large_files: Array<{
    path: string;
    size_mb: number;
    category: string;
  }>;
}

interface QuickAction {
  action: string;
  title: string;
  description: string;
  priority: string;
  estimated_savings_mb?: number;
}

const FileManager: React.FC = () => {
  const { makeApiRequest } = useApi();
  const [activeTab, setActiveTab] = useState<'organize' | 'storage' | 'operations' | 'browser'>('browser');

  // Helper function to categorize files based on extension
  const getFileCategory = (extension: string): string => {
    const categories: Record<string, string> = {
      // Documents
      'pdf': 'documents',
      'doc': 'documents', 
      'docx': 'documents',
      'txt': 'documents',
      'odt': 'documents',
      'rtf': 'documents',
      
      // Spreadsheets
      'xls': 'business',
      'xlsx': 'business', 
      'csv': 'business',
      'ods': 'business',
      
      // Presentations
      'ppt': 'marketing',
      'pptx': 'marketing',
      'odp': 'marketing',
      
      // Images
      'jpg': 'design',
      'jpeg': 'design',
      'png': 'design',
      'gif': 'design',
      'bmp': 'design',
      'svg': 'design',
      'webp': 'design',
      
      // Videos
      'mp4': 'media',
      'avi': 'media',
      'mkv': 'media',
      'mov': 'media',
      
      // Audio
      'mp3': 'media',
      'wav': 'media',
      'flac': 'media',
      
      // Code
      'js': 'development',
      'ts': 'development',
      'py': 'development',
      'java': 'development',
      'cpp': 'development',
      'html': 'development',
      'css': 'development',
      
      // Archives
      'zip': 'archives',
      'rar': 'archives',
      '7z': 'archives',
      'tar': 'archives'
    };
    
    return categories[extension] || 'general';
  };
  
  // Organization State
  const [sourceDirectory, setSourceDirectory] = useState('');
  const [organizeMode, setOrganizeMode] = useState<'copy' | 'move'>('copy');
  const [organizing, setOrganizing] = useState(false);
  const [organizeResult, setOrganizeResult] = useState<any>(null);
  
  // Storage Analysis State
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [analyzingStorage, setAnalyzingStorage] = useState(false);
  const [quickActions, setQuickActions] = useState<QuickAction[]>([]);
  
  // File Operations State
  const [operations, setOperations] = useState<FileOperation[]>([]);
  const [newOperation, setNewOperation] = useState<FileOperation>({
    type: 'copy',
    source: ''
  });
  const [operationResults, setOperationResults] = useState<any>(null);
  
  // Deduplication State
  const [duplicateResults, setDuplicateResults] = useState<any>(null);
  const [deduplicating, setDeduplicating] = useState(false);

  // Drag & Drop State
  const [isDragOver, setIsDragOver] = useState(false);
  const [draggedFiles, setDraggedFiles] = useState<string[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(1); // Default to workspace 1
  const dropZoneRef = useRef<HTMLDivElement>(null);
  
  // Upload Progress State
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([]);

  // File Browser State
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'name' | 'modified' | 'size' | 'type' | 'category' | 'workspace'>('modified');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [groupBy, setGroupBy] = useState<'none' | 'category' | 'workspace' | 'type'>('none');
  const [loading, setLoading] = useState(false);
  
  // Advanced Filters State
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FileFilter>({
    search: '',
    type: '',
    category: '',
    workspace: '',
    tags: [],
    dateRange: { start: '', end: '' },
    sizeRange: { min: 0, max: 0 }
  });
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  
  // Preview State
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewContent, setPreviewContent] = useState<string>('');
  const [editingTags, setEditingTags] = useState(false);
  const [newTagInput, setNewTagInput] = useState('');

  // File Browser Functions
  const loadFiles = useCallback(async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      if (filters.search) queryParams.append('q', filters.search);
      if (filters.category) queryParams.append('category', filters.category);
      if (filters.workspace) queryParams.append('workspace', filters.workspace);
      if (filters.tags.length > 0) queryParams.append('tags', filters.tags.join(','));
      
      const response = await makeApiRequest(`/search/files?user_id=1&${queryParams.toString()}`);
      if (response.success) {
        // Transform backend data to match frontend FileItem interface
        const transformedFiles: FileItem[] = response.results.map((file: any) => ({
          id: file.id.toString(),
          name: file.file_name,
          type: file.file_extension || 'unknown',
          size: formatFileSize(file.file_size || 0),
          modified: formatDate(file.indexed_at),
          tags: file.ai_tags ? file.ai_tags.split(',').map((tag: string) => tag.trim()) : [],
          category: file.user_category || file.ai_category || 'uncategorized',
          priority: 'medium', // Default priority
          workspace_id: file.workspace_id,
          workspace_name: file.workspace_id ? `Workspace ${file.workspace_id}` : undefined,
          folder: file.file_path,
          thumbnail: undefined // Could generate thumbnails later
        }));
        
        const sortedFiles = sortFiles(transformedFiles, sortBy, sortOrder);
        setFiles(sortedFiles);
      }
    } catch (error) {
      console.error('Failed to load files:', error);
    }
    setLoading(false);
  }, [filters, sortBy, sortOrder, makeApiRequest]);

  // Helper functions
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  useEffect(() => {
    loadQuickActions();
    loadFiles();
    loadFilterOptions();
  }, [loadFiles]);

  // Drag & Drop Handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only set drag over to false if leaving the drop zone entirely
    if (!dropZoneRef.current?.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    
    if (files.length > 0) {
      // Show loading state
      setLoading(true);
      
      try {
        // Initialize upload progress
        const fileNames = files.map(f => f.name);
        setUploadingFiles(fileNames);
        const initialProgress: {[key: string]: number} = {};
        fileNames.forEach(name => initialProgress[name] = 0);
        setUploadProgress(initialProgress);
        
        // Upload files to backend with progress tracking
        const uploadPromises = files.map(async (file) => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('user_id', '1'); // TODO: Get actual user ID from context
          
          // Add workspace ID if on organize tab
          if (activeTab === 'organize' && selectedWorkspace) {
            formData.append('workspace_id', selectedWorkspace.toString());
          }
          
          // Add default category based on file type
          const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
          const category = getFileCategory(fileExt);
          if (category) {
            formData.append('user_category', category);
          }
          
          // Create XMLHttpRequest for progress tracking
          return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
              if (e.lengthComputable) {
                const progress = Math.round((e.loaded / e.total) * 100);
                setUploadProgress(prev => ({
                  ...prev,
                  [file.name]: progress
                }));
              }
            });
            
            xhr.addEventListener('load', () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                try {
                  const response = JSON.parse(xhr.responseText);
                  resolve(response);
                } catch (error) {
                  reject(new Error('Failed to parse response'));
                }
              } else {
                try {
                  const error = JSON.parse(xhr.responseText);
                  reject(new Error(error.detail || 'Upload failed'));
                } catch {
                  reject(new Error('Upload failed'));
                }
              }
            });
            
            xhr.addEventListener('error', () => {
              reject(new Error('Network error'));
            });
            
            xhr.open('POST', 'http://localhost:8000/files/upload');
            xhr.send(formData);
          });
        });
        
        const results = await Promise.allSettled(uploadPromises);
        
        // Count successful uploads
        const successful = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;
        
        // Update dropped files list
        const uploadedFiles = results
          .filter(r => r.status === 'fulfilled')
          .map((r: any) => r.value.file.filename);
        setDraggedFiles(uploadedFiles);
        
        // Refresh file list
        await loadFiles();
        
        // Show result message
        if (failed === 0) {
          alert(`Successfully uploaded ${successful} file(s)!`);
        } else {
          alert(`Uploaded ${successful} file(s), ${failed} failed.`);
        }
        
        // For operations tab, add uploaded files as operations
        if (activeTab === 'operations' && uploadedFiles.length > 0) {
          const newOps = uploadedFiles.map(filename => ({
            type: 'move' as const,
            source: filename,
            destination: ''
          }));
          
          setOperations(prev => [...prev, ...newOps]);
        }
        
      } catch (error) {
        console.error('Upload error:', error);
        alert(`Failed to upload files: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        setLoading(false);
        setUploadingFiles([]);
        setUploadProgress({});
      }
    }
  }, [activeTab, selectedWorkspace, loadFiles]);

  const loadQuickActions = async () => {
    try {
      const response = await makeApiRequest('/file-management/quick-actions?user_id=1', 'GET');
      setQuickActions(response.quick_actions || []);
    } catch (error) {
      console.error('Error loading quick actions:', error);
    }
  };

  const organizeFiles = async () => {
    if (!sourceDirectory.trim()) return;
    
    setOrganizing(true);
    try {
      const result = await makeApiRequest('/file-management/organize-by-category', 'POST', {
        source_directory: sourceDirectory,
        user_id: 1, // TODO: Get actual user ID
        organize_mode: organizeMode
      });
      setOrganizeResult(result);
      // Reload quick actions after organization
      loadQuickActions();
    } catch (error) {
      console.error('Error organizing files:', error);
    } finally {
      setOrganizing(false);
    }
  };

  const analyzeStorage = async () => {
    setAnalyzingStorage(true);
    try {
      const result = await makeApiRequest('/file-management/analyze-storage', 'POST', {
        user_id: 1 // TODO: Get actual user ID
      });
      setStorageStats(result);
    } catch (error) {
      console.error('Error analyzing storage:', error);
    } finally {
      setAnalyzingStorage(false);
    }
  };

  const findDuplicates = async (deleteDuplicates: boolean = false) => {
    setDeduplicating(true);
    try {
      const result = await makeApiRequest('/file-management/deduplicate', 'POST', {
        user_id: 1, // TODO: Get actual user ID
        delete_duplicates: deleteDuplicates
      });
      setDuplicateResults(result);
      // Reload quick actions if duplicates were deleted
      if (deleteDuplicates) {
        loadQuickActions();
      }
    } catch (error) {
      console.error('Error finding duplicates:', error);
    } finally {
      setDeduplicating(false);
    }
  };

  const performBatchOperations = async () => {
    if (operations.length === 0) return;
    
    try {
      const result = await makeApiRequest('/file-management/batch-operations', 'POST', {
        operations
      });
      setOperationResults(result);
      setOperations([]); // Clear operations after execution
    } catch (error) {
      console.error('Error performing operations:', error);
    }
  };

  const addOperation = () => {
    if (newOperation.source.trim()) {
      setOperations([...operations, { ...newOperation }]);
      setNewOperation({ type: 'copy', source: '' });
    }
  };

  const removeOperation = (index: number) => {
    setOperations(operations.filter((_, i) => i !== index));
  };

  const performQuickAction = async (action: QuickAction) => {
    switch (action.action) {
      case 'deduplicate':
        await findDuplicates(true);
        break;
      case 'organize':
        // Set a default directory and trigger organization
        setSourceDirectory('/Users/username/Downloads'); // TODO: Get user's downloads folder
        setActiveTab('organize');
        break;
      case 'archive_large':
      case 'archive_old':
        // These would trigger archive operations
        alert('Archive feature coming soon!');
        break;
    }
  };

  const loadFilterOptions = async () => {
    try {
      const [tagsResponse, categoriesResponse] = await Promise.all([
        makeApiRequest('/search/tags'),
        makeApiRequest('/search/categories?user_id=1')
      ]);
      
      // Handle new format with success wrapper or old array format
      if (tagsResponse && tagsResponse.success && tagsResponse.tags) {
        setAvailableTags(tagsResponse.tags.map((tag: any) => tag.name || tag));
      } else if (Array.isArray(tagsResponse)) {
        // Fallback for old format
        setAvailableTags(tagsResponse.map((tag: any) => tag.name || tag));
      } else {
        // Default tags if API fails
        setAvailableTags(['urgent', 'project', 'document', 'image', 'code', 'review']);
      }
      
      // Handle new format with success wrapper or old array format
      if (categoriesResponse && categoriesResponse.success && categoriesResponse.categories) {
        setAvailableCategories(categoriesResponse.categories.map((cat: any) => cat.name || cat));
      } else if (Array.isArray(categoriesResponse)) {
        // Fallback for old format
        setAvailableCategories(categoriesResponse.map((cat: any) => cat.name || cat));
      } else {
        // Default categories if API fails
        setAvailableCategories(['Documents', 'Images', 'Projects', 'Archives', 'Media', 'Data']);
      }
    } catch (error) {
      console.error('Failed to load filter options:', error);
      // Set defaults on error
      setAvailableTags(['urgent', 'project', 'document', 'image', 'code', 'review']);
      setAvailableCategories(['Documents', 'Images', 'Projects', 'Archives', 'Media', 'Data']);
    }
  };

  const sortFiles = (fileList: FileItem[], sortField: string, order: 'asc' | 'desc') => {
    return [...fileList].sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'modified':
          comparison = new Date(a.modified).getTime() - new Date(b.modified).getTime();
          break;
        case 'size':
          const sizeA = parseSize(a.size);
          const sizeB = parseSize(b.size);
          comparison = sizeA - sizeB;
          break;
        case 'type':
          comparison = a.type.localeCompare(b.type);
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'workspace':
          const workspaceA = a.workspace_name || 'No workspace';
          const workspaceB = b.workspace_name || 'No workspace';
          comparison = workspaceA.localeCompare(workspaceB);
          break;
        default:
          return 0;
      }
      
      return order === 'asc' ? comparison : -comparison;
    });
  };

  const groupFiles = (fileList: FileItem[], groupField: string) => {
    if (groupField === 'none') {
      return { 'All Files': fileList };
    }

    const grouped: {[key: string]: FileItem[]} = {};
    
    fileList.forEach(file => {
      let groupKey = '';
      
      switch (groupField) {
        case 'category':
          groupKey = file.category || 'Uncategorized';
          break;
        case 'workspace':
          groupKey = file.workspace_name || 'No Workspace';
          break;
        case 'type':
          groupKey = file.type || 'Unknown';
          break;
        default:
          groupKey = 'All Files';
      }
      
      if (!grouped[groupKey]) {
        grouped[groupKey] = [];
      }
      grouped[groupKey].push(file);
    });
    
    // Sort groups by name
    const sortedGroups: {[key: string]: FileItem[]} = {};
    Object.keys(grouped).sort().forEach(key => {
      sortedGroups[key] = grouped[key];
    });
    
    return sortedGroups;
  };

  const parseSize = (sizeStr: string): number => {
    const match = sizeStr.match(/(\d+(?:\.\d+)?)\s*(KB|MB|GB)/i);
    if (!match) return 0;
    
    const value = parseFloat(match[1]);
    const unit = match[2].toLowerCase();
    
    switch (unit) {
      case 'kb': return value * 1024;
      case 'mb': return value * 1024 * 1024;
      case 'gb': return value * 1024 * 1024 * 1024;
      default: return value;
    }
  };

  // Selection Functions
  const toggleFileSelection = (fileId: string) => {
    const newSelection = new Set(selectedFiles);
    if (newSelection.has(fileId)) {
      newSelection.delete(fileId);
    } else {
      newSelection.add(fileId);
    }
    setSelectedFiles(newSelection);
  };

  const selectAllFiles = () => {
    setSelectedFiles(new Set(files.map(f => f.id)));
  };

  const deselectAllFiles = () => {
    setSelectedFiles(new Set());
  };

  const selectAllVisible = () => {
    setSelectedFiles(new Set(files.map(f => f.id)));
  };

  // Bulk Operations
  const performBulkAction = async (action: string) => {
    const selectedFileIds = Array.from(selectedFiles);
    if (selectedFileIds.length === 0) {
      alert('Please select files first');
      return;
    }

    const selectedFileObjects = files.filter(f => selectedFileIds.includes(f.id));
    setLoading(true);

    try {
      switch (action) {
        case 'delete':
          if (confirm(`Delete ${selectedFileIds.length} selected files?`)) {
            const deletePromises = selectedFileIds.map(async (fileId) => {
              const response = await fetch(`http://localhost:8000/files/upload/${fileId}?user_id=1&permanent=false`, {
                method: 'DELETE',
              });
              return { fileId, success: response.ok };
            });
            
            const results = await Promise.allSettled(deletePromises);
            const successful = results.filter(r => r.status === 'fulfilled' && (r.value as any).success).length;
            const failed = results.length - successful;
            
            alert(`Deleted ${successful} files${failed > 0 ? `, ${failed} failed` : ''}`);
            setSelectedFiles(new Set());
            await loadFiles();
          }
          break;
          
        case 'move':
          const workspace = prompt('Enter workspace ID to move files to (leave empty for general):');
          if (workspace !== null) {
            const movePromises = selectedFileIds.map(async (fileId) => {
              const formData = new FormData();
              if (workspace.trim()) {
                formData.append('workspace_id', workspace.trim());
              }
              formData.append('user_id', '1');
              
              const response = await fetch(`http://localhost:8000/files/${fileId}/move`, {
                method: 'POST',
                body: formData,
              });
              return { fileId, success: response.ok };
            });
            
            const results = await Promise.allSettled(movePromises);
            const successful = results.filter(r => r.status === 'fulfilled' && (r.value as any).success).length;
            const failed = results.length - successful;
            
            alert(`Moved ${successful} files${failed > 0 ? `, ${failed} failed` : ''}`);
            setSelectedFiles(new Set());
            await loadFiles();
          }
          break;
          
        case 'favorite':
          const favoritePromises = selectedFileIds.map(async (fileId) => {
            const response = await fetch(`http://localhost:8000/files/${fileId}/favorite`, {
              method: 'POST',
            });
            return { fileId, success: response.ok };
          });
          
          const favoriteResults = await Promise.allSettled(favoritePromises);
          const successfulFavorites = favoriteResults.filter(r => r.status === 'fulfilled' && (r.value as any).success).length;
          const failedFavorites = favoriteResults.length - successfulFavorites;
          
          alert(`Toggled favorite for ${successfulFavorites} files${failedFavorites > 0 ? `, ${failedFavorites} failed` : ''}`);
          setSelectedFiles(new Set());
          await loadFiles();
          break;
          
        case 'archive':
          const archivePromises = selectedFileIds.map(async (fileId) => {
            const response = await fetch(`http://localhost:8000/files/${fileId}/archive`, {
              method: 'POST',
            });
            return { fileId, success: response.ok };
          });
          
          const archiveResults = await Promise.allSettled(archivePromises);
          const successfulArchives = archiveResults.filter(r => r.status === 'fulfilled' && (r.value as any).success).length;
          const failedArchives = archiveResults.length - successfulArchives;
          
          alert(`Archived ${successfulArchives} files${failedArchives > 0 ? `, ${failedArchives} failed` : ''}`);
          setSelectedFiles(new Set());
          await loadFiles();
          break;
          
        default:
          alert(`Action "${action}" not implemented yet`);
      }
    } catch (error) {
      console.error('Bulk operation error:', error);
      alert('Bulk operation failed');
    } finally {
      setLoading(false);
    }
  };

  // Preview Functions
  const openPreview = async (file: FileItem) => {
    setPreviewFile(file);
    setShowPreview(true);
    setPreviewContent('');
    
    // Try to load content for text files
    const textExtensions = ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.ts', '.html', '.css', '.yaml', '.yml'];
    if (textExtensions.includes(file.type)) {
      try {
        const response = await fetch(`http://localhost:8000/files/${file.id}/content?user_id=1`);
        if (response.ok) {
          const data = await response.json();
          setPreviewContent(data.content);
        } else {
          setPreviewContent('Failed to load file content');
        }
      } catch (error) {
        console.error('Error loading file content:', error);
        setPreviewContent('Error loading file content');
      }
    }
  };

  const closePreview = () => {
    setPreviewFile(null);
    setShowPreview(false);
    setPreviewContent('');
    setEditingTags(false);
    setNewTagInput('');
  };

  // Filter Functions
  const updateFilter = (key: keyof FileFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      type: '',
      category: '',
      workspace: '',
      tags: [],
      dateRange: { start: '', end: '' },
      sizeRange: { min: 0, max: 0 }
    });
  };

  const addTagFilter = (tag: string) => {
    if (!filters.tags.includes(tag)) {
      updateFilter('tags', [...filters.tags, tag]);
    }
  };

  const removeTagFilter = (tag: string) => {
    updateFilter('tags', filters.tags.filter(t => t !== tag));
  };

  // File Operation Functions
  const toggleFileFavorite = async (fileId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/files/${fileId}/favorite`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Refresh file list to show updated favorite status
        await loadFiles();
      } else {
        alert('Failed to toggle favorite status');
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Failed to toggle favorite status');
    }
  };

  const deleteFile = async (fileId: string, fileName: string) => {
    if (!confirm(`Are you sure you want to delete "${fileName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/files/upload/${fileId}?user_id=1&permanent=false`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        // Remove file from local state
        setFiles(prev => prev.filter(f => f.id !== fileId));
        // Also remove from selection if selected
        setSelectedFiles(prev => {
          const newSet = new Set(prev);
          newSet.delete(fileId);
          return newSet;
        });
      } else {
        const error = await response.json();
        alert(`Failed to delete file: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      alert('Failed to delete file');
    }
  };

  const renameFile = async (fileId: string, currentName: string) => {
    const newName = prompt(`Enter new name for "${currentName}":`, currentName);
    if (!newName || newName === currentName) {
      return;
    }

    try {
      const formData = new FormData();
      formData.append('new_name', newName);
      formData.append('user_id', '1');

      const response = await fetch(`http://localhost:8000/files/${fileId}/rename`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        // Refresh file list to show updated name
        await loadFiles();
      } else {
        const error = await response.json();
        alert(`Failed to rename file: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error renaming file:', error);
      alert('Failed to rename file');
    }
  };

  const moveFileToWorkspace = async (fileId: string) => {
    const workspaceId = prompt('Enter workspace ID to move file to (leave empty for general):');
    if (workspaceId === null) {
      return; // User cancelled
    }

    try {
      const formData = new FormData();
      if (workspaceId.trim()) {
        formData.append('workspace_id', workspaceId.trim());
      }
      formData.append('user_id', '1');

      const response = await fetch(`http://localhost:8000/files/${fileId}/move`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        // Refresh file list to show updated location
        await loadFiles();
      } else {
        const error = await response.json();
        alert(`Failed to move file: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error moving file:', error);
      alert('Failed to move file');
    }
  };

  // Download Function
  const downloadFile = async (fileId: string, fileName: string) => {
    try {
      // Create a temporary link to trigger download
      const downloadUrl = `http://localhost:8000/files/${fileId}/download?user_id=1`;
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = fileName;
      link.target = '_blank';
      
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('Failed to download file');
    }
  };

  // Tag Management Functions
  const addTagsToFile = async (fileId: string, tagNames: string) => {
    try {
      const formData = new FormData();
      formData.append('tag_names', tagNames);
      formData.append('user_id', '1');

      const response = await fetch(`http://localhost:8000/files/${fileId}/tags`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const result = await response.json();
        // Update the preview file if it's the same file
        if (previewFile && previewFile.id === fileId) {
          setPreviewFile({
            ...previewFile,
            tags: result.tags
          });
        }
        // Refresh file list
        await loadFiles();
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add tags');
      }
    } catch (error) {
      console.error('Error adding tags:', error);
      throw error;
    }
  };

  const removeTagFromFile = async (fileId: string, tagName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/files/${fileId}/tags?tag_names=${encodeURIComponent(tagName)}&user_id=1`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        const result = await response.json();
        // Update the preview file if it's the same file
        if (previewFile && previewFile.id === fileId) {
          setPreviewFile({
            ...previewFile,
            tags: result.remaining_tags
          });
        }
        // Refresh file list
        await loadFiles();
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to remove tag');
      }
    } catch (error) {
      console.error('Error removing tag:', error);
      throw error;
    }
  };

  const handleAddTags = async () => {
    if (!newTagInput.trim() || !previewFile) return;
    
    try {
      await addTagsToFile(previewFile.id, newTagInput.trim());
      setNewTagInput('');
      setEditingTags(false);
    } catch (error) {
      alert(`Failed to add tags: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleRemoveTag = async (tagName: string) => {
    if (!previewFile) return;
    
    try {
      await removeTagFromFile(previewFile.id, tagName);
    } catch (error) {
      alert(`Failed to remove tag: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const renderOrganizeTab = () => (
    <div className="organize-tab">
      <h3>📁 Organize Files by Category</h3>
      
      {/* Drag & Drop Zone */}
      <div 
        ref={dropZoneRef}
        className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className="drop-zone-content">
          <div className="drop-icon">📂</div>
          <h4>Drag & Drop Files Here</h4>
          <p>Drop files or folders to organize them automatically</p>
          <div className="drop-zone-hint">
            {isDragOver ? 'Release to add files!' : 'Or use the manual controls below'}
          </div>
        </div>
      </div>

      {/* Upload Progress Indicator */}
      {uploadingFiles.length > 0 && (
        <div className="upload-progress">
          <h5>Uploading Files ({uploadingFiles.length})</h5>
          <div className="progress-list">
            {uploadingFiles.map((fileName) => (
              <div key={fileName} className="progress-item">
                <div className="progress-info">
                  <span className="file-name">{fileName}</span>
                  <span className="progress-percent">{uploadProgress[fileName] || 0}%</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress[fileName] || 0}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {draggedFiles.length > 0 && (
        <div className="dropped-files-preview">
          <h5>Recently Dropped Files ({draggedFiles.length})</h5>
          <div className="file-list">
            {draggedFiles.slice(0, 5).map((file, index) => (
              <div key={index} className="file-item">
                <span className="file-icon">📄</span>
                <span className="file-name">{file}</span>
              </div>
            ))}
            {draggedFiles.length > 5 && (
              <div className="more-files">...and {draggedFiles.length - 5} more files</div>
            )}
          </div>
        </div>
      )}
      
      <div className="organize-controls">
        <input
          type="text"
          value={sourceDirectory}
          onChange={(e) => setSourceDirectory(e.target.value)}
          placeholder="Enter directory path to organize (e.g., /Users/username/Downloads)"
          className="directory-input"
        />
        <div className="organize-options">
          <label className="radio-option">
            <input
              type="radio"
              value="copy"
              checked={organizeMode === 'copy'}
              onChange={(e) => setOrganizeMode(e.target.value as 'copy')}
            />
            <span>Copy files (keep originals)</span>
          </label>
          <label className="radio-option">
            <input
              type="radio"
              value="move"
              checked={organizeMode === 'move'}
              onChange={(e) => setOrganizeMode(e.target.value as 'move')}
            />
            <span>Move files</span>
          </label>
        </div>
        <button
          onClick={organizeFiles}
          disabled={organizing || !sourceDirectory.trim()}
          className="btn btn-primary"
        >
          {organizing ? 'Organizing...' : 'Start Organization'}
        </button>
      </div>
      
      {organizeResult && (
        <div className="organize-results">
          <h4>✅ Organization Complete</h4>
          <div className="result-stats">
            <div className="stat-item">
              <span className="stat-value">{organizeResult.total_files}</span>
              <span className="stat-label">Total Files</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{organizeResult.organized_files}</span>
              <span className="stat-label">Organized</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{organizeResult.errors}</span>
              <span className="stat-label">Errors</span>
            </div>
          </div>
          
          <div className="category-breakdown">
            <h5>Files by Category:</h5>
            {Object.entries(organizeResult.categories).map(([category, data]: [string, any]) => (
              <div key={category} className="category-result">
                <span className="category-name">{category}</span>
                <span className="file-count">{data.count} files</span>
                <span className="file-size">{(data.size / (1024 * 1024)).toFixed(2)} MB</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderStorageTab = () => (
    <div className="storage-tab">
      <h3>💾 Speicher-Analyse</h3>
      <button
        onClick={analyzeStorage}
        disabled={analyzingStorage}
        className="btn btn-primary"
      >
        {analyzingStorage ? 'Analysiere...' : 'Speicher Analysieren'}
      </button>
      
      {storageStats && (
        <div className="storage-results">
          <div className="storage-overview">
            <div className="overview-card">
              <h4>Gesamtspeicher</h4>
              <p className="big-number">{storageStats.total_size_gb} GB</p>
              <p className="sub-text">{storageStats.total_files.toLocaleString()} Dateien</p>
            </div>
          </div>
          
          <div className="storage-insights">
            <h4>💡 Erkenntnisse & Empfehlungen</h4>
            {storageStats.insights.map((insight, index) => (
              <div key={index} className="insight-card">
                <p className="insight-message">{insight.message}</p>
                <p className="insight-action">{insight.action}</p>
              </div>
            ))}
          </div>
          
          <div className="large-files">
            <h4>📊 Größte Dateien</h4>
            {storageStats.large_files.slice(0, 10).map((file, index) => (
              <div key={index} className="large-file-item">
                <span className="file-path">{file.path.split('/').pop()}</span>
                <span className="file-size">{file.size_mb} MB</span>
                <span className="file-category">{file.category}</span>
              </div>
            ))}
          </div>
          
          <div className="deduplication-section">
            <h4>🔍 Duplicate Files</h4>
            <button
              onClick={() => findDuplicates(false)}
              disabled={deduplicating}
              className="btn btn-secondary"
            >
              {deduplicating ? 'Scanning...' : 'Find Duplicates'}
            </button>
            
            {duplicateResults && (
              <div className="duplicate-results">
                <p className="duplicate-summary">
                  Found {duplicateResults.total_duplicates} duplicate files
                  wasting {duplicateResults.space_wasted_mb} MB
                </p>
                {duplicateResults.total_duplicates > 0 && (
                  <button
                    onClick={() => findDuplicates(true)}
                    className="btn btn-danger"
                  >
                    Delete All Duplicates
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      
      {quickActions.length > 0 && (
        <div className="quick-actions">
          <h4>⚡ Quick Actions</h4>
          {quickActions.map((action, index) => (
            <div key={index} className={`action-card priority-${action.priority}`}>
              <h5>{action.title}</h5>
              <p>{action.description}</p>
              {action.estimated_savings_mb && (
                <p className="savings">Save ~{action.estimated_savings_mb} MB</p>
              )}
              <button
                onClick={() => performQuickAction(action)}
                className="btn btn-small"
              >
                Execute
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderOperationsTab = () => (
    <div className="operations-tab">
      <h3>🔧 Batch File Operations</h3>
      <div className="operation-builder">
        <select
          value={newOperation.type}
          onChange={(e) => setNewOperation({ ...newOperation, type: e.target.value as any })}
          className="operation-type"
        >
          <option value="copy">Copy</option>
          <option value="move">Move</option>
          <option value="rename">Rename</option>
          <option value="delete">Delete</option>
        </select>
        
        <input
          type="text"
          value={newOperation.source}
          onChange={(e) => setNewOperation({ ...newOperation, source: e.target.value })}
          placeholder="Source path"
          className="source-input"
        />
        
        {newOperation.type !== 'delete' && (
          <input
            type="text"
            value={newOperation.destination || ''}
            onChange={(e) => setNewOperation({ ...newOperation, destination: e.target.value })}
            placeholder="Destination path"
            className="destination-input"
          />
        )}
        
        <button
          onClick={addOperation}
          disabled={!newOperation.source.trim()}
          className="btn btn-add"
        >
          Add Operation
        </button>
      </div>
      
      {operations.length > 0 && (
        <div className="operations-list">
          <h4>Pending Operations ({operations.length})</h4>
          {operations.map((op, index) => (
            <div key={index} className="operation-item">
              <span className="op-type">{op.type}</span>
              <span className="op-source">{op.source}</span>
              {op.destination && (
                <>
                  <span className="op-arrow">→</span>
                  <span className="op-dest">{op.destination}</span>
                </>
              )}
              <button
                onClick={() => removeOperation(index)}
                className="btn btn-remove"
              >
                Remove
              </button>
            </div>
          ))}
          
          <button
            onClick={performBatchOperations}
            className="btn btn-primary"
          >
            Execute All Operations
          </button>
        </div>
      )}
      
      {operationResults && (
        <div className="operation-results">
          <h4>Operation Results</h4>
          <div className="result-summary">
            <span className="success">✅ Successful: {operationResults.successful}</span>
            <span className="failed">❌ Failed: {operationResults.failed}</span>
          </div>
          {operationResults.results.filter((r: any) => r.status === 'error').map((result: any, index: number) => (
            <div key={index} className="error-item">
              <strong>Error:</strong> {result.error}
              <br />
              <small>{result.operation.source}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderFileBrowserTab = () => (
    <div className="file-browser-tab">
      {/* Toolbar */}
      <div className="file-browser-toolbar">
        <div className="toolbar-left">
          <h3>📂 File Browser</h3>
          <span className="file-count">{files.length} files</span>
          {selectedFiles.size > 0 && (
            <span className="selection-count">({selectedFiles.size} selected)</span>
          )}
        </div>
        
        <div className="toolbar-right">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn btn-secondary ${showFilters ? 'active' : ''}`}
          >
            🔍 Filters
          </button>
          
          <div className="view-controls">
            <button
              onClick={() => setViewMode('grid')}
              className={`btn btn-sm ${viewMode === 'grid' ? 'active' : ''}`}
            >
              ⊞
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`btn btn-sm ${viewMode === 'list' ? 'active' : ''}`}
            >
              ☰
            </button>
          </div>
          
          <div className="sort-controls">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="sort-select"
            >
              <option value="modified">Modified</option>
              <option value="name">Name</option>
              <option value="size">Size</option>
              <option value="type">Type</option>
              <option value="category">Category</option>
              <option value="workspace">Workspace</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="btn btn-sm"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
          
          <div className="group-controls">
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as any)}
              className="group-select"
            >
              <option value="none">No Grouping</option>
              <option value="category">Group by Category</option>
              <option value="workspace">Group by Workspace</option>
              <option value="type">Group by Type</option>
            </select>
          </div>
        </div>
      </div>

      {/* Advanced Filters Panel */}
      {showFilters && (
        <div className="filters-panel">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Search</label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => updateFilter('search', e.target.value)}
                placeholder="Search files..."
                className="filter-input"
              />
            </div>
            
            <div className="filter-group">
              <label>Category</label>
              <select
                value={filters.category}
                onChange={(e) => updateFilter('category', e.target.value)}
                className="filter-select"
              >
                <option value="">All Categories</option>
                {availableCategories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            
            <div className="filter-group">
              <label>File Type</label>
              <select
                value={filters.type}
                onChange={(e) => updateFilter('type', e.target.value)}
                className="filter-select"
              >
                <option value="">All Types</option>
                <option value="image">Images</option>
                <option value="document">Documents</option>
                <option value="video">Videos</option>
                <option value="audio">Audio</option>
                <option value="code">Code</option>
              </select>
            </div>
            
            <div className="filter-group">
              <label>Tags</label>
              <div className="tags-filter">
                <div className="selected-tags">
                  {filters.tags.map(tag => (
                    <span key={tag} className="tag-chip">
                      {tag}
                      <button onClick={() => removeTagFilter(tag)}>×</button>
                    </span>
                  ))}
                </div>
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      addTagFilter(e.target.value);
                      e.target.value = '';
                    }
                  }}
                  className="filter-select"
                >
                  <option value="">Add tag filter...</option>
                  {availableTags.map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          
          <div className="filters-actions">
            <button onClick={clearFilters} className="btn btn-secondary">
              Clear Filters
            </button>
          </div>
        </div>
      )}

      {/* Bulk Actions Bar */}
      {selectedFiles.size > 0 && (
        <div className="bulk-actions-bar">
          <div className="bulk-actions-left">
            <button onClick={selectAllVisible} className="btn btn-sm">
              Select All ({files.length})
            </button>
            <button onClick={deselectAllFiles} className="btn btn-sm">
              Deselect All
            </button>
          </div>
          
          <div className="bulk-actions-right">
            <button
              onClick={() => performBulkAction('favorite')}
              className="btn btn-sm btn-secondary"
            >
              ⭐ Favorite
            </button>
            <button
              onClick={() => performBulkAction('move')}
              className="btn btn-sm btn-secondary"
            >
              📁 Move
            </button>
            <button
              onClick={() => performBulkAction('archive')}
              className="btn btn-sm btn-secondary"
            >
              📦 Archive
            </button>
            <button
              onClick={() => performBulkAction('delete')}
              className="btn btn-sm btn-danger"
            >
              🗑️ Delete
            </button>
          </div>
        </div>
      )}

      {/* File Grid/List */}
      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading files...</p>
        </div>
      ) : (
        <div className={`files-container ${viewMode}`}>
          {(() => {
            const sortedFiles = sortFiles(files, sortBy, sortOrder);
            const groupedFiles = groupFiles(sortedFiles, groupBy);
            
            return Object.entries(groupedFiles).map(([groupName, groupFiles]) => (
              <div key={groupName} className="file-group">
                {groupBy !== 'none' && (
                  <div className="group-header">
                    <h4>{groupName}</h4>
                    <span className="group-count">({groupFiles.length} files)</span>
                  </div>
                )}
                <div className={`group-files ${viewMode}`}>
                  {groupFiles.map(file => (
            <div
              key={file.id}
              className={`file-item ${selectedFiles.has(file.id) ? 'selected' : ''}`}
              onClick={() => toggleFileSelection(file.id)}
              onDoubleClick={() => openPreview(file)}
            >
              <div className="file-checkbox">
                <input
                  type="checkbox"
                  checked={selectedFiles.has(file.id)}
                  onChange={() => toggleFileSelection(file.id)}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
              
              <div className="file-thumbnail">
                {file.thumbnail ? (
                  <img src={file.thumbnail} alt={file.name} />
                ) : (
                  <div className="file-icon">{getFileIcon(file.type)}</div>
                )}
              </div>
              
              <div className="file-details">
                <div className="file-name" title={file.name}>
                  {file.name}
                </div>
                <div className="file-meta">
                  <span className="file-size">{file.size}</span>
                  <span className="file-modified">{new Date(file.modified).toLocaleDateString()}</span>
                </div>
                <div className="file-tags">
                  {file.tags.slice(0, 3).map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                  {file.tags.length > 3 && (
                    <span className="tag-more">+{file.tags.length - 3}</span>
                  )}
                </div>
                {file.workspace_name && (
                  <div className="file-workspace">
                    📁 {file.workspace_name}
                  </div>
                )}
              </div>
              
              <div className="file-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFileFavorite(file.id);
                  }}
                  className="btn btn-sm"
                  title="Toggle Favorite"
                >
                  ⭐
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    renameFile(file.id, file.name);
                  }}
                  className="btn btn-sm"
                  title="Rename"
                >
                  ✏️
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    moveFileToWorkspace(file.id);
                  }}
                  className="btn btn-sm"
                  title="Move"
                >
                  📁
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteFile(file.id, file.name);
                  }}
                  className="btn btn-sm btn-danger"
                  title="Delete"
                >
                  🗑️
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    downloadFile(file.id, file.name);
                  }}
                  className="btn btn-sm"
                  title="Download"
                >
                  💾
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openPreview(file);
                  }}
                  className="btn btn-sm"
                  title="Preview"
                >
                  👁️
                </button>
              </div>
            </div>
                  ))}
                </div>
              </div>
            ));
          })()}
          
          {files.length === 0 && !loading && (
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <h4>No files found</h4>
              <p>Try adjusting your filters or upload some files</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image': return '🖼️';
      case 'document': return '📄';
      case 'video': return '🎥';
      case 'audio': return '🎵';
      case 'code': return '💻';
      case 'archive': return '📦';
      default: return '📄';
    }
  };

  const renderPreviewModal = () => {
    if (!showPreview || !previewFile) return null;

    return (
      <div className="preview-modal-overlay" onClick={closePreview}>
        <div className="preview-modal" onClick={(e) => e.stopPropagation()}>
          <div className="preview-header">
            <h3>{previewFile.name}</h3>
            <button onClick={closePreview} className="btn btn-close">×</button>
          </div>
          
          <div className="preview-content">
            <div className="preview-main">
              {previewFile.type === 'image' ? (
                <img src={previewFile.thumbnail || '/placeholder-image.png'} alt={previewFile.name} />
              ) : previewContent ? (
                <div className="preview-text">
                  <pre className="text-content">{previewContent}</pre>
                </div>
              ) : ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.ts', '.html', '.css', '.yaml', '.yml'].includes(previewFile.type) ? (
                <div className="preview-loading">
                  <p>Loading file content...</p>
                </div>
              ) : (
                <div className="preview-placeholder">
                  <div className="preview-icon">{getFileIcon(previewFile.type)}</div>
                  <p>Preview not available for this file type</p>
                </div>
              )}
            </div>
            
            <div className="preview-sidebar">
              <div className="preview-info">
                <h4>File Information</h4>
                <div className="info-item">
                  <label>Name:</label>
                  <span>{previewFile.name}</span>
                </div>
                <div className="info-item">
                  <label>Size:</label>
                  <span>{previewFile.size}</span>
                </div>
                <div className="info-item">
                  <label>Type:</label>
                  <span>{previewFile.type}</span>
                </div>
                <div className="info-item">
                  <label>Modified:</label>
                  <span>{new Date(previewFile.modified).toLocaleString()}</span>
                </div>
                <div className="info-item">
                  <label>Category:</label>
                  <span>{previewFile.category}</span>
                </div>
                {previewFile.workspace_name && (
                  <div className="info-item">
                    <label>Workspace:</label>
                    <span>{previewFile.workspace_name}</span>
                  </div>
                )}
              </div>
              
              <div className="preview-tags">
                <div className="tags-header">
                  <h4>Tags</h4>
                  <button 
                    onClick={() => setEditingTags(!editingTags)}
                    className="btn btn-sm"
                  >
                    {editingTags ? 'Cancel' : 'Edit'}
                  </button>
                </div>
                
                <div className="tags-list">
                  {previewFile.tags.map(tag => (
                    <span key={tag} className="tag">
                      {tag}
                      {editingTags && (
                        <button 
                          onClick={() => handleRemoveTag(tag)}
                          className="tag-remove"
                          title={`Remove ${tag}`}
                        >
                          ×
                        </button>
                      )}
                    </span>
                  ))}
                  {previewFile.tags.length === 0 && (
                    <span className="no-tags">No tags</span>
                  )}
                </div>
                
                {editingTags && (
                  <div className="tag-input">
                    <input
                      type="text"
                      value={newTagInput}
                      onChange={(e) => setNewTagInput(e.target.value)}
                      placeholder="Add tags (comma-separated)"
                      className="tag-input-field"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleAddTags();
                        }
                      }}
                    />
                    <button 
                      onClick={handleAddTags}
                      className="btn btn-sm btn-primary"
                      disabled={!newTagInput.trim()}
                    >
                      Add
                    </button>
                  </div>
                )}
              </div>
              
              <div className="preview-actions">
                <button 
                  onClick={() => downloadFile(previewFile.id, previewFile.name)}
                  className="btn btn-primary"
                >
                  💾 Download
                </button>
                <button className="btn btn-secondary">Edit Tags</button>
                <button 
                  onClick={closePreview}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="file-manager">
      <div className="file-manager-header">
        <h2>📂 File Manager</h2>
        <p>Advanced file organization and management tools</p>
      </div>
      
      <div className="file-manager-tabs">
        <button
          className={`tab-button ${activeTab === 'browser' ? 'active' : ''}`}
          onClick={() => setActiveTab('browser')}
        >
          📂 File Browser
        </button>
        <button
          className={`tab-button ${activeTab === 'organize' ? 'active' : ''}`}
          onClick={() => setActiveTab('organize')}
        >
          📁 Organize
        </button>
        <button
          className={`tab-button ${activeTab === 'storage' ? 'active' : ''}`}
          onClick={() => setActiveTab('storage')}
        >
          💾 Storage Analysis
        </button>
        <button
          className={`tab-button ${activeTab === 'operations' ? 'active' : ''}`}
          onClick={() => setActiveTab('operations')}
        >
          🔧 Batch Operations
        </button>
      </div>
      
      <div className="file-manager-content">
        {activeTab === 'browser' && renderFileBrowserTab()}
        {activeTab === 'organize' && renderOrganizeTab()}
        {activeTab === 'storage' && renderStorageTab()}
        {activeTab === 'operations' && renderOperationsTab()}
      </div>
      
      {/* Preview Modal */}
      {renderPreviewModal()}
    </div>
  );
};

export default FileManager;