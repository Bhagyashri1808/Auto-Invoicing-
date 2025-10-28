"""Llama 3.2 REST API client for invoice data extraction."""

import asyncio
import base64
import json
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aiohttp
import httpx

from .error_handler import error_handler, ErrorType, ProcessingError
from .timeout_manager import timeout_manager, llm_circuit_breaker
from database.config import LLM_BASE_URL, LLM_MODEL_NAME, LLM_TIMEOUT_SECONDS


class LLMClient:
    """Client for interacting with local Llama 3.2 model via REST API."""
    
    def __init__(self, base_url: str = LLM_BASE_URL, model_name: str = LLM_MODEL_NAME):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout_seconds = LLM_TIMEOUT_SECONDS
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.models_endpoint = f"{self.base_url}/api/tags"
        self.health_endpoint = f"{self.base_url}/api/version"
    
    async def check_health(self) -> Dict[str, Any]:
        """Check if LLM service is available and healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.health_endpoint, timeout=10) as response:
                    if response.status == 200:
                        version_data = await response.json()
                        
                        # Check if model is available
                        models = await self.list_models()
                        model_available = any(
                            model["name"] == self.model_name 
                            for model in models.get("models", [])
                        )
                        
                        return {
                            "status": "healthy" if model_available else "degraded",
                            "model_loaded": self.model_name if model_available else None,
                            "response_time_ms": None,  # Could measure this
                            "memory_usage_mb": None,   # Not available from API
                            "last_check": time.time(),
                            "error_message": None if model_available else f"Model {self.model_name} not available"
                        }
                    else:
                        return {
                            "status": "unavailable",
                            "model_loaded": None,
                            "response_time_ms": None,
                            "memory_usage_mb": None,
                            "last_check": time.time(),
                            "error_message": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unavailable",
                "model_loaded": None,
                "response_time_ms": None,
                "memory_usage_mb": None,
                "last_check": time.time(),
                "error_message": str(e)
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available LLM models."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.models_endpoint, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise ProcessingError(
                            message=f"Failed to fetch models: HTTP {response.status}",
                            error_type=ErrorType.LLM_CONNECTION_ERROR
                        )
        except Exception as e:
            raise error_handler.handle_llm_error(
                operation="list_models",
                model_name=self.model_name,
                error=e
            )
    
    async def extract_data(self, image_path: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract structured data from invoice image using LLM.
        
        Args:
            image_path: Path to the image file (preprocessed or original)
            custom_prompt: Optional custom prompt for extraction
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        try:
            # Use circuit breaker to handle service failures
            return await llm_circuit_breaker.call(
                self._perform_extraction, image_path, custom_prompt
            )
        except Exception as e:
            raise error_handler.handle_llm_error(
                operation="extract_data",
                model_name=self.model_name,
                error=e,
                context={"image_path": image_path}
            )
    
    async def _perform_extraction(self, image_path: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Perform the actual LLM extraction with timeout management."""
        start_time = time.time()

        # Prepare the prompt
        prompt = custom_prompt or self._create_extraction_prompt()
        print(image_path, "IMAGE FILE PATH")
        # Read and encode the image in base64 for vision model
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            raise ProcessingError(
                message=f"Failed to read image file: {e}",
                error_type=ErrorType.PREPROCESSING_ERROR,
                context={"image_path": image_path}
            )

        try:
            async with timeout_manager.async_timeout(self.timeout_seconds):
                # Prepare request payload for vision model
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [image_base64],  # Include base64-encoded image
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent extraction
                        "top_p": 0.9,
                        "num_predict": 1000  # max_tokens equivalent for Ollama
                    }
                }
                
                # Make request to LLM API
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.generate_endpoint,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                    ) as response:
                        
                        if response.status != 200:
                            raise ProcessingError(
                                message=f"LLM API request failed: HTTP {response.status}",
                                error_type=ErrorType.LLM_CONNECTION_ERROR,
                                context={"status_code": response.status, "url": self.generate_endpoint}
                            )
                        
                        response_data = await response.json()
                        print(response_data, "LLM RESPONSE DATA")
                        # Process LLM response
                        return await self._process_llm_response(
                            response_data, image_path, start_time, payload
                        )
                        
        except asyncio.TimeoutError:
            raise ProcessingError(
                message=f"LLM request timeout after {self.timeout_seconds} seconds",
                error_type=ErrorType.LLM_TIMEOUT_ERROR,
                context={
                    "timeout_seconds": self.timeout_seconds,
                    "image_path": image_path,
                    "model_name": self.model_name
                }
            )
    
    def _create_extraction_prompt(self) -> str:
        """Create prompt for invoice data extraction."""
        return """
You are an expert at extracting structured data from invoice documents.
Analyze the provided invoice image and extract ALL the actual information you can see.

CRITICAL: Extract the ACTUAL text and numbers from the image, NOT placeholder descriptions!

Return the data in this exact JSON format:

{
    "vendor_name": <actual company/vendor name from invoice>,
    "vendor_address": <actual full address from invoice>,
    "invoice_number": <actual invoice/document number>,
    "invoice_date": <actual date in YYYY-MM-DD format>,
    "due_date": <actual due date in YYYY-MM-DD format>,
    "total_amount": <actual total amount as number>,
    "tax_amount": <actual tax/GST amount as number>,
    "subtotal_amount": <actual subtotal as number>,
    "currency": <currency code like USD, AUD, EUR>,
    "line_items": [
        {
            "description": <actual item/service description>,
            "quantity": <actual quantity as number>,
            "unit_price": <actual price per unit as number>,
            "total_price": <actual line total as number>
        }
    ]
}

Example of CORRECT extraction from an invoice:
{
    "vendor_name": "Bhagyshri Patil",
    "vendor_address": "Melbourne, Australia",
    "invoice_number": "INV-2025-001",
    "invoice_date": "2025-10-13",
    "due_date": "2025-10-27",
    "total_amount": 3767.50,
    "tax_amount": 342.50,
    "subtotal_amount": 3425.00,
    "currency": "AUD",
    "line_items": [
        {
            "description": "Frontend development (React.js)",
            "quantity": 25,
            "unit_price": 85,
            "total_price": 2125.00
        }
    ]
}

Important rules:
- Read ALL text carefully from the image
- Extract REAL data, not field descriptions
- Use null only if information is truly missing
- Numeric values must be numbers, not strings
- For dates use YYYY-MM-DD format
- Include ALL line items you can see

Return ONLY the JSON, no other text.
"""
    
    async def _process_llm_response(
        self,
        response_data: Dict[str, Any],
        image_path: str,
        start_time: float,
        request_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and validate LLM response."""
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract response text
        response_text = response_data.get("response", "")
        if not response_text:
            raise ProcessingError(
                message="Empty response from LLM",
                error_type=ErrorType.LLM_RESPONSE_ERROR,
                context={"response_data": response_data}
            )
        
        # Try to parse JSON from response
        try:
            # Clean response text (remove markdown formatting if present)
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            extracted_data = json.loads(clean_text)
            
        except json.JSONDecodeError as e:
            raise ProcessingError(
                message=f"Failed to parse LLM response as JSON: {e}",
                error_type=ErrorType.LLM_RESPONSE_ERROR,
                context={
                    "response_text": response_text[:500],  # First 500 chars for debugging
                    "json_error": str(e)
                }
            )
        
        # Validate extracted data structure
        validated_data = self._validate_extracted_data(extracted_data)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(validated_data, response_text)
        
        return {
            "extracted_data": validated_data,
            "confidence_scores": confidence_scores,
            "processing_metadata": {
                "model_name": self.model_name,
                "processing_time_ms": processing_time_ms,
                "image_path": image_path,
                "request_id": str(uuid4()),
                "llm_response_length": len(response_text),
                "validation_passed": True
            },
            "raw_response": {
                "text": response_text,
                "full_response": response_data
            }
        }
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data."""
        # Expected fields with their types
        expected_fields = {
            "vendor_name": (str, type(None)),
            "vendor_address": (str, type(None)),
            "invoice_number": (str, type(None)),
            "invoice_date": (str, type(None)),
            "due_date": (str, type(None)),
            "total_amount": (int, float, type(None)),
            "tax_amount": (int, float, type(None)),
            "subtotal_amount": (int, float, type(None)),
            "currency": (str, type(None)),
            "line_items": (list, type(None))
        }
        
        validated = {}
        validation_errors = {}
        
        for field, expected_types in expected_fields.items():
            value = data.get(field)
            
            if value is not None and not isinstance(value, expected_types):
                validation_errors[field] = f"Expected {expected_types}, got {type(value)}"
                validated[field] = None
            else:
                validated[field] = value
        
        # Validate line items structure if present
        if validated.get("line_items"):
            validated_line_items = []
            for i, item in enumerate(validated["line_items"]):
                if isinstance(item, dict):
                    validated_item = {
                        "description": item.get("description"),
                        "quantity": item.get("quantity") if isinstance(item.get("quantity"), (int, float, type(None))) else None,
                        "unit_price": item.get("unit_price") if isinstance(item.get("unit_price"), (int, float, type(None))) else None,
                        "total_price": item.get("total_price") if isinstance(item.get("total_price"), (int, float, type(None))) else None
                    }
                    validated_line_items.append(validated_item)
                else:
                    validation_errors[f"line_items[{i}]"] = "Expected dictionary"
            
            validated["line_items"] = validated_line_items
        
        if validation_errors:
            self.logger.warning(f"Validation errors in LLM response: {validation_errors}")
        
        return validated
    
    def _calculate_confidence_scores(self, extracted_data: Dict[str, Any], response_text: str) -> Dict[str, Any]:
        """Calculate confidence scores for extracted data."""
        # Simple heuristic-based confidence calculation
        # In a real implementation, this could be more sophisticated
        
        field_scores = {}
        non_null_fields = 0
        total_fields = 0
        
        for field, value in extracted_data.items():
            if field == "line_items":
                continue  # Handle separately
                
            total_fields += 1
            if value is not None:
                non_null_fields += 1
                # Simple confidence based on field presence and type
                if isinstance(value, str) and len(value.strip()) > 0:
                    field_scores[field] = 0.8  # High confidence for non-empty strings
                elif isinstance(value, (int, float)) and value > 0:
                    field_scores[field] = 0.9  # Very high confidence for positive numbers
                else:
                    field_scores[field] = 0.6  # Medium confidence
            else:
                field_scores[field] = 0.0
        
        # Calculate overall confidence
        if total_fields > 0:
            overall_confidence = non_null_fields / total_fields
        else:
            overall_confidence = 0.0
        
        # Adjust confidence based on response quality indicators
        quality_indicators = [
            len(response_text) > 100,  # Sufficient response length
            '"' in response_text,      # JSON formatting present
            any(field in response_text.lower() for field in ["invoice", "total", "vendor"]),  # Domain terms present
        ]
        
        quality_bonus = sum(quality_indicators) * 0.05  # Up to 15% bonus
        overall_confidence = min(1.0, overall_confidence + quality_bonus)
        
        return {
            "overall_confidence": round(overall_confidence, 3),
            "field_confidence_scores": field_scores,
            "confidence_metadata": {
                "non_null_fields": non_null_fields,
                "total_fields": total_fields,
                "quality_indicators_met": sum(quality_indicators),
                "response_length": len(response_text)
            }
        }


# Global LLM client instance
llm_client = LLMClient()