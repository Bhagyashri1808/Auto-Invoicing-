"""OCR processing service using OpenCV and Tesseract."""

import cv2
import numpy as np
import pytesseract
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing."""
    text: str
    confidence: float
    page_count: int = 1
    processing_time: float = 0.0
    error: Optional[str] = None


class OCRProcessor:
    """Service for extracting text from documents using OCR."""
    
    def __init__(self):
        """Initialize OCR processor."""
        self.tesseract_config = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
    
    def process_document(self, file_path: str) -> OCRResult:
        """
        Process document and extract text.
        
        Args:
            file_path: Path to document file
            
        Returns:
            OCRResult with extracted text and metadata
        """
        import time
        start_time = time.time()
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return OCRResult(
                    text="",
                    confidence=0.0,
                    error=f"File not found: {file_path}"
                )
            
            # Determine file type and process accordingly
            extension = file_path_obj.suffix.lower()
            
            if extension == '.pdf':
                result = self._process_pdf(file_path)
            elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                result = self._process_image(file_path)
            else:
                return OCRResult(
                    text="",
                    confidence=0.0,
                    error=f"Unsupported file type: {extension}"
                )
            
            # Add processing time
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"OCR processing failed for {file_path}: {str(e)}")
            return OCRResult(
                text="",
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _process_pdf(self, file_path: str) -> OCRResult:
        """
        Process PDF document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            OCRResult with extracted text
        """
        try:
            doc = fitz.open(file_path)
            all_text = []
            total_confidence = 0.0
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                # First try to extract text directly (for text-based PDFs)
                text = page.get_text()
                
                if text.strip():
                    # Text-based PDF - high confidence
                    all_text.append(text)
                    total_confidence += 0.95
                else:
                    # Image-based PDF - use OCR
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    
                    # Process image with OCR
                    image = Image.open(self._bytes_to_io(img_data))
                    page_result = self._ocr_image(image)
                    
                    all_text.append(page_result.text)
                    total_confidence += page_result.confidence
            
            doc.close()
            
            # Calculate average confidence
            avg_confidence = total_confidence / page_count if page_count > 0 else 0.0
            
            return OCRResult(
                text="\n\n--- PAGE BREAK ---\n\n".join(all_text),
                confidence=avg_confidence,
                page_count=page_count
            )
            
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            return OCRResult(
                text="",
                confidence=0.0,
                error=f"PDF processing failed: {str(e)}"
            )
    
    def _process_image(self, file_path: str) -> OCRResult:
        """
        Process image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            OCRResult with extracted text
        """
        try:
            # Load image
            image = Image.open(file_path)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Perform OCR
            return self._ocr_image(processed_image)
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            return OCRResult(
                text="",
                confidence=0.0,
                error=f"Image processing failed: {str(e)}"
            )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply image enhancement techniques
            
            # 1. Noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # 2. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 3. Threshold to binary
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 4. Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(cleaned)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {str(e)}")
            return image
    
    def _ocr_image(self, image: Image.Image) -> OCRResult:
        """
        Perform OCR on preprocessed image.
        
        Args:
            image: PIL Image object
            
        Returns:
            OCRResult with extracted text and confidence
        """
        try:
            # Extract text with confidence data
            ocr_data = pytesseract.image_to_data(
                image,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            # Calculate confidence
            confidences = [
                int(conf) for conf in ocr_data['conf'] 
                if int(conf) > 0
            ]
            
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence
            )
            
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return OCRResult(
                text="",
                confidence=0.0,
                error=f"OCR failed: {str(e)}"
            )
    
    def _bytes_to_io(self, data: bytes):
        """Convert bytes to BytesIO object."""
        from io import BytesIO
        return BytesIO(data)
    
    def get_tesseract_info(self) -> dict:
        """Get Tesseract installation information."""
        try:
            version = pytesseract.get_tesseract_version()
            languages = pytesseract.get_languages()
            
            return {
                "version": str(version),
                "languages": languages,
                "config": self.tesseract_config
            }
        except Exception as e:
            return {
                "error": f"Tesseract not available: {str(e)}"
            }
    
    def test_ocr_setup(self) -> bool:
        """Test if OCR setup is working correctly."""
        try:
            # Create a simple test image with text
            test_image = Image.new('RGB', (200, 50), color='white')
            
            # Try OCR on test image
            result = self._ocr_image(test_image)
            
            # If no error occurred, setup is working
            return result.error is None
            
        except Exception:
            return False