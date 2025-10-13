import React from 'react'

const ConfigurationPage: React.FC = () => {
  return (
    <div className="configuration-page">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-description">
          Configure OCR processing and application settings.
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Processing Configuration</h2>
        </div>
        <div className="card-body">
          <p>Configuration component will be implemented here.</p>
          <p>This will allow users to configure OCR confidence thresholds, processing modes, and other settings.</p>
        </div>
      </div>
    </div>
  )
}

export default ConfigurationPage