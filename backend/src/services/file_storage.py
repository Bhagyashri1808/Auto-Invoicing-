"""File storage service for invoice documents."""

import os
import shutil
from pathlib import Path
from typing import BinaryIO
import uuid

class FileStorageService:
    """Service for managing file storage operations."""
    
    def __init__(self):
        self.storage_root = Path(__file__).parent.parent.parent.parent / "shared" / "storage"
        self.invoices_dir = self.storage_root / "invoices"
        self.temp_dir = self.storage_root / "temp"
        
        # Ensure directories exist
        self.invoices_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def store_invoice_file(self, file_content: BinaryIO, original_filename: str) -> tuple[str, int]:
        """
        Store an invoice file and return the storage path and file size.
        
        Args:
            file_content: Binary file content
            original_filename: Original filename
            
        Returns:
            Tuple of (storage_path, file_size)
        """
        # Generate unique filename to avoid conflicts
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        storage_path = self.invoices_dir / unique_filename
        
        # Write file content
        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file_content, f)
        
        # Get file size
        file_size = storage_path.stat().st_size
        
        return str(storage_path), file_size
    
    def get_file_path(self, stored_path: str) -> Path:
        """Get the full path to a stored file."""
        return Path(stored_path)
    
    def delete_file(self, stored_path: str) -> bool:
        """
        Delete a stored file.
        
        Args:
            stored_path: Path to the stored file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            Path(stored_path).unlink()
            return True
        except (FileNotFoundError, OSError):
            return False
    
    def file_exists(self, stored_path: str) -> bool:
        """Check if a stored file exists."""
        return Path(stored_path).exists()