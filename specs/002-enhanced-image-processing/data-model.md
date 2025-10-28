# Data Model Design

**Feature**: Enhanced Image Processing with Local LLM Integration  
**Date**: 2025-01-23  
**Backend**: SQLAlchemy models with Pydantic schemas  
**Frontend**: TypeScript interfaces generated from Pydantic

## Enhanced Core Entities

### Preprocessing Configuration *(New)*

Stores user-configurable parameters for image preprocessing operations.

**Fields**:
- `id`: UUID (Primary Key)
- `user_id`: String (for future multi-user support, default: "default")
- `operation_type`: Enum (THRESHOLD, DESKEW, COMBINED)
- `target_width`: Integer (range: 800-3200, default: 1600)
- `threshold_block_size`: Integer (range: 11-51, odd numbers, default: 11)
- `threshold_constant`: Float (range: 5.0-20.0, default: 10.0)
- `bilateral_filter_d`: Integer (range: 5-15, default: 9)
- `bilateral_sigma_color`: Float (range: 50-150, default: 75.0)
- `bilateral_sigma_space`: Float (range: 50-150, default: 75.0)
- `is_default`: Boolean (default: False)
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- `threshold_block_size` must be odd number
- `target_width` must be between 800 and 3200
- Only one configuration can have `is_default = True` per user
- `operation_type` determines which parameters are applied

**Relationships**:
- One-to-Many with Processing Job

### LLM Processing Job *(New)*

Manages local LLM model interaction and processing state.

**Fields**:
- `id`: UUID (Primary Key)
- `invoice_document_id`: UUID (Foreign Key to Invoice Document)
- `preprocessing_config_id`: UUID (Foreign Key to Preprocessing Configuration)
- `llm_model_name`: String (e.g., "llama3.2:3b")
- `preprocessed_image_path`: String (path to temporary processed image)
- `llm_request_payload`: JSON (full request sent to LLM)
- `llm_response_raw`: JSON (raw response from LLM)
- `llm_response_validated`: JSON (validated and parsed response)
- `processing_started_at`: DateTime
- `llm_started_at`: DateTime (nullable)
- `llm_completed_at`: DateTime (nullable)
- `processing_completed_at`: DateTime (nullable)
- `timeout_occurred`: Boolean (default: False)
- `fallback_triggered`: Boolean (default: False)
- `error_message`: Text (nullable)
- `retry_count`: Integer (default: 0)
- `max_retries`: Integer (default: 3)
- `memory_peak_mb`: Integer (nullable)
- `processing_duration_ms`: Integer (nullable)

**Validation Rules**:
- `retry_count` must be <= `max_retries`
- `llm_completed_at` must be after `llm_started_at` if both provided
- `processing_completed_at` must be after `processing_started_at` if provided
- `preprocessed_image_path` must be valid file path if provided

**Relationships**:
- One-to-One with Invoice Document
- Many-to-One with Preprocessing Configuration

### Enhanced Extracted Data *(Extended)*

Extended from existing model to include LLM-specific fields and confidence tracking.

**New Fields** (additions to existing model):
- `extraction_method`: Enum (OCR_ONLY, LLM_PRIMARY, LLM_FALLBACK)
- `llm_processing_job_id`: UUID (Foreign Key to LLM Processing Job, nullable)
- `ocr_confidence_avg`: Float (0.0-1.0, nullable)
- `llm_confidence_score`: Float (0.0-1.0, nullable)
- `field_confidence_scores`: JSON (confidence per field)
- `preprocessing_applied`: Boolean (default: False)
- `preprocessing_method`: String (nullable, e.g., "threshold+deskew")
- `validation_errors`: JSON (nullable, validation failure details)
- `has_manual_corrections`: Boolean (default: False)

**Enhanced Validation Rules**:
- At least one of `ocr_confidence_avg` or `llm_confidence_score` must be provided
- `extraction_method` determines which confidence scores are required
- `field_confidence_scores` must contain scores for all non-null extracted fields
- `llm_processing_job_id` required when `extraction_method` includes LLM

**Relationships**:
- One-to-One with Invoice Document (existing)
- One-to-Many with Line Items (existing)
- One-to-One with LLM Processing Job (new)

### Processing Performance Metrics *(New)*

Tracks performance and accuracy metrics for optimization and monitoring.

**Fields**:
- `id`: UUID (Primary Key)
- `invoice_document_id`: UUID (Foreign Key to Invoice Document)
- `processing_date`: Date
- `extraction_method`: Enum (OCR_ONLY, LLM_PRIMARY, LLM_FALLBACK)
- `preprocessing_duration_ms`: Integer (nullable)
- `ocr_duration_ms`: Integer (nullable)
- `llm_duration_ms`: Integer (nullable)
- `total_duration_ms`: Integer
- `memory_peak_mb`: Float
- `file_size_mb`: Float
- `image_dimensions`: String (e.g., "1200x800")
- `preprocessing_applied`: Boolean
- `timeout_occurred`: Boolean
- `error_occurred`: Boolean
- `accuracy_score`: Float (0.0-1.0, nullable, manual assessment)
- `user_corrections_count`: Integer (default: 0)

**Validation Rules**:
- `total_duration_ms` must be >= sum of individual durations
- `memory_peak_mb` must be > 0
- `accuracy_score` between 0.0 and 1.0 if provided
- `user_corrections_count` must be >= 0

**Relationships**:
- Many-to-One with Invoice Document

### Enhanced Configuration *(Extended)*

Extended from existing model to include LLM and preprocessing settings.

**New Entries** (additions to existing configuration):
- `llm_model_name`: "llama3.2:3b" (String)
- `llm_timeout_seconds`: 60 (Integer)
- `llm_base_url`: "http://localhost:11434" (String)
- `memory_limit_mb`: 2048 (Integer)
- `preprocessing_enabled`: true (Boolean)
- `default_preprocessing_operation`: "threshold" (String)
- `enable_fallback_to_ocr`: true (Boolean)
- `max_preprocessing_retries`: 2 (Integer)
- `cleanup_temp_files`: true (Boolean)
- `temp_file_retention_hours`: 24 (Integer)

**Enhanced Validation Rules**:
- `llm_timeout_seconds` must be between 10 and 300
- `memory_limit_mb` must be between 512 and 8192
- `llm_base_url` must be valid URL format
- `default_preprocessing_operation` must be valid operation type

## Entity Relationships

```
Invoice Document (1) ←→ (1) Enhanced Extracted Data
Invoice Document (1) ←→ (1) LLM Processing Job
Invoice Document (1) ←→ (many) Processing Performance Metrics
Enhanced Extracted Data (1) ←→ (many) Line Item
LLM Processing Job (many) ←→ (1) Preprocessing Configuration
LLM Processing Job (1) ←→ (1) Enhanced Extracted Data
```

## Database Schema Extensions

### New Tables

```sql
-- Preprocessing configurations
CREATE TABLE preprocessing_configurations (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL DEFAULT 'default',
    operation_type VARCHAR(50) NOT NULL,
    target_width INTEGER NOT NULL DEFAULT 1600,
    threshold_block_size INTEGER NOT NULL DEFAULT 11,
    threshold_constant FLOAT NOT NULL DEFAULT 10.0,
    bilateral_filter_d INTEGER NOT NULL DEFAULT 9,
    bilateral_sigma_color FLOAT NOT NULL DEFAULT 75.0,
    bilateral_sigma_space FLOAT NOT NULL DEFAULT 75.0,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_threshold_block_size CHECK (threshold_block_size % 2 = 1),
    CONSTRAINT valid_target_width CHECK (target_width BETWEEN 800 AND 3200),
    CONSTRAINT valid_operation_type CHECK (operation_type IN ('THRESHOLD', 'DESKEW', 'COMBINED'))
);

-- LLM processing jobs
CREATE TABLE llm_processing_jobs (
    id UUID PRIMARY KEY,
    invoice_document_id UUID NOT NULL REFERENCES invoice_documents(id),
    preprocessing_config_id UUID REFERENCES preprocessing_configurations(id),
    llm_model_name VARCHAR(255) NOT NULL,
    preprocessed_image_path TEXT,
    llm_request_payload JSON,
    llm_response_raw JSON,
    llm_response_validated JSON,
    processing_started_at TIMESTAMP NOT NULL,
    llm_started_at TIMESTAMP,
    llm_completed_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    timeout_occurred BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    memory_peak_mb INTEGER,
    processing_duration_ms INTEGER,
    
    CONSTRAINT valid_retry_count CHECK (retry_count <= max_retries)
);

-- Processing performance metrics
CREATE TABLE processing_performance_metrics (
    id UUID PRIMARY KEY,
    invoice_document_id UUID NOT NULL REFERENCES invoice_documents(id),
    processing_date DATE NOT NULL,
    extraction_method VARCHAR(50) NOT NULL,
    preprocessing_duration_ms INTEGER,
    ocr_duration_ms INTEGER,
    llm_duration_ms INTEGER,
    total_duration_ms INTEGER NOT NULL,
    memory_peak_mb FLOAT NOT NULL,
    file_size_mb FLOAT NOT NULL,
    image_dimensions VARCHAR(50),
    preprocessing_applied BOOLEAN NOT NULL,
    timeout_occurred BOOLEAN NOT NULL,
    error_occurred BOOLEAN NOT NULL,
    accuracy_score FLOAT,
    user_corrections_count INTEGER NOT NULL DEFAULT 0,
    
    CONSTRAINT valid_accuracy_score CHECK (accuracy_score IS NULL OR (accuracy_score BETWEEN 0.0 AND 1.0)),
    CONSTRAINT valid_extraction_method CHECK (extraction_method IN ('OCR_ONLY', 'LLM_PRIMARY', 'LLM_FALLBACK'))
);
```

### Extended Tables

```sql
-- Add columns to existing extracted_data table
ALTER TABLE extracted_data ADD COLUMN extraction_method VARCHAR(50) DEFAULT 'OCR_ONLY';
ALTER TABLE extracted_data ADD COLUMN llm_processing_job_id UUID REFERENCES llm_processing_jobs(id);
ALTER TABLE extracted_data ADD COLUMN ocr_confidence_avg FLOAT;
ALTER TABLE extracted_data ADD COLUMN llm_confidence_score FLOAT;
ALTER TABLE extracted_data ADD COLUMN field_confidence_scores JSON;
ALTER TABLE extracted_data ADD COLUMN preprocessing_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE extracted_data ADD COLUMN preprocessing_method VARCHAR(255);
ALTER TABLE extracted_data ADD COLUMN validation_errors JSON;
ALTER TABLE extracted_data ADD COLUMN has_manual_corrections BOOLEAN DEFAULT FALSE;
```

## Database Indexes

```sql
-- Performance optimization indexes
CREATE INDEX idx_llm_jobs_invoice_id ON llm_processing_jobs(invoice_document_id);
CREATE INDEX idx_llm_jobs_status ON llm_processing_jobs(processing_completed_at, timeout_occurred);
CREATE INDEX idx_preprocessing_configs_default ON preprocessing_configurations(is_default) WHERE is_default = TRUE;
CREATE INDEX idx_performance_metrics_date ON processing_performance_metrics(processing_date);
CREATE INDEX idx_performance_metrics_method ON processing_performance_metrics(extraction_method);
CREATE INDEX idx_extracted_data_method ON extracted_data(extraction_method);
```

## Migration Strategy

1. **Phase 1**: Create new tables (preprocessing_configurations, llm_processing_jobs, processing_performance_metrics)
2. **Phase 2**: Add new columns to extracted_data table with default values
3. **Phase 3**: Populate default preprocessing configuration
4. **Phase 4**: Create database indexes for performance optimization
5. **Phase 5**: Update application code to use enhanced data models

All migrations maintain backward compatibility with existing data and API contracts.