import React from 'react'
import { useParams } from 'react-router-dom'

const ReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="review-page">
      <div className="page-header">
        <h1 className="page-title">Review Document</h1>
        <p className="page-description">
          Human-in-the-loop review for document {id}.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Side-by-Side Review</h2>
        </div>
        <div className="card-body">
          <p>HITL review component will be implemented here.</p>
          <p>This will show the original document side-by-side with extracted data for review and correction.</p>
        </div>
      </div>
    </div>
  )
}

export default ReviewPage