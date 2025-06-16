// File Upload Component Implementation
// src/frontend/components/files/FileUpload.jsx

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const FileUpload = ({ workspaceId, onUploadComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({});

  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workspace_id', workspaceId);

    try {
      const response = await fetch('http://localhost:8001/api/files/upload', {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(prev => ({
            ...prev,
            [file.name]: percentCompleted
          }));
        }
      });

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true);
    
    try {
      const uploadPromises = acceptedFiles.map(file => uploadFile(file));
      const results = await Promise.all(uploadPromises);
      
      if (onUploadComplete) {
        onUploadComplete(results);
      }
    } catch (error) {
      console.error('Batch upload failed:', error);
    } finally {
      setUploading(false);
      setProgress({});
    }
  }, [workspaceId, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true
  });

  return (
    <div className="file-upload-container">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the files here...</p>
        ) : (
          <p>Drag & drop files here, or click to select</p>
        )}
      </div>

      {uploading && (
        <div className="upload-progress">
          {Object.entries(progress).map(([filename, percent]) => (
            <div key={filename} className="progress-item">
              <span>{filename}</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${percent}%` }}
                />
              </div>
              <span>{percent}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;