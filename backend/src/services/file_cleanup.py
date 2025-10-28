"""Temporary file cleanup service for preprocessed images and general temp files."""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

from database.config import DATABASE_DIR


class FileCleanupService:
    """Service for managing temporary file cleanup."""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.retention_seconds = retention_hours * 3600
        self.logger = logging.getLogger(__name__)
        
        # Define cleanup directories
        self.temp_dir = Path(__file__).parent.parent.parent.parent / "shared" / "storage" / "temp"
        self.preprocessed_dir = Path(__file__).parent.parent.parent.parent / "shared" / "storage" / "preprocessed"
        
        # Ensure directories exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessed_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_file(self, file_path: str) -> bool:
        """Clean up a specific file immediately."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.info(f"Cleaned up file: {file_path}")
                return True
            else:
                self.logger.debug(f"File not found for cleanup: {file_path}")
                return False
        except Exception as e:
            self.logger.error(f"Error cleaning up file {file_path}: {e}")
            return False
    
    def cleanup_preprocessed_image(self, image_path: str) -> bool:
        """Clean up a specific preprocessed image file."""
        if not image_path:
            return True
        
        # Ensure we're only cleaning up files in the preprocessed directory
        path = Path(image_path)
        if not str(path).startswith(str(self.preprocessed_dir)):
            self.logger.warning(f"Attempted to clean up file outside preprocessed directory: {image_path}")
            return False
        
        return self.cleanup_file(image_path)
    
    def cleanup_old_files(self, directory: Path, max_age_seconds: Optional[int] = None) -> int:
        """Clean up old files in a directory."""
        max_age = max_age_seconds or self.retention_seconds
        current_time = time.time()
        cleaned_count = 0
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            self.logger.debug(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            self.logger.error(f"Error cleaning up old file {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return cleaned_count
    
    def cleanup_old_preprocessed_images(self, max_age_seconds: Optional[int] = None) -> int:
        """Clean up old preprocessed image files."""
        self.logger.info("Starting cleanup of old preprocessed images")
        cleaned_count = self.cleanup_old_files(self.preprocessed_dir, max_age_seconds)
        self.logger.info(f"Cleaned up {cleaned_count} old preprocessed images")
        return cleaned_count
    
    def cleanup_old_temp_files(self, max_age_seconds: Optional[int] = None) -> int:
        """Clean up old temporary files."""
        self.logger.info("Starting cleanup of old temporary files")
        cleaned_count = self.cleanup_old_files(self.temp_dir, max_age_seconds)
        self.logger.info(f"Cleaned up {cleaned_count} old temporary files")
        return cleaned_count
    
    def cleanup_all_old_files(self, max_age_seconds: Optional[int] = None) -> dict:
        """Clean up all old files in temp and preprocessed directories."""
        results = {
            "temp_files_cleaned": self.cleanup_old_temp_files(max_age_seconds),
            "preprocessed_images_cleaned": self.cleanup_old_preprocessed_images(max_age_seconds)
        }
        
        total_cleaned = sum(results.values())
        self.logger.info(f"Total files cleaned: {total_cleaned}")
        
        return results
    
    async def schedule_cleanup(
        self,
        interval_hours: int = 6,
        max_age_seconds: Optional[int] = None
    ) -> None:
        """Schedule periodic cleanup of old files."""
        interval_seconds = interval_hours * 3600
        self.logger.info(f"Starting scheduled cleanup every {interval_hours} hours")
        
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                self.cleanup_all_old_files(max_age_seconds)
            except Exception as e:
                self.logger.error(f"Error in scheduled cleanup: {e}")
    
    def get_directory_stats(self) -> dict:
        """Get statistics about temporary directories."""
        stats = {}
        
        for name, directory in [("temp", self.temp_dir), ("preprocessed", self.preprocessed_dir)]:
            try:
                files = list(directory.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                
                stats[name] = {
                    "file_count": file_count,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "directory_path": str(directory)
                }
            except Exception as e:
                self.logger.error(f"Error getting stats for {name} directory: {e}")
                stats[name] = {"error": str(e)}
        
        return stats


# Global cleanup service instance
file_cleanup_service = FileCleanupService()