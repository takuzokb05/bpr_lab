"""
PDF preprocessing - Convert PDF to individual page images
"""

import os
from pathlib import Path
from typing import List, Tuple
from pdf2image import convert_from_path
from PIL import Image

# Poppler path configuration (local installation)
POPPLER_PATH = Path(__file__).parent / "poppler" / "poppler-25.12.0" / "Library" / "bin"


class PDFProcessor:
    """Handles PDF to image conversion"""
    
    def __init__(self, output_dir: str = "temp_pages", dpi: int = 300, image_format: str = "png"):
        """
        Initialize PDF processor
        
        Args:
            output_dir: Directory to save page images
            dpi: DPI for image conversion (default: 300)
            image_format: Image format - 'png' or 'jpg' (default: png)
        """
        self.output_dir = output_dir
        self.dpi = dpi
        self.image_format = image_format.lower()
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def convert_pdf(self, pdf_path: str, force: bool = False) -> int:
        """
        Convert PDF to individual page images
        
        Args:
            pdf_path: Path to PDF file
            force: If True, reconvert even if images exist
        
        Returns:
            Number of pages converted
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Check if already converted
        if not force and self._check_existing_pages(pdf_path):
            existing_count = len(list(Path(self.output_dir).glob(f"P*.{self.image_format}")))
            print(f"✓ Found {existing_count} existing page images. Use --force to reconvert.")
            return existing_count
        
        print(f"Converting PDF to images (DPI: {self.dpi})...")
        
        try:
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt=self.image_format,
                poppler_path=str(POPPLER_PATH) if POPPLER_PATH.exists() else None
            )
            
            # Save each page
            for i, image in enumerate(images, start=1):
                page_num = str(i).zfill(3)
                output_path = os.path.join(self.output_dir, f"P{page_num}.{self.image_format}")
                image.save(output_path, self.image_format.upper())
                
                if i % 10 == 0:
                    print(f"  Converted {i}/{len(images)} pages...")
            
            print(f"✓ Converted {len(images)} pages to {self.output_dir}/")
            return len(images)
            
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF: {e}")
    
    def _check_existing_pages(self, pdf_path: str) -> bool:
        """
        Check if page images already exist
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            True if images exist and are up-to-date
        """
        page_files = list(Path(self.output_dir).glob(f"P*.{self.image_format}"))
        if not page_files:
            return False
        
        # Check if PDF is newer than images
        pdf_mtime = os.path.getmtime(pdf_path)
        oldest_image_mtime = min(os.path.getmtime(f) for f in page_files)
        
        return oldest_image_mtime > pdf_mtime
    
    def get_page_path(self, page_num: int) -> str:
        """
        Get path to specific page image
        
        Args:
            page_num: Page number (1-indexed)
        
        Returns:
            Path to page image
        """
        page_str = str(page_num).zfill(3)
        return os.path.join(self.output_dir, f"P{page_str}.{self.image_format}")
    
    def get_page_paths(self, start: int, end: int) -> List[str]:
        """
        Get paths to range of page images
        
        Args:
            start: Start page (1-indexed, inclusive)
            end: End page (1-indexed, inclusive)
        
        Returns:
            List of paths to page images
        """
        paths = []
        for page_num in range(start, end + 1):
            path = self.get_page_path(page_num)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Page image not found: {path}")
            paths.append(path)
        return paths
    
    def validate_pages(self, total_pages: int) -> Tuple[bool, List[int]]:
        """
        Validate that all page images exist
        
        Args:
            total_pages: Expected total number of pages
        
        Returns:
            Tuple of (all_valid, missing_pages)
        """
        missing = []
        for page_num in range(1, total_pages + 1):
            if not os.path.exists(self.get_page_path(page_num)):
                missing.append(page_num)
        
        return (len(missing) == 0, missing)
    
    def cleanup(self) -> None:
        """Remove all page images"""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            print(f"✓ Cleaned up {self.output_dir}/")
