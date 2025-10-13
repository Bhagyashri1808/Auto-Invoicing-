"""Line item model for invoice line items."""

from sqlalchemy import Column, String, Numeric, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class LineItem(BaseModel):
    """Model for individual invoice line items."""
    
    __tablename__ = "line_items"
    
    # Foreign key to extracted data
    extracted_data_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extracted_data.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Line item details
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(precision=10, scale=3), nullable=True)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=True)
    total_price = Column(Numeric(precision=10, scale=2), nullable=True)
    line_number = Column(Integer, nullable=False)
    
    # Extraction confidence for this line item
    confidence_score = Column(Float, nullable=False)
    
    # Relationships
    extracted_data = relationship("ExtractedData", back_populates="line_items")
    
    def __repr__(self):
        return f"<LineItem(description='{self.description}', quantity={self.quantity}, total={self.total_price})>"