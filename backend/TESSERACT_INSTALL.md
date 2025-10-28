# Tesseract OCR Installation Guide

## Issue
You're getting the error: "OCR failed: tesseract is not installed or it's not in your PATH"

## Current Status
- Tesseract binary was installed successfully at `/usr/local/Cellar/tesseract/5.5.1`
- However, there's a dependency issue with `leptonica` library that prevents Tesseract from running

## Solutions (in order of preference)

### Option 1: Fix Homebrew Dependencies (Recommended)
```bash
# Clean up brew dependencies
brew doctor

# Fix the zstd conflict manually
sudo rm -rf /usr/local/lib/cmake/zstd
sudo rm -rf /usr/local/Cellar/zstd/1.5.2

# Reinstall zstd and tesseract
brew install zstd
brew install leptonica
brew install tesseract

# Test installation
tesseract --version
```

### Option 2: Install via Conda (Alternative)
```bash
# Install miniconda first if not available
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Create environment and install tesseract
conda create -n tesseract python=3.9
conda activate tesseract
conda install -c conda-forge tesseract
```

### Option 3: Manual Binary Installation
```bash
# Download pre-compiled binary
wget https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.0/tesseract-ocr-setup-5.3.0.20221214.exe

# Or use MacPorts
sudo port install tesseract
```

### Option 4: Use Docker (Development)
```bash
# Pull tesseract docker image
docker pull tesseractshadow/tesseract4re

# Run OCR processing in container
docker run --rm -v $(pwd):/app tesseractshadow/tesseract4re tesseract /app/invoice.png stdout
```

## Quick Test
After installation, test with:
```bash
# Check version
tesseract --version

# Test with sample text
echo "Hello World" | tesseract stdin stdout
```

## Current Workaround
For now, the application will show an error message when Tesseract is not available. Once installed properly, simply retry uploading your invoice document.

## Invoice Formats Supported
Once Tesseract is working, the system supports:
- PDF documents (both text-based and image-based)
- PNG images
- JPG/JPEG images  
- TIFF images

The system will automatically:
1. Extract text from images using OCR
2. Parse invoice data (vendor, invoice number, amounts, dates)
3. Provide a review interface for corrections
4. Export structured data