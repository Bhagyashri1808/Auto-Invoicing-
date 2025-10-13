# Data Model Design

**Feature**: Invoice Automation with HITL Review  
**Date**: 2025-01-10  
**Backend**: SQLAlchemy models with Pydantic schemas  
**Frontend**: TypeScript interfaces generated from Pydantic

## Core Entities

### Invoice Document

Represents the uploaded invoice file and its metadata.

**Fields**:
- `id`: UUID (Primary Key)
- `filename`: String (Original filename)
- `file_path`: String (Path to stored file)
- `file_type`: Enum (PDF, JPG, PNG, TIFF)
- `file_size`: Integer (Bytes)
- `upload_date`: DateTime (ISO format)
- `processing_status`: Enum (PENDING, PROCESSING, COMPLETED, FAILED, REVIEWING, APPROVED, REJECTED)
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- `filename` must not be empty
- `file_type` must be one of supported formats
- `file_size` must be > 0 and < 50MB
- `processing_status` follows defined state transitions

**State Transitions**:
PENDING → PROCESSING → COMPLETED → REVIEWING → (APPROVED | REJECTED)
Any state → FAILED (on errors)

### Extracted Data

Contains structured information extracted from the invoice document.

**Fields**:
- `id`: UUID (Primary Key)
- `invoice_document_id`: UUID (Foreign Key to Invoice Document)
- `vendor_name`: String (nullable)
- `vendor_address`: String (nullable)
- `invoice_number`: String (nullable)
- `invoice_date`: Date (nullable)
- `due_date`: Date (nullable)
- `total_amount`: Decimal (nullable)
- `tax_amount`: Decimal (nullable)
- `subtotal_amount`: Decimal (nullable)
- `currency`: String (default "USD")
- `extraction_confidence`: Float (0.0-1.0)
- `extracted_at`: DateTime
- `is_human_verified`: Boolean (default False)

**Validation Rules**:
- `extraction_confidence` between 0.0 and 1.0
- Amount fields must be >= 0 if provided
- `currency` must be valid ISO currency code
- `invoice_date` <= current date if provided

**Relationships**:
- One-to-One with Invoice Document
- One-to-Many with Line Items
- One-to-Many with Confidence Scores

### Line Item

Represents individual invoice line items extracted from the document.

**Fields**:
- `id`: UUID (Primary Key)
- `extracted_data_id`: UUID (Foreign Key to Extracted Data)
- `description`: String (nullable)
- `quantity`: Decimal (nullable)
- `unit_price`: Decimal (nullable)
- `total_price`: Decimal (nullable)
- `line_number`: Integer
- `confidence_score`: Float (0.0-1.0)

**Validation Rules**:
- `line_number` must be > 0
- `confidence_score` between 0.0 and 1.0
- Prices must be >= 0 if provided
- `quantity` must be > 0 if provided

**Relationships**:
- Many-to-One with Extracted Data

### Review Session

Tracks human review activities and corrections made to extracted data.

**Fields**:
- `id`: UUID (Primary Key)
- `invoice_document_id`: UUID (Foreign Key to Invoice Document)
- `review_started_at`: DateTime
- `review_completed_at`: DateTime (nullable)
- `time_spent_seconds`: Integer (nullable)
- `corrections_made`: Integer (default 0)
- `final_decision`: Enum (APPROVED, REJECTED, REQUIRES_REPROCESSING)
- `reviewer_notes`: Text (nullable)

**Validation Rules**:
- `review_completed_at` must be after `review_started_at` if provided
- `time_spent_seconds` must be >= 0 if provided
- `corrections_made` must be >= 0

**Relationships**:
- One-to-One with Invoice Document
- One-to-Many with Field Corrections

### Field Correction

Records specific corrections made during human review.

**Fields**:
- `id`: UUID (Primary Key)
- `review_session_id`: UUID (Foreign Key to Review Session)
- `field_name`: String (e.g., "vendor_name", "total_amount")
- `original_value`: String (nullable)
- `corrected_value`: String (nullable)
- `original_confidence`: Float (0.0-1.0)
- `correction_timestamp`: DateTime

**Validation Rules**:
- `field_name` must be valid extractable field
- `original_confidence` between 0.0 and 1.0
- `corrected_value` must be different from `original_value`

**Relationships**:
- Many-to-One with Review Session

### Processing Job

Manages document processing workflow and queue operations.

**Fields**:
- `id`: UUID (Primary Key)
- `invoice_document_id`: UUID (Foreign Key to Invoice Document)
- `queue_position`: Integer
- `processing_mode`: Enum (SEQUENTIAL, PARALLEL)
- `started_at`: DateTime (nullable)
- `completed_at`: DateTime (nullable)
- `error_message`: Text (nullable)
- `retry_count`: Integer (default 0)
- `max_retries`: Integer (default 3)

**Validation Rules**:
- `queue_position` must be > 0
- `retry_count` must be <= `max_retries`
- `completed_at` must be after `started_at` if both provided

**Relationships**:
- One-to-One with Invoice Document

### Configuration

Stores user-configurable application settings.

**Fields**:
- `id`: UUID (Primary Key)
- `key`: String (Unique)
- `value`: String
- `data_type`: Enum (STRING, INTEGER, FLOAT, BOOLEAN)
- `updated_at`: DateTime

**Validation Rules**:
- `key` must be unique
- `value` must be parseable as specified `data_type`

**Default Configuration**:
- `ocr_confidence_threshold`: 0.7 (Float)
- `processing_mode`: "SEQUENTIAL" (String)
- `max_file_size_mb`: 50 (Integer)
- `auto_save_corrections`: true (Boolean)

## Entity Relationships

```
Invoice Document (1) ←→ (1) Extracted Data
Invoice Document (1) ←→ (1) Review Session  
Invoice Document (1) ←→ (1) Processing Job
Extracted Data (1) ←→ (many) Line Item
Review Session (1) ←→ (many) Field Correction
```

## Database Schema Notes

- All entities use UUIDs for primary keys to avoid conflicts
- Timestamps stored in UTC with timezone information
- Decimal fields use appropriate precision for currency (2 decimal places)
- Soft deletes not implemented (permanent record keeping for audit)
- Database indexes on frequently queried fields (processing_status, upload_date)
- Foreign key constraints enforce referential integrity