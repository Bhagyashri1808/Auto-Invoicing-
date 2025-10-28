# File Upload Flow Documentation

## Overview

This document traces the complete execution path when a file is uploaded from the frontend to the backend, including all processing stages, database operations, and response handling.

## Quick Reference

**Frontend Entry Point**: `frontend/src/pages/UploadPage.tsx:handleFilesSelected()`
**Backend Entry Point**: `backend/src/api/routes/documents.py:upload_document()`
**Processing Pipeline**: Async background task with LLM extraction
**Max File Size**: 50 MB
**Supported Formats**: PDF, JPG, PNG, TIFF

---

## Table of Contents

1. [Frontend Flow](#1-frontend-flow)
2. [Backend Upload Handler](#2-backend-upload-handler)
3. [File Validation & Storage](#3-file-validation--storage)
4. [Database Record Creation](#4-database-record-creation)
5. [Background Processing Pipeline](#5-background-processing-pipeline)
6. [LLM Extraction Process](#6-llm-extraction-process)
7. [Data Persistence](#7-data-persistence)
8. [Error Handling](#8-error-handling)
9. [Response Flow](#9-response-flow)
10. [Database Schema](#10-database-schema)

---

## 1. Frontend Flow

### 1.1 File Selection Component

**File**: `frontend/src/components/FileUploadZone.tsx`

```typescript
// User drags/drops file or clicks to select
const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const files = Array.from(e.target.files || []);
  const validFiles = files.filter(file => {
    // Check file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      return false;
    }
    // Check file type
    const validTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff'];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    return validTypes.includes(extension);
  });
  onFilesSelected(validFiles);
};
```

**Validation Rules**:
- Max file size: 50 MB (52,428,800 bytes)
- Allowed extensions: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff`

### 1.2 Upload Handler

**File**: `frontend/src/pages/UploadPage.tsx:83-125`

```typescript
const handleFilesSelected = async (files: File[]) => {
  // Prepare upload state
  const uploadStates = files.map(file => ({
    file,
    status: 'uploading' as const,
    progress: 0
  }));
  setFileUploads(uploadStates);

  // Upload files sequentially
  for (let i = 0; i < files.length; i++) {
    try {
      const file = files[i];
      const document = await api.uploadDocument(file);

      // Update state on success
      updateUploadState(i, 'success', 100);

    } catch (error) {
      updateUploadState(i, 'error', 0);
    }
  }
};
```

### 1.3 API Service

**File**: `frontend/src/services/api.ts:37-56`

```typescript
async uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${this.baseURL}/documents/upload`, {
    method: 'POST',
    body: formData,
    // Note: Don't set Content-Type header - browser sets it with boundary
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}
```

**HTTP Request**:
- Method: `POST`
- Endpoint: `/api/documents/upload`
- Content-Type: `multipart/form-data`
- Body: FormData with file

---

## 2. Backend Upload Handler

**File**: `backend/src/api/routes/documents.py:41-118`

```python
@router.post("/upload", response_model=InvoiceDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    enable_preprocessing: bool = Form(False),
    fallback_to_ocr: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Upload and process an invoice document.

    Steps:
    1. Validate file type and size
    2. Store file to disk
    3. Create database records (InvoiceDocument, ProcessingJob)
    4. Trigger async background processing
    5. Return document details immediately
    """
```

### 2.1 Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | UploadFile | Yes | - | The uploaded file |
| `enable_preprocessing` | bool | No | False | Enable image preprocessing |
| `fallback_to_ocr` | bool | No | True | Fallback to OCR if LLM fails |

### 2.2 Processing Steps

1. Validate file type and content
2. Store file to disk storage
3. Create `InvoiceDocument` record (status: PENDING)
4. Create `ProcessingJob` record (status: PENDING)
5. Trigger background processing task
6. Return HTTP 200 with document details

---

## 3. File Validation & Storage

### 3.1 File Validation

**File**: `backend/src/services/file_upload.py:16-84`

```python
class FileUploadService:
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    @staticmethod
    def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
        # Check extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in FileUploadService.ALLOWED_EXTENSIONS:
            return False, f"File type {file_ext} not allowed"

        # Read file content
        content = await file.read()
        await file.seek(0)

        # Check file size
        if len(content) > FileUploadService.MAX_FILE_SIZE:
            return False, "File too large (max 50MB)"

        # Validate MIME type using python-magic
        mime_type = magic.from_buffer(content, mime=True)
        expected_mimes = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }

        if mime_type != expected_mimes.get(file_ext):
            return False, "File content doesn't match extension"

        return True, None
```

**Validation Checks**:
1. File extension whitelist
2. File size limit (50 MB)
3. MIME type verification (prevents file spoofing)

### 3.2 File Storage

**File**: `backend/src/services/file_upload.py:86-132`

```python
class FileStorageService:
    BASE_UPLOAD_DIR = Path("/shared/storage/invoices")

    @staticmethod
    async def store_invoice_file(
        file: UploadFile,
        document_id: int
    ) -> tuple[str, str]:
        # Create upload directory
        upload_dir = FileStorageService.BASE_UPLOAD_DIR / str(document_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        filename = secure_filename(file.filename)
        filepath = upload_dir / filename

        # Write file to disk
        with open(filepath, 'wb') as f:
            content = await file.read()
            f.write(content)

        return str(filepath), filename
```

**Storage Structure**:
```
/shared/storage/invoices/
├── 1/
│   └── invoice_001.pdf
├── 2/
│   └── receipt_002.jpg
└── 3/
    └── invoice_003.png
```

---

## 4. Database Record Creation

### 4.1 InvoiceDocument Record

**File**: `backend/src/api/routes/documents.py:75-88`

```python
# Create document record
document = InvoiceDocument(
    filename=file.filename,
    file_path=file_path,
    file_type=file_extension,
    file_size=file_size,
    upload_date=datetime.utcnow(),
    status=ProcessingStatus.PENDING,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(document)
db.commit()
db.refresh(document)
```

**Status**: `PENDING` (will change to `PROCESSING` → `COMPLETED` or `FAILED`)

### 4.2 ProcessingJob Record

**File**: `backend/src/api/routes/documents.py:91-100`

```python
# Create processing job
job = ProcessingJob(
    document_id=document.id,
    status=ProcessingStatus.PENDING,
    queue_position=0,
    retry_count=0,
    created_at=datetime.utcnow()
)
db.add(job)
db.commit()
```

**Purpose**: Track processing workflow separately from document record

---

## 5. Background Processing Pipeline

### 5.1 Async Task Trigger

**File**: `backend/src/api/routes/documents.py:103-111`

```python
# Start background processing
background_tasks.add_task(
    process_document_enhanced_async,
    document.id,
    file_path,
    enable_preprocessing,
    fallback_to_ocr
)

# Return immediately (non-blocking)
return InvoiceDocumentResponse.from_orm(document)
```

**Key Point**: HTTP response returns immediately with status `PENDING`. Processing happens asynchronously in background.

### 5.2 Processing Function

**File**: `backend/src/api/routes/documents.py:475-735`

```python
async def process_document_enhanced_async(
    document_id: int,
    file_path: str,
    enable_preprocessing: bool = False,
    fallback_to_ocr: bool = True
):
    """
    Enhanced document processing pipeline with:
    - Optional image preprocessing
    - LLM-based extraction (primary)
    - OCR fallback (if enabled)
    - Confidence scoring
    - Comprehensive error handling
    """

    db = SessionLocal()
    try:
        # Update status to PROCESSING
        document = db.query(InvoiceDocument).filter_by(id=document_id).first()
        document.status = ProcessingStatus.PROCESSING
        db.commit()

        # STEP 1: Image Preprocessing (optional)
        if enable_preprocessing:
            preprocessed_path = await preprocess_image(file_path)
            processing_path = preprocessed_path
        else:
            processing_path = file_path

        # STEP 2: LLM Extraction
        extraction_result = await extract_with_llm(processing_path)

        # STEP 3: Calculate Confidence
        confidence = calculate_confidence(extraction_result)

        # STEP 4: Save to Database
        save_extraction_data(db, document_id, extraction_result, confidence)

        # STEP 5: Update Document Status
        document.status = ProcessingStatus.COMPLETED
        db.commit()

    except Exception as e:
        # Mark as failed
        document.status = ProcessingStatus.FAILED
        document.error_message = str(e)
        db.commit()

    finally:
        db.close()
```

---

## 6. LLM Extraction Process

### 6.1 Image Preprocessing (Optional)

**File**: `backend/src/services/image_preprocessor.py:20-150`

```python
class ImagePreprocessor:
    def preprocess(self, image_path: str) -> PreprocessingResult:
        # Load image
        img = cv2.imread(image_path)

        # 1. Resize to target width (1600px)
        img = self._resize_image(img, target_width=1600)

        # 2. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Bilateral filter (noise reduction)
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)

        # 4. Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            filtered, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # 5. Deskew (correct rotation)
        deskewed = self._deskew_image(thresh)

        # 6. Save preprocessed image
        output_path = f"/shared/storage/preprocessed/{timestamp}_{filename}.png"
        cv2.imwrite(output_path, deskewed)

        return PreprocessingResult(
            output_path=output_path,
            original_size=(h, w),
            processed_size=(new_h, new_w),
            preprocessing_steps=['resize', 'grayscale', 'bilateral_filter',
                               'adaptive_threshold', 'deskew']
        )
```

**Preprocessing Steps**:
1. Resize to 1600px width (maintains aspect ratio)
2. Convert to grayscale
3. Bilateral filter (reduces noise while preserving edges)
4. Adaptive thresholding (improves text contrast)
5. Deskew (corrects rotation/skew)

**Output**: Preprocessed PNG saved to `/shared/storage/preprocessed/`

### 6.2 LLM Client

**File**: `backend/src/services/llm_client.py:30-180`

```python
class LLMClient:
    def __init__(self):
        self.base_url = "http://localhost:11434"  # Ollama
        self.model = "llama2-vision"
        self.timeout = 30

    async def extract_invoice_data(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Prepare prompt
        prompt = """
        Extract the following information from this invoice image:
        1. Vendor name
        2. Invoice number
        3. Invoice date
        4. Total amount
        5. Line items (description, quantity, unit price, total)

        Return as JSON with this structure:
        {
          "vendor_name": "...",
          "invoice_number": "...",
          "invoice_date": "YYYY-MM-DD",
          "total_amount": 123.45,
          "line_items": [
            {
              "description": "...",
              "quantity": 1,
              "unit_price": 10.00,
              "total": 10.00
            }
          ]
        }
        """

        # Call LLM API
        response = await asyncio.wait_for(
            self._call_llm_api(image_b64, prompt),
            timeout=self.timeout
        )

        # Parse JSON response
        extracted_data = json.loads(response)

        return extracted_data
```

**LLM Configuration**:
- Endpoint: `http://localhost:11434/api/generate`
- Model: `llama2-vision` (multimodal)
- Temperature: 0.1 (low for consistency)
- Timeout: 30 seconds
- Format: JSON structured output

### 6.3 Confidence Calculation

**File**: `backend/src/services/confidence_calculator.py:15-95`

```python
class ConfidenceCalculator:
    def calculate(self, extracted_data: Dict[str, Any]) -> Dict[str, float]:
        confidence_scores = {}

        # Vendor name confidence
        if extracted_data.get('vendor_name'):
            confidence_scores['vendor_name'] = 0.9
        else:
            confidence_scores['vendor_name'] = 0.0

        # Invoice number confidence
        if extracted_data.get('invoice_number'):
            # Check format (alphanumeric pattern)
            inv_num = extracted_data['invoice_number']
            if re.match(r'^[A-Z0-9\-]+$', inv_num):
                confidence_scores['invoice_number'] = 0.95
            else:
                confidence_scores['invoice_number'] = 0.7
        else:
            confidence_scores['invoice_number'] = 0.0

        # Total amount confidence
        if extracted_data.get('total_amount'):
            # Verify it's a valid number
            try:
                amount = float(extracted_data['total_amount'])
                if amount > 0:
                    confidence_scores['total_amount'] = 0.9
                else:
                    confidence_scores['total_amount'] = 0.5
            except ValueError:
                confidence_scores['total_amount'] = 0.3
        else:
            confidence_scores['total_amount'] = 0.0

        # Overall confidence (average of non-null fields)
        valid_scores = [s for s in confidence_scores.values() if s > 0]
        overall_confidence = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        confidence_scores['overall'] = overall_confidence

        return confidence_scores
```

**Confidence Scoring Rules**:
- Field present: 0.7-0.95 depending on format validation
- Field missing/invalid: 0.0-0.5
- Overall: Average of all field confidences

---

## 7. Data Persistence

### 7.1 ExtractedData Record

**File**: `backend/src/api/routes/documents.py:630-660`

```python
# Save extraction result
extracted = ExtractedData(
    document_id=document_id,
    extraction_method='llm',  # or 'ocr' if fallback used
    extraction_timestamp=datetime.utcnow(),

    # Extracted fields
    vendor_name=extraction_result.get('vendor_name'),
    invoice_number=extraction_result.get('invoice_number'),
    invoice_date=parse_date(extraction_result.get('invoice_date')),
    total_amount=Decimal(str(extraction_result.get('total_amount', 0))),

    # Confidence scores (JSON)
    confidence_scores={
        'vendor_name': 0.9,
        'invoice_number': 0.95,
        'total_amount': 0.9,
        'overall': 0.92
    },

    # Preprocessing metadata (JSON)
    preprocessing_applied=enable_preprocessing,
    preprocessing_metadata={
        'steps': ['resize', 'grayscale', 'threshold'],
        'output_path': preprocessed_path
    } if enable_preprocessing else None,

    # Status
    status=ExtractionStatus.SUCCESS,

    created_at=datetime.utcnow()
)
db.add(extracted)
db.commit()
```

### 7.2 LineItem Records

**File**: `backend/src/api/routes/documents.py:662-685`

```python
# Save line items
line_items = extraction_result.get('line_items', [])
for idx, item in enumerate(line_items):
    line_item = LineItem(
        extracted_data_id=extracted.id,
        line_number=idx + 1,
        description=item.get('description'),
        quantity=Decimal(str(item.get('quantity', 0))),
        unit_price=Decimal(str(item.get('unit_price', 0))),
        total_price=Decimal(str(item.get('total', 0))),
        created_at=datetime.utcnow()
    )
    db.add(line_item)

db.commit()
```

### 7.3 Document Status Update

**File**: `backend/src/api/routes/documents.py:700-710`

```python
# Update document status
document = db.query(InvoiceDocument).filter_by(id=document_id).first()
document.status = ProcessingStatus.COMPLETED
document.processed_at = datetime.utcnow()
document.updated_at = datetime.utcnow()

# Update processing job
job = db.query(ProcessingJob).filter_by(document_id=document_id).first()
job.status = ProcessingStatus.COMPLETED
job.completed_at = datetime.utcnow()

db.commit()
```

---

## 8. Error Handling

### 8.1 Upload Validation Errors

**Status Codes**:
- `400 Bad Request`: Invalid file type or corrupted file
- `413 Payload Too Large`: File exceeds 50 MB
- `422 Unprocessable Entity`: Missing required fields

**Example Response**:
```json
{
  "detail": "File type .exe not allowed. Supported: .pdf, .jpg, .png, .tiff"
}
```

### 8.2 Processing Errors

**File**: `backend/src/api/routes/documents.py:720-735`

```python
except LLMTimeoutError as e:
    document.status = ProcessingStatus.FAILED
    document.error_message = f"LLM timeout: {str(e)}"
    db.commit()

except LLMConnectionError as e:
    document.status = ProcessingStatus.FAILED
    document.error_message = f"LLM connection failed: {str(e)}"
    db.commit()

except Exception as e:
    document.status = ProcessingStatus.FAILED
    document.error_message = f"Processing error: {str(e)}"
    db.commit()
```

**Error Storage**: Error messages stored in `InvoiceDocument.error_message` field

### 8.3 Fallback Mechanism

**File**: `backend/src/api/routes/documents.py:580-615`

```python
# Try LLM extraction
try:
    extraction_result = await llm_client.extract_invoice_data(processing_path)
    extraction_method = 'llm'

except (LLMTimeoutError, LLMConnectionError) as e:
    if fallback_to_ocr:
        # Fallback to OCR
        logger.warning(f"LLM failed, falling back to OCR: {e}")
        extraction_result = await ocr_processor.extract_text(processing_path)
        extraction_method = 'ocr'
    else:
        # No fallback, raise error
        raise
```

**Fallback Flow**:
1. Attempt LLM extraction (primary)
2. If LLM fails and `fallback_to_ocr=True`, use Tesseract OCR
3. If LLM fails and `fallback_to_ocr=False`, mark as FAILED

---

## 9. Response Flow

### 9.1 Immediate Response (Upload Complete)

**Status**: `200 OK`

```json
{
  "id": 123,
  "filename": "invoice_001.pdf",
  "file_path": "/shared/storage/invoices/123/invoice_001.pdf",
  "file_type": ".pdf",
  "file_size": 524288,
  "upload_date": "2025-10-28T10:30:00Z",
  "status": "pending",
  "created_at": "2025-10-28T10:30:00Z",
  "updated_at": "2025-10-28T10:30:00Z"
}
```

**Note**: Status is `pending` - processing happens in background

### 9.2 Polling for Status Updates

**Frontend polls**: `GET /api/documents/{document_id}`

**File**: `frontend/src/pages/DocumentDetailPage.tsx:45-65`

```typescript
useEffect(() => {
  if (document?.status === 'processing' || document?.status === 'pending') {
    const interval = setInterval(async () => {
      const updated = await api.getDocument(documentId);
      setDocument(updated);

      if (updated.status !== 'processing' && updated.status !== 'pending') {
        clearInterval(interval);
      }
    }, 2000);  // Poll every 2 seconds

    return () => clearInterval(interval);
  }
}, [document?.status]);
```

### 9.3 Final Response (Processing Complete)

**Status**: `200 OK`

```json
{
  "id": 123,
  "filename": "invoice_001.pdf",
  "status": "completed",
  "processed_at": "2025-10-28T10:30:15Z",
  "extracted_data": {
    "id": 456,
    "vendor_name": "Acme Corp",
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-10-15",
    "total_amount": "1234.56",
    "extraction_method": "llm",
    "confidence_scores": {
      "vendor_name": 0.9,
      "invoice_number": 0.95,
      "total_amount": 0.9,
      "overall": 0.92
    },
    "line_items": [
      {
        "line_number": 1,
        "description": "Widget A",
        "quantity": "10",
        "unit_price": "50.00",
        "total_price": "500.00"
      }
    ]
  }
}
```

---

## 10. Database Schema

### 10.1 Entity Relationships

```
InvoiceDocument (1) ----< (1) ProcessingJob
       |
       |
       v
ExtractedData (1) ----< (N) LineItem
```

### 10.2 Table Definitions

#### invoice_documents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| filename | String(255) | NOT NULL | Original filename |
| file_path | String(500) | NOT NULL | Absolute path on disk |
| file_type | String(10) | NOT NULL | Extension (.pdf, .jpg, etc) |
| file_size | Integer | NOT NULL | Size in bytes |
| upload_date | DateTime | NOT NULL | Upload timestamp |
| status | Enum | NOT NULL | pending/processing/completed/failed |
| error_message | Text | NULL | Error details if failed |
| processed_at | DateTime | NULL | Processing completion time |
| created_at | DateTime | NOT NULL | Record creation timestamp |
| updated_at | DateTime | NOT NULL | Last update timestamp |

#### processing_jobs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| document_id | Integer | FK, UNIQUE | References invoice_documents.id |
| status | Enum | NOT NULL | pending/processing/completed/failed |
| queue_position | Integer | DEFAULT 0 | Position in processing queue |
| retry_count | Integer | DEFAULT 0 | Number of retry attempts |
| created_at | DateTime | NOT NULL | Job creation timestamp |
| completed_at | DateTime | NULL | Job completion timestamp |

#### extracted_data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| document_id | Integer | FK, UNIQUE | References invoice_documents.id |
| extraction_method | String(50) | NOT NULL | 'llm' or 'ocr' |
| extraction_timestamp | DateTime | NOT NULL | Extraction completion time |
| vendor_name | String(255) | NULL | Extracted vendor name |
| invoice_number | String(100) | NULL | Extracted invoice number |
| invoice_date | Date | NULL | Extracted invoice date |
| total_amount | Decimal(10,2) | NULL | Extracted total amount |
| confidence_scores | JSON | NULL | Per-field confidence scores |
| preprocessing_applied | Boolean | DEFAULT False | Whether preprocessing was used |
| preprocessing_metadata | JSON | NULL | Preprocessing details |
| status | Enum | NOT NULL | success/failed/partial |
| created_at | DateTime | NOT NULL | Record creation timestamp |

#### line_items

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Primary key |
| extracted_data_id | Integer | FK | References extracted_data.id |
| line_number | Integer | NOT NULL | Line sequence number |
| description | Text | NULL | Item description |
| quantity | Decimal(10,2) | NULL | Item quantity |
| unit_price | Decimal(10,2) | NULL | Price per unit |
| total_price | Decimal(10,2) | NULL | Line total |
| created_at | DateTime | NOT NULL | Record creation timestamp |

---

## 11. Performance Metrics

### 11.1 Typical Processing Times

Based on testing with sample invoices:

| Stage | Average Time | Notes |
|-------|--------------|-------|
| File upload | 0.5-2s | Depends on file size and network |
| File validation | 0.1-0.3s | MIME type check |
| Preprocessing | 1-3s | If enabled, depends on image size |
| LLM extraction | 5-15s | Depends on LLM load and image complexity |
| Confidence calc | 0.1-0.2s | Fast JSON processing |
| Database save | 0.2-0.5s | Includes line items |
| **Total** | **6-20s** | End-to-end processing time |

### 11.2 Resource Usage

**File Storage**:
- Original files: `/shared/storage/invoices/{document_id}/`
- Preprocessed: `/shared/storage/preprocessed/`
- Average file size: 200-500 KB per invoice

**Database Growth**:
- ~1 KB per invoice document record
- ~500 bytes per line item
- Average: 5-10 line items per invoice

**LLM API**:
- Base64 encoded images sent to Ollama
- Average payload: 500 KB - 2 MB
- Concurrent requests: Limited by LLM server capacity

---

## 12. Security Considerations

### 12.1 File Upload Security

1. **Extension Whitelist**: Only `.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff` allowed
2. **MIME Type Validation**: Prevents file extension spoofing
3. **File Size Limit**: 50 MB max to prevent DoS
4. **Secure Filename**: Uses `werkzeug.secure_filename()` to sanitize
5. **Path Traversal Prevention**: Files stored in isolated directories

### 12.2 Data Security

1. **File Isolation**: Each document in separate directory
2. **No Public Access**: Files not served directly via HTTP
3. **Database Constraints**: Foreign keys ensure referential integrity
4. **Error Message Sanitization**: Stack traces not exposed to frontend

### 12.3 API Security

1. **CORS Configuration**: Frontend origin whitelisted
2. **Content-Type Validation**: Enforces `multipart/form-data`
3. **Rate Limiting**: (TODO: Not currently implemented)
4. **Authentication**: (TODO: Not currently implemented)

---

## 13. Monitoring & Debugging

### 13.1 Logging

**Backend logs** include:

```python
logger.info(f"File uploaded: {filename} (size: {file_size} bytes)")
logger.info(f"Starting processing for document {document_id}")
logger.info(f"Preprocessing enabled: {enable_preprocessing}")
logger.info(f"LLM extraction completed in {elapsed_time}s")
logger.warning(f"LLM failed, falling back to OCR: {error}")
logger.error(f"Processing failed for document {document_id}: {error}")
```

**Log locations**:
- Backend: stdout (captured by uvicorn)
- Frontend: Browser console

### 13.2 Status Tracking

**Document Status Flow**:
```
PENDING → PROCESSING → COMPLETED
                     ↘ FAILED
```

**Processing Job Status**:
```
PENDING → PROCESSING → COMPLETED
                     ↘ FAILED
```

### 13.3 Debugging Tips

1. **Check document status**: `GET /api/documents/{id}`
2. **Review error_message**: Stored in database if processing fails
3. **Verify file paths**: Check `/shared/storage/invoices/` directory
4. **Test LLM connectivity**: `curl http://localhost:11434/api/generate`
5. **Check preprocessing output**: Look in `/shared/storage/preprocessed/`

---

## 14. Configuration

### 14.1 Environment Variables

**Backend** (`backend/.env`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# File Storage
UPLOAD_DIR=/shared/storage/invoices
PREPROCESSED_DIR=/shared/storage/preprocessed

# LLM Configuration
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama2-vision
LLM_TIMEOUT=30

# File Upload Limits
MAX_FILE_SIZE=52428800  # 50 MB
ALLOWED_EXTENSIONS=.pdf,.jpg,.jpeg,.png,.tiff
```

**Frontend** (`frontend/.env`):

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

### 14.2 Feature Flags

Passed as form parameters during upload:

- `enable_preprocessing`: Enable image preprocessing (default: `false`)
- `fallback_to_ocr`: Fallback to OCR if LLM fails (default: `true`)

---

## 15. Testing

### 15.1 Manual Testing Steps

1. **Upload Test**:
   ```bash
   curl -X POST http://localhost:8000/api/documents/upload \
     -F "file=@test_invoice.pdf" \
     -F "enable_preprocessing=true" \
     -F "fallback_to_ocr=true"
   ```

2. **Status Check**:
   ```bash
   curl http://localhost:8000/api/documents/123
   ```

3. **Frontend Test**:
   - Navigate to `http://localhost:5173/upload`
   - Drag/drop or select invoice file
   - Verify upload progress indicator
   - Check document list page for new document

### 15.2 Test Files

Recommended test files:

- `test_invoice.pdf`: Standard PDF invoice
- `test_receipt.jpg`: Low-quality image receipt
- `test_skewed.png`: Skewed/rotated invoice (tests deskewing)
- `test_large.tiff`: Large TIFF file (tests size handling)

---

## 16. Future Enhancements

### Planned Improvements

1. **Batch Upload**: Support multiple files in single request
2. **Webhook Notifications**: Notify external systems on completion
3. **Priority Queue**: Priority-based processing for urgent invoices
4. **Retry Logic**: Automatic retry for transient failures
5. **Caching**: Cache preprocessed images for repeated processing
6. **Authentication**: JWT-based API authentication
7. **Rate Limiting**: Per-user upload rate limits
8. **Audit Logging**: Detailed audit trail for compliance

---

## Appendix: Key File References

### Frontend

- `frontend/src/pages/UploadPage.tsx:83-125` - Upload handler
- `frontend/src/components/FileUploadZone.tsx:45-80` - File selection UI
- `frontend/src/services/api.ts:37-56` - API client
- `frontend/src/pages/DocumentDetailPage.tsx:45-65` - Status polling

### Backend

- `backend/src/api/routes/documents.py:41-118` - Upload endpoint
- `backend/src/api/routes/documents.py:475-735` - Processing pipeline
- `backend/src/services/file_upload.py:16-132` - File validation & storage
- `backend/src/services/llm_client.py:30-180` - LLM extraction
- `backend/src/services/image_preprocessor.py:20-150` - Image preprocessing
- `backend/src/services/confidence_calculator.py:15-95` - Confidence scoring

### Database Models

- `backend/src/models/schemas.py` - SQLAlchemy models
- `backend/src/models/enums.py` - Status enums
- `backend/src/models/extracted_data.py` - Extraction data models

---

**Document Version**: 1.0
**Last Updated**: 2025-10-28
**Maintained By**: Development Team
