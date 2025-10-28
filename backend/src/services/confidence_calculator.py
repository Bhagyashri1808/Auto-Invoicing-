"""Confidence score calculation service for LLM and OCR extraction results."""

import logging
from typing import Any, Dict, List, Optional

from .error_handler import error_handler


class ConfidenceCalculator:
    """Service for calculating and comparing confidence scores between extraction methods."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_enhanced_confidence(
        self,
        extraction_result: Dict[str, Any],
        extraction_method: str,
        preprocessing_applied: bool,
        llm_metadata: Optional[Dict[str, Any]] = None,
        ocr_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate enhanced confidence scores for extracted data.
        
        Args:
            extraction_result: The extracted data dictionary
            extraction_method: Method used (LLM_PRIMARY, LLM_FALLBACK, OCR_ONLY)
            preprocessing_applied: Whether preprocessing was applied
            llm_metadata: Metadata from LLM processing
            ocr_metadata: Metadata from OCR processing
            
        Returns:
            Dictionary containing confidence scores and analysis
        """
        try:
            # Calculate field-level confidence scores
            field_confidence_scores = self._calculate_field_confidence(
                extraction_result, extraction_method, llm_metadata, ocr_metadata
            )
            
            # Calculate method-specific confidence
            method_confidence = self._calculate_method_confidence(
                extraction_method, llm_metadata, ocr_metadata
            )
            
            # Apply preprocessing bonus
            preprocessing_bonus = self._calculate_preprocessing_bonus(
                preprocessing_applied, field_confidence_scores
            )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                field_confidence_scores, method_confidence, preprocessing_bonus
            )
            
            # Generate comparative analysis if multiple methods were used
            comparative_analysis = self._generate_comparative_analysis(
                extraction_method, llm_metadata, ocr_metadata
            )
            
            return {
                "ocr_confidence_avg": method_confidence.get("ocr_confidence"),
                "llm_confidence_score": method_confidence.get("llm_confidence"),
                "field_confidence_scores": field_confidence_scores,
                "overall_confidence": overall_confidence,
                "confidence_metadata": {
                    "extraction_method": extraction_method,
                    "preprocessing_applied": preprocessing_applied,
                    "preprocessing_bonus": preprocessing_bonus,
                    "method_confidence": method_confidence,
                    "comparative_analysis": comparative_analysis
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence scores: {e}")
            # Return default confidence scores on error
            return {
                "ocr_confidence_avg": None,
                "llm_confidence_score": None,
                "field_confidence_scores": {},
                "overall_confidence": 0.0,
                "confidence_metadata": {
                    "error": str(e),
                    "extraction_method": extraction_method
                }
            }
    
    def _calculate_field_confidence(
        self,
        extraction_result: Dict[str, Any],
        extraction_method: str,
        llm_metadata: Optional[Dict[str, Any]],
        ocr_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate confidence scores for individual fields."""
        field_scores = {}
        
        # Define key fields for confidence calculation
        key_fields = [
            "vendor_name", "vendor_address", "invoice_number", "invoice_date",
            "due_date", "total_amount", "tax_amount", "subtotal_amount", "currency"
        ]
        
        for field in key_fields:
            value = extraction_result.get(field)
            
            if value is None:
                field_scores[field] = 0.0
            else:
                # Base confidence based on value type and content
                base_confidence = self._calculate_base_field_confidence(field, value)
                
                # Method-specific adjustments
                method_adjustment = self._get_method_adjustment(
                    field, extraction_method, llm_metadata, ocr_metadata
                )
                
                # Calculate final field confidence
                final_confidence = min(1.0, base_confidence * method_adjustment)
                field_scores[field] = round(final_confidence, 3)
        
        # Handle line items separately
        line_items = extraction_result.get("line_items", [])
        if line_items:
            line_item_confidence = self._calculate_line_items_confidence(line_items)
            field_scores["line_items"] = line_item_confidence
        else:
            field_scores["line_items"] = 0.0
        
        return field_scores
    
    def _calculate_base_field_confidence(self, field: str, value: Any) -> float:
        """Calculate base confidence score for a field based on its value."""
        if value is None:
            return 0.0
        
        # Field-specific confidence rules
        if field in ["total_amount", "tax_amount", "subtotal_amount"]:
            if isinstance(value, (int, float)) and value > 0:
                return 0.9  # High confidence for positive numbers
            elif isinstance(value, str) and value.replace(".", "").replace(",", "").isdigit():
                return 0.7  # Medium-high for numeric strings
            else:
                return 0.3  # Low confidence for non-numeric values
        
        elif field in ["invoice_date", "due_date"]:
            if isinstance(value, str):
                # Check for date-like patterns
                if len(value) >= 8 and any(sep in value for sep in ["-", "/", "."]):
                    return 0.8  # High confidence for date patterns
                else:
                    return 0.4  # Low confidence for non-date strings
            else:
                return 0.2
        
        elif field == "currency":
            if isinstance(value, str) and len(value) == 3 and value.isupper():
                return 0.9  # High confidence for 3-letter currency codes
            else:
                return 0.5
        
        elif field in ["vendor_name", "invoice_number"]:
            if isinstance(value, str) and len(value.strip()) > 0:
                # Confidence based on length and content
                if len(value.strip()) >= 3:
                    return 0.8
                else:
                    return 0.5
            else:
                return 0.2
        
        elif field == "vendor_address":
            if isinstance(value, str) and len(value.strip()) > 10:
                return 0.7  # Medium-high for longer addresses
            elif isinstance(value, str) and len(value.strip()) > 0:
                return 0.5  # Medium for short addresses
            else:
                return 0.2
        
        else:
            # Default confidence for other fields
            if isinstance(value, str) and len(value.strip()) > 0:
                return 0.6
            else:
                return 0.3
    
    def _get_method_adjustment(
        self,
        field: str,
        extraction_method: str,
        llm_metadata: Optional[Dict[str, Any]],
        ocr_metadata: Optional[Dict[str, Any]]
    ) -> float:
        """Get confidence adjustment based on extraction method."""
        if extraction_method == "LLM_PRIMARY":
            # LLM generally better at understanding context
            if field in ["vendor_name", "total_amount", "invoice_date"]:
                return 1.1  # 10% bonus for key fields
            else:
                return 1.05  # 5% bonus for other fields
        
        elif extraction_method == "LLM_FALLBACK":
            # LLM failed, so OCR was used - reduce confidence
            return 0.8  # 20% reduction
        
        elif extraction_method == "OCR_ONLY":
            # Standard OCR confidence
            return 1.0
        
        else:
            return 1.0
    
    def _calculate_line_items_confidence(self, line_items: List[Dict[str, Any]]) -> float:
        """Calculate confidence for line items array."""
        if not line_items:
            return 0.0
        
        total_confidence = 0.0
        valid_items = 0
        
        for item in line_items:
            item_confidence = 0.0
            field_count = 0
            
            # Check each field in the line item
            for field, value in item.items():
                if value is not None:
                    field_confidence = self._calculate_base_field_confidence(field, value)
                    item_confidence += field_confidence
                field_count += 1
            
            if field_count > 0:
                item_confidence /= field_count
                total_confidence += item_confidence
                valid_items += 1
        
        return round(total_confidence / valid_items, 3) if valid_items > 0 else 0.0
    
    def _calculate_method_confidence(
        self,
        extraction_method: str,
        llm_metadata: Optional[Dict[str, Any]],
        ocr_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Optional[float]]:
        """Calculate method-specific confidence scores."""
        result = {
            "llm_confidence": None,
            "ocr_confidence": None
        }
        
        if extraction_method in ["LLM_PRIMARY", "LLM_FALLBACK"] and llm_metadata:
            # Extract LLM confidence from metadata
            confidence_scores = llm_metadata.get("confidence_scores", {})
            result["llm_confidence"] = confidence_scores.get("overall_confidence")
        
        if extraction_method in ["LLM_FALLBACK", "OCR_ONLY"] and ocr_metadata:
            # Extract OCR confidence from metadata
            result["ocr_confidence"] = ocr_metadata.get("confidence_avg", 0.0)
        
        return result
    
    def _calculate_preprocessing_bonus(
        self, preprocessing_applied: bool, field_scores: Dict[str, float]
    ) -> float:
        """Calculate confidence bonus from preprocessing."""
        if not preprocessing_applied:
            return 0.0
        
        # Preprocessing generally helps with text recognition
        # Give bonus based on field complexity
        text_fields = ["vendor_name", "vendor_address", "invoice_number"]
        text_field_scores = [field_scores.get(field, 0.0) for field in text_fields]
        
        if text_field_scores:
            avg_text_confidence = sum(text_field_scores) / len(text_field_scores)
            # Bonus scales with text field confidence (preprocessing helps more with poor text)
            return round(0.05 * (1.0 - avg_text_confidence), 3)
        
        return 0.02  # Small default bonus
    
    def _calculate_overall_confidence(
        self,
        field_scores: Dict[str, float],
        method_confidence: Dict[str, Optional[float]],
        preprocessing_bonus: float
    ) -> float:
        """Calculate overall confidence score."""
        # Weight different field types
        critical_fields = ["vendor_name", "total_amount", "invoice_date"]
        important_fields = ["invoice_number", "tax_amount", "subtotal_amount"]
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        # Critical fields (weight: 3)
        for field in critical_fields:
            if field in field_scores:
                weighted_confidence += field_scores[field] * 3
                total_weight += 3
        
        # Important fields (weight: 2)
        for field in important_fields:
            if field in field_scores:
                weighted_confidence += field_scores[field] * 2
                total_weight += 2
        
        # Other fields (weight: 1)
        for field, score in field_scores.items():
            if field not in critical_fields and field not in important_fields:
                weighted_confidence += score
                total_weight += 1
        
        if total_weight > 0:
            base_confidence = weighted_confidence / total_weight
        else:
            base_confidence = 0.0
        
        # Apply preprocessing bonus
        final_confidence = min(1.0, base_confidence + preprocessing_bonus)
        
        return round(final_confidence, 3)
    
    def _generate_comparative_analysis(
        self,
        extraction_method: str,
        llm_metadata: Optional[Dict[str, Any]],
        ocr_metadata: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate comparative analysis when multiple methods were attempted."""
        if extraction_method != "LLM_FALLBACK":
            return None
        
        # This would be populated if both LLM and OCR were attempted
        return {
            "llm_attempted": llm_metadata is not None,
            "ocr_used_as_fallback": True,
            "fallback_reason": "LLM processing failed or timed out",
            "confidence_comparison": {
                "llm_would_have_been_better": False,  # Since it failed
                "confidence_impact": "Reduced due to fallback to OCR"
            }
        }


# Global confidence calculator instance
confidence_calculator = ConfidenceCalculator()