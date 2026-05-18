"""PDF to image conversion service using PyMuPDF."""

import logging
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io


class PDFConverter:
    """Service for converting PDF files to images."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Storage path for converted images
        self.converted_dir = Path(__file__).parent.parent.parent.parent / "shared" / "storage" / "converted"
        self.converted_dir.mkdir(parents=True, exist_ok=True)

    def is_pdf(self, file_path: str) -> bool:
        """Check if file is a PDF."""
        return Path(file_path).suffix.lower() == '.pdf'

    def convert_pdf_to_images(
        self,
        pdf_path: str,
        dpi: int = 300,
        first_page_only: bool = True
    ) -> List[str]:
        """
        Convert PDF file to images.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (default 300 DPI)
            first_page_only: Only convert first page (default True for invoices)

        Returns:
            List of paths to converted image files
        """
        try:
            self.logger.info(f"Converting PDF to images: {pdf_path}")

            # Open PDF
            pdf_document = fitz.open(pdf_path)

            # Determine pages to convert
            if first_page_only:
                pages_to_convert = [0]
            else:
                pages_to_convert = range(len(pdf_document))

            converted_images = []
            pdf_name = Path(pdf_path).stem

            for page_num in pages_to_convert:
                # Get page
                page = pdf_document[page_num]

                # Calculate zoom factor for desired DPI
                # PyMuPDF default is 72 DPI
                zoom = dpi / 72
                matrix = fitz.Matrix(zoom, zoom)

                # Render page to pixmap
                pix = page.get_pixmap(matrix=matrix)

                # Convert pixmap to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # Save image
                output_filename = f"{pdf_name}_page{page_num + 1}.png"
                output_path = self.converted_dir / output_filename

                img.save(str(output_path), "PNG")
                converted_images.append(str(output_path))

                self.logger.info(f"Converted page {page_num + 1} to: {output_path}")

            pdf_document.close()

            self.logger.info(f"PDF conversion completed: {len(converted_images)} image(s) created")
            return converted_images

        except Exception as e:
            self.logger.error(f"PDF conversion failed for {pdf_path}: {e}")
            raise RuntimeError(f"Failed to convert PDF to images: {e}")

    def convert_first_page(self, pdf_path: str, dpi: int = 300) -> str:
        """
        Convert only the first page of a PDF to an image.
        Convenience method for invoice processing.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (default 300 DPI)

        Returns:
            Path to converted image file
        """
        images = self.convert_pdf_to_images(pdf_path, dpi=dpi, first_page_only=True)
        return images[0] if images else None


# Global PDF converter instance
pdf_converter = PDFConverter()
