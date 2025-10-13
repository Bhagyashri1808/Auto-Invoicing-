import React from 'react'

const DocumentListPage: React.FC = () => {
  return (
    <div className="document-list-page">
      <div className="page-header">
        <h1 className="page-title">Documents</h1>
        <p className="page-description">
          View and manage uploaded invoice documents.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Document List</h2>
        </div>
        <div className="card-body">
          <p>Document list component will be implemented here.</p>
          <p>This will show all uploaded documents with their processing status, extracted data, and review options.</p>
        </div>
      </div>
    </div>
  )
}

export default DocumentListPage