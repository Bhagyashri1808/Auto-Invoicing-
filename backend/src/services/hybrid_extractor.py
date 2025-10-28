"""Hybrid OCR + LLM data extraction service."""

import json
import logging
import requests
import easyocr
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from models.schemas import ExtractedDataCreate
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class HybridExtractor:
    """Service for extracting structured data using OCR + LLM."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize hybrid extractor."""
        self.ollama_url = ollama_url
        self.model = "llama3.1:8b"
        self.ocr_reader = None
        
    def _init_ocr(self):
        """Initialize OCR reader lazily."""
        if self.ocr_reader is None:
            try:
                self.ocr_reader = easyocr.Reader(['en'])
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {str(e)}")
                raise
    
    def extract_structured_data(
        self, 
        file_path: str, 
        invoice_document_id: str
    ) -> ExtractedDataCreate:
        """
        Extract structured data from invoice using OCR + LLM.
        
        Args:
            file_path: Path to invoice file
            invoice_document_id: UUID of invoice document
            
        Returns:
            ExtractedDataCreate schema with structured data
        """
        try:
            # Step 1: Extract text using EasyOCR
            ocr_text = self._extract_text_with_ocr(file_path)
            
            if not ocr_text.strip():
                return self._create_error_result(
                    invoice_document_id, 
                    "No text could be extracted from the document"
                )
            
            logger.info(f"OCR extracted text: {ocr_text[:200]}...")
            
            # Step 2: Use LLM to structure the extracted text
            extraction_result = self._extract_with_llm(ocr_text)
            
            if extraction_result.get("error"):
                return self._create_error_result(invoice_document_id, extraction_result["error"])
            
            # Step 3: Convert to Pydantic schema
            return self._convert_to_schema(extraction_result, invoice_document_id)
            
        except Exception as e:
            logger.error(f"Hybrid extraction failed: {str(e)}")
            return self._create_error_result(invoice_document_id, str(e))
    
    def _extract_text_with_ocr(self, file_path: str) -> str:
        """Extract text from document using EasyOCR."""
        try:
            self._init_ocr()
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise Exception(f"File not found: {file_path}")
            
            extension = file_path_obj.suffix.lower()
            
            if extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                return self._extract_text_from_image(file_path)
            else:
                raise Exception(f"Unsupported file type: {extension}")
                
        except Exception as e:
            logger.error(f"OCR text extraction failed: {str(e)}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF + OCR."""
        try:
            doc = fitz.open(file_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Try direct text extraction first
                text = page.get_text()
                
                if text.strip():
                    # Text-based PDF
                    all_text.append(text)
                else:
                    # Image-based PDF - use OCR
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
                    img_data = pix.tobytes("png")
                    
                    # Convert to OpenCV format for EasyOCR
                    nparr = np.frombuffer(img_data, np.uint8)
                    cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Extract text with EasyOCR
                    results = self.ocr_reader.readtext(cv_image)
                    page_text = " ".join([result[1] for result in results])
                    all_text.append(page_text)
            
            doc.close()
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            raise
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using EasyOCR."""
        try:
            # Read image with OpenCV
            image = cv2.imread(file_path)
            if image is None:
                raise Exception(f"Could not read image: {file_path}")
            
            # Extract text with EasyOCR
            results = self.ocr_reader.readtext(image)
            
            # Combine all text results
            extracted_text = " ".join([result[1] for result in results])
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Image text extraction failed: {str(e)}")
            raise
    
    def _extract_with_llm(self, ocr_text: str) -> Dict:
        """Extract structured data from OCR text using LLM."""
        try:
            # Build prompt for invoice data extraction
            prompt = f"""You are an expert invoice data extraction system. Extract structured data from the following OCR text from an invoice:

OCR TEXT:
{ocr_text}

Extract the following information and return ONLY valid JSON (no other text):

{{
  "vendor_name": "Vendor/company name that issued the invoice",
  "vendor_address": "Full address of the vendor",
  "invoice_number": "Invoice number (look for formats like INV-XXXX-XXX)",
  "invoice_date": "Invoice date in YYYY-MM-DD format",
  "due_date": "Due date in YYYY-MM-DD format (if present, otherwise null)",
  "total_amount": "Total amount as decimal number only (no currency symbols)",
  "tax_amount": "Tax/GST amount as decimal number only (if present, otherwise null)",
  "subtotal_amount": "Subtotal amount as decimal number only (if present, otherwise null)",
  "currency": "Currency code (USD, AUD, EUR, etc.)",
  "line_items": [
    {{
      "description": "Item/service description",
      "quantity": "Quantity as decimal",
      "unit_price": "Unit price as decimal",
      "total_price": "Total price as decimal"
    }}
  ],
  "extraction_confidence": "Confidence score from 0.0 to 1.0 based on text clarity"
}}

Rules:
1. Return ONLY valid JSON, no explanations
2. Use null for missing values
3. For amounts, return only numbers (no $, commas, or currency symbols)
4. Be precise with invoice numbers - look for patterns like INV-2025-001
5. Date format must be YYYY-MM-DD
6. If text is unclear, lower the confidence score
7. Extract ALL line items you can identify

JSON Response:"""

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent extraction
                        "top_p": 0.9,
                        "num_predict": 2048
                    }
                },
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code != 200:
                return {"error": f"LLM API error: {response.status_code} - {response.text}"}
            
            # Parse LLM response
            llm_response = response.json()
            extracted_json = llm_response.get("response", "")
            
            # Parse JSON response from LLM
            try:
                data = json.loads(extracted_json)
                return self._parse_llm_response(data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"LLM returned invalid JSON: {extracted_json}")
                return {"error": "LLM returned invalid JSON response"}
                
        except requests.exceptions.Timeout:
            return {"error": "LLM request timed out"}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to Ollama. Make sure Ollama is running (ollama serve)"}
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
                        logger.warning(f"Invalid {date_field} format: {data[date_field]}")
                        result[date_field] = None
                else:
                    result[date_field] = None
            
            # Parse amounts
            for field in ["total_amount", "tax_amount", "subtotal_amount"]:
                if data.get(field):
                    try:
                        result[field] = Decimal(str(data[field]))
                    except (InvalidOperation, ValueError):
                        logger.warning(f"Invalid {field}: {data[field]}")
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
                    except (InvalidOperation, ValueError, TypeError) as e:
                        logger.warning(f"Invalid line item {i}: {e}")
                        continue
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to parse LLM response: {str(e)}"}
    
    def _convert_to_schema(self, result: Dict, invoice_document_id: str) -> ExtractedDataCreate:
        """Convert result to ExtractedDataCreate schema."""
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
        """Create error result schema."""
        return ExtractedDataCreate(
            invoice_document_id=invoice_document_id,
            extraction_confidence=0.0,
            extracted_at=datetime.utcnow()
        )
    
    def test_connection(self) -> Dict:
        """Test OCR and LLM connections."""
        try:
            # Test OCR
            self._init_ocr()
            ocr_status = "✅ EasyOCR ready"
        except Exception as e:
            ocr_status = f"❌ EasyOCR failed: {str(e)}"
        
        # Test LLM
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                llm_status = f"✅ Ollama connected - Models: {model_names}"
            else:
                llm_status = f"❌ Ollama HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            llm_status = "❌ Ollama disconnected"
        except Exception as e:
            llm_status = f"❌ Ollama error: {str(e)}"
        
        return {
            "ocr_status": ocr_status,
            "llm_status": llm_status
        }