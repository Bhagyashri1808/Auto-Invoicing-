# Implementation Tasks: Invoice Automation with HITL Review

**Feature**: Invoice Automation with HITL Review  
**Branch**: `001-lets-build-an`  
**Date**: 2025-01-10  
**Total Tasks**: 52  
**Constitution**: Test-First Methodology (TDD mandatory)

## Task Organization

Tasks are organized by user story phases to enable independent implementation and testing. Each user story represents a complete, deliverable increment.

### User Story Mapping
- **P1 Stories (MVP)**: US1 (Document Upload), US2 (HITL Review Interface)
- **P2 Stories**: US3 (Batch Processing)  
- **P3 Stories**: US4 (Review Workflow)

## Phase 1: Project Setup (Foundation)

### T001: Initialize Repository Structure [P] ✅
**File**: Repository root  
**Description**: Create monorepo directory structure for React/Vite frontend and Python/FastAPI backend
```bash
mkdir -p backend/src/{models,services,api,database} backend/tests/{contract,integration,unit}
mkdir -p frontend/src/{components,pages,services,types,hooks} frontend/tests/{components,integration}
mkdir -p shared/{storage,database}
```

### T002: Setup Backend Dependencies [P] ✅
**File**: `backend/requirements.txt`, `backend/pyproject.toml`  
**Description**: Configure Python dependencies for FastAPI, SQLAlchemy, Pydantic, OpenCV, Tesseract, pytest
```
fastapi[all]==0.104.1
sqlalchemy==2.0.23
pydantic==2.5.0
opencv-python==4.8.1.78
pytesseract==0.3.10
alembic==1.13.1
pytest==7.4.3
httpx==0.25.2
```

### T003: Setup Frontend Dependencies [P] ✅
**File**: `frontend/package.json`, `frontend/vite.config.ts`  
**Description**: Configure Node.js dependencies for React 18, Vite 5, TypeScript, Vitest
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.2.0",
    "vite": "^5.0.0"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0"
  }
}
```

### T004: Database Configuration and Migrations ✅
**File**: `backend/src/database/config.py`, `backend/alembic.ini`  
**Description**: Setup SQLAlchemy database configuration, Alembic migrations, initial schema

### T005: Shared Storage Setup ✅
**File**: `shared/storage/`, `backend/src/services/file_storage.py`  
**Description**: Create file storage directory structure and storage service interface

## Phase 2: Foundational Services (Prerequisites)

### T006: Core Data Models ✅
**File**: `backend/src/models/base.py`  
**Description**: Base SQLAlchemy model with UUID primary keys, timestamps, common fields

### T007: Invoice Document Model [US1] ✅
**File**: `backend/src/models/invoice_document.py`  
**Description**: SQLAlchemy model for invoice document entity with file metadata and processing status

### T008: Extracted Data Model [US1] ✅
**File**: `backend/src/models/extracted_data.py`  
**Description**: SQLAlchemy model for structured invoice data with confidence scores

### T009: Line Item Model [US1] ✅
**File**: `backend/src/models/line_item.py`  
**Description**: SQLAlchemy model for invoice line items with quantity, pricing

### T010: Processing Job Model [US3] ✅
**File**: `backend/src/models/processing_job.py`  
**Description**: SQLAlchemy model for queue management and processing workflow

### T011: Review Session Model [US2,US4] ✅
**File**: `backend/src/models/review_session.py`  
**Description**: SQLAlchemy model for tracking human review activities

### T012: Field Correction Model [US2,US4] ✅
**File**: `backend/src/models/field_correction.py`  
**Description**: SQLAlchemy model for recording user corrections during review

### T013: Configuration Model [US3] ✅
**File**: `backend/src/models/configuration.py`  
**Description**: SQLAlchemy model for user-configurable application settings

### T014: Pydantic Schemas [P] ✅
**File**: `backend/src/models/schemas.py`  
**Description**: Pydantic schemas for all models with validation rules, API serialization

### T015: TypeScript Interfaces [P] ✅
**File**: `frontend/src/types/api.ts`  
**Description**: TypeScript interfaces generated from Pydantic schemas for type safety

## Phase 3: User Story 1 - Document Upload and Processing (P1)

**Story Goal**: User uploads an invoice document and receives structured data extraction results  
**Independent Test**: Upload sample invoice → verify structured data extracted and displayed

### T016: Test - File Upload API Contract [US1]
**File**: `backend/tests/contract/test_upload_api.py`  
**Description**: Contract test for POST /invoices endpoint with file validation, size limits

### T017: Test - OCR Processing Service [US1]
**File**: `backend/tests/unit/test_ocr_service.py`  
**Description**: Unit tests for OCR extraction service with sample invoice documents

### T018: Test - Document Processing Workflow [US1]
**File**: `backend/tests/integration/test_document_processing.py`  
**Description**: Integration test for complete upload → OCR → storage workflow

### T019: File Upload Service [US1]
**File**: `backend/src/services/file_upload.py`  
**Description**: File validation, storage, metadata extraction service with error handling

### T020: OCR Processing Service [US1]
**File**: `backend/src/services/ocr_processor.py`  
**Description**: OpenCV + Tesseract integration for text extraction from PDF/images

### T021: Data Extraction Service [US1]
**File**: `backend/src/services/data_extractor.py`  
**Description**: Parse OCR text into structured invoice data with confidence scoring

### T022: Upload API Endpoint [US1]
**File**: `backend/src/api/invoices.py`  
**Description**: POST /invoices endpoint for file upload with multipart form data

### T023: Processing Status API [US1]
**File**: `backend/src/api/invoices.py`  
**Description**: GET /invoices/{id} endpoint for processing status and extracted data

### T024: Test - Upload Component [US1]
**File**: `frontend/tests/components/test_upload.test.tsx`  
**Description**: Component tests for file upload UI with drag-drop, validation feedback

### T025: Test - Processing Status Display [US1]
**File**: `frontend/tests/components/test_processing_status.test.tsx`  
**Description**: Component tests for processing progress and status indicators

### T026: File Upload Component [US1]
**File**: `frontend/src/components/FileUpload.tsx`  
**Description**: React component for file selection, drag-drop, upload progress

### T027: Processing Status Component [US1]
**File**: `frontend/src/components/ProcessingStatus.tsx`  
**Description**: Real-time status display with polling for processing updates

### T028: Upload Page [US1]
**File**: `frontend/src/pages/UploadPage.tsx`  
**Description**: Main upload interface with file selection and processing status

### T029: API Client Service [US1]
**File**: `frontend/src/services/api.ts`  
**Description**: HTTP client for backend API with error handling, file uploads

**US1 Checkpoint**: ✅ Basic upload → processing → display pipeline functional

## Phase 4: User Story 2 - Side-by-Side Review Interface (P1)

**Story Goal**: User compares original document against extracted data in split-screen interface  
**Independent Test**: Display processed invoice → verify side-by-side view → edit data → save corrections

### T030: Test - Review API Contract [US2]
**File**: `backend/tests/contract/test_review_api.py`  
**Description**: Contract tests for review session creation and data update endpoints

### T031: Test - Data Correction Service [US2]
**File**: `backend/tests/unit/test_correction_service.py`  
**Description**: Unit tests for tracking and saving user corrections with audit trail

### T032: Review Session API [US2]
**File**: `backend/src/api/review.py`  
**Description**: POST /invoices/{id}/review endpoint to start review session

### T033: Data Update API [US2]
**File**: `backend/src/api/invoices.py`  
**Description**: PUT /invoices/{id}/extracted-data endpoint for saving corrections

### T034: File Serving API [US2]
**File**: `backend/src/api/files.py`  
**Description**: GET /invoices/{id}/file endpoint for serving original documents

### T035: Correction Tracking Service [US2]
**File**: `backend/src/services/correction_tracker.py`  
**Description**: Track field corrections, confidence scores, audit history

### T036: Test - Document Viewer Component [US2]
**File**: `frontend/tests/components/test_document_viewer.test.tsx`  
**Description**: Component tests for PDF/image display with highlighting capabilities

### T037: Test - Data Editor Component [US2]
**File**: `frontend/tests/components/test_data_editor.test.tsx`  
**Description**: Component tests for editable data fields with validation

### T038: Test - Split Screen Layout [US2]
**File**: `frontend/tests/components/test_split_layout.test.tsx`  
**Description**: Component tests for responsive side-by-side layout

### T039: Document Viewer Component [US2]
**File**: `frontend/src/components/DocumentViewer.tsx`  
**Description**: PDF/image viewer with highlighting and zoom capabilities

### T040: Data Editor Component [US2]
**File**: `frontend/src/components/DataEditor.tsx`  
**Description**: Editable form fields for extracted data with confidence indicators

### T041: Split Screen Layout [US2]
**File**: `frontend/src/components/SplitLayout.tsx`  
**Description**: Responsive layout component for side-by-side document and data view

### T042: Review Interface Page [US2]
**File**: `frontend/src/pages/ReviewPage.tsx`  
**Description**: Complete review interface combining document viewer and data editor

### T043: Data Highlighting Hook [US2]
**File**: `frontend/src/hooks/useDocumentHighlight.ts`  
**Description**: Custom React hook for coordinating field selection and document highlighting

**US2 Checkpoint**: ✅ Full HITL review workflow with side-by-side comparison functional

## Phase 5: User Story 3 - Batch Processing and Queue Management (P2)

**Story Goal**: User processes multiple invoices with queue tracking and status management  
**Independent Test**: Upload multiple files → verify queue processing → track status for each document

### T044: Test - Queue Management API [US3]
**File**: `backend/tests/contract/test_queue_api.py`  
**Description**: Contract tests for processing queue endpoints and configuration

### T045: Test - Batch Processing Service [US3]
**File**: `backend/tests/integration/test_batch_processing.py`  
**Description**: Integration tests for sequential and parallel processing modes

### T046: Queue Management Service [US3]
**File**: `backend/src/services/queue_manager.py`  
**Description**: Processing queue with configurable sequential/parallel execution

### T047: Batch Processing API [US3]
**File**: `backend/src/api/processing.py`  
**Description**: GET /processing/queue and PUT /processing/config endpoints

### T048: Test - Queue Dashboard Component [US3]
**File**: `frontend/tests/components/test_queue_dashboard.test.tsx`  
**Description**: Component tests for queue status display and processing controls

### T049: Queue Dashboard Component [US3]
**File**: `frontend/src/components/QueueDashboard.tsx`  
**Description**: Real-time queue status with processing progress and error handling

### T050: Configuration Panel Component [US3]
**File**: `frontend/src/components/ConfigPanel.tsx`  
**Description**: User interface for processing mode and threshold configuration

**US3 Checkpoint**: ✅ Batch processing with queue management functional

## Phase 6: User Story 4 - Review Workflow and Approval (P3)

**Story Goal**: User follows structured workflow to approve, reject, or reprocess invoices  
**Independent Test**: Complete review → approve/reject → verify status and audit trail

### T051: Review Completion API [US4]
**File**: `backend/src/api/review.py`  
**Description**: PUT /invoices/{id}/review endpoint for approval workflow

### T052: Data Export API [US4]
**File**: `backend/src/api/export.py`  
**Description**: POST /export endpoint for approved invoice data in CSV/JSON formats

**US4 Checkpoint**: ✅ Complete workflow with approval and export functional

## Dependencies

### User Story Dependencies
- **US1** (Document Upload) → Foundation for all other stories
- **US2** (Review Interface) → Requires US1 completion  
- **US3** (Batch Processing) → Independent, can be developed in parallel with US2
- **US4** (Workflow Approval) → Requires US2 completion

### Critical Path
US1 → US2 → US4 (MVP with complete single-document workflow)  
US3 can be developed in parallel after US1

## Parallel Execution Opportunities

### Within User Stories
- **US1**: Tests [P], Models [P], API endpoints [P], Frontend components [P]
- **US2**: Document viewer and data editor can be developed in parallel [P]
- **US3**: Queue API and dashboard UI can be developed in parallel [P]

### Cross-Story Parallelism
- US3 (Batch Processing) can start after US1 while US2 is in development
- Frontend and backend tasks within same story can run in parallel [P]

## Implementation Strategy

### MVP Definition
**Phase 3 + Phase 4** = Complete single-document upload, processing, and review workflow
- Essential for validating core value proposition
- Delivers immediate user value for single invoice processing
- Foundation for all subsequent features

### Incremental Delivery
1. **Week 1**: Phase 1-2 (Setup + Foundation) + US1 (Document Upload)
2. **Week 2**: US2 (Review Interface) - Complete MVP
3. **Week 3**: US3 (Batch Processing) - Production scalability  
4. **Week 4**: US4 (Workflow) + Polish - Complete feature set

### Test Strategy
- **TDD Mandatory**: All tests written before implementation per constitution
- **Contract-First**: API contracts drive both backend and frontend development
- **Independent Testing**: Each user story has complete test coverage for independent validation
- **Integration Checkpoints**: After each user story phase for end-to-end validation