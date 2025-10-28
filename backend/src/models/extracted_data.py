"""Extracted data model for structured invoice information."""

from datetime import date, datetime
from sqlalchemy import Column, String, Numeric, Date, DateTime, Boolean, Float, ForeignKey, Enum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from .enums import ExtractionMethod


class ExtractedData(BaseModel):
    """Model for structured data extracted from invoice documents."""
    
    __tablename__ = "extracted_data"
    
    # Foreign key to invoice document
    invoice_document_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("invoice_documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    # Vendor information
    vendor_name = Column(String(255), nullable=True)
    vendor_address = Column(String(500), nullable=True)
    
    # Invoice details
    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    
    # Financial information
    total_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    tax_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    subtotal_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Extraction metadata
    extraction_confidence = Column(Float, nullable=False)
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_human_verified = Column(Boolean, default=False, nullable=False)

    # Enhanced processing fields
    extraction_method = Column(Enum(ExtractionMethod), default=ExtractionMethod.OCR_ONLY, nullable=False)
    llm_processing_job_id = Column(UUID(as_uuid=True), ForeignKey("llm_processing_jobs.id", ondelete="SET NULL"), nullable=True)
    ocr_confidence_avg = Column(Float, nullable=True)
    llm_confidence_score = Column(Float, nullable=True)
    field_confidence_scores = Column(JSON, nullable=True)
    preprocessing_applied = Column(Boolean, default=False, nullable=False)
    preprocessing_method = Column(String(255), nullable=True)
    validation_errors = Column(JSON, nullable=True)
    has_manual_corrections = Column(Boolean, default=False, nullable=False)

    # Relationships
    invoice_document = relationship("InvoiceDocument", back_populates="extracted_data")
    line_items = relationship("LineItem", back_populates="extracted_data", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExtractedData(vendor='{self.vendor_name}', total={self.total_amount}, confidence={self.extraction_confidence})>"