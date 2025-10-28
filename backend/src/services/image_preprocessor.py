"""OpenCV-based image preprocessing service for invoice enhancement."""

import cv2
import numpy as np
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from PIL import Image

from .error_handler import error_handler, ErrorType, ProcessingError
from .file_cleanup import file_cleanup_service
from models.preprocessing import PreprocessingOperation
from database.config import MEMORY_LIMIT_MB


class ImagePreprocessor:
    """Service for preprocessing invoice images to improve OCR and LLM accuracy."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_limit_bytes = MEMORY_LIMIT_MB * 1024 * 1024
        
        # Storage path for preprocessed images
        self.preprocessed_dir = Path(__file__).parent.parent.parent.parent / "shared" / "storage" / "preprocessed"
        self.preprocessed_dir.mkdir(parents=True, exist_ok=True)
    
    def preprocess_image(
        self,
        image_path: str,
        operation: PreprocessingOperation,
        target_width: int = 1600,
        threshold_block_size: int = 11,
        threshold_constant: float = 10.0,
        bilateral_filter_d: int = 9,
        bilateral_sigma_color: float = 75.0,
        bilateral_sigma_space: float = 75.0
    ) -> Dict[str, Any]:
        """
        Preprocess an image using specified operations.
        
        Args:
            image_path: Path to input image
            operation: Type of preprocessing operation
            target_width: Target width for resizing
            threshold_block_size: Block size for adaptive thresholding (must be odd)
            threshold_constant: Constant for adaptive thresholding
            bilateral_filter_d: Diameter for bilateral filtering
            bilateral_sigma_color: Sigma color for bilateral filtering
            bilateral_sigma_space: Sigma space for bilateral filtering
            
        Returns:
            Dictionary containing processed image path and metadata
        """
        start_time = time.time()
        
        try:
            # Validate input parameters
            self._validate_parameters(
                threshold_block_size, threshold_constant, target_width,
                bilateral_filter_d, bilateral_sigma_color, bilateral_sigma_space
            )
            
            # Load and validate image
            image = self._load_image(image_path)
            
            # Check memory constraints
            self._check_memory_constraints(image, target_width)
            
            # Apply preprocessing operations
            processed_image, metadata = self._apply_preprocessing(
                image, operation, target_width, threshold_block_size,
                threshold_constant, bilateral_filter_d, bilateral_sigma_color, bilateral_sigma_space
            )
            
            # Save processed image
            output_path = self._save_processed_image(processed_image, image_path)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Prepare result
            result = {
                "processed_image_path": str(output_path),
                "operation_type": operation.value,
                "processing_metadata": {
                    **metadata,
                    "processing_time_ms": processing_time_ms,
                    "original_image_path": image_path,
                    "target_width": target_width,
                    "parameters_used": {
                        "threshold_block_size": threshold_block_size,
                        "threshold_constant": threshold_constant,
                        "bilateral_filter_d": bilateral_filter_d,
                        "bilateral_sigma_color": bilateral_sigma_color,
                        "bilateral_sigma_space": bilateral_sigma_space
                    }
                }
            }
            
            self.logger.info(f"Successfully preprocessed image: {image_path} -> {output_path}")
            return result
            
        except Exception as e:
            # Handle and re-raise as ProcessingError
            raise error_handler.handle_preprocessing_error(
                operation=f"preprocess_image_{operation.value}",
                file_path=image_path,
                error=e,
                context={
                    "target_width": target_width,
                    "threshold_block_size": threshold_block_size,
                    "operation": operation.value
                }
            )
    
    def _validate_parameters(
        self,
        threshold_block_size: int,
        threshold_constant: float,
        target_width: int,
        bilateral_filter_d: int,
        bilateral_sigma_color: float,
        bilateral_sigma_space: float
    ) -> None:
        """Validate preprocessing parameters."""
        if threshold_block_size % 2 == 0:
            raise ValueError("threshold_block_size must be odd")
        
        if not 11 <= threshold_block_size <= 51:
            raise ValueError("threshold_block_size must be between 11 and 51")
        
        if not 5.0 <= threshold_constant <= 20.0:
            raise ValueError("threshold_constant must be between 5.0 and 20.0")
        
        if not 800 <= target_width <= 3200:
            raise ValueError("target_width must be between 800 and 3200")
        
        if not 5 <= bilateral_filter_d <= 15:
            raise ValueError("bilateral_filter_d must be between 5 and 15")
        
        if not 50.0 <= bilateral_sigma_color <= 150.0:
            raise ValueError("bilateral_sigma_color must be between 50.0 and 150.0")
        
        if not 50.0 <= bilateral_sigma_space <= 150.0:
            raise ValueError("bilateral_sigma_space must be between 50.0 and 150.0")
    
    def _load_image(self, image_path: str) -> np.ndarray:
        """Load and validate image file."""
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Load image using OpenCV
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Unable to load image: {image_path}")
        
        return image
    
    def _check_memory_constraints(self, image: np.ndarray, target_width: int) -> None:
        """Check if processing will exceed memory limits."""
        height, width = image.shape[:2]
        
        # Calculate target dimensions
        aspect_ratio = height / width
        target_height = int(target_width * aspect_ratio)
        
        # Estimate memory usage (bytes per pixel * channels * safety factor)
        estimated_memory = target_width * target_height * 3 * 4  # 4 bytes per channel for safety
        
        if estimated_memory > self.memory_limit_bytes:
            raise MemoryError(
                f"Processing would exceed memory limit: {estimated_memory / (1024*1024):.1f}MB > {MEMORY_LIMIT_MB}MB"
            )
    
    def _apply_preprocessing(
        self,
        image: np.ndarray,
        operation: PreprocessingOperation,
        target_width: int,
        threshold_block_size: int,
        threshold_constant: float,
        bilateral_filter_d: int,
        bilateral_sigma_color: float,
        bilateral_sigma_space: float
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply the specified preprocessing operations."""
        metadata = {"operations_applied": []}
        processed_image = image.copy()
        
        # Resize to target width first
        processed_image, resize_metadata = self._resize_image(processed_image, target_width)
        metadata.update(resize_metadata)
        metadata["operations_applied"].append("resize")
        
        if operation == PreprocessingOperation.THRESHOLD:
            processed_image = self._apply_adaptive_threshold(
                processed_image, threshold_block_size, threshold_constant
            )
            metadata["operations_applied"].append("adaptive_threshold")
            
        elif operation == PreprocessingOperation.DESKEW:
            processed_image, skew_metadata = self._apply_deskew(processed_image)
            metadata.update(skew_metadata)
            metadata["operations_applied"].append("deskew")
            
        elif operation == PreprocessingOperation.COMBINED:
            # Apply bilateral filter first to reduce noise
            processed_image = self._apply_bilateral_filter(
                processed_image, bilateral_filter_d, bilateral_sigma_color, bilateral_sigma_space
            )
            metadata["operations_applied"].append("bilateral_filter")
            
            # Then apply deskewing
            processed_image, skew_metadata = self._apply_deskew(processed_image)
            metadata.update(skew_metadata)
            metadata["operations_applied"].append("deskew")
            
            # Finally apply adaptive thresholding
            processed_image = self._apply_adaptive_threshold(
                processed_image, threshold_block_size, threshold_constant
            )
            metadata["operations_applied"].append("adaptive_threshold")
        
        return processed_image, metadata
    
    def _resize_image(self, image: np.ndarray, target_width: int) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Resize image to target width while maintaining aspect ratio."""
        height, width = image.shape[:2]
        
        if width == target_width:
            return image, {"resize_applied": False, "original_dimensions": f"{width}x{height}"}
        
        # Calculate target height maintaining aspect ratio
        aspect_ratio = height / width
        target_height = int(target_width * aspect_ratio)
        
        # Resize image
        resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
        
        metadata = {
            "resize_applied": True,
            "original_dimensions": f"{width}x{height}",
            "resized_dimensions": f"{target_width}x{target_height}",
            "scale_factor": target_width / width
        }
        
        return resized, metadata
    
    def _apply_adaptive_threshold(
        self, image: np.ndarray, block_size: int, constant: float
    ) -> np.ndarray:
        """Apply adaptive thresholding to enhance text readability."""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            constant
        )
        
        # Convert back to 3-channel if original was color
        if len(image.shape) == 3:
            thresh = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        
        return thresh
    
    def _apply_bilateral_filter(
        self, image: np.ndarray, d: int, sigma_color: float, sigma_space: float
    ) -> np.ndarray:
        """Apply bilateral filter to reduce noise while preserving edges."""
        # Bilateral filter works on each channel separately for color images
        filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
        return filtered
    
    def _apply_deskew(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Detect and correct image skew."""
        # Convert to grayscale for skew detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Use Hough line transform to detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        # Calculate skew angle
        skew_angle = self._calculate_skew_angle(lines)
        
        metadata = {
            "skew_angle_detected": skew_angle,
            "skew_corrected": abs(skew_angle) > 0.5  # Only correct if skew > 0.5 degrees
        }
        
        # Apply rotation if skew is significant
        if abs(skew_angle) > 0.5:
            corrected = self._rotate_image(image, -skew_angle)  # Negative to correct
            metadata["correction_applied"] = True
            return corrected, metadata
        else:
            metadata["correction_applied"] = False
            return image, metadata
    
    def _calculate_skew_angle(self, lines: Optional[np.ndarray]) -> float:
        """Calculate skew angle from detected lines."""
        if lines is None or len(lines) == 0:
            return 0.0
        
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            
            # Only consider lines that are roughly horizontal
            if -45 <= angle <= 45:
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Return median angle to reduce impact of outliers
        return float(np.median(angles))
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle."""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Calculate rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new dimensions to avoid cropping
        cos_angle = abs(rotation_matrix[0, 0])
        sin_angle = abs(rotation_matrix[0, 1])
        
        new_width = int((height * sin_angle) + (width * cos_angle))
        new_height = int((height * cos_angle) + (width * sin_angle))
        
        # Adjust rotation matrix for new dimensions
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # Apply rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                flags=cv2.INTER_LANCZOS4, borderValue=(255, 255, 255))
        
        return rotated
    
    def _save_processed_image(self, image: np.ndarray, original_path: str) -> Path:
        """Save processed image to storage directory."""
        # Generate unique filename
        original_name = Path(original_path).stem
        timestamp = int(time.time())
        unique_id = str(uuid4())[:8]
        
        output_filename = f"{original_name}_processed_{timestamp}_{unique_id}.png"
        output_path = self.preprocessed_dir / output_filename
        
        # Save image
        success = cv2.imwrite(str(output_path), image)
        if not success:
            raise RuntimeError(f"Failed to save processed image: {output_path}")
        
        return output_path
    
    def cleanup_processed_image(self, image_path: str) -> bool:
        """Clean up a specific processed image file."""
        return file_cleanup_service.cleanup_preprocessed_image(image_path)


# Global preprocessor instance
image_preprocessor = ImagePreprocessor()