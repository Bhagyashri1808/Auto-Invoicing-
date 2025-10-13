import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import DocumentListPage from './pages/DocumentListPage'
import DocumentDetailPage from './pages/DocumentDetailPage'
import ReviewPage from './pages/ReviewPage'
import ConfigurationPage from './pages/ConfigurationPage'
import Navigation from './components/Navigation'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/documents" element={<DocumentListPage />} />
            <Route path="/documents/:id" element={<DocumentDetailPage />} />
            <Route path="/review/:id" element={<ReviewPage />} />
            <Route path="/config" element={<ConfigurationPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App