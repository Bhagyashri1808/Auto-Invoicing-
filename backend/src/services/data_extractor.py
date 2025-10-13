"""Data extraction service for parsing OCR text into structured invoice data."""

import re
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from models.schemas import ExtractedDataCreate, LineItemCreate

logger = logging.getLogger(__name__)


@dataclass
class ExtractedInvoiceData:
    """Structured invoice data extracted from OCR text."""
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    subtotal_amount: Optional[Decimal] = None
    currency: str = "USD"
    extraction_confidence: float = 0.0
    line_items: List[Dict] = None
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []


class DataExtractor:
    """Service for extracting structured data from OCR text."""
    
    def __init__(self):
        """Initialize data extractor with patterns."""
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup regex patterns for data extraction."""
        # Invoice number patterns
        self.invoice_number_patterns = [
            r'invoice\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
            r'inv\s*#?\s*:?\s*([A-Za-z0-9\-_]+)',
            r'#\s*([A-Za-z0-9\-_]+)',
            r'number\s*:?\s*([A-Za-z0-9\-_]+)',
        ]
        
        # Date patterns
        self.date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # MM-DD-YYYY or MM/DD/YYYY
            r'(\w+\s+\d{1,2},?\s+\d{4})',      # Month DD, YYYY
            r'(\d{1,2}\s+\w+\s+\d{4})',       # DD Month YYYY
        ]
        
        # Amount patterns
        self.amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 1,234.56$
            r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', # USD 1234.56
            r'(\d+\.\d{2})',                           # Simple decimal
        ]
        
        # Vendor patterns (usually at top of invoice)
        self.vendor_patterns = [
            r'from\s*:?\s*(.+?)(?:\n.*?(?:bill\s+to|invoice\s+to|to\s*:|date|amount))',
            r'vendor\s*:?\s*(.+?)(?:\n|$)',
            r'bill\s+from\s*:?\s*(.+?)(?:\n.*?(?:bill\s+to|invoice\s+to))',
            # More specific pattern that looks for company info before "Bill To" or invoice metadata
            r'^([^\n]+(?:\n[^\n]*address[^\n]*)?[^\n]*)(?:\n.*?(?:bill\s+to|invoice\s+(?:number|date)|customer))',
        ]
        
        # Tax patterns
        self.tax_patterns = [
            r'tax\s*:?\s*\$?\s*(\d+(?:\.\d{2})?)',
            r'vat\s*:?\s*\$?\s*(\d+(?:\.\d{2})?)',
            r'sales\s+tax\s*:?\s*\$?\s*(\d+(?:\.\d{2})?)',
        ]
        
        # Total patterns
        self.total_patterns = [
            r'total\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'amount\s+due\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'grand\s+total\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        # Subtotal patterns
        self.subtotal_patterns = [
            r'subtotal\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'sub\s*total\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
    
    def extract_structured_data(
        self, 
        ocr_text: str, 
        invoice_document_id: str,
        base_confidence: float = 0.0
    ) -> ExtractedDataCreate:
        """
        Extract structured data from OCR text.
        
        Args:
            ocr_text: Raw OCR text
            invoice_document_id: UUID of invoice document
            base_confidence: Base confidence from OCR
            
        Returns:
            ExtractedDataCreate schema with structured data
        """
        try:
            # Clean the text
            cleaned_text = self._clean_text(ocr_text)
            
            # Extract individual fields
            extracted_data = ExtractedInvoiceData()
            
            # Extract vendor information
            extracted_data.vendor_name, extracted_data.vendor_address = self._extract_vendor_info(cleaned_text)
            
            # Extract invoice metadata
            extracted_data.invoice_number = self._extract_invoice_number(cleaned_text)
            extracted_data.invoice_date = self._extract_invoice_date(cleaned_text)
            extracted_data.due_date = self._extract_due_date(cleaned_text)
            
            # Extract financial amounts
            extracted_data.total_amount = self._extract_total_amount(cleaned_text)
            extracted_data.tax_amount = self._extract_tax_amount(cleaned_text)
            extracted_data.subtotal_amount = self._extract_subtotal_amount(cleaned_text)
            
            # Extract currency
            extracted_data.currency = self._extract_currency(cleaned_text)
            
            # Extract line items
            extracted_data.line_items = self._extract_line_items(cleaned_text)
            
            # Calculate extraction confidence
            extracted_data.extraction_confidence = self._calculate_extraction_confidence(
                extracted_data, base_confidence
            )
            
            # Convert to Pydantic schema
            return ExtractedDataCreate(
                invoice_document_id=invoice_document_id,
                vendor_name=extracted_data.vendor_name,
                vendor_address=extracted_data.vendor_address,
                invoice_number=extracted_data.invoice_number,
                invoice_date=extracted_data.invoice_date,
                due_date=extracted_data.due_date,
                total_amount=extracted_data.total_amount,
                tax_amount=extracted_data.tax_amount,
                subtotal_amount=extracted_data.subtotal_amount,
                currency=extracted_data.currency,
                extraction_confidence=extracted_data.extraction_confidence,
                extracted_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            # Return minimal data with low confidence
            return ExtractedDataCreate(
                invoice_document_id=invoice_document_id,
                extraction_confidence=0.0,
                extracted_at=datetime.utcnow()
            )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text."""
        # Normalize line breaks first
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove extra whitespace within lines but preserve line structure
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove extra spaces within the line
            cleaned_line = re.sub(r'\s+', ' ', line.strip())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        # Join lines back with newlines
        text = '\n'.join(cleaned_lines)
        
        return text.strip()
    
    def _extract_vendor_info(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract vendor name and address."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        vendor_name = None
        vendor_address = None
        
        # Try to find "From:" or similar patterns
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                vendor_info = match.group(1).strip()
                vendor_lines = [line.strip() for line in vendor_info.split('\n') if line.strip()]
                vendor_name = vendor_lines[0] if vendor_lines else None
                vendor_address = '\n'.join(vendor_lines[1:3]) if len(vendor_lines) > 1 else None
                break
        
        # Fallback: Look for company-like patterns in first few lines
        if not vendor_name and lines:
            # Look for the first line that looks like a company name
            for i, line in enumerate(lines[:5]):  # Check first 5 lines
                # Skip lines that look like document titles, invoice numbers, or metadata
                skip_keywords = [
                    'invoice', 'receipt', 'bill', 'quote', 'estimate', 'statement',
                    'number', 'date', 'due', 'from:', 'to:', 'total:', 'amount:',
                    'email:', 'phone:', 'fax:', 'www.', 'http', '@', 'inv-', 'inv#',
                    'ref:', 'reference', 'customer:', 'client:', 'attention:', 'attn:'
                ]
                if any(keyword in line.lower() for keyword in skip_keywords):
                    continue
                if re.search(r'^\s*#?\s*\d+', line):  # Skip lines starting with numbers
                    continue
                if re.search(r'^\s*[A-Z]{2,}[\-#]?\s*\d+', line):  # Skip reference codes like "INV-001"
                    continue
                if re.search(r':\s*[A-Z0-9\-]+$', line):  # Skip "Label: VALUE" patterns
                    continue
                # Must be substantial non-numeric text and look like a company name
                if (len(line) > 3 and not line.isdigit() and 
                    self._looks_like_company_name(line)):
                    vendor_name = line
                    # Try to find address in next 1-2 lines
                    if i + 1 < len(lines):
                        address_lines = []
                        for j in range(i + 1, min(i + 4, len(lines))):
                            addr_line = lines[j]
                            # Stop if we hit invoice content
                            if any(keyword in addr_line.lower() for keyword in ['invoice', 'bill to', 'date:', 'customer']):
                                break
                            # Include if it looks like address info
                            if (len(addr_line) > 5 and 
                                not addr_line.isdigit() and 
                                not re.search(r'^\s*[A-Z]{2,}\s*\d+', addr_line)):
                                address_lines.append(addr_line)
                        vendor_address = '\n'.join(address_lines) if address_lines else None
                    break
        
        # Truncate fields to fit database constraints
        if vendor_name and len(vendor_name) > 255:
            vendor_name = vendor_name[:252] + "..."
        if vendor_address and len(vendor_address) > 500:
            vendor_address = vendor_address[:497] + "..."
            
        return vendor_name, vendor_address
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number."""
        for pattern in self.invoice_number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_number = match.group(1).strip()
                # Clean up common OCR artifacts
                invoice_number = re.sub(r'[^\w\-_.]', '', invoice_number)
                # Truncate if too long
                if len(invoice_number) > 50:
                    invoice_number = invoice_number[:50]
                return invoice_number if invoice_number else None
        return None
    
    def _extract_invoice_date(self, text: str) -> Optional[date]:
        """Extract invoice date."""
        # Look for "invoice date" specifically first
        invoice_date_pattern = r'invoice\s+date\s*:?\s*([^\n]+)'
        match = re.search(invoice_date_pattern, text, re.IGNORECASE)
        
        if match:
            date_str = match.group(1).strip()
            return self._parse_date(date_str)
        
        # Fallback to general date patterns
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return self._parse_date(match.group(1))
        
        return None
    
    def _extract_due_date(self, text: str) -> Optional[date]:
        """Extract due date."""
        due_date_pattern = r'due\s+date\s*:?\s*([^\n]+)'
        match = re.search(due_date_pattern, text, re.IGNORECASE)
        
        if match:
            date_str = match.group(1).strip()
            return self._parse_date(date_str)
        
        return None
    
    def _extract_total_amount(self, text: str) -> Optional[Decimal]:
        """Extract total amount."""
        for pattern in self.total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        return None
    
    def _extract_tax_amount(self, text: str) -> Optional[Decimal]:
        """Extract tax amount."""
        for pattern in self.tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        return None
    
    def _extract_subtotal_amount(self, text: str) -> Optional[Decimal]:
        """Extract subtotal amount."""
        for pattern in self.subtotal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        return None
    
    def _extract_currency(self, text: str) -> str:
        """Extract currency code."""
        currency_patterns = [
            r'\b(USD|EUR|GBP|CAD|AUD)\b',
            r'\$',  # Dollar sign
            r'€',   # Euro sign
            r'£',   # Pound sign
        ]
        
        for pattern in currency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol_to_code = {'$': 'USD', '€': 'EUR', '£': 'GBP'}
                return symbol_to_code.get(match.group(0), match.group(0))
        
        return "USD"  # Default
    
    def _extract_line_items(self, text: str) -> List[Dict]:
        """Extract line items from invoice."""
        # This is a simplified implementation
        # In a real system, this would be more sophisticated
        line_items = []
        
        # Look for table-like structures
        lines = text.split('\n')
        
        # Find lines that look like item descriptions with amounts
        item_pattern = r'(.+?)\s+(\d+(?:\.\d+)?)\s+\$?(\d+(?:\.\d{2})?)\s+\$?(\d+(?:\.\d{2})?)'
        
        line_number = 1
        for line in lines:
            match = re.search(item_pattern, line)
            if match:
                try:
                    description = match.group(1).strip()
                    quantity = Decimal(match.group(2))
                    unit_price = Decimal(match.group(3))
                    total_price = Decimal(match.group(4))
                    
                    line_items.append({
                        "description": description,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price,
                        "line_number": line_number,
                        "confidence_score": 0.7  # Default confidence for line items
                    })
                    line_number += 1
                except (InvalidOperation, ValueError):
                    continue
        
        return line_items
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Parse amount string into Decimal."""
        try:
            # Remove commas and dollar signs
            clean_amount = re.sub(r'[,$]', '', amount_str.strip())
            return Decimal(clean_amount)
        except (InvalidOperation, ValueError):
            return None
    
    def _calculate_extraction_confidence(
        self, 
        data: ExtractedInvoiceData, 
        base_confidence: float
    ) -> float:
        """Calculate overall extraction confidence."""
        field_scores = []
        
        # Score each field based on whether it was extracted
        if data.vendor_name:
            field_scores.append(0.9)
        if data.invoice_number:
            field_scores.append(0.9)
        if data.invoice_date:
            field_scores.append(0.8)
        if data.total_amount:
            field_scores.append(0.9)
        if data.tax_amount:
            field_scores.append(0.7)
        if data.subtotal_amount:
            field_scores.append(0.7)
        if data.line_items:
            field_scores.append(0.8)
        
        # Calculate average field extraction score
        if field_scores:
            field_confidence = sum(field_scores) / len(field_scores)
        else:
            field_confidence = 0.0
        
        # Combine with base OCR confidence
        overall_confidence = (base_confidence + field_confidence) / 2.0
        
        return min(overall_confidence, 1.0)
    
    def _looks_like_company_name(self, text: str) -> bool:
        """Check if a line of text looks like a company name."""
        text = text.strip()
        
        # Skip empty or very short text
        if len(text) < 3:
            return False
        
        # Skip lines that are mostly numbers
        if re.search(r'\d', text) and len(re.sub(r'[^\d]', '', text)) / len(text) > 0.5:
            return False
        
        # Skip lines with colons followed by values (metadata patterns)
        if re.search(r':\s*[A-Z0-9\-]+', text):
            return False
        
        # Skip lines that start with common invoice keywords
        start_keywords = ['invoice', 'bill', 'receipt', 'quote', 'estimate', 'statement', 'order']
        if any(text.lower().startswith(keyword) for keyword in start_keywords):
            return False
        
        # Positive indicators of company names
        company_indicators = [
            'inc', 'corp', 'ltd', 'llc', 'company', 'corporation', 'limited',
            'co.', 'inc.', 'corp.', 'ltd.', 'llc.', 'university', 'college',
            'school', 'institute', 'foundation', 'organization', 'association'
        ]
        
        # Higher likelihood if it contains company indicators
        if any(indicator in text.lower() for indicator in company_indicators):
            return True
        
        # Check if it looks like a person's name (could be a business owner)
        words = text.split()
        if len(words) >= 2:
            # Check for proper case (Title Case or multiple capital letters)
            capital_words = sum(1 for word in words if word and word[0].isupper())
            if capital_words >= 2:  # Multiple capitalized words suggest proper nouns
                return True
        
        # Check if it has reasonable length and mixed case
        if 5 <= len(text) <= 100 and any(c.isupper() for c in text) and any(c.islower() for c in text):
            return True
        
        return False