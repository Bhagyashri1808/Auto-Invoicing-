"""LLM-based data extraction service using Llama 3.1."""

import json
import logging
import requests
import base64
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, asdict
from models.schemas import ExtractedDataCreate, LineItemCreate
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class LLMExtractionResult:
    """Result of LLM-based data extraction."""
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    subtotal_amount: Optional[Decimal] = None
    currency: str = "USD"
    line_items: List[Dict] = None
    extraction_confidence: float = 0.0
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []


class LLMExtractor:
    """Service for extracting structured data from invoices using Llama 3.1."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize LLM extractor."""
        self.ollama_url = ollama_url
        self.model = "llama3.1:8b"
        
    def extract_structured_data(
        self, 
        file_path: str, 
        invoice_document_id: str
    ) -> ExtractedDataCreate:
        """
        Extract structured data from invoice using LLM.
        
        Args:
            file_path: Path to invoice file
            invoice_document_id: UUID of invoice document
            
        Returns:
            ExtractedDataCreate schema with structured data
        """
        try:
            # Convert document to text/image for LLM processing
            document_content = self._prepare_document_content(file_path)
            
            if document_content.get("error"):
                return self._create_error_result(
                    invoice_document_id, 
                    document_content["error"]
                )
            
            # Extract data using LLM
            extraction_result = self._extract_with_llm(document_content)
            
            if extraction_result.error:
                return self._create_error_result(invoice_document_id, extraction_result.error)
            
            # Convert to Pydantic schema
            return self._convert_to_schema(extraction_result, invoice_document_id)
            
        except Exception as e:
            logger.error(f"LLM data extraction failed: {str(e)}")
            return self._create_error_result(invoice_document_id, str(e))
    
    def _prepare_document_content(self, file_path: str) -> Dict:
        """
        Prepare document content for LLM processing.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dict with document content and metadata
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return {"error": f"File not found: {file_path}"}
            
            extension = file_path_obj.suffix.lower()
            
            if extension == '.pdf':
                return self._extract_pdf_content(file_path)
            elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']:
                return self._extract_image_content(file_path)
            else:
                return {"error": f"Unsupported file type: {extension}"}
                
        except Exception as e:
            return {"error": f"Document preparation failed: {str(e)}"}
    
    def _extract_pdf_content(self, file_path: str) -> Dict:
        """Extract content from PDF for LLM processing."""
        try:
            doc = fitz.open(file_path)
            pages_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Try to extract text first
                text = page.get_text()
                
                if text.strip():
                    # Text-based PDF
                    pages_content.append({
                        "type": "text",
                        "content": text,
                        "page": page_num + 1
                    })
                else:
                    # Image-based PDF - convert to base64 image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    pages_content.append({
                        "type": "image",
                        "content": img_base64,
                        "page": page_num + 1
                    })
            
            doc.close()
            
            return {
                "content": pages_content,
                "file_type": "pdf",
                "page_count": len(pages_content)
            }
            
        except Exception as e:
            return {"error": f"PDF processing failed: {str(e)}"}
    
    def _extract_image_content(self, file_path: str) -> Dict:
        """Extract content from image for LLM processing."""
        try:
            # Convert image to base64
            with open(file_path, "rb") as image_file:
                img_data = image_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            return {
                "content": [{
                    "type": "image",
                    "content": img_base64,
                    "page": 1
                }],
                "file_type": "image",
                "page_count": 1
            }
            
        except Exception as e:
            return {"error": f"Image processing failed: {str(e)}"}
    
    def _extract_with_llm(self, document_content: Dict) -> LLMExtractionResult:
        """
        Extract invoice data using Llama 3.1 LLM.
        
        Args:
            document_content: Prepared document content
            
        Returns:
            LLMExtractionResult with extracted data
        """
        try:
            # Build prompt for invoice data extraction
            prompt = self._build_extraction_prompt(document_content)
            
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
                return LLMExtractionResult(
                    error=f"LLM API error: {response.status_code} - {response.text}"
                )
            
            # Parse LLM response
            llm_response = response.json()
            extracted_json = llm_response.get("response", "")
            
            # Parse JSON response from LLM
            try:
                data = json.loads(extracted_json)
                return self._parse_llm_response(data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"LLM returned invalid JSON: {extracted_json}")
                # Try to extract data from text response
                return self._parse_text_response(extracted_json)
                
        except requests.exceptions.Timeout:
            return LLMExtractionResult(error="LLM request timed out")
        except requests.exceptions.ConnectionError:
            return LLMExtractionResult(error="Could not connect to Ollama. Make sure Ollama is running (ollama serve)")
        except Exception as e:
            return LLMExtractionResult(error=f"LLM extraction failed: {str(e)}")
    
    def _build_extraction_prompt(self, document_content: Dict) -> str:
        """Build prompt for LLM invoice data extraction."""
        
        content_desc = ""
        if document_content["file_type"] == "pdf":
            content_desc = f"PDF document with {document_content['page_count']} page(s)"
        else:
            content_desc = "Image document"
        
        # Check if we have text content
        has_text = any(page.get("type") == "text" for page in document_content["content"])
        
        if has_text:
            # Include text content in prompt
            text_content = "\n".join([
                page["content"] for page in document_content["content"] 
                if page.get("type") == "text"
            ])
            
            prompt = f"""You are an expert invoice data extraction system. Extract structured data from the following invoice text:

INVOICE TEXT:
{text_content}

Extract the following information and return as JSON:"""
        else:
            prompt = f"""You are an expert invoice data extraction system. I have an invoice image that I need you to analyze and extract data from.

The document is: {content_desc}

Extract the following information and return as JSON:"""
        
        prompt += """
{
  "vendor_name": "Company name that issued the invoice",
  "vendor_address": "Full address of the vendor/company",
  "invoice_number": "Invoice number or reference number",
  "invoice_date": "Invoice date in YYYY-MM-DD format",
  "due_date": "Due date in YYYY-MM-DD format (if present)",
  "total_amount": "Total amount as decimal number only",
  "tax_amount": "Tax amount as decimal number only (if present)",
  "subtotal_amount": "Subtotal amount as decimal number only (if present)",
  "currency": "Currency code (USD, EUR, etc.)",
  "line_items": [
    {
      "description": "Item description",
      "quantity": "Quantity as decimal",
      "unit_price": "Unit price as decimal",
      "total_price": "Total price as decimal"
    }
  ],
  "extraction_confidence": "Confidence score from 0.0 to 1.0"
}

Important rules:
1. Return ONLY valid JSON, no other text
2. Use null for missing values
3. For amounts, return only numbers (no currency symbols)
4. Be very careful to extract the correct invoice number (not "From" or other text)
5. If you can't find a field, use null
6. Date format must be YYYY-MM-DD
7. Confidence should reflect how clearly you can read the information

RESPOND WITH JSON ONLY:"""
        
        return prompt
    
    def _parse_llm_response(self, data: Dict) -> LLMExtractionResult:
        """Parse structured JSON response from LLM."""
        try:
            result = LLMExtractionResult()
            
            # Extract basic fields
            result.vendor_name = data.get("vendor_name")
            result.vendor_address = data.get("vendor_address") 
            result.invoice_number = data.get("invoice_number")
            result.currency = data.get("currency", "USD")
            result.extraction_confidence = float(data.get("extraction_confidence", 0.8))
            
            # Parse dates
            if data.get("invoice_date"):
                try:
                    result.invoice_date = datetime.strptime(data["invoice_date"], "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"Invalid invoice date format: {data['invoice_date']}")
            
            if data.get("due_date"):
                try:
                    result.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"Invalid due date format: {data['due_date']}")
            
            # Parse amounts
            for field in ["total_amount", "tax_amount", "subtotal_amount"]:
                if data.get(field):
                    try:
                        setattr(result, field, Decimal(str(data[field])))
                    except (InvalidOperation, ValueError):
                        logger.warning(f"Invalid {field}: {data[field]}")
            
            # Parse line items
            if data.get("line_items") and isinstance(data["line_items"], list):
                result.line_items = []
                for i, item in enumerate(data["line_items"], 1):
                    try:
                        line_item = {
                            "description": item.get("description"),
                            "quantity": Decimal(str(item.get("quantity", 1))),
                            "unit_price": Decimal(str(item.get("unit_price", 0))),
                            "total_price": Decimal(str(item.get("total_price", 0))),
                            "line_number": i,
                            "confidence_score": result.extraction_confidence
                        }
                        result.line_items.append(line_item)
                    except (InvalidOperation, ValueError, TypeError) as e:
                        logger.warning(f"Invalid line item {i}: {e}")
                        continue
            
            return result
            
        except Exception as e:
            return LLMExtractionResult(error=f"Failed to parse LLM response: {str(e)}")
    
    def _parse_text_response(self, text_response: str) -> LLMExtractionResult:
        """Fallback parser for text-based LLM responses."""
        # This is a simple fallback - in practice, you might want more sophisticated parsing
        return LLMExtractionResult(
            extraction_confidence=0.3,
            error="LLM returned non-JSON response, manual parsing needed"
        )
    
    def _convert_to_schema(
        self, 
        result: LLMExtractionResult, 
        invoice_document_id: str
    ) -> ExtractedDataCreate:
        """Convert LLMExtractionResult to ExtractedDataCreate schema."""
        return ExtractedDataCreate(
            invoice_document_id=invoice_document_id,
            vendor_name=result.vendor_name,
            vendor_address=result.vendor_address,
            invoice_number=result.invoice_number,
            invoice_date=result.invoice_date,
            due_date=result.due_date,
            total_amount=result.total_amount,
            tax_amount=result.tax_amount,
            subtotal_amount=result.subtotal_amount,
            currency=result.currency,
            extraction_confidence=result.extraction_confidence,
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
        """Test connection to Ollama."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                return {
                    "status": "connected",
                    "models": model_names,
                    "llama3_available": any("llama3.1" in name for name in model_names)
                }
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {
                "status": "disconnected", 
                "message": "Could not connect to Ollama. Run 'ollama serve' to start it."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}