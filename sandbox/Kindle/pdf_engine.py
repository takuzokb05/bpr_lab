"""
PDF Engine for Kindle Auto-Capture Tool
Converts captured images to optimized PDF
"""

import img2pdf
import os
from datetime import datetime
from typing import List


class PdfEngine:
    """Handles PDF generation from captured images"""
    
    @staticmethod
    def getOutputPath() -> str:
        """
        Generate output path for PDF in Downloads folder
        
        Returns:
            str: Full path to output PDF file
        """
        # Get user's Downloads folder
        downloadsPath = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        filename = f"Kindle_Export_{timestamp}.pdf"
        
        return os.path.join(downloadsPath, filename)
    
    @staticmethod
    def convertToPdf(imagePaths: List[str], outputPath: str = None) -> str:
        """
        Convert list of images to PDF
        
        Args:
            imagePaths: List of paths to image files (in order)
            outputPath: Optional custom output path. If None, uses Downloads folder
            
        Returns:
            str: Path to created PDF file
            
        Raises:
            ValueError: If no images provided
            Exception: If PDF creation fails
        """
        if not imagePaths:
            raise ValueError("画像が指定されていません")
        
        # Use default path if not specified
        if outputPath is None:
            outputPath = PdfEngine.getOutputPath()
        
        try:
            print(f"📄 PDF生成中... ({len(imagePaths)}ページ)")
            
            # Convert images to PDF
            with open(outputPath, "wb") as f:
                f.write(img2pdf.convert(imagePaths))
            
            # Get file size
            fileSize = os.path.getsize(outputPath)
            fileSizeMb = fileSize / (1024 * 1024)
            
            print(f"✅ PDF生成完了!")
            print(f"   📁 保存先: {outputPath}")
            print(f"   📊 ファイルサイズ: {fileSizeMb:.2f} MB")
            print(f"   📖 ページ数: {len(imagePaths)}")
            
            return outputPath
            
        except Exception as e:
            print(f"❌ PDF生成エラー: {e}")
            raise
    
    @staticmethod
    def validateImages(imagePaths: List[str]) -> bool:
        """
        Validate that all image files exist and are readable
        
        Args:
            imagePaths: List of paths to validate
            
        Returns:
            bool: True if all images are valid
        """
        for imgPath in imagePaths:
            if not os.path.exists(imgPath):
                print(f"❌ 画像が見つかりません: {imgPath}")
                return False
            
            if not os.path.isfile(imgPath):
                print(f"❌ ファイルではありません: {imgPath}")
                return False
        
        return True
