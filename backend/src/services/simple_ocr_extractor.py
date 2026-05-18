"""Simple OCR + LLM extractor that works reliably."""

import json
import logging
import requests
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from models.schemas import ExtractedDataCreate
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class SimpleOCRExtractor:
    """Reliable OCR + LLM extractor with fallbacks."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize simple OCR extractor."""
        self.ollama_url = ollama_url
        self.model = "llama3.1:8b"
    
    def extract_structured_data(
        self, 
        file_path: str, 
        invoice_document_id: str
    ) -> ExtractedDataCreate:
        """
        Extract structured data from invoice.
        
        Args:
            file_path: Path to invoice file
            invoice_document_id: UUID of invoice document
            
        Returns:
            ExtractedDataCreate schema with structured data
        """
        try:
            # Step 1: Extract text using available methods
            text = self._extract_text_safely(file_path)
            
            if not text.strip():
                logger.warning("No text extracted from document")
                # For now, provide a helpful error message
                return self._create_error_result(
                    invoice_document_id, 
                    "Text extraction from image failed. Please ensure the image has clear, readable text."
                )
            
            logger.info(f"Extracted text: {text[:100]}...")
            
            # Step 2: Use LLM to structure the text
            structured_data = self._extract_with_llm(text)
            
            if structured_data.get("error"):
                return self._create_error_result(invoice_document_id, structured_data["error"])
            
            # Step 3: Convert to schema
            return self._convert_to_schema(structured_data, invoice_document_id)
            
        except Exception as e:
            logger.error(f"Simple OCR extraction failed: {str(e)}")
            return self._create_error_result(invoice_document_id, str(e))
    
    def _extract_text_safely(self, file_path: str) -> str:
        """Extract text using multiple fallback methods."""
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise Exception(f"File not found: {file_path}")
        
        extension = file_path_obj.suffix.lower()
        
        # Method 1: For PDFs, try direct text extraction
        if extension == '.pdf':
            try:
                text = self._extract_pdf_text(file_path)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"PDF text extraction failed: {e}")
        
        # Method 2: Try pytesseract if available
        try:
            import pytesseract
            from PIL import Image
            
            if extension == '.pdf':
                # Convert PDF page to image first
                doc = fitz.open(file_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                
                from io import BytesIO
                image = Image.open(BytesIO(img_data))
                doc.close()
            else:
                image = Image.open(file_path)
            
            # Extract text with pytesseract
            text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
            if text.strip():
                logger.info("Successfully extracted text using pytesseract")
                return text
                
        except Exception as e:
            logger.warning(f"Pytesseract extraction failed: {e}")
        
        # Method 3: If all else fails, return a placeholder that suggests manual entry
        logger.warning("All OCR methods failed")
        return f"""
        OCR_EXTRACTION_FAILED
        
        Please manually review this document. The system could not extract text automatically.
        Document path: {file_path}
        
        For testing purposes, you can:
        1. Check if the image is clear and readable
        2. Try a different image format
        3. Manually enter the invoice data through the review interface
        """
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text directly from PDF."""
        doc = fitz.open(file_path)
        all_text = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                all_text.append(text)
        
        doc.close()
        return "\n".join(all_text)
    
    def _extract_with_llm(self, text: str) -> Dict:
        """Extract structured data using LLM."""
        if "OCR_EXTRACTION_FAILED" in text:
            return {"error": "OCR extraction failed - manual review required"}
        
        try:
            prompt = f"""Extract invoice data from this text. Be very precise and extract EXACTLY what you see:

TEXT:
{text}

Return ONLY valid JSON:
{{
  "vendor_name": "Exact vendor/company name",
  "vendor_address": "Complete address and contact info",
  "invoice_number": "Exact invoice number (like INV-2025-001)",
  "invoice_date": "Date in YYYY-MM-DD format",
  "due_date": "Due date in YYYY-MM-DD format (null if not found)",
  "total_amount": "Total amount as number only",
  "tax_amount": "Tax/GST amount as number (null if not found)",
  "subtotal_amount": "Subtotal as number (null if not found)",
  "currency": "Currency code (USD, AUD, EUR, etc.)",
  "line_items": [
    {{
      "description": "Service/item description",
      "quantity": "Quantity as number",
      "unit_price": "Unit price as number",
      "total_price": "Line total as number"
    }}
  ],
  "extraction_confidence": "Confidence 0.0-1.0 based on text clarity"
}}

CRITICAL: Return ONLY the JSON, no other text. Extract exactly what you see in the text."""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.0,  # Deterministic extraction
                        "top_p": 0.9,
                        "num_predict": 2048
                    }
                },
                timeout=120
            )
            
            if response.status_code != 200:
                return {"error": f"LLM API error: {response.status_code}"}
            
            llm_response = response.json()
            extracted_json = llm_response.get("response", "")
            
            try:
                data = json.loads(extracted_json)
                return self._parse_llm_response(data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from LLM: {extracted_json}")
                return {"error": "LLM returned invalid JSON"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to Ollama. Make sure it's running: ollama serve"}
        except Exception as e:
            return {"error": f"LLM extraction failed: {str(e)}"}
    
    def _parse_llm_response(self, data: Dict) -> Dict:
        """Parse and validate LLM response."""
        try:
            result = {
                "vendor_name": data.get("vendor_name"),
                "vendor_address": data.get("vendor_address"),
                "invoice_number": data.get("invoice_number"),
                "currency": data.get("currency", "USD"),
                "extraction_confidence": float(data.get("extraction_confidence", 0.8)),
                "line_items": []
            }
            
            # Parse dates
            for date_field in ["invoice_date", "due_date"]:
                if data.get(date_field):
                    try:
                        result[date_field] = datetime.strptime(data[date_field], "%Y-%m-%d").date()
                    except ValueError:
                        result[date_field] = None
                else:
                    result[date_field] = None
            
            # Parse amounts
            for field in ["total_amount", "tax_amount", "subtotal_amount"]:
                if data.get(field) is not None:
                    try:
                        result[field] = Decimal(str(data[field]))
                    except (InvalidOperation, ValueError):
                        result[field] = None
                else:
                    result[field] = None
            
            # Parse line items
            if data.get("line_items") and isinstance(data["line_items"], list):
                for i, item in enumerate(data["line_items"], 1):
                    try:
                        line_item = {
                            "description": item.get("description"),
                            "quantity": Decimal(str(item.get("quantity", 1))),
                            "unit_price": Decimal(str(item.get("unit_price", 0))),
                            "total_price": Decimal(str(item.get("total_price", 0))),
                            "line_number": i,
                            "confidence_score": result["extraction_confidence"]
                        }
                        result["line_items"].append(line_item)
                    except (InvalidOperation, ValueError, TypeError):
                        continue
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to parse LLM response: {str(e)}"}
    
    def _convert_to_schema(self, result: Dict, invoice_document_id: str) -> ExtractedDataCreate:
        """Convert result to schema."""
        return ExtractedDataCreate(
            invoice_document_id=invoice_document_id,
            vendor_name=result.get("vendor_name"),
            vendor_address=result.get("vendor_address"),
            invoice_number=result.get("invoice_number"),
            invoice_date=result.get("invoice_date"),
            due_date=result.get("due_date"),
            total_amount=result.get("total_amount"),
            tax_amount=result.get("tax_amount"),
            subtotal_amount=result.get("subtotal_amount"),
            currency=result.get("currency", "USD"),
            extraction_confidence=result.get("extraction_confidence", 0.5),
            extracted_at=datetime.utcnow()
        )
    
    def _create_error_result(self, invoice_document_id: str, error: str) -> ExtractedDataCreate:
        """Create error result."""
        return ExtractedDataCreate(
            invoice_document_id=invoice_document_id,
            extraction_confidence=0.0,
            extracted_at=datetime.utcnow()
        )

    async def extract_data(self, image_path: str) -> Dict:
        """
        Extract data from image for enhanced extractor compatibility.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with extracted_data and processing_metadata
        """
        import time
        start_time = time.time()

        try:
            # Extract text
            text = self._extract_text_safely(image_path)

            if not text.strip():
                logger.warning("No text extracted from document")
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
                        "processing_time_ms": int((time.time() - start_time) * 1000),
                        "error": "No text extracted"
                    }
                }

            logger.info(f"Extracted text: {text[:100]}...")

            # Use LLM to structure the text
            structured_data = self._extract_with_llm(text)

            if structured_data.get("error"):
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
                        "processing_time_ms": int((time.time() - start_time) * 1000),
                        "error": structured_data["error"]
                    }
                }

            # Parse structured data
            result = self._parse_llm_response(structured_data)

            processing_time_ms = int((time.time() - start_time) * 1000)

            return {
                "extracted_data": {
                    "vendor_name": result.get("vendor_name"),
                    "vendor_address": result.get("vendor_address"),
                    "invoice_number": result.get("invoice_number"),
                    "invoice_date": result.get("invoice_date"),
                    "due_date": result.get("due_date"),
                    "total_amount": result.get("total_amount"),
                    "tax_amount": result.get("tax_amount"),
                    "subtotal_amount": result.get("subtotal_amount"),
                    "currency": result.get("currency", "USD"),
                    "line_items": result.get("line_items", [])
                },
                "processing_metadata": {
                    "method": "OCR",
                    "confidence_avg": result.get("extraction_confidence", 0.0),
                    "processing_time_ms": processing_time_ms
                }
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
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
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "error": str(e)
                }
            }


# Global instance
simple_extractor = SimpleOCRExtractor()