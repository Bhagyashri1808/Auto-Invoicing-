# Troubleshooting Guide - Invoice Automation Setup

This document contains all problems encountered during development and their solutions, providing a complete reference for setup issues and fixes.

## 📋 Table of Contents

1. [Python Dependencies Issues](#python-dependencies-issues)
2. [Import Path Problems](#import-path-problems) 
3. [Pydantic Version Compatibility](#pydantic-version-compatibility)
4. [Missing Schema Classes](#missing-schema-classes)
5. [OCR and System Dependencies](#ocr-and-system-dependencies)
6. [Database and Model Issues](#database-and-model-issues)
7. [Quick Setup Commands](#quick-setup-commands)

---

## 🐛 Python Dependencies Issues

### Problem: pip install subprocess-exited-with-error
```bash
error: subprocess-exited-with-error
note: This error originates from a subprocess, and is likely not a problem with pip.
```

### Root Cause:
Compilation issues with certain packages, particularly OpenCV and its dependencies requiring system libraries.

### Solution:
1. **Use headless versions** to avoid GUI dependencies:
   ```bash
   # Instead of opencv-python
   pip install opencv-python-headless
   ```

2. **Install system dependencies first**:
   ```bash
   # macOS with Homebrew
   brew install tesseract libmagic
   ```

3. **Updated requirements.txt** with compatible versions:
   ```txt
   # Core FastAPI dependencies
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   
   # Image processing (headless versions)
   Pillow>=10.0.0
   opencv-python-headless>=4.8.0
   pytesseract>=0.3.10
   PyMuPDF  # Added missing PDF processing
   
   # Make python-magic optional in code
   python-magic  # Graceful fallback if fails
   ```

4. **Install in correct order** to avoid conflicts:
   ```bash
   # Step 1: Upgrade pip and tools
   pip install --upgrade pip wheel setuptools
   
   # Step 2: Core dependencies
   pip install fastapi "uvicorn[standard]" sqlalchemy alembic pydantic
   
   # Step 3: File handling
   pip install python-multipart httpx pytest pytest-asyncio
   
   # Step 4: Image processing (most likely to fail)
   pip install Pillow opencv-python-headless pytesseract PyMuPDF python-magic
   ```

### Code Changes Made:
Made python-magic optional in `file_upload.py`:
```python
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

def validate_file_content(self, file_content: bytes, expected_type: FileType) -> bool:
    if not MAGIC_AVAILABLE:
        # Graceful fallback - trust extension validation
        return True
    # ... rest of magic-based validation
```

---

## 🔗 Import Path Problems

### Problem: Relative import beyond top-level package
```bash
ImportError: attempted relative import beyond top-level package
```

### Root Cause:
Incorrect relative imports in model files when running as a module.

### Files Affected:
- `/backend/src/models/base.py`

### Solution:
Changed relative imports to absolute imports:
```python
# Before (causing error)
from ..database.config import Base

# After (working)
from database.config import Base
```

### Prevention:
When creating new model files, use absolute imports from the `src` directory as the root.

---

## 📦 Pydantic Version Compatibility

### Problem: Pydantic v2 breaking changes
```bash
pydantic.errors.PydanticUserError: `regex` is removed. use `pattern` instead
```

### Root Cause:
Pydantic v2 removed the `regex` parameter in favor of `pattern`.

### Files Affected:
- `/backend/src/models/schemas.py` line 225

### Solution:
Updated Field validation syntax:
```python
# Before (Pydantic v1 syntax)
format: str = Field(..., regex="^(csv|json)$")

# After (Pydantic v2 syntax)  
format: str = Field(..., pattern="^(csv|json)$")
```

### Prevention:
When adding new validation fields, use Pydantic v2 syntax with `pattern` instead of `regex`.

---

## 🏗️ Missing Schema Classes

### Problem: Cannot import Response classes
```bash
ImportError: cannot import name 'InvoiceDocumentResponse' from 'models.schemas'
```

### Root Cause:
API routes were expecting `*Response` schema classes that didn't exist in the schemas file.

### Missing Classes:
- `InvoiceDocumentResponse`
- `ProcessingJobResponse`
- `ExtractedDataResponse`
- `ReviewSessionResponse`

### Solution:
Added missing response schema classes:
```python
class InvoiceDocumentResponse(InvoiceDocument):
    """Response schema for invoice document API endpoints."""
    pass

class ProcessingJobResponse(ProcessingJob):
    """Response schema for processing job API endpoints."""
    pass

class ExtractedDataResponse(ExtractedData):
    """Response schema for extracted data API endpoints."""
    pass

class ReviewSessionResponse(ReviewSession):
    """Response schema for review session API endpoints."""
    pass
```

### Prevention:
When creating new API endpoints, ensure corresponding response schemas exist or create them alongside the endpoints.

---

## 🔍 OCR and System Dependencies

### Problem 1: Tesseract not found in PATH
```bash
tesseract is not installed or it's not in your PATH
```

### Root Cause:
Tesseract binary not properly installed or not in system PATH.

### Solution:
```bash
# macOS - Install via Homebrew
brew install tesseract

# If installation fails due to conflicts
brew unlink zstd && brew install tesseract && brew link zstd

# Verify installation
tesseract --version
```

### Problem 2: python-magic can't find libmagic
```bash
failed to find libmagic. Check your installation
```

### Root Cause:
libmagic system library not installed or not properly linked.

### Solution:
```bash
# Install libmagic
brew install libmagic

# If linking issues occur, made it optional in code
# See "Code Changes Made" in Dependencies section above
```

### Graceful Degradation:
The system now works even if these optional dependencies are missing:
- **Without Tesseract**: OCR processing will fail gracefully with error messages
- **Without libmagic**: File validation falls back to extension-based checking

---

## 🗃️ Database and Model Issues

### Problem: Import conflicts between models
```bash
ImportError: cannot import name 'ProcessingMode' from 'models.invoice_document'
```

### Root Cause:
`ProcessingMode` enum was defined in `processing_job.py` but imported from `invoice_document.py`.

### Files Affected:
- `/backend/src/api/routes/documents.py`
- `/backend/src/api/routes/processing.py`

### Solution:
Fixed import statements to import from correct modules:
```python
# Before (incorrect)
from models.invoice_document import ProcessingStatus, FileType, ProcessingMode

# After (correct)
from models.invoice_document import ProcessingStatus, FileType
from models.processing_job import ProcessingMode
```

### Prevention:
When adding new enums or models, document their location and ensure imports reference the correct module.

---

## ⚡ Quick Setup Commands

### Complete Backend Setup (Copy-Paste Ready):
```bash
# Navigate to backend directory
cd /Users/bhagyashri/Spec-Kit/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install build tools
pip install --upgrade pip wheel setuptools

# Install dependencies in order
pip install fastapi "uvicorn[standard]" sqlalchemy alembic pydantic
pip install python-multipart httpx pytest pytest-asyncio
pip install Pillow opencv-python-headless pytesseract PyMuPDF python-magic

# Install system dependencies (macOS)
brew install tesseract libmagic

# Test installation
cd src
python -c "from main import app; print('FastAPI app imported successfully')"

# Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup (Copy-Paste Ready):
```bash
# Navigate to frontend directory
cd /Users/bhagyashri/Spec-Kit/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Verification Commands:
```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test API documentation
open http://localhost:8000/docs

# Test frontend
open http://localhost:3000
```

---

## 🧪 Testing Commands

### Backend Tests:
```bash
cd /Users/bhagyashri/Spec-Kit/backend
source venv/bin/activate
cd src
python test_installation.py  # Our custom test script
pytest tests/ -v             # Run all tests
```

### Frontend Tests:
```bash
cd /Users/bhagyashri/Spec-Kit/frontend
npm test                     # Run React tests
npm run build               # Test build process
```

---

## 📚 Reference Information

### Key File Locations:
- **Backend Source**: `/backend/src/`
- **API Routes**: `/backend/src/api/routes/`
- **Models**: `/backend/src/models/`
- **Services**: `/backend/src/services/`
- **Database**: `shared/database/invoices.db` (auto-created)
- **File Storage**: `shared/storage/invoices/`

### Port Configuration:
- **Backend API**: http://localhost:8000
- **Frontend Dev**: http://localhost:3000 (default Vite)
- **API Docs**: http://localhost:8000/docs

### Important Dependencies:
- **Python**: 3.11+ (tested with 3.13.7)
- **Node.js**: 18+ (for frontend)
- **Tesseract**: 5.5.1+ (for OCR)
- **libmagic**: For file type detection

---

## 🎯 Success Indicators

When setup is complete, you should see:
- ✅ `python -c "from main import app"` runs without errors
- ✅ `curl http://localhost:8000/health` returns `{"status":"healthy"}`
- ✅ API docs accessible at http://localhost:8000/docs
- ✅ Frontend loads at http://localhost:3000
- ✅ File upload interface is functional

---

## 🔄 Common Issues and Quick Fixes

### "Module not found" errors:
```bash
# Ensure you're in the right directory and venv is activated
cd /Users/bhagyashri/Spec-Kit/backend/src
source ../venv/bin/activate
```

### Port already in use:
```bash
# Kill existing processes
pkill -f uvicorn
pkill -f "npm run dev"
```

### Permission errors on macOS:
```bash
# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*
```

### Import path issues:
- Always run Python commands from `/backend/src/` directory
- Use absolute imports in new files
- Check that all required Response classes exist in schemas

---

## 🔍 Data Extraction Issues

### Problem: String too long validation errors
```bash
1 validation error for ExtractedDataCreate
vendor_name
  String should have at most 255 characters [type=string_too_long]
```

### Root Cause:
OCR extraction is pulling too much text into fields with database length constraints.

### Solution:
Updated data extraction logic with:
```python
# Field length validation
if vendor_name and len(vendor_name) > 255:
    vendor_name = vendor_name[:252] + "..."
if vendor_address and len(vendor_address) > 500:
    vendor_address = vendor_address[:497] + "..."
```

### Prevention:
- **Use high-quality scans**: 300+ DPI resolution
- **Standard invoice formats**: See [INVOICE_FORMATS.md](./INVOICE_FORMATS.md)
- **Clear text layout**: Avoid complex backgrounds or overlapping text

---

*Last Updated: January 10, 2025*  
*Version: 1.1.0*  
*Status: Tested and Verified ✅*