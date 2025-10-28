import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const Navigation: React.FC = () => {
  const location = useLocation()

  const isActive = (path: string) => {
    if (path === '/documents') {
      return location.pathname === '/documents' || location.pathname.startsWith('/documents/')
    }
    if (path === '/review') {
      return location.pathname.startsWith('/review/')
    }
    return location.pathname === path
  }

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          Invoice Automation
        </Link>
        <ul className="nav-links">
          <li>
            <Link 
              to="/upload" 
              className={isActive('/upload') ? 'active' : ''}
            >
              Upload
            </Link>
          </li>
          <li>
            <Link 
              to="/documents" 
              className={isActive('/documents') ? 'active' : ''}
            >
              Documents
            </Link>
          </li>
          <li>
            <Link 
              to="/config" 
              className={isActive('/config') ? 'active' : ''}
            >
              Settings
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  )
}

export default Navigation