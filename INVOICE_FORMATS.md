# Supported Invoice Formats

This document describes the invoice formats that the Invoice Automation system can process and extract data from effectively.

## 📋 Overview

The system uses **OpenCV + Tesseract OCR** with intelligent text extraction patterns to process invoice documents. It works best with **standard business invoice layouts** but can adapt to various formats.

## ✅ Supported Invoice Types

### 1. **Standard Business Invoices**
- Traditional invoice layout with clear sections
- Company letterhead at the top
- "Bill To" and "Bill From" sections
- Line items in tabular format
- Clear totals and tax information

### 2. **PDF Invoices**
- Text-based PDFs (preferred for highest accuracy)
- Scanned PDF documents (processed via OCR)
- Multi-page invoices supported

### 3. **Image-based Invoices**
- Scanned invoices (JPG, PNG, TIFF)
- Photographed invoices with good lighting
- High contrast black text on white background

## 🎯 Data Extraction Capabilities

### **Vendor Information**
- **Company Name**: Extracted from document header
- **Address**: Business address (up to 500 characters)
- **Contact Information**: When clearly formatted

### **Invoice Metadata**
- **Invoice Number**: Various formats (INV-001, #12345, etc.)
- **Invoice Date**: Multiple date formats supported
- **Due Date**: When specified
- **Currency**: USD, EUR, GBP ($ € £ symbols)

### **Financial Data**
- **Subtotal**: Pre-tax amount
- **Tax Amount**: Sales tax, VAT, etc.
- **Total Amount**: Final amount due
- **Line Items**: Individual products/services with quantities and prices

## 📐 Format Requirements

### **For Best Results:**

1. **Text Quality**
   - Clear, readable text (minimum 10pt font)
   - High contrast (black text on white background)
   - Minimal background patterns or watermarks

2. **Layout Structure**
   - Standard top-to-bottom layout
   - Clear section separation
   - Vendor info at the top
   - Line items in table format

3. **File Quality**
   - Resolution: 300 DPI or higher for images
   - File size: Under 50MB
   - Clean, undamaged documents

### **Supported Layouts:**

```
Example Layout 1 - Standard Invoice:
┌─────────────────────────────────────┐
│ ACME Corporation                    │
│ 123 Business St, City, ST 12345     │
│                                     │
│ INVOICE                             │
│ Invoice #: INV-2024-001             │
│ Date: January 15, 2024              │
│                                     │
│ Bill To:                           │
│ Customer Name                       │
│ Customer Address                    │
│                                     │
│ Description    Qty   Price   Total  │
│ Widget A        2    $50.00  $100.00│
│ Service B       1    $25.00   $25.00│
│                                     │
│ Subtotal:              $125.00      │
│ Tax (8%):               $10.00      │
│ Total:                 $135.00      │
└─────────────────────────────────────┘
```

## 🔧 OCR Processing Pipeline

### **Step 1: Image Preprocessing**
- Grayscale conversion
- Noise reduction (median blur)
- Contrast enhancement (CLAHE)
- Binary thresholding
- Morphological operations

### **Step 2: Text Extraction**
- Tesseract OCR with optimized settings
- Multiple page support for PDFs
- Confidence scoring for extracted text

### **Step 3: Data Parsing**
- Regex pattern matching for structured data
- Intelligent field detection
- Format validation and cleanup

### **Step 4: Validation**
- Field length validation (vendor name ≤ 255 chars)
- Data type validation (dates, amounts)
- Confidence scoring and quality assessment

## ⚠️ Current Limitations

### **Format Limitations:**
- **Handwritten invoices**: Not supported (requires printed/typed text)
- **Complex layouts**: Tables with merged cells may cause issues
- **Multiple currencies**: Mixed currency invoices not fully supported
- **Non-English**: Optimized for English language invoices

### **Quality Limitations:**
- **Poor scan quality**: Low resolution or blurry images
- **Rotated documents**: Must be properly oriented
- **Watermarks**: Heavy watermarks can interfere with OCR
- **Background patterns**: Complex backgrounds reduce accuracy

### **Data Extraction Notes:**
- **Line items**: Simple table formats work best
- **Vendor detection**: First clear company name in document
- **Amount parsing**: Requires clear currency symbols and formatting

## 🎨 Sample Invoice Formats

### **Format A: Professional Service Invoice**
```
Professional Services LLC
456 Office Drive, Suite 100
Business City, ST 54321
Phone: (555) 123-4567

INVOICE #2024-0156
Date: March 15, 2024
Due Date: April 14, 2024

Bill To:
Client Company Inc.
789 Customer Avenue
Client City, ST 98765

Description                    Hours    Rate      Total
Consulting Services             40      $150.00   $6,000.00
Project Management             10      $125.00   $1,250.00

                           Subtotal:   $7,250.00
                          Tax (7.5%):    $543.75
                             Total:   $7,793.75
```

### **Format B: Product Sales Invoice**
```
RETAIL SOLUTIONS
321 Commerce Blvd
Sales City, ST 11111

Invoice Number: RS-2024-0892
Invoice Date: 2024-02-28

Customer:
ABC Retail Store
555 Shopping Center
Retail Town, ST 22222

Item                     Qty    Unit Price    Amount
Product SKU-001           50        $12.99    $649.50
Product SKU-002           25        $24.99    $624.75
Shipping                   1        $45.00     $45.00

                      Subtotal:              $1,319.25
                    Sales Tax:                $105.54
                        Total:              $1,424.79
```

## 🔄 Confidence Scoring

The system provides confidence scores for extracted data:

- **High Confidence (>85%)**: Direct pattern matches, clear formatting
- **Medium Confidence (60-85%)**: Fuzzy matches, some formatting issues  
- **Low Confidence (<60%)**: Poor quality OCR, unclear formatting

## 📈 Improvement Recommendations

### **For Users:**
1. **Scan Quality**: Use 300+ DPI, ensure good lighting
2. **File Format**: PDF preferred over images when possible
3. **Orientation**: Ensure documents are properly oriented
4. **Cleanup**: Remove staples, smooth wrinkles before scanning

### **For Developers:**
1. **Pattern Enhancement**: Add more vendor/amount patterns based on real data
2. **ML Integration**: Consider adding machine learning for better pattern recognition
3. **Language Support**: Extend to support multiple languages
4. **Layout Detection**: Add automatic layout detection for complex formats

---

**Last Updated**: January 10, 2025  
**Version**: 1.0.0  
**Status**: Active Development 🚧