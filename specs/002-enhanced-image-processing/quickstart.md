# Development Quickstart Guide

**Feature**: Enhanced Image Processing with Local LLM Integration  
**Date**: 2025-01-23  
**Stack**: React/Vite + Python/FastAPI + Llama 3.2 + OpenCV

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- **Hardware**: Minimum 8GB RAM, 4-core CPU
- **Disk Space**: 5GB free (for Llama 3.2 model)

## Environment Setup

### 1. Repository Setup

```bash
# Navigate to project root (already cloned)
cd /Users/bhagyashri/Spec-Kit

# Ensure on correct feature branch
git checkout 002-enhanced-image-processing

# Verify branch status
git status
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create/activate Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install existing dependencies
pip install -r requirements.txt

# Install additional dependencies for enhanced processing
pip install opencv-python==4.8.1.78
pip install aiohttp==3.9.1
pip install psutil==5.9.6
pip install tenacity==8.2.3
```

### 3. Ollama and Llama 3.2 Setup

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Pull Llama 3.2 3B model (recommended for 8GB RAM)
ollama pull llama3.2:3b

# Verify model installation
ollama list

# Test model functionality
ollama run llama3.2:3b "Hello, can you extract invoice data?"
```

### 4. Database Migration

```bash
# From backend directory
# Run existing migrations first
python -m alembic upgrade head

# Generate migration for enhanced processing
python -m alembic revision --autogenerate -m "Add enhanced processing tables"

# Apply new migrations
python -m alembic upgrade head

# Seed default preprocessing configuration
python scripts/seed_preprocessing_config.py
```

### 5. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies (already done, but verify)
npm install

# Install additional dependencies for enhanced UI
npm install @types/uuid
npm install recharts  # For performance metrics visualization
```

## Development Workflows

### 1. Enhanced Invoice Processing Flow

**Backend Flow**:
1. `POST /invoices` - File upload with preprocessing options
2. `ImagePreprocessor.preprocess()` - OpenCV enhancement
3. `LLMClient.extract_data()` - Llama 3.2 API call
4. `FallbackManager.handle_timeout()` - OCR fallback if needed
5. `ExtractedData` validation and storage

**Frontend Flow**:
1. Enhanced file upload component with preprocessing options
2. Real-time processing status with LLM progress indicators
3. Results comparison (OCR vs LLM) in review interface
4. Configuration panel for preprocessing parameters

### 2. Start Development Servers

**Terminal 1 - Ollama Service**:
```bash
# Ensure Ollama is running
ollama serve
# Keep this terminal open
```

**Terminal 2 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Terminal 3 - Frontend**:
```bash
cd frontend
npm run dev
```

**Access Application**: http://localhost:5173

### 3. Enhanced Processing Configuration

**Create Custom Preprocessing Config**:
```bash
curl -X POST http://localhost:8000/preprocessing/configurations \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "COMBINED",
    "target_width": 1200,
    "threshold_block_size": 15,
    "threshold_constant": 8.0,
    "is_default": false
  }'
```

**Test LLM Health**:
```bash
curl http://localhost:8000/llm/health
```

**Upload with Enhanced Processing**:
```bash
curl -X POST http://localhost:8000/invoices \
  -F "file=@sample_invoice.pdf" \
  -F "enable_preprocessing=true" \
  -F "enable_llm_processing=true" \
  -F "fallback_to_ocr=true"
```

## Key Development Components

### 1. Backend Services

**New Service Files**:
```
backend/src/services/
├── image_preprocessor.py    # OpenCV preprocessing operations
├── llm_client.py           # Llama 3.2 REST API integration
├── enhanced_extractor.py   # Orchestrates preprocessing + LLM
└── fallback_manager.py     # Timeout and fallback handling
```

**Enhanced API Endpoints**:
```
POST /invoices                              # Upload with preprocessing options
GET  /preprocessing/configurations          # List preprocessing configs
POST /preprocessing/configurations          # Create new config
GET  /llm/health                           # Check LLM service status
GET  /llm/models                           # List available models
GET  /processing/metrics                   # Performance analytics
```

### 2. Frontend Components

**New Component Files**:
```
frontend/src/components/
├── PreprocessingConfig.tsx  # Parameter configuration UI
├── ProcessingStatus.tsx     # Enhanced status with LLM progress
├── QualityIndicator.tsx     # Confidence score visualization
└── MetricsDashboard.tsx     # Processing performance charts
```

**Enhanced Pages**:
- `UploadPage.tsx` - Added preprocessing options
- `ReviewPage.tsx` - LLM vs OCR comparison view
- `ConfigurationPage.tsx` - Preprocessing parameter management

### 3. Processing Pipeline Testing

**Unit Test Example**:
```bash
# Test image preprocessing
cd backend
python -m pytest tests/unit/test_image_preprocessor.py -v

# Test LLM integration
python -m pytest tests/unit/test_llm_client.py -v

# Test complete pipeline
python -m pytest tests/integration/test_enhanced_extraction.py -v
```

**Frontend Component Testing**:
```bash
# Test preprocessing configuration UI
cd frontend
npm run test -- PreprocessingConfig.test.tsx

# Test processing status display
npm run test -- ProcessingStatus.test.tsx
```

## API Integration Patterns

### 1. Enhanced Processing Request

```typescript
// Frontend API call with preprocessing options
const uploadWithEnhancedProcessing = async (file: File, options: ProcessingOptions) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('enable_preprocessing', options.enablePreprocessing.toString());
  formData.append('enable_llm_processing', options.enableLLM.toString());
  
  if (options.configId) {
    formData.append('preprocessing_config_id', options.configId);
  }
  
  const response = await fetch('/api/invoices', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

### 2. Real-time Processing Status

```typescript
// Poll for enhanced processing status
const pollProcessingStatus = async (invoiceId: string) => {
  const response = await fetch(`/api/invoices/${invoiceId}?include_processing_details=true`);
  const invoice = await response.json();
  
  if (invoice.processing_status === 'PROCESSING') {
    // Show LLM processing progress
    if (invoice.llm_processing_job?.llm_started_at) {
      updateProgressIndicator('LLM processing in progress...');
    } else {
      updateProgressIndicator('Preprocessing image...');
    }
    
    setTimeout(() => pollProcessingStatus(invoiceId), 2000);
  } else if (invoice.processing_status === 'COMPLETED') {
    // Show results with extraction method
    displayResults(invoice.extracted_data);
  }
};
```

### 3. Error Handling with Fallback Context

```typescript
// Enhanced error handling
const handleProcessingError = (error: ProcessingError) => {
  if (error.processing_context?.fallback_used) {
    showWarning('LLM processing failed, OCR results displayed');
  } else if (error.processing_context?.preprocessing_attempted === false) {
    showError('Image preprocessing failed - check file format');
  } else {
    showError(`Processing failed: ${error.message}`);
  }
};
```

## Configuration Management

### 1. Environment Variables

**Backend** (.env):
```
# Existing settings
DATABASE_URL=sqlite:///./shared/database/invoices.db
STORAGE_PATH=./shared/storage/

# Enhanced processing settings
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL_NAME=llama3.2:3b
LLM_TIMEOUT_SECONDS=60
MEMORY_LIMIT_MB=2048
PREPROCESSING_ENABLED=true
ENABLE_PERFORMANCE_METRICS=true
TEMP_FILE_CLEANUP_ENABLED=true
```

**Frontend** (.env.local):
```
# Existing settings
VITE_API_BASE_URL=http://localhost:8000

# Enhanced processing settings
VITE_ENABLE_PREPROCESSING_CONFIG=true
VITE_ENABLE_METRICS_DASHBOARD=true
VITE_DEFAULT_PROCESSING_TIMEOUT=65000
```

### 2. Runtime Configuration Updates

```bash
# Update preprocessing defaults
curl -X PUT http://localhost:8000/processing/config \
  -H "Content-Type: application/json" \
  -d '{
    "preprocessing_enabled": true,
    "llm_model_name": "llama3.2:3b",
    "llm_timeout_seconds": 60,
    "memory_limit_mb": 2048
  }'
```

## Monitoring and Debugging

### 1. Processing Metrics

```bash
# View processing performance
curl "http://localhost:8000/processing/metrics?date_from=2025-01-20&extraction_method=LLM_PRIMARY"
```

### 2. LLM Service Monitoring

```bash
# Check LLM health
curl http://localhost:8000/llm/health

# View available models
curl http://localhost:8000/llm/models
```

### 3. Debug Logging

**Backend** - Enable detailed logging:
```python
# In src/main.py
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("enhanced_processing")
```

**Frontend** - Processing debug info:
```typescript
// Enable processing debug mode
localStorage.setItem('debug_processing', 'true');
```

## Common Issues & Solutions

### 1. Ollama Connection Issues
```bash
# Restart Ollama service
killall ollama
ollama serve &

# Verify model is loaded
ollama list
```

### 2. Memory Limit Exceeded
```bash
# Monitor memory usage
top -p $(pgrep -f "uvicorn\|ollama")

# Reduce image size in preprocessing config
# or switch to smaller model (llama3.2:1b)
```

### 3. Processing Timeouts
- Check LLM service health: `curl http://localhost:8000/llm/health`
- Verify timeout settings in configuration
- Review processing metrics for performance trends

### 4. Frontend Build Issues
```bash
# Clear build cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Production Considerations

### 1. Performance Optimization
- Use model quantization for memory efficiency
- Implement processing queue for multiple documents
- Configure appropriate worker processes
- Monitor disk space for temporary files

### 2. Resource Management
- Set up proper memory limits in Docker/systemd
- Configure log rotation for processing logs
- Implement health checks for all services
- Monitor processing metrics and set up alerts

### 3. Security
- Validate all preprocessing parameters
- Sanitize temporary file paths
- Implement rate limiting for API endpoints
- Secure LLM service access

This quickstart guide provides the foundation for developing enhanced invoice processing with local LLM integration while maintaining compatibility with the existing application architecture.