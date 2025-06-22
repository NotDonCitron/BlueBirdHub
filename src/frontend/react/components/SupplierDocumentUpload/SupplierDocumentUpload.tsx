import React, { useState, useRef, useCallback } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './SupplierDocumentUpload.css';

interface UploadedDocument {
  document_id: number;
  file_name: string;
  file_size: number;
  document_type: string;
  processing_status: string;
  extraction_summary: {
    page_count: number;
    text_length: number;
    processing_time_ms: number;
    extraction_method: string;
  };
  analysis_summary: {
    quality_score: number;
    products_found: number;
    prices_found: number;
    categories: string[];
  };
  verification_status: string;
  created_at: string;
}

interface DocumentAnalysis {
  document_id: number;
  quality_score: number;
  products: Array<{
    line_number: number;
    raw_text: string;
    extracted_name: string;
    extracted_price: number;
    category: string;
  }>;
  prices: Array<{
    value: number;
    currency: string;
    context: string;
  }>;
  terms: {
    delivery_days?: number;
    payment_days?: number;
  };
  validation_errors: string[];
}

interface SupplierDocumentUploadProps {
  supplierId: number;
  onDocumentUploaded?: (document: UploadedDocument) => void;
  onClose?: () => void;
}

const SupplierDocumentUpload: React.FC<SupplierDocumentUploadProps> = ({
  supplierId,
  onDocumentUploaded,
  onClose
}) => {
  const { makeApiRequest } = useApi();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null);
  const [documentAnalysis, setDocumentAnalysis] = useState<DocumentAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState('price_list');
  const [notes, setNotes] = useState('');

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'image/png', 'image/jpeg', 'image/jpg'];
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(file.type) && !['pdf', 'txt', 'png', 'jpg', 'jpeg'].includes(fileExt || '')) {
      setError('Invalid file type. Please upload PDF, TXT, PNG, or JPG files.');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB.');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (notes) {
      formData.append('notes', notes);
    }

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await makeApiRequest(
        `/suppliers/${supplierId}/documents/upload`,
        'POST',
        formData,
        { 'Content-Type': 'multipart/form-data' }
      );

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response) {
        setUploadedDocument(response);
        
        // Fetch detailed analysis
        await fetchDocumentAnalysis(response.document_id);
        
        if (onDocumentUploaded) {
          onDocumentUploaded(response);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const fetchDocumentAnalysis = async (documentId: number) => {
    try {
      const analysis = await makeApiRequest(
        `/suppliers/${supplierId}/documents/${documentId}/analysis`,
        'GET'
      );
      
      if (analysis) {
        setDocumentAnalysis(analysis);
      }
    } catch (err) {
      console.error('Failed to fetch document analysis:', err);
    }
  };

  const handleVerifyDocument = async (status: 'verified' | 'rejected') => {
    if (!uploadedDocument) return;

    try {
      const formData = new FormData();
      formData.append('verification_status', status);
      formData.append('notes', notes);

      await makeApiRequest(
        `/suppliers/${supplierId}/documents/${uploadedDocument.document_id}/verify`,
        'POST',
        formData
      );

      // Update local state
      setUploadedDocument({
        ...uploadedDocument,
        verification_status: status
      });
    } catch (err: any) {
      setError(err.message || 'Verification failed.');
    }
  };

  const handleApplyToProducts = async () => {
    if (!uploadedDocument || uploadedDocument.verification_status !== 'verified') return;

    try {
      const result = await makeApiRequest(
        `/suppliers/${supplierId}/documents/${uploadedDocument.document_id}/apply-to-products`,
        'POST'
      );

      if (result) {
        setError(null);
        alert(`Successfully imported ${result.products_created} products!`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to apply products.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="document-upload-container">
      <div className="upload-header">
        <h2>📄 Upload Supplier Document</h2>
        {onClose && (
          <button className="close-button" onClick={onClose}>×</button>
        )}
      </div>

      {!uploadedDocument && (
        <>
          <div className="document-type-selector">
            <label>Document Type:</label>
            <select 
              value={documentType} 
              onChange={(e) => setDocumentType(e.target.value)}
            >
              <option value="price_list">Price List</option>
              <option value="invoice">Invoice</option>
              <option value="contract">Contract</option>
              <option value="certificate">Certificate</option>
              <option value="quotation">Quotation</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div
            className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.png,.jpg,.jpeg"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {isUploading ? (
              <div className="upload-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p>Uploading and analyzing document... {uploadProgress}%</p>
              </div>
            ) : (
              <>
                <div className="upload-icon">📤</div>
                <h3>Drag & Drop your document here</h3>
                <p>or click to browse</p>
                <p className="file-types">Supported: PDF, TXT, PNG, JPG (max 10MB)</p>
              </>
            )}
          </div>

          <div className="notes-section">
            <label>Notes (optional):</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this document..."
              rows={3}
            />
          </div>
        </>
      )}

      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {uploadedDocument && (
        <div className="upload-result">
          <div className="result-header">
            <h3>✅ Document Uploaded Successfully</h3>
            <span className={`status-badge status-${uploadedDocument.verification_status}`}>
              {uploadedDocument.verification_status}
            </span>
          </div>

          <div className="document-info">
            <div className="info-row">
              <span className="label">File:</span>
              <span>{uploadedDocument.file_name}</span>
            </div>
            <div className="info-row">
              <span className="label">Size:</span>
              <span>{formatFileSize(uploadedDocument.file_size)}</span>
            </div>
            <div className="info-row">
              <span className="label">Type:</span>
              <span>{uploadedDocument.document_type}</span>
            </div>
            <div className="info-row">
              <span className="label">Processing Time:</span>
              <span>{uploadedDocument.extraction_summary.processing_time_ms}ms</span>
            </div>
          </div>

          <div className="extraction-summary">
            <h4>📊 Extraction Summary</h4>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="value">{uploadedDocument.extraction_summary.page_count}</span>
                <span className="label">Pages</span>
              </div>
              <div className="summary-item">
                <span className="value">{uploadedDocument.analysis_summary.products_found}</span>
                <span className="label">Products</span>
              </div>
              <div className="summary-item">
                <span className="value">{uploadedDocument.analysis_summary.prices_found}</span>
                <span className="label">Prices</span>
              </div>
              <div className="summary-item">
                <span className="value">{uploadedDocument.analysis_summary.quality_score}%</span>
                <span className="label">Quality</span>
              </div>
            </div>
          </div>

          {documentAnalysis && documentAnalysis.products.length > 0 && (
            <div className="extracted-products">
              <h4>🛒 Extracted Products (Preview)</h4>
              <div className="products-preview">
                {documentAnalysis.products.slice(0, 5).map((product, index) => (
                  <div key={index} className="product-preview-item">
                    <span className="product-name">{product.extracted_name || product.raw_text}</span>
                    {product.extracted_price && (
                      <span className="product-price">€{product.extracted_price.toFixed(2)}</span>
                    )}
                  </div>
                ))}
                {documentAnalysis.products.length > 5 && (
                  <p className="more-products">
                    ... and {documentAnalysis.products.length - 5} more products
                  </p>
                )}
              </div>
            </div>
          )}

          {documentAnalysis && documentAnalysis.validation_errors.length > 0 && (
            <div className="validation-errors">
              <h4>⚠️ Validation Issues</h4>
              <ul>
                {documentAnalysis.validation_errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="action-buttons">
            {uploadedDocument.verification_status === 'pending' && (
              <>
                <button 
                  className="btn-verify"
                  onClick={() => handleVerifyDocument('verified')}
                >
                  ✅ Verify & Approve
                </button>
                <button 
                  className="btn-reject"
                  onClick={() => handleVerifyDocument('rejected')}
                >
                  ❌ Reject
                </button>
              </>
            )}
            
            {uploadedDocument.verification_status === 'verified' && (
              <button 
                className="btn-apply"
                onClick={handleApplyToProducts}
              >
                📥 Apply to Product Catalog
              </button>
            )}

            <button 
              className="btn-new"
              onClick={() => {
                setUploadedDocument(null);
                setDocumentAnalysis(null);
                setError(null);
                setNotes('');
              }}
            >
              📤 Upload Another Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SupplierDocumentUpload;