import React, { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { InvoiceDocument, ProcessingStatus } from '../types/api'

const DocumentListPage: React.FC = () => {
  const [documents, setDocuments] = useState<InvoiceDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<ProcessingStatus | 'ALL'>('ALL')
  const [refreshing, setRefreshing] = useState(false)

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      const filter = statusFilter === 'ALL' ? undefined : statusFilter
      const docs = await apiService.listDocuments(0, 100, filter)
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to load documents:', err)
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const refreshDocuments = async () => {
    setRefreshing(true)
    await loadDocuments()
    setRefreshing(false)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      await apiService.deleteDocument(id)
      setDocuments(docs => docs.filter(doc => doc.id !== id))
    } catch (err) {
      console.error('Failed to delete document:', err)
      setError(err instanceof Error ? err.message : 'Failed to delete document')
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [statusFilter])

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

  if (loading) {
    return (
      <div className="document-list-page">
        <div className="page-header">
          <h1 className="page-title">Documents</h1>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading documents...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="document-list-page">
      <div className="page-header">
        <h1 className="page-title">Documents</h1>
        <p className="page-description">
          View and manage uploaded invoice documents.
        </p>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
          <button className="btn btn-sm" onClick={loadDocuments}>
            Retry
          </button>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <div className="header-actions">
            <h2 className="card-title">Document List ({documents.length})</h2>
            <div className="actions">
              <select 
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value as ProcessingStatus | 'ALL')}
                className="select"
              >
                <option value="ALL">All Status</option>
                <option value={ProcessingStatus.PENDING}>Pending</option>
                <option value={ProcessingStatus.PROCESSING}>Processing</option>
                <option value={ProcessingStatus.COMPLETED}>Completed</option>
                <option value={ProcessingStatus.FAILED}>Failed</option>
                <option value={ProcessingStatus.REVIEWING}>Reviewing</option>
                <option value={ProcessingStatus.APPROVED}>Approved</option>
                <option value={ProcessingStatus.REJECTED}>Rejected</option>
              </select>
              <button 
                className="btn btn-secondary"
                onClick={refreshDocuments}
                disabled={refreshing}
              >
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>
        </div>
        
        <div className="card-body">
          {documents.length === 0 ? (
            <div className="empty-state">
              <p>No documents found.</p>
              <p>Upload your first invoice to get started.</p>
              <a href="/upload" className="btn btn-primary">Upload Document</a>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Upload Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>
                        <div className="file-info">
                          <strong>{doc.filename}</strong>
                        </div>
                      </td>
                      <td>
                        <span className="file-type">{doc.file_type}</span>
                      </td>
                      <td>{formatFileSize(doc.file_size)}</td>
                      <td>{formatDate(doc.upload_date)}</td>
                      <td>
                        <span className={`badge ${getStatusBadgeClass(doc.processing_status)}`}>
                          {doc.processing_status}
                        </span>
                      </td>
                      <td>
                        <div className="action-buttons">
                          <a 
                            href={`/documents/${doc.id}`}
                            className="btn btn-sm btn-primary"
                          >
                            View
                          </a>
                          {doc.processing_status === ProcessingStatus.COMPLETED && (
                            <a 
                              href={`/review/${doc.id}`}
                              className="btn btn-sm btn-secondary"
                            >
                              Review
                            </a>
                          )}
                          {doc.processing_status === ProcessingStatus.FAILED && (
                            <button 
                              className="btn btn-sm btn-warning"
                              onClick={() => window.location.reload()} // TODO: Implement retry
                            >
                              Retry
                            </button>
                          )}
                          <button 
                            className="btn btn-sm btn-danger"
                            onClick={() => handleDelete(doc.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DocumentListPage