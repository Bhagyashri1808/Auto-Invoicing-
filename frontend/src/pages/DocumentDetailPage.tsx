import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'
import { InvoiceDocument, ExtractedData, ProcessingStatus } from '../types/api'
import ProcessingStatusComponent from '../components/ProcessingStatus'
import QualityIndicator from '../components/QualityIndicator'
import type { ExtractionMethod } from '../types/preprocessing'

const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [document, setDocument] = useState<InvoiceDocument | null>(null)
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [extractedDataLoading, setExtractedDataLoading] = useState(false)

  const loadDocument = async () => {
    if (!id) {
      setError('No document ID provided')
      setLoading(false)
      return
    }

    try {
      setError(null)
      const doc = await apiService.getDocument(id)
      setDocument(doc)
    } catch (err) {
      console.error('Failed to load document:', err)
      setError(err instanceof Error ? err.message : 'Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const loadExtractedData = async () => {
    if (!id) return

    try {
      setExtractedDataLoading(true)
      const data = await apiService.getDocumentExtractedData(id)
      setExtractedData(data)
    } catch (err) {
      console.error('Failed to load extracted data:', err)
      // Don't set error for extracted data - it might not exist yet
    } finally {
      setExtractedDataLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!id || !document) return
    
    if (!confirm(`Are you sure you want to delete "${document.filename}"?`)) {
      return
    }

    try {
      await apiService.deleteDocument(id)
      navigate('/documents')
    } catch (err) {
      console.error('Failed to delete document:', err)
      setError(err instanceof Error ? err.message : 'Failed to delete document')
    }
  }

  useEffect(() => {
    loadDocument()
  }, [id])

  useEffect(() => {
    if (document && document.processing_status === ProcessingStatus.COMPLETED) {
      loadExtractedData()
    }
  }, [document])

  const getStatusBadgeClass = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return 'badge-success'
      case ProcessingStatus.PROCESSING:
        return 'badge-info'
      case ProcessingStatus.PENDING:
        return 'badge-warning'
      case ProcessingStatus.FAILED:
        return 'badge-error'
      case ProcessingStatus.REVIEWING:
        return 'badge-info'
      case ProcessingStatus.APPROVED:
        return 'badge-success'
      case ProcessingStatus.REJECTED:
        return 'badge-error'
      default:
        return 'badge-default'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const formatCurrency = (amount: number | undefined, currency: string = 'USD') => {
    if (amount === undefined || amount === null) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount)
  }

  if (loading) {
    return (
      <div className="document-detail-page">
        <div className="page-header">
          <h1 className="page-title">Document Details</h1>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading document...</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="document-detail-page">
        <div className="page-header">
          <h1 className="page-title">Document Details</h1>
        </div>
        <div className="alert alert-error">
          <strong>Error:</strong> {error || 'Document not found'}
          <div className="actions">
            <button className="btn btn-sm" onClick={loadDocument}>
              Retry
            </button>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/documents')}>
              Back to Documents
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="document-detail-page">
      <div className="page-header">
        <div className="header-actions">
          <div>
            <h1 className="page-title">{document.filename}</h1>
            <p className="page-description">
              Document uploaded on {formatDate(document.upload_date)}
            </p>
          </div>
          <div className="actions">
            <button className="btn btn-secondary" onClick={() => navigate('/documents')}>
              ← Back to Documents
            </button>
            {document.processing_status === ProcessingStatus.COMPLETED && (
              <button className="btn btn-primary" onClick={() => navigate(`/review/${document.id}`)}>
                Start Review
              </button>
            )}
            <button className="btn btn-danger" onClick={handleDelete}>
              Delete
            </button>
          </div>
        </div>
      </div>

      <div className="document-grid">
        {/* Document Information Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Document Information</h2>
          </div>
          <div className="card-body">
            <div className="info-grid">
              <div className="info-item">
                <label>Filename:</label>
                <span>{document.filename}</span>
              </div>
              <div className="info-item">
                <label>File Type:</label>
                <span className="file-type">{document.file_type}</span>
              </div>
              <div className="info-item">
                <label>File Size:</label>
                <span>{formatFileSize(document.file_size)}</span>
              </div>
              <div className="info-item">
                <label>Upload Date:</label>
                <span>{formatDate(document.upload_date)}</span>
              </div>
              <div className="info-item">
                <label>Processing Status:</label>
                <span className={`badge ${getStatusBadgeClass(document.processing_status)}`}>
                  {document.processing_status}
                </span>
              </div>
              <div className="info-item">
                <label>Document ID:</label>
                <span className="document-id">{document.id}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Extracted Data Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Extracted Data</h2>
            {document.processing_status === ProcessingStatus.COMPLETED && (
              <button 
                className="btn btn-sm btn-secondary"
                onClick={loadExtractedData}
                disabled={extractedDataLoading}
              >
                {extractedDataLoading ? 'Refreshing...' : 'Refresh'}
              </button>
            )}
          </div>
          <div className="card-body">
            {(document.processing_status === ProcessingStatus.PENDING || 
              document.processing_status === ProcessingStatus.PROCESSING ||
              document.processing_status === ProcessingStatus.FAILED) && (
              <ProcessingStatusComponent
                documentId={document.id}
                initialStatus={{
                  id: document.id,
                  status: document.processing_status,
                  current_step: document.processing_status === ProcessingStatus.PENDING ? 'queued' : 
                               document.processing_status === ProcessingStatus.PROCESSING ? 'processing' : 'error',
                  error_message: document.processing_status === ProcessingStatus.FAILED ? 'Processing failed' : undefined
                }}
              />
            )}
            
            {document.processing_status === ProcessingStatus.COMPLETED && (
              <div>
                {extractedDataLoading ? (
                  <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading extracted data...</p>
                  </div>
                ) : extractedData ? (
                  <div className="extracted-data">
                    <div className="info-grid">
                      <div className="info-item">
                        <label>Vendor Name:</label>
                        <span>{extractedData.vendor_name || 'Not detected'}</span>
                      </div>
                      <div className="info-item">
                        <label>Vendor Address:</label>
                        <span className="address">{extractedData.vendor_address || 'Not detected'}</span>
                      </div>
                      <div className="info-item">
                        <label>Invoice Number:</label>
                        <span>{extractedData.invoice_number || 'Not detected'}</span>
                      </div>
                      <div className="info-item">
                        <label>Invoice Date:</label>
                        <span>{extractedData.invoice_date ? formatDate(extractedData.invoice_date) : 'Not detected'}</span>
                      </div>
                      <div className="info-item">
                        <label>Due Date:</label>
                        <span>{extractedData.due_date ? formatDate(extractedData.due_date) : 'Not detected'}</span>
                      </div>
                      <div className="info-item">
                        <label>Subtotal:</label>
                        <span>{formatCurrency(extractedData.subtotal_amount, extractedData.currency)}</span>
                      </div>
                      <div className="info-item">
                        <label>Tax Amount:</label>
                        <span>{formatCurrency(extractedData.tax_amount, extractedData.currency)}</span>
                      </div>
                      <div className="info-item">
                        <label>Total Amount:</label>
                        <span className="total-amount">{formatCurrency(extractedData.total_amount, extractedData.currency)}</span>
                      </div>
                      <div className="info-item">
                        <label>Currency:</label>
                        <span>{extractedData.currency}</span>
                      </div>
                      <div className="info-item">
                        <label>Extraction Confidence:</label>
                        <span className="confidence">
                          {(extractedData.extraction_confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="info-item">
                        <label>Extracted At:</label>
                        <span>{formatDate(extractedData.extracted_at)}</span>
                      </div>
                      <div className="info-item">
                        <label>Human Verified:</label>
                        <span className={`verification-status ${extractedData.is_human_verified ? 'verified' : 'unverified'}`}>
                          {extractedData.is_human_verified ? '✅ Verified' : '⏳ Pending Review'}
                        </span>
                      </div>
                    </div>

                    {/* Enhanced Quality Indicator */}
                    <div className="mt-4">
                      <QualityIndicator
                        ocrConfidence={(extractedData as any).ocr_confidence_avg}
                        llmConfidence={(extractedData as any).llm_confidence_score}
                        extractionMethod={(extractedData as any).extraction_method as ExtractionMethod || 'OCR_ONLY'}
                        fieldConfidenceScores={(extractedData as any).field_confidence_scores}
                        showComparison={true}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="status-message">
                    <p>No extracted data available. Processing may have failed.</p>
                    <button className="btn btn-sm btn-secondary" onClick={loadExtractedData}>
                      Retry Loading
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DocumentDetailPage