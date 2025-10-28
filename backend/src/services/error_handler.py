"""Error handling framework for preprocessing operations."""

import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel


class ErrorType(str, Enum):
    """Types of errors that can occur during processing."""
    PREPROCESSING_ERROR = "PREPROCESSING_ERROR"
    LLM_CONNECTION_ERROR = "LLM_CONNECTION_ERROR"
    LLM_TIMEOUT_ERROR = "LLM_TIMEOUT_ERROR"
    LLM_RESPONSE_ERROR = "LLM_RESPONSE_ERROR"
    MEMORY_LIMIT_ERROR = "MEMORY_LIMIT_ERROR"
    FILE_ACCESS_ERROR = "FILE_ACCESS_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ProcessingError(Exception):
    """Custom exception for processing errors."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_type = error_type
        self.context = context or {}
        self.original_exception = original_exception
        self.error_id = str(uuid4())
        super().__init__(message)


class ErrorContext(BaseModel):
    """Context information for error reporting."""
    error_id: str
    error_type: ErrorType
    message: str
    context: Dict[str, Any]
    timestamp: str
    traceback: Optional[str] = None


class ErrorHandler:
    """Centralized error handling for preprocessing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_preprocessing_error(
        self,
        operation: str,
        file_path: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessingError:
        """Handle preprocessing operation errors."""
        error_context = {
            "operation": operation,
            "file_path": file_path,
            **(context or {})
        }
        
        if isinstance(error, MemoryError):
            error_type = ErrorType.MEMORY_LIMIT_ERROR
            message = f"Memory limit exceeded during {operation}"
        elif isinstance(error, FileNotFoundError):
            error_type = ErrorType.FILE_ACCESS_ERROR
            message = f"File not found during {operation}: {file_path}"
        elif isinstance(error, PermissionError):
            error_type = ErrorType.FILE_ACCESS_ERROR
            message = f"Permission denied accessing file during {operation}: {file_path}"
        else:
            error_type = ErrorType.PREPROCESSING_ERROR
            message = f"Error during {operation}: {str(error)}"
        
        processing_error = ProcessingError(
            message=message,
            error_type=error_type,
            context=error_context,
            original_exception=error
        )
        
        self._log_error(processing_error)
        return processing_error
    
    def handle_llm_error(
        self,
        operation: str,
        model_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessingError:
        """Handle LLM operation errors."""
        error_context = {
            "operation": operation,
            "model_name": model_name,
            **(context or {})
        }
        
        if "timeout" in str(error).lower():
            error_type = ErrorType.LLM_TIMEOUT_ERROR
            message = f"LLM request timeout for {model_name} during {operation}"
        elif "connection" in str(error).lower():
            error_type = ErrorType.LLM_CONNECTION_ERROR
            message = f"Failed to connect to LLM {model_name} during {operation}"
        elif "response" in str(error).lower() or "json" in str(error).lower():
            error_type = ErrorType.LLM_RESPONSE_ERROR
            message = f"Invalid response from LLM {model_name} during {operation}"
        else:
            error_type = ErrorType.LLM_CONNECTION_ERROR
            message = f"LLM error for {model_name} during {operation}: {str(error)}"
        
        processing_error = ProcessingError(
            message=message,
            error_type=error_type,
            context=error_context,
            original_exception=error
        )
        
        self._log_error(processing_error)
        return processing_error
    
    def handle_validation_error(
        self,
        field: str,
        value: Any,
        expected: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessingError:
        """Handle validation errors."""
        error_context = {
            "field": field,
            "value": str(value),
            "expected": expected,
            **(context or {})
        }
        
        message = f"Validation error for {field}: expected {expected}, got {value}"
        
        processing_error = ProcessingError(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            context=error_context
        )
        
        self._log_error(processing_error)
        return processing_error
    
    def handle_unknown_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessingError:
        """Handle unknown/unexpected errors."""
        error_context = {
            "operation": operation,
            **(context or {})
        }
        
        message = f"Unknown error during {operation}: {str(error)}"
        
        processing_error = ProcessingError(
            message=message,
            error_type=ErrorType.UNKNOWN_ERROR,
            context=error_context,
            original_exception=error
        )
        
        self._log_error(processing_error)
        return processing_error
    
    def _log_error(self, error: ProcessingError) -> None:
        """Log error with appropriate level and context."""
        error_context = ErrorContext(
            error_id=error.error_id,
            error_type=error.error_type,
            message=error.message,
            context=error.context,
            timestamp=str(error.__class__.__module__),
            traceback=traceback.format_exc() if error.original_exception else None
        )
        
        # Log with appropriate level based on error type
        if error.error_type in [ErrorType.MEMORY_LIMIT_ERROR, ErrorType.LLM_TIMEOUT_ERROR]:
            self.logger.warning(f"Processing warning [{error.error_id}]: {error.message}")
        elif error.error_type in [ErrorType.VALIDATION_ERROR, ErrorType.FILE_ACCESS_ERROR]:
            self.logger.error(f"Processing error [{error.error_id}]: {error.message}")
        else:
            self.logger.critical(f"Critical processing error [{error.error_id}]: {error.message}")
        
        # Log context details at debug level
        self.logger.debug(f"Error context [{error.error_id}]: {error_context.dict()}")
    
    def create_error_response(self, error: ProcessingError) -> Dict[str, Any]:
        """Create standardized error response for API."""
        return {
            "error": error.error_type.value,
            "message": error.message,
            "error_id": error.error_id,
            "details": error.context,
            "processing_context": {
                "preprocessing_attempted": error.context.get("preprocessing_attempted", False),
                "llm_attempted": error.context.get("llm_attempted", False),
                "fallback_used": error.context.get("fallback_used", False)
            }
        }


# Global error handler instance
error_handler = ErrorHandler()