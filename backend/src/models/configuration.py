"""Configuration model for user-configurable application settings."""

import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UniqueConstraint, Enum
from .base import BaseModel


class ConfigDataType(enum.Enum):
    """Configuration data type enumeration."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"


class Configuration(BaseModel):
    """Model for storing user-configurable application settings."""
    
    __tablename__ = "configurations"
    
    key = Column(String(100), nullable=False, unique=True)
    value = Column(String(500), nullable=False)
    data_type = Column(Enum(ConfigDataType), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Ensure key uniqueness at database level
    __table_args__ = (
        UniqueConstraint('key', name='uq_configuration_key'),
    )
    
    def get_typed_value(self):
        """Get the configuration value converted to its proper type."""
        if self.data_type == ConfigDataType.STRING:
            return self.value
        elif self.data_type == ConfigDataType.INTEGER:
            return int(self.value)
        elif self.data_type == ConfigDataType.FLOAT:
            return float(self.value)
        elif self.data_type == ConfigDataType.BOOLEAN:
            return self.value.lower() in ("true", "1", "yes")
        else:
            return self.value
    
    def set_typed_value(self, value):
        """Set the configuration value from a typed value."""
        if self.data_type == ConfigDataType.BOOLEAN:
            self.value = "true" if value else "false"
        else:
            self.value = str(value)
    
    @classmethod
    def get_default_configs(cls):
        """Get default configuration values."""
        return [
            {
                "key": "ocr_confidence_threshold",
                "value": "0.7",
                "data_type": ConfigDataType.FLOAT
            },
            {
                "key": "processing_mode",
                "value": "SEQUENTIAL",
                "data_type": ConfigDataType.STRING
            },
            {
                "key": "max_file_size_mb",
                "value": "50",
                "data_type": ConfigDataType.INTEGER
            },
            {
                "key": "auto_save_corrections",
                "value": "true",
                "data_type": ConfigDataType.BOOLEAN
            }
        ]
    
    def __repr__(self):
        return f"<Configuration(key='{self.key}', value='{self.value}', type='{self.data_type.value}')>"