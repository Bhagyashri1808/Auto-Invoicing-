"""Pydantic schemas for API serialization and validation."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from .enums import ProcessingStatus, FileType, ProcessingMode, ReviewDecision, ConfigDataType


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime


# Invoice Document schemas
class InvoiceDocumentBase(BaseSchema):
    filename: str = Field(..., max_length=255)
    file_type: FileType
    file_size: int = Field(..., gt=0)
    upload_date: datetime
    processing_status: ProcessingStatus = ProcessingStatus.PENDING


class InvoiceDocumentCreate(InvoiceDocumentBase):
    file_path: str = Field(..., max_length=500)


class InvoiceDocument(InvoiceDocumentBase, TimestampedSchema):
    pass


class InvoiceDocumentResponse(InvoiceDocument):
    """Response schema for invoice document API endpoints."""
    pass


class InvoiceDocumentDetail(InvoiceDocument):
    extracted_data: Optional["ExtractedData"] = None
    review_session: Optional["ReviewSession"] = None
    processing_job: Optional["ProcessingJob"] = None


# Extracted Data schemas
class ExtractedDataBase(BaseSchema):
    vendor_name: Optional[str] = Field(None, max_length=255)
    vendor_address: Optional[str] = Field(None, max_length=500)
    invoice_number: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    subtotal_amount: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)
    is_human_verified: bool = False


class ExtractedDataCreate(ExtractedDataBase):
    invoice_document_id: UUID
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractedData(ExtractedDataBase, TimestampedSchema):
    invoice_document_id: UUID


class ExtractedDataResponse(ExtractedData):
    """Response schema for extracted data API endpoints."""
    pass


class ExtractedDataUpdate(BaseSchema):
    vendor_name: Optional[str] = Field(None, max_length=255)
    vendor_address: Optional[str] = Field(None, max_length=500)
    invoice_number: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    subtotal_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)


class ExtractedDataDetail(ExtractedData):
    line_items: List["LineItem"] = []


# Line Item schemas
class LineItemBase(BaseSchema):
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)
    line_number: int = Field(..., gt=0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class LineItemCreate(LineItemBase):
    extracted_data_id: UUID


class LineItem(LineItemBase, TimestampedSchema):
    extracted_data_id: UUID


class LineItemUpdate(BaseSchema):
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)


# Processing Job schemas
class ProcessingJobBase(BaseSchema):
    queue_position: int = Field(..., gt=0)
    processing_mode: ProcessingMode
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = Field(0, ge=0)
    max_retries: int = Field(3, ge=0)


class ProcessingJobCreate(ProcessingJobBase):
    invoice_document_id: UUID


class ProcessingJob(ProcessingJobBase, TimestampedSchema):
    invoice_document_id: UUID


class ProcessingJobResponse(ProcessingJob):
    """Response schema for processing job API endpoints."""
    pass


# Review Session schemas
class ReviewSessionBase(BaseSchema):
    review_started_at: datetime
    review_completed_at: Optional[datetime] = None
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    corrections_made: int = Field(0, ge=0)
    final_decision: Optional[ReviewDecision] = None
    reviewer_notes: Optional[str] = None


class ReviewSessionCreate(BaseSchema):
    invoice_document_id: UUID
    review_started_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewSession(ReviewSessionBase, TimestampedSchema):
    invoice_document_id: UUID


class ReviewSessionResponse(ReviewSession):
    """Response schema for review session API endpoints."""
    pass


class ReviewCompletion(BaseSchema):
    final_decision: ReviewDecision
    reviewer_notes: Optional[str] = None


# Field Correction schemas
class FieldCorrectionBase(BaseSchema):
    field_name: str = Field(..., max_length=100)
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    original_confidence: float = Field(..., ge=0.0, le=1.0)
    correction_timestamp: datetime = Field(default_factory=datetime.utcnow)


class FieldCorrectionCreate(FieldCorrectionBase):
    review_session_id: UUID


class FieldCorrection(FieldCorrectionBase, TimestampedSchema):
    review_session_id: UUID


# Configuration schemas
class ConfigurationBase(BaseSchema):
    key: str = Field(..., max_length=100)
    value: str = Field(..., max_length=500)
    data_type: ConfigDataType


class ConfigurationCreate(ConfigurationBase):
    pass


class Configuration(ConfigurationBase, TimestampedSchema):
    pass


class ProcessingConfig(BaseSchema):
    ocr_confidence_threshold: float = Field(..., ge=0.0, le=1.0)
    processing_mode: ProcessingMode
    max_file_size_mb: int = Field(..., ge=1, le=100)
    auto_save_corrections: bool


class ProcessingConfigUpdate(BaseSchema):
    ocr_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_mode: Optional[ProcessingMode] = None
    max_file_size_mb: Optional[int] = Field(None, ge=1, le=100)
    auto_save_corrections: Optional[bool] = None


# Error response schema
class ErrorResponse(BaseSchema):
    error: str
    message: str
    details: Optional[dict] = None


# Pagination schemas
class PaginatedResponse(BaseSchema):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)


class InvoiceDocumentList(PaginatedResponse):
    invoices: List[InvoiceDocument]


# Export schemas
class ExportRequest(BaseSchema):
    format: str = Field(..., pattern="^(csv|json)$")
    invoice_ids: List[UUID]
    include_line_items: bool = True


# Forward references
ExtractedDataDetail.model_rebuild()
InvoiceDocumentDetail.model_rebuild()