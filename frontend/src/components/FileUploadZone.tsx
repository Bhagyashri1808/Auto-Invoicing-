import React, { useCallback, useState, useRef } from 'react'

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void
  disabled?: boolean
  multiple?: boolean
  acceptedTypes?: string[]
  maxFileSize?: number // in MB
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFilesSelected,
  disabled = false,
  multiple = true,
  acceptedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif'],
  maxFileSize = 50
}) => {
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    // Check file size
    const maxSizeBytes = maxFileSize * 1024 * 1024
    if (file.size > maxSizeBytes) {
      return `File "${file.name}" is too large. Maximum size is ${maxFileSize}MB.`
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!acceptedTypes.includes(fileExtension)) {
      return `File "${file.name}" has an unsupported format. Accepted formats: ${acceptedTypes.join(', ')}`
    }

    return null
  }

  const validateFiles = (files: File[]): { validFiles: File[], errors: string[] } => {
    const validFiles: File[] = []
    const errors: string[] = []

    for (const file of files) {
      const error = validateFile(file)
      if (error) {
        errors.push(error)
      } else {
        validFiles.push(file)
      }
    }

    return { validFiles, errors }
  }

  const handleFiles = useCallback((fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return

    const files = Array.from(fileList)
    const { validFiles, errors } = validateFiles(files)

    if (errors.length > 0) {
      setError(errors.join('\n'))
      return
    }

    setError(null)
    onFilesSelected(validFiles)
  }, [onFilesSelected, acceptedTypes, maxFileSize])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (disabled) return

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [disabled])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (disabled) return

    const files = e.dataTransfer.files
    handleFiles(files)
  }, [disabled, handleFiles])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (disabled) return

    const files = e.target.files
    handleFiles(files)
    
    // Reset the input value so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [disabled, handleFiles])

  const handleClick = useCallback(() => {
    if (disabled) return
    fileInputRef.current?.click()
  }, [disabled])

  const dismissError = () => {
    setError(null)
  }

  return (
    <div className="file-upload-zone">
      {error && (
        <div className="alert alert-danger">
          <div className="alert-content">
            <strong>Upload Error:</strong>
            <pre>{error}</pre>
          </div>
          <button 
            className="alert-dismiss"
            onClick={dismissError}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}
      
      <div
        className={`upload-dropzone ${dragActive ? 'drag-active' : ''} ${disabled ? 'disabled' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={acceptedTypes.join(',')}
          onChange={handleChange}
          disabled={disabled}
          style={{ display: 'none' }}
        />
        
        <div className="upload-content">
          <div className="upload-icon">
            📁
          </div>
          <h3 className="upload-title">
            {dragActive ? 'Drop files here' : 'Drag & drop files here'}
          </h3>
          <p className="upload-subtitle">
            or <span className="upload-link">browse files</span>
          </p>
          <div className="upload-hints">
            <p>Supported formats: {acceptedTypes.join(', ')}</p>
            <p>Maximum file size: {maxFileSize}MB</p>
            {multiple && <p>Multiple files allowed</p>}
          </div>
        </div>
      </div>

      <style jsx>{`
        .file-upload-zone {
          width: 100%;
        }

        .alert {
          padding: 1rem;
          margin-bottom: 1rem;
          border-radius: 4px;
          position: relative;
        }

        .alert-danger {
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          color: #721c24;
        }

        .alert-content {
          margin-right: 2rem;
        }

        .alert-content pre {
          white-space: pre-wrap;
          margin-top: 0.5rem;
          font-family: inherit;
        }

        .alert-dismiss {
          position: absolute;
          top: 0.5rem;
          right: 0.75rem;
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: inherit;
        }

        .upload-dropzone {
          border: 2px dashed #ced4da;
          border-radius: 8px;
          padding: 3rem 2rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
          background-color: #f8f9fa;
        }

        .upload-dropzone:hover:not(.disabled) {
          border-color: #007bff;
          background-color: #e3f2fd;
        }

        .upload-dropzone.drag-active {
          border-color: #007bff;
          background-color: #e3f2fd;
          transform: scale(1.02);
        }

        .upload-dropzone.disabled {
          opacity: 0.6;
          cursor: not-allowed;
          background-color: #e9ecef;
        }

        .upload-content {
          pointer-events: none;
        }

        .upload-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .upload-title {
          font-size: 1.5rem;
          margin-bottom: 0.5rem;
          color: #343a40;
        }

        .upload-subtitle {
          font-size: 1rem;
          color: #6c757d;
          margin-bottom: 1rem;
        }

        .upload-link {
          color: #007bff;
          text-decoration: underline;
        }

        .upload-hints {
          font-size: 0.875rem;
          color: #6c757d;
        }

        .upload-hints p {
          margin: 0.25rem 0;
        }

        @media (prefers-color-scheme: dark) {
          .alert-danger {
            background-color: #2d1b1e;
            border-color: #842029;
            color: #ea868f;
          }

          .upload-dropzone {
            border-color: #444;
            background-color: #2d2d2d;
          }

          .upload-dropzone:hover:not(.disabled) {
            border-color: #007bff;
            background-color: #1a1a2e;
          }

          .upload-dropzone.drag-active {
            background-color: #1a1a2e;
          }

          .upload-dropzone.disabled {
            background-color: #1a1a1a;
          }

          .upload-title {
            color: #ffffff;
          }

          .upload-subtitle {
            color: #aaa;
          }

          .upload-hints {
            color: #aaa;
          }
        }
      `}</style>
    </div>
  )
}

export default FileUploadZone