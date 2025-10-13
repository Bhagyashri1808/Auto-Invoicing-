"""File upload service with validation and error handling."""

import os
from pathlib import Path
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
from typing import BinaryIO, Tuple, Optional
from fastapi import UploadFile, HTTPException
from models.invoice_document import FileType
from .file_storage import FileStorageService


class FileUploadService:
    """Service for handling file uploads with validation."""
    
    # Supported MIME types
    SUPPORTED_MIME_TYPES = {
        "application/pdf": FileType.PDF,
        "image/jpeg": FileType.JPG,
        "image/jpg": FileType.JPG,
        "image/png": FileType.PNG,
        "image/tiff": FileType.TIFF,
        "image/tif": FileType.TIFF,
    }
    
    # File extensions mapping
    SUPPORTED_EXTENSIONS = {
        ".pdf": FileType.PDF,
        ".jpg": FileType.JPG,
        ".jpeg": FileType.JPG,
        ".png": FileType.PNG,
        ".tiff": FileType.TIFF,
        ".tif": FileType.TIFF,
    }
    
    def __init__(self, max_file_size_mb: int = 50):
        """Initialize file upload service."""
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.storage_service = FileStorageService()
    
    def validate_file(self, file: UploadFile) -> FileType:
        """
        Validate uploaded file and return file type.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            FileType enum value
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check if file is empty
        if file.size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file not allowed"
            )
        
        # Check file size
        if file.size > self.max_file_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.max_file_size_bytes // (1024*1024)}MB"
            )
        
        # Get file extension
        file_extension = Path(file.filename or "").suffix.lower()
        
        # Validate by extension first
        if file_extension not in self.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
            )
        
        return self.SUPPORTED_EXTENSIONS[file_extension]
    
    def validate_file_content(self, file_content: bytes, expected_type: FileType) -> bool:
        """
        Validate file content matches expected type.
        
        Args:
            file_content: Raw file bytes
            expected_type: Expected FileType
            
        Returns:
            True if content matches expected type
        """
        if not MAGIC_AVAILABLE:
            # If python-magic is not available, just trust the extension validation
            return True
            
        try:
            # Use python-magic to detect file type
            mime_type = magic.from_buffer(file_content, mime=True)
            
            # Check if detected MIME type matches expected type
            if mime_type in self.SUPPORTED_MIME_TYPES:
                detected_type = self.SUPPORTED_MIME_TYPES[mime_type]
                return detected_type == expected_type
            
            return False
        except Exception:
            # If magic detection fails, trust the extension validation
            return True
    
    async def process_upload(
        self, 
        file: UploadFile
    ) -> Tuple[str, int, FileType]:
        """
        Process file upload with full validation.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (storage_path, file_size, file_type)
            
        Raises:
            HTTPException: If upload fails validation
        """
        # Validate file metadata
        file_type = self.validate_file(file)
        
        # Read file content
        try:
            file_content = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Validate file content
        if not self.validate_file_content(file_content, file_type):
            raise HTTPException(
                status_code=400,
                detail="File content does not match expected format"
            )
        
        # Store file
        try:
            # Create a BytesIO object for storage
            from io import BytesIO
            file_stream = BytesIO(file_content)
            
            storage_path, actual_size = self.storage_service.store_invoice_file(
                file_stream, 
                file.filename or f"upload.{file_type.value.lower()}"
            )
            
            return storage_path, actual_size, file_type
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store file: {str(e)}"
            )
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a stored file.
        
        Args:
            file_path: Path to stored file
            
        Returns:
            Dictionary with file information
        """
        file_obj = Path(file_path)
        
        if not file_obj.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        return {
            "path": str(file_path),
            "size": file_obj.stat().st_size,
            "exists": True,
            "extension": file_obj.suffix.lower()
        }
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a stored file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully
        """
        return self.storage_service.delete_file(file_path)
    
    @classmethod
    def get_supported_formats(cls) -> dict:
        """Get list of supported file formats."""
        return {
            "extensions": list(cls.SUPPORTED_EXTENSIONS.keys()),
            "mime_types": list(cls.SUPPORTED_MIME_TYPES.keys()),
            "types": [ft.value for ft in cls.SUPPORTED_EXTENSIONS.values()]
        }