"""Pydantic models for preprocessing configuration."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class PreprocessingOperation(str, Enum):
    """Enum for preprocessing operation types."""
    THRESHOLD = "THRESHOLD"
    DESKEW = "DESKEW"
    COMBINED = "COMBINED"


class PreprocessingConfigurationDB(Base):
    """SQLAlchemy model for preprocessing configurations."""
    __tablename__ = "preprocessing_configurations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(255), nullable=False, default="default")
    operation_type = Column(String(50), nullable=False)
    target_width = Column(Integer, nullable=False, default=1600)
    threshold_block_size = Column(Integer, nullable=False, default=11)
    threshold_constant = Column(Float, nullable=False, default=10.0)
    bilateral_filter_d = Column(Integer, nullable=False, default=9)
    bilateral_sigma_color = Column(Float, nullable=False, default=75.0)
    bilateral_sigma_space = Column(Float, nullable=False, default=75.0)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    llm_jobs = relationship("LLMProcessingJobDB", back_populates="preprocessing_config", lazy="select")

    __table_args__ = (
        CheckConstraint('threshold_block_size % 2 = 1', name='valid_threshold_block_size'),
        CheckConstraint('target_width BETWEEN 800 AND 3200', name='valid_target_width'),
        CheckConstraint("operation_type IN ('THRESHOLD', 'DESKEW', 'COMBINED')", name='valid_operation_type'),
    )


class PreprocessingConfigurationBase(BaseModel):
    """Base schema for preprocessing configuration."""
    operation_type: PreprocessingOperation
    target_width: int = Field(default=1600, ge=800, le=3200)
    threshold_block_size: int = Field(default=11, ge=11, le=51)
    threshold_constant: float = Field(default=10.0, ge=5.0, le=20.0)
    bilateral_filter_d: int = Field(default=9, ge=5, le=15)
    bilateral_sigma_color: float = Field(default=75.0, ge=50.0, le=150.0)
    bilateral_sigma_space: float = Field(default=75.0, ge=50.0, le=150.0)
    is_default: bool = False

    @validator('threshold_block_size')
    def validate_threshold_block_size_odd(cls, v):
        """Ensure threshold_block_size is odd."""
        if v % 2 == 0:
            raise ValueError('threshold_block_size must be an odd number')
        return v


class PreprocessingConfigurationCreate(PreprocessingConfigurationBase):
    """Schema for creating preprocessing configuration."""
    user_id: str = "default"


class PreprocessingConfigurationUpdate(BaseModel):
    """Schema for updating preprocessing configuration."""
    operation_type: Optional[PreprocessingOperation] = None
    target_width: Optional[int] = Field(None, ge=800, le=3200)
    threshold_block_size: Optional[int] = Field(None, ge=11, le=51)
    threshold_constant: Optional[float] = Field(None, ge=5.0, le=20.0)
    bilateral_filter_d: Optional[int] = Field(None, ge=5, le=15)
    bilateral_sigma_color: Optional[float] = Field(None, ge=50.0, le=150.0)
    bilateral_sigma_space: Optional[float] = Field(None, ge=50.0, le=150.0)
    is_default: Optional[bool] = None

    @validator('threshold_block_size')
    def validate_threshold_block_size_odd(cls, v):
        """Ensure threshold_block_size is odd."""
        if v is not None and v % 2 == 0:
            raise ValueError('threshold_block_size must be an odd number')
        return v


class PreprocessingConfiguration(PreprocessingConfigurationBase):
    """Schema for preprocessing configuration response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True