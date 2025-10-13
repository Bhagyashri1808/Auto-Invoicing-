# Development Quickstart Guide

**Feature**: Invoice Automation with HITL Review  
**Date**: 2025-01-10  
**Stack**: React/Vite + Python/FastAPI + SQLite

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git

## Development Setup

### 1. Environment Setup

```bash
# Clone repository (when available)
git clone <repository-url>
cd invoice-automation

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install Node dependencies
cd ../frontend
npm install
```

### 2. Database Setup

```bash
# From backend directory
python -m alembic upgrade head  # Run database migrations
python scripts/seed_config.py   # Set default configuration
```

### 3. Start Development Servers

**Terminal 1 - Backend**:
```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

**Access Application**: http://localhost:5173

## Key Development Workflows

### 1. Document Upload & Processing Flow

**User Action**: Upload invoice file
**Backend Flow**:
1. `POST /invoices` - File validation and storage
2. Create `InvoiceDocument` record
3. Queue `ProcessingJob` 
4. OCR service extracts data → `ExtractedData` record
5. Update status to `COMPLETED`

**Frontend Flow**:
1. File upload component
2. Progress indicator during processing
3. Redirect to review interface when complete

### 2. HITL Review Flow

**User Action**: Review extracted data
**Backend Flow**:
1. `POST /invoices/{id}/review` - Start review session
2. `PUT /invoices/{id}/extracted-data` - Save corrections
3. `PUT /invoices/{id}/review` - Complete with decision

**Frontend Flow**:
1. Side-by-side comparison component
2. Editable data fields with confidence indicators
3. Approval/rejection workflow

### 3. Batch Processing Flow

**User Action**: Upload multiple files
**Backend Flow**:
1. Multiple `POST /invoices` calls
2. Queue management based on configuration
3. Sequential or parallel processing
4. Status updates via polling

**Frontend Flow**:
1. Bulk upload interface
2. Queue status dashboard
3. Progress tracking per document

## API Integration Patterns

### Authentication
Single-user application - no authentication required.

### Error Handling
All API responses follow consistent error format:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "File size exceeds limit",
  "details": {"max_size": "50MB", "received": "75MB"}
}
```

### File Upload
Use multipart/form-data with file size validation:
```typescript
const formData = new FormData();
formData.append('file', file);
const response = await fetch('/invoices', {
  method: 'POST',
  body: formData
});
```

### Real-time Updates
Polling-based updates for processing status:
```typescript
const pollStatus = async (invoiceId: string) => {
  const response = await fetch(`/invoices/${invoiceId}`);
  const invoice = await response.json();
  if (invoice.processing_status === 'COMPLETED') {
    // Redirect to review
  } else {
    setTimeout(() => pollStatus(invoiceId), 2000);
  }
};
```

## Database Operations

### Common Queries

**Get invoices needing review**:
```sql
SELECT * FROM invoice_documents 
WHERE processing_status = 'COMPLETED'
ORDER BY upload_date ASC;
```

**Get extraction accuracy metrics**:
```sql
SELECT AVG(extraction_confidence) as avg_confidence,
       COUNT(*) as total_extractions
FROM extracted_data 
WHERE created_at >= datetime('now', '-7 days');
```

**Get review performance**:
```sql
SELECT AVG(time_spent_seconds) as avg_review_time,
       AVG(corrections_made) as avg_corrections
FROM review_sessions 
WHERE review_completed_at IS NOT NULL;
```

## Testing Strategy

### Backend Tests

**Unit Tests** (pytest):
```bash
cd backend
pytest tests/unit/ -v
```

**Integration Tests**:
```bash
pytest tests/integration/ -v
```

**Contract Tests**:
```bash
pytest tests/contract/ -v
```

### Frontend Tests

**Component Tests** (Vitest):
```bash
cd frontend
npm run test
```

**E2E Tests**:
```bash
npm run test:e2e
```

## Configuration Management

### Environment Variables

**Backend** (.env):
```
DATABASE_URL=sqlite:///./shared/database/invoices.db
STORAGE_PATH=./shared/storage/
OCR_TESSERACT_PATH=/usr/bin/tesseract
LOG_LEVEL=INFO
```

**Frontend** (.env.local):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_MAX_FILE_SIZE_MB=50
```

### Runtime Configuration

Update via API:
```bash
curl -X PUT http://localhost:8000/processing/config \
  -H "Content-Type: application/json" \
  -d '{"ocr_confidence_threshold": 0.8, "processing_mode": "PARALLEL"}'
```

## Common Issues & Solutions

### OCR Not Working
- Verify Tesseract installation: `tesseract --version`
- Check file permissions on uploaded documents
- Validate image preprocessing pipeline

### Performance Issues
- Monitor database query performance
- Check file storage disk space
- Tune OCR processing parameters

### UI Responsiveness
- Implement loading states for long operations
- Use debouncing for search/filter inputs
- Optimize re-renders with React.memo

## Production Considerations

### Database
- Regular SQLite VACUUM operations
- Backup strategy for database and files
- Monitor disk space usage

### Security
- File type validation beyond extensions
- Virus scanning for uploaded files
- Input sanitization for all user data

### Monitoring
- Log all processing operations
- Track extraction accuracy trends
- Monitor processing queue depth