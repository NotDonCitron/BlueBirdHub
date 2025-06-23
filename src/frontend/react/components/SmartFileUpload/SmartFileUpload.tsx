import React, { useState, useRef, useCallback } from 'react';
import { makeApiRequest } from '../../lib/api';
import './SmartFileUpload.css';

interface FileUploadProps {
  workspaceId?: number;
  taskId?: string;
  onUploadComplete?: (files: any[]) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
}

interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  result?: any;
  error?: string;
}

const SmartFileUpload: React.FC<FileUploadProps> = ({
  workspaceId = 1,
  taskId,
  onUploadComplete,
  maxFiles = 10,
  maxSize = 50 * 1024 * 1024 // 50MB
}) => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > maxSize) {
      return `File too large. Maximum size: ${Math.round(maxSize / (1024 * 1024))}MB`;
    }
    
    const allowedTypes = [
      'image/', 'video/', 'audio/', 'application/pdf', 'text/',
      'application/msword', 'application/vnd.ms-excel',
      'application/vnd.openxmlformats', 'application/zip'
    ];
    
    const isAllowed = allowedTypes.some(type => file.type.startsWith(type));
    if (!isAllowed) {
      return 'File type not supported';
    }
    
    return null;
  };

  const processFiles = async (files: FileList) => {
    if (files.length + uploads.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`);
      return;
    }

    setIsProcessing(true);
    const newUploads: UploadProgress[] = [];

    // Validate all files first
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const error = validateFile(file);
      
      newUploads.push({
        file,
        progress: 0,
        status: error ? 'error' : 'uploading',
        error
      });
    }

    setUploads(prev => [...prev, ...newUploads]);

    // Upload valid files
    const validUploads = newUploads.filter(upload => !upload.error);
    const uploadPromises = validUploads.map(upload => uploadFile(upload));
    
    try {
      const results = await Promise.all(uploadPromises);
      
      // Organize files with AI
      const fileIds = results.filter(r => r.success).map(r => r.file.id);
      if (fileIds.length > 0) {
        await organizeFiles(fileIds);
      }
      
      onUploadComplete?.(results.filter(r => r.success));
    } catch (error) {
      console.error('Upload batch failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const uploadFile = async (uploadProgress: UploadProgress): Promise<any> => {
    try {
      // Simulate progress for demo
      for (let progress = 0; progress <= 100; progress += 10) {
        setUploads(prev => prev.map(u => 
          u.file === uploadProgress.file 
            ? { ...u, progress }
            : u
        ));
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Simulate file upload (in real app would use FormData)
      const fileData = {
        filename: uploadProgress.file.name,
        size: uploadProgress.file.size,
        type: uploadProgress.file.type,
        workspace_id: workspaceId,
        task_id: taskId,
        content: await fileToBase64(uploadProgress.file)
      };

      const result = await makeApiRequest('/files/upload', 'POST', fileData);
      
      setUploads(prev => prev.map(u => 
        u.file === uploadProgress.file 
          ? { ...u, status: 'completed', result }
          : u
      ));

      return { success: true, file: result.file };
    } catch (error) {
      setUploads(prev => prev.map(u => 
        u.file === uploadProgress.file 
          ? { ...u, status: 'error', error: error.message }
          : u
      ));
      return { success: false, error };
    }
  };

  const organizeFiles = async (fileIds: string[]) => {
    try {
      await makeApiRequest('/files/batch-organize', 'POST', { file_ids: fileIds });
    } catch (error) {
      console.error('AI organization failed:', error);
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFiles(files);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFiles(files);
    }
  };

  const clearUploads = () => {
    setUploads([]);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="smart-file-upload">
      <div 
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="upload-icon">📁</div>
        <div className="upload-text">
          <h3>Smart File Upload</h3>
          <p>Drag & drop files here or click to browse</p>
          <small>AI-powered organization • Max {maxFiles} files • {formatFileSize(maxSize)} each</small>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.zip,.csv,.xlsx"
      />

      {uploads.length > 0 && (
        <div className="upload-progress-list">
          <div className="progress-header">
            <h4>Upload Progress</h4>
            <button onClick={clearUploads} disabled={isProcessing}>
              Clear All
            </button>
          </div>
          
          {uploads.map((upload, index) => (
            <div key={index} className={`upload-item ${upload.status}`}>
              <div className="file-info">
                <div className="file-name">{upload.file.name}</div>
                <div className="file-size">{formatFileSize(upload.file.size)}</div>
              </div>
              
              <div className="upload-status">
                {upload.status === 'uploading' && (
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${upload.progress}%` }}
                    ></div>
                  </div>
                )}
                
                {upload.status === 'completed' && (
                  <div className="status-completed">
                    ✅ Uploaded & Organized
                    {upload.result?.category && (
                      <span className="category">→ {upload.result.category}</span>
                    )}
                  </div>
                )}
                
                {upload.status === 'error' && (
                  <div className="status-error">
                    ❌ {upload.error}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {isProcessing && (
        <div className="ai-processing">
          <div className="processing-spinner"></div>
          <span>🤖 AI is organizing your files...</span>
        </div>
      )}
    </div>
  );
};

export default SmartFileUpload;