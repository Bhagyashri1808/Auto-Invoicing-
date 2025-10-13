"""Review session model for tracking human review activities."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class ReviewDecision(enum.Enum):
    """Review decision enumeration."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REPROCESSING = "REQUIRES_REPROCESSING"


class ReviewSession(BaseModel):
    """Model for tracking human review activities and corrections."""
    
    __tablename__ = "review_sessions"
    
    # Foreign key to invoice document
    invoice_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoice_documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    # Review timing
    review_started_at = Column(DateTime, nullable=False)
    review_completed_at = Column(DateTime, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    
    # Review metrics
    corrections_made = Column(Integer, default=0, nullable=False)
    final_decision = Column(Enum(ReviewDecision), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    
    # Relationships
    invoice_document = relationship("InvoiceDocument", back_populates="review_session")
    field_corrections = relationship("FieldCorrection", back_populates="review_session", cascade="all, delete-orphan")
    
    @property
    def is_completed(self) -> bool:
        """Check if review is completed."""
        return self.review_completed_at is not None and self.final_decision is not None
    
    @property
    def duration_minutes(self) -> float | None:
        """Get review duration in minutes."""
        if self.time_spent_seconds is not None:
            return round(self.time_spent_seconds / 60.0, 2)
        return None
    
    def __repr__(self):
        return f"<ReviewSession(corrections={self.corrections_made}, decision='{self.final_decision}', completed={self.is_completed})>"