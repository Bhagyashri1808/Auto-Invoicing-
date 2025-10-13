import React from 'react'
import { useParams } from 'react-router-dom'

const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="document-detail-page">
      <div className="page-header">
        <h1 className="page-title">Document Details</h1>
        <p className="page-description">
          View detailed information about document {id}.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Document Information</h2>
        </div>
        <div className="card-body">
          <p>Document detail component will be implemented here.</p>
          <p>This will show the original document, extracted data, processing status, and review options.</p>
        </div>
      </div>
    </div>
  )
}

export default DocumentDetailPage