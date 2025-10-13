"""Field correction model for recording user corrections during review."""

from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class FieldCorrection(BaseModel):
    """Model for recording specific corrections made during human review."""
    
    __tablename__ = "field_corrections"
    
    # Foreign key to review session
    review_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("review_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Correction details
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=True)
    original_confidence = Column(Float, nullable=False)
    correction_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    review_session = relationship("ReviewSession", back_populates="field_corrections")
    
    def __repr__(self):
        return f"<FieldCorrection(field='{self.field_name}', original='{self.original_value}', corrected='{self.corrected_value}')>"