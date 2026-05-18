import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiService, ApiError } from '../services/api'
import { ProcessingMode, FileUploadProgress } from '../types/api'
import FileUploadZone from '../components/FileUploadZone'
import UploadProgress from '../components/UploadProgress'

const UploadPage: React.FC = () => {
  const navigate = useNavigate()
  const [uploads, setUploads] = useState<FileUploadProgress[]>([])
  const [processingMode, setProcessingMode] = useState<ProcessingMode>(ProcessingMode.SEQUENTIAL)
  const [isUploading, setIsUploading] = useState(false)

  const handleFilesSelected = useCallback(async (files: File[]) => {
    if (files.length === 0) return

    setIsUploading(true)
    
    // Initialize upload progress for all files
    const initialUploads: FileUploadProgress[] = files.map(file => ({
      file,
      progress: 0,
      status: 'uploading'
    }))
    
    setUploads(initialUploads)

    // Process files sequentially or in parallel based on mode
    if (processingMode === ProcessingMode.SEQUENTIAL) {
      await processFilesSequentially(files, initialUploads)
    } else {
      await processFilesInParallel(files, initialUploads)
    }

    setIsUploading(false)
  }, [processingMode])

  const processFilesSequentially = async (files: File[], initialUploads: FileUploadProgress[]) => {
    for (let i = 0; i < files.length; i++) {
      await processFile(files[i], i, initialUploads)
    }
  }

  const processFilesInParallel = async (files: File[], initialUploads: FileUploadProgress[]) => {
    const promises = files.map((file, index) => processFile(file, index, initialUploads))
    await Promise.allSettled(promises)
  }

  const processFile = async (file: File, index: number, currentUploads: FileUploadProgress[]) => {
    try {
      // Update status to processing
      setUploads(prev => prev.map((upload, i) => 
        i === index 
          ? { ...upload, progress: 50, status: 'processing' as const }
          : upload
      ))

      // Upload file
      const response = await apiService.uploadDocument(file, processingMode)

      // Update status to completed
      setUploads(prev => prev.map((upload, i) => 
        i === index 
          ? { ...upload, progress: 100, status: 'completed' as const }
          : upload
      ))

      console.log('Upload successful:', response)

    } catch (error) {
      console.error('Upload failed:', error)
      
      const errorMessage = error instanceof ApiError 
        ? `Upload failed: ${error.message}` 
        : 'Upload failed: Unknown error'

      // Update status to error
      setUploads(prev => prev.map((upload, i) => 
        i === index 
          ? { ...upload, status: 'error' as const, error: errorMessage }
          : upload
      ))
    }
  }

  const clearUploads = () => {
    setUploads([])
  }

  const viewDocuments = () => {
    navigate('/documents')
  }

  const retryFailedUploads = async () => {
    const failedUploads = uploads.filter(upload => upload.status === 'error')
    if (failedUploads.length === 0) return

    const filesToRetry = failedUploads.map(upload => upload.file)
    await handleFilesSelected(filesToRetry)
  }

  const hasCompletedUploads = uploads.some(upload => upload.status === 'completed')
  const hasFailedUploads = uploads.some(upload => upload.status === 'error')
  const allCompleted = uploads.length > 0 && uploads.every(upload => upload.status === 'completed')

  return (
    <div className="upload-page">
      <div className="page-header">
        <h1 className="page-title">Upload Documents</h1>
        <p className="page-description">
          Upload PDF, JPG, PNG, or TIFF files for automatic invoice processing and data extraction.
        </p>
      </div>

      <div className="upload-container">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Processing Configuration</h2>
          </div>
          
          <div className="form-group">
            <label className="form-label">Processing Mode</label>
            <select 
              className="form-control"
              value={processingMode}
              onChange={(e) => setProcessingMode(e.target.value as ProcessingMode)}
              disabled={isUploading}
            >
              <option value={ProcessingMode.SEQUENTIAL}>
                Sequential - Process files one by one
              </option>
              <option value={ProcessingMode.PARALLEL}>
                Parallel - Process files simultaneously
              </option>
            </select>
            <small className="form-text text-muted">
              Sequential processing is more reliable, parallel processing is faster.
            </small>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">File Upload</h2>
          </div>
          
          <FileUploadZone 
            onFilesSelected={handleFilesSelected}
            disabled={isUploading}
            multiple={true}
            acceptedTypes={['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif']}
          />
        </div>

        {uploads.length > 0 && (
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h2 className="card-title">Upload Progress</h2>
              <div className="upload-actions">
                {hasFailedUploads && (
                  <button 
                    className="btn btn-outline-primary mr-2"
                    onClick={retryFailedUploads}
                    disabled={isUploading}
                  >
                    Retry Failed
                  </button>
                )}
                {hasCompletedUploads && (
                  <button 
                    className="btn btn-primary mr-2"
                    onClick={viewDocuments}
                  >
                    View Documents
                  </button>
                )}
                <button 
                  className="btn btn-secondary"
                  onClick={clearUploads}
                  disabled={isUploading}
                >
                  Clear
                </button>
              </div>
            </div>
            
            <UploadProgress uploads={uploads} />
            
            {allCompleted && (
              <div className="upload-success">
                <p className="text-success">
                  ✅ All files uploaded successfully! 
                  Documents are being processed in the background.
                </p>
              </div>
            )}
          </div>
        )}

        <div className="upload-info card">
          <div className="card-header">
            <h3 className="card-title">Supported File Types</h3>
          </div>
          <div className="supported-formats">
            <div className="format-item">
              <strong>PDF:</strong> Best for text-based invoices with high accuracy
            </div>
            <div className="format-item">
              <strong>JPG/PNG:</strong> Good for scanned invoices, requires OCR processing
            </div>
            <div className="format-item">
              <strong>TIFF:</strong> High-quality scanned documents, excellent OCR results
            </div>
          </div>
          <div className="upload-limits">
            <p><strong>Maximum file size:</strong> 50MB per file</p>
            <p><strong>Processing time:</strong> Typically 10-30 seconds per document</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadPage