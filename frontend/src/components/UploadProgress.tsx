import React from 'react'
import { FileUploadProgress } from '../types/api'

interface UploadProgressProps {
  uploads: FileUploadProgress[]
}

const UploadProgress: React.FC<UploadProgressProps> = ({ uploads }) => {
  const getStatusIcon = (status: FileUploadProgress['status']) => {
    switch (status) {
      case 'uploading':
        return '⏳'
      case 'processing':
        return '⚙️'
      case 'completed':
        return '✅'
      case 'error':
        return '❌'
      default:
        return '📄'
    }
  }

  const getStatusText = (status: FileUploadProgress['status']) => {
    switch (status) {
      case 'uploading':
        return 'Uploading...'
      case 'processing':
        return 'Processing...'
      case 'completed':
        return 'Completed'
      case 'error':
        return 'Failed'
      default:
        return 'Unknown'
    }
  }

  const getStatusColor = (status: FileUploadProgress['status']) => {
    switch (status) {
      case 'uploading':
        return '#007bff'
      case 'processing':
        return '#ffc107'
      case 'completed':
        return '#28a745'
      case 'error':
        return '#dc3545'
      default:
        return '#6c757d'
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (uploads.length === 0) {
    return null
  }

  return (
    <div className="upload-progress">
      {uploads.map((upload, index) => (
        <div key={index} className="upload-item">
          <div className="upload-item-header">
            <div className="file-info">
              <span className="status-icon">
                {getStatusIcon(upload.status)}
              </span>
              <div className="file-details">
                <div className="file-name">{upload.file.name}</div>
                <div className="file-meta">
                  {formatFileSize(upload.file.size)} • {upload.file.type || 'Unknown type'}
                </div>
              </div>
            </div>
            <div className="status-info">
              <span 
                className="status-text"
                style={{ color: getStatusColor(upload.status) }}
              >
                {getStatusText(upload.status)}
              </span>
              {upload.status !== 'error' && (
                <span className="progress-percentage">
                  {upload.progress}%
                </span>
              )}
            </div>
          </div>

          {upload.status !== 'error' && (
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ 
                  width: `${upload.progress}%`,
                  backgroundColor: getStatusColor(upload.status)
                }}
              />
            </div>
          )}

          {upload.error && (
            <div className="error-message">
              {upload.error}
            </div>
          )}
        </div>
      ))}

      <style jsx>{`
        .upload-progress {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .upload-item {
          border: 1px solid #dee2e6;
          border-radius: 4px;
          padding: 1rem;
          background-color: white;
        }

        .upload-item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .file-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex: 1;
        }

        .status-icon {
          font-size: 1.25rem;
        }

        .file-details {
          flex: 1;
        }

        .file-name {
          font-weight: 500;
          color: #343a40;
          margin-bottom: 0.25rem;
        }

        .file-meta {
          font-size: 0.875rem;
          color: #6c757d;
        }

        .status-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 0.25rem;
        }

        .status-text {
          font-weight: 500;
          font-size: 0.875rem;
        }

        .progress-percentage {
          font-size: 0.75rem;
          color: #6c757d;
        }

        .progress-bar {
          width: 100%;
          height: 6px;
          background-color: #e9ecef;
          border-radius: 3px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.3s ease, background-color 0.3s ease;
        }

        .error-message {
          margin-top: 0.5rem;
          padding: 0.5rem;
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 4px;
          color: #721c24;
          font-size: 0.875rem;
        }

        @media (prefers-color-scheme: dark) {
          .upload-item {
            background-color: #1e1e1e;
            border-color: #333;
          }

          .file-name {
            color: #ffffff;
          }

          .file-meta {
            color: #aaa;
          }

          .progress-percentage {
            color: #aaa;
          }

          .progress-bar {
            background-color: #333;
          }

          .error-message {
            background-color: #2d1b1e;
            border-color: #842029;
            color: #ea868f;
          }
        }

        @media (max-width: 768px) {
          .upload-item-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
          }

          .status-info {
            align-items: flex-start;
            flex-direction: row;
            gap: 1rem;
          }
        }
      `}</style>
    </div>
  )
}

export default UploadProgress