import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'
import { InvoiceDocument, ExtractedData, ReviewDecision, ProcessingStatus } from '../types/api'

interface ReviewFormData {
  vendor_name: string
  vendor_address: string
  invoice_number: string
  invoice_date: string
  due_date: string
  total_amount: string
  tax_amount: string
  subtotal_amount: string
  currency: string
  reviewer_notes: string
}

const ReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [document, setDocument] = useState<InvoiceDocument | null>(null)
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  
  const [reviewData, setReviewData] = useState<ReviewFormData>({
    vendor_name: '',
    vendor_address: '',
    invoice_number: '',
    invoice_date: '',
    due_date: '',
    total_amount: '',
    tax_amount: '',
    subtotal_amount: '',
    currency: 'USD',
    reviewer_notes: ''
  })

  const [hasChanges, setHasChanges] = useState(false)

  const loadDocumentAndData = async () => {
    if (!id) {
      setError('No document ID provided')
      setLoading(false)
      return
    }

    try {
      setError(null)
      
      // Load document
      const doc = await apiService.getDocument(id)
      setDocument(doc)

      // Load extracted data if available
      if (doc.processing_status === ProcessingStatus.COMPLETED) {
        try {
          const data = await apiService.getDocumentExtractedData(id)
          setExtractedData(data)
          
          // Initialize form with extracted data
          setReviewData({
            vendor_name: data.vendor_name || '',
            vendor_address: data.vendor_address || '',
            invoice_number: data.invoice_number || '',
            invoice_date: data.invoice_date || '',
            due_date: data.due_date || '',
            total_amount: data.total_amount?.toString() || '',
            tax_amount: data.tax_amount?.toString() || '',
            subtotal_amount: data.subtotal_amount?.toString() || '',
            currency: data.currency || 'USD',
            reviewer_notes: ''
          })
        } catch (err) {
          console.error('Failed to load extracted data:', err)
          // Continue without extracted data
        }
      }
    } catch (err) {
      console.error('Failed to load document:', err)
      setError(err instanceof Error ? err.message : 'Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof ReviewFormData, value: string) => {
    setReviewData(prev => ({
      ...prev,
      [field]: value
    }))
    setHasChanges(true)
  }

  const handleApprove = async () => {
    if (!id) return

    try {
      setSaving(true)
      
      // Start review session
      await apiService.startReviewSession(id, {
        review_started_at: new Date().toISOString(),
        review_completed_at: new Date().toISOString(),
        time_spent_seconds: 0, // TODO: Track actual time
        corrections_made: hasChanges ? 1 : 0,
        final_decision: ReviewDecision.APPROVED,
        reviewer_notes: reviewData.reviewer_notes
      })

      // Navigate back to document detail
      navigate(`/documents/${id}`)
    } catch (err) {
      console.error('Failed to approve document:', err)
      setError(err instanceof Error ? err.message : 'Failed to approve document')
    } finally {
      setSaving(false)
    }
  }

  const handleReject = async () => {
    if (!id) return

    if (!reviewData.reviewer_notes.trim()) {
      setError('Please provide notes when rejecting a document')
      return
    }

    try {
      setSaving(true)
      
      await apiService.startReviewSession(id, {
        review_started_at: new Date().toISOString(),
        review_completed_at: new Date().toISOString(),
        time_spent_seconds: 0,
        corrections_made: 0,
        final_decision: ReviewDecision.REJECTED,
        reviewer_notes: reviewData.reviewer_notes
      })

      navigate(`/documents/${id}`)
    } catch (err) {
      console.error('Failed to reject document:', err)
      setError(err instanceof Error ? err.message : 'Failed to reject document')
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    loadDocumentAndData()
  }, [id])

  const formatCurrency = (amount: number | undefined, currency: string = 'USD') => {
    if (amount === undefined || amount === null) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount)
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Not detected'
    return new Date(dateString).toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="review-page">
        <div className="page-header">
          <h1 className="page-title">Review Document</h1>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading document for review...</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="review-page">
        <div className="page-header">
          <h1 className="page-title">Review Document</h1>
        </div>
        <div className="alert alert-error">
          <strong>Error:</strong> {error || 'Document not found'}
          <div className="actions">
            <button className="btn btn-sm" onClick={loadDocumentAndData}>
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

  if (document.processing_status !== ProcessingStatus.COMPLETED) {
    return (
      <div className="review-page">
        <div className="page-header">
          <h1 className="page-title">Review Document</h1>
        </div>
        <div className="alert alert-warning">
          <strong>Document not ready for review</strong>
          <p>Document processing status: {document.processing_status}</p>
          <button className="btn btn-secondary" onClick={() => navigate(`/documents/${id}`)}>
            View Document Details
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="review-page">
      <div className="page-header">
        <div className="header-actions">
          <div>
            <h1 className="page-title">Review: {document.filename}</h1>
            <p className="page-description">
              Verify and correct the extracted invoice data below
            </p>
          </div>
          <div className="actions">
            <button className="btn btn-secondary" onClick={() => navigate(`/documents/${id}`)}>
              ← Back to Document
            </button>
          </div>
        </div>
      </div>

      <div className="review-container">
        {/* Original Document Info */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Original Document</h2>
          </div>
          <div className="card-body">
            <div className="document-info">
              <p><strong>Filename:</strong> {document.filename}</p>
              <p><strong>Type:</strong> {document.file_type}</p>
              <p><strong>Upload Date:</strong> {new Date(document.upload_date).toLocaleString()}</p>
              {extractedData && (
                <p><strong>Extraction Confidence:</strong> {(extractedData.extraction_confidence * 100).toFixed(1)}%</p>
              )}
            </div>
            
            {extractedData && (
              <div className="original-data">
                <h3>Original Extracted Data:</h3>
                <div className="original-values">
                  <div className="original-item">
                    <label>Vendor Name:</label>
                    <span>{extractedData.vendor_name || 'Not detected'}</span>
                  </div>
                  <div className="original-item">
                    <label>Invoice Number:</label>
                    <span>{extractedData.invoice_number || 'Not detected'}</span>
                  </div>
                  <div className="original-item">
                    <label>Total Amount:</label>
                    <span>{formatCurrency(extractedData.total_amount, extractedData.currency)}</span>
                  </div>
                  <div className="original-item">
                    <label>Invoice Date:</label>
                    <span>{formatDate(extractedData.invoice_date)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Editable Review Form */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Review & Corrections</h2>
            {hasChanges && (
              <span className="changes-indicator">📝 Modified</span>
            )}
          </div>
          <div className="card-body">
            <form className="review-form">
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Vendor Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={reviewData.vendor_name}
                    onChange={(e) => handleInputChange('vendor_name', e.target.value)}
                    placeholder="Enter vendor name"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Invoice Number</label>
                  <input
                    type="text"
                    className="form-control"
                    value={reviewData.invoice_number}
                    onChange={(e) => handleInputChange('invoice_number', e.target.value)}
                    placeholder="Enter invoice number"
                  />
                </div>

                <div className="form-group full-width">
                  <label className="form-label">Vendor Address</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={reviewData.vendor_address}
                    onChange={(e) => handleInputChange('vendor_address', e.target.value)}
                    placeholder="Enter vendor address"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Invoice Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={reviewData.invoice_date}
                    onChange={(e) => handleInputChange('invoice_date', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Due Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={reviewData.due_date}
                    onChange={(e) => handleInputChange('due_date', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select
                    className="form-control"
                    value={reviewData.currency}
                    onChange={(e) => handleInputChange('currency', e.target.value)}
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="CAD">CAD</option>
                    <option value="AUD">AUD</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Subtotal Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={reviewData.subtotal_amount}
                    onChange={(e) => handleInputChange('subtotal_amount', e.target.value)}
                    placeholder="0.00"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Tax Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={reviewData.tax_amount}
                    onChange={(e) => handleInputChange('tax_amount', e.target.value)}
                    placeholder="0.00"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Total Amount</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={reviewData.total_amount}
                    onChange={(e) => handleInputChange('total_amount', e.target.value)}
                    placeholder="0.00"
                  />
                </div>

                <div className="form-group full-width">
                  <label className="form-label">Reviewer Notes</label>
                  <textarea
                    className="form-control"
                    rows={4}
                    value={reviewData.reviewer_notes}
                    onChange={(e) => handleInputChange('reviewer_notes', e.target.value)}
                    placeholder="Add any notes about this review..."
                  />
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="review-actions">
        <div className="action-buttons">
          <button
            className="btn btn-success"
            onClick={handleApprove}
            disabled={saving}
          >
            {saving ? 'Saving...' : '✅ Approve'}
          </button>
          <button
            className="btn btn-danger"
            onClick={handleReject}
            disabled={saving}
          >
            {saving ? 'Saving...' : '❌ Reject'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate(`/documents/${id}`)}
            disabled={saving}
          >
            Cancel
          </button>
        </div>
        
        {hasChanges && (
          <div className="changes-warning">
            <p>⚠️ You have unsaved changes. They will be saved when you approve or reject.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReviewPage