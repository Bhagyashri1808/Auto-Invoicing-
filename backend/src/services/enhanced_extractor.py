"""Enhanced extraction orchestrator that coordinates preprocessing, LLM, and OCR fallback."""

import logging
import time
from typing import Any, Dict, Optional
from uuid import uuid4

from .image_preprocessor import image_preprocessor
from .llm_client import llm_client
from .confidence_calculator import confidence_calculator
from .error_handler import error_handler, ErrorType, ProcessingError
from .file_cleanup import file_cleanup_service
from .pdf_converter import pdf_converter
from .simple_ocr_extractor import simple_extractor
from models.preprocessing import PreprocessingOperation


class EnhancedExtractor:
    """Orchestrates the complete enhanced extraction pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract_data(
        self,
        image_path: str,
        enable_preprocessing: bool = True,
        enable_llm_processing: bool = True,
        fallback_to_ocr: bool = True,
        preprocessing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract data using the complete enhanced pipeline.
        
        Args:
            image_path: Path to the original image file
            enable_preprocessing: Whether to apply image preprocessing
            enable_llm_processing: Whether to use LLM for extraction
            fallback_to_ocr: Whether to fallback to OCR on LLM failure
            preprocessing_config: Configuration for preprocessing operations
            
        Returns:
            Dictionary containing extracted data and processing metadata
        """
        start_time = time.time()
        processing_context = {
            "preprocessing_attempted": False,
            "llm_attempted": False,
            "fallback_used": False,
            "extraction_method": "OCR_ONLY",
            "pdf_converted": False
        }

        try:
            # Step 0: Convert PDF to image if necessary
            working_image_path = image_path
            pdf_converted = False

            if pdf_converter.is_pdf(image_path):
                self.logger.info(f"PDF detected, converting to image: {image_path}")
                try:
                    working_image_path = pdf_converter.convert_first_page(image_path)
                    pdf_converted = True
                    processing_context["pdf_converted"] = True
                    self.logger.info(f"PDF converted to: {working_image_path}")
                except Exception as e:
                    self.logger.error(f"PDF conversion failed: {e}")
                    raise error_handler.handle_preprocessing_error(
                        operation="pdf_conversion",
                        file_path=image_path,
                        error=e
                    )

            # Step 1: Preprocessing (if enabled)
            processed_image_path = working_image_path
            preprocessing_metadata = {}
            
            if enable_preprocessing:
                self.logger.info(f"Starting preprocessing for: {image_path}")
                processing_context["preprocessing_attempted"] = True
                
                try:
                    preprocessing_result = await self._apply_preprocessing(
                        working_image_path, preprocessing_config
                    )
                    print(preprocessing_result)
                    processed_image_path = preprocessing_result["processed_image_path"]
                    preprocessing_metadata = preprocessing_result["processing_metadata"]

                    self.logger.info(f"Preprocessing completed: {processed_image_path}")

                except Exception as e:
                    self.logger.warning(f"Preprocessing failed: {e}")
                    if not fallback_to_ocr:
                        raise
                    # Continue with working image (PDF converted or original) if fallback is enabled
                    processed_image_path = working_image_path
            
            # Step 2: LLM Extraction (if enabled)
            extraction_result = None
            llm_metadata = {}
            
            if enable_llm_processing:
                self.logger.info(f"Starting LLM extraction for: {processed_image_path}")
                processing_context["llm_attempted"] = True
                
                try:
                    llm_result = await llm_client.extract_data(processed_image_path)
                    
                    extraction_result = llm_result["extracted_data"]
                    llm_metadata = llm_result["processing_metadata"]
                    processing_context["extraction_method"] = "LLM_PRIMARY"
                    
                    self.logger.info("LLM extraction completed successfully")
                    
                except Exception as e:
                    self.logger.warning(f"LLM extraction failed: {e}")
                    if not fallback_to_ocr:
                        raise
                    
                    # Fallback to OCR
                    processing_context["fallback_used"] = True
                    processing_context["extraction_method"] = "LLM_FALLBACK"
                    
            # Step 3: OCR Fallback (if needed or if LLM is disabled)
            if extraction_result is None:
                self.logger.info(f"Starting OCR extraction for: {processed_image_path}")
                
                try:
                    ocr_result = await self._apply_ocr_extraction(processed_image_path)
                    extraction_result = ocr_result["extracted_data"]
                    
                    if processing_context["extraction_method"] == "OCR_ONLY":
                        # OCR was the primary method
                        pass
                    else:
                        # OCR was used as fallback
                        processing_context["fallback_used"] = True
                    
                    self.logger.info("OCR extraction completed")
                    
                except Exception as e:
                    self.logger.error(f"OCR extraction failed: {e}")
                    raise error_handler.handle_preprocessing_error(
                        operation="ocr_extraction",
                        file_path=processed_image_path,
                        error=e
                    )
            
            # Step 4: Calculate enhanced confidence scores
            confidence_result = confidence_calculator.calculate_enhanced_confidence(
                extraction_result=extraction_result,
                extraction_method=processing_context["extraction_method"],
                preprocessing_applied=enable_preprocessing and processing_context["preprocessing_attempted"],
                llm_metadata=llm_metadata,
                ocr_metadata={}  # Would be populated in real OCR implementation
            )
            
            # Step 5: Compile final result
            total_processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract only database-relevant fields from confidence_result
            # overall_confidence and confidence_metadata are metadata only, not stored in DB
            result = {
                "extracted_data": {
                    **extraction_result,
                    "extraction_method": processing_context["extraction_method"],
                    "preprocessing_applied": enable_preprocessing and processing_context["preprocessing_attempted"],
                    "preprocessing_method": preprocessing_metadata.get("operations_applied", []) if preprocessing_metadata else None,
                    "ocr_confidence_avg": confidence_result.get("ocr_confidence_avg"),
                    "llm_confidence_score": confidence_result.get("llm_confidence_score"),
                    "field_confidence_scores": confidence_result.get("field_confidence_scores", {}),
                },
                "processing_metadata": {
                    "total_processing_time_ms": total_processing_time_ms,
                    "extraction_method": processing_context["extraction_method"],
                    "preprocessing_metadata": preprocessing_metadata,
                    "llm_metadata": llm_metadata,
                    "processing_steps": self._get_processing_steps(processing_context),
                    "files_processed": {
                        "original_image": image_path,
                        "processed_image": processed_image_path if processed_image_path != image_path else None
                    },
                    "overall_confidence": confidence_result.get("overall_confidence"),
                    "confidence_metadata": confidence_result.get("confidence_metadata")
                },
                **processing_context
            }
            
            # Step 6: Cleanup temporary files
            if processed_image_path != image_path:
                # Schedule cleanup of preprocessed image
                file_cleanup_service.cleanup_preprocessed_image(processed_image_path)

            # Cleanup PDF-converted image if it was created
            if pdf_converted and working_image_path != image_path:
                file_cleanup_service.cleanup_preprocessed_image(working_image_path)

            self.logger.info(f"Enhanced extraction completed in {total_processing_time_ms}ms")
            return result

        except Exception as e:
            # Ensure cleanup on error
            if 'processed_image_path' in locals() and processed_image_path != image_path:
                file_cleanup_service.cleanup_preprocessed_image(processed_image_path)

            # Cleanup PDF-converted image on error
            if 'pdf_converted' in locals() and pdf_converted and 'working_image_path' in locals() and working_image_path != image_path:
                file_cleanup_service.cleanup_preprocessed_image(working_image_path)
            
            # Re-raise with processing context
            if isinstance(e, ProcessingError):
                e.context.update(processing_context)
                raise e
            else:
                raise error_handler.handle_unknown_error(
                    operation="enhanced_extraction",
                    error=e,
                    context={**processing_context, "image_path": image_path}
                )
    
    async def _apply_preprocessing(
        self, image_path: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply image preprocessing with the specified configuration."""
        if config is None:
            config = {
                "operation_type": "THRESHOLD",
                "target_width": 1600,
                "threshold_block_size": 11,
                "threshold_constant": 10.0
            }
        
        # Convert operation type string to enum
        operation_type = config.get("operation_type", "THRESHOLD")
        operation = PreprocessingOperation(operation_type)
        
        # Extract parameters with defaults
        params = {
            "target_width": config.get("target_width", 1600),
            "threshold_block_size": config.get("threshold_block_size", 11),
            "threshold_constant": config.get("threshold_constant", 10.0),
            "bilateral_filter_d": config.get("bilateral_filter_d", 9),
            "bilateral_sigma_color": config.get("bilateral_sigma_color", 75.0),
            "bilateral_sigma_space": config.get("bilateral_sigma_space", 75.0)
        }
        
        # Apply preprocessing
        return image_preprocessor.preprocess_image(
            image_path=image_path,
            operation=operation,
            **params
        )
    
    async def _apply_ocr_extraction(self, image_path: str) -> Dict[str, Any]:
        """Apply OCR extraction as fallback method."""
        self.logger.info(f"Applying OCR extraction: {image_path}")

        try:
            # Use the existing simple OCR extractor
            ocr_result = await simple_extractor.extract_data(image_path)

            self.logger.info("OCR extraction completed successfully")
            return ocr_result

        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            # Return empty data as last resort
            return {
                "extracted_data": {
                    "vendor_name": None,
                    "vendor_address": None,
                    "invoice_number": None,
                    "invoice_date": None,
                    "due_date": None,
                    "total_amount": None,
                    "tax_amount": None,
                    "subtotal_amount": None,
                    "currency": "USD",
                    "line_items": []
                },
                "processing_metadata": {
                    "method": "OCR",
                    "confidence_avg": 0.0,
                    "processing_time_ms": 100,
                    "error": str(e)
                }
            }
    
    def _get_processing_steps(self, context: Dict[str, Any]) -> list:
        """Generate list of processing steps that were executed."""
        steps = []
        
        if context["preprocessing_attempted"]:
            steps.append("image_preprocessing")
        
        if context["llm_attempted"]:
            if context["fallback_used"]:
                steps.append("llm_extraction_failed")
                steps.append("ocr_fallback")
            else:
                steps.append("llm_extraction")
        else:
            steps.append("ocr_extraction")
        
        steps.append("confidence_calculation")
        
        return steps


# Global enhanced extractor instance
enhanced_extractor = EnhancedExtractor()