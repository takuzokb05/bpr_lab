"""
Capture Module for Kindle Auto-Capture Tool
Handles area selection, click position capture, screenshot capture, and auto-capture loop
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
from PIL import Image, ImageChops, ImageTk
import time
import os
import tempfile
from typing import Tuple, Optional, List
import threading


class AreaSelector:
    """Transparent overlay for area selection with drag-to-select"""
    
    def __init__(self):
        self.selectedArea = None
        self.startX = None
        self.startY = None
        self.rect = None
        
    def show(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Display overlay and allow user to select area
        
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) or None if cancelled
        """
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root,
            bg='black',
            highlightthickness=0,
            cursor='cross'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add instruction label
        label = tk.Label(
            self.root,
            text="📖 Kindleの本文エリアをドラッグで選択してください",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='black'
        )
        label.place(relx=0.5, rely=0.05, anchor='center')
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self._onMouseDown)
        self.canvas.bind('<B1-Motion>', self._onMouseDrag)
        self.canvas.bind('<ButtonRelease-1>', self._onMouseUp)
        
        self.root.mainloop()
        
        return self.selectedArea
    
    def _onMouseDown(self, event):
        """Handle mouse button press"""
        self.startX = event.x
        self.startY = event.y
        
        # Create rectangle
        self.rect = self.canvas.create_rectangle(
            self.startX, self.startY, self.startX, self.startY,
            outline='red', width=3
        )
    
    def _onMouseDrag(self, event):
        """Handle mouse drag"""
        if self.rect:
            self.canvas.coords(self.rect, self.startX, self.startY, event.x, event.y)
    
    def _onMouseUp(self, event):
        """Handle mouse button release"""
        endX = event.x
        endY = event.y
        
        # Calculate area
        x = min(self.startX, endX)
        y = min(self.startY, endY)
        width = abs(endX - self.startX)
        height = abs(endY - self.startY)
        
        # Validate area size
        if width < 50 or height < 50:
            messagebox.showerror("エラー", "選択範囲が小さすぎます。もう一度選択してください。")
            self.canvas.delete(self.rect)
            self.rect = None
            return
        
        # Store area
        self.selectedArea = (x, y, width, height)
        
        # Close overlay
        self.root.quit()
        self.root.destroy()
    
    def confirmSelection(self, area: Tuple[int, int, int, int]) -> bool:
        """
        Show confirmation dialog for selected area
        
        Args:
            area: (x, y, width, height)
            
        Returns:
            bool: True if user confirms, False otherwise
        """
        root = tk.Tk()
        root.withdraw()
        
        result = messagebox.askyesno(
            "範囲確認",
            f"この範囲で正しいですか？\n\n"
            f"位置: ({area[0]}, {area[1]})\n"
            f"サイズ: {area[2]} x {area[3]} px",
            icon='question'
        )
        
        root.destroy()
        return result


class ClickPositionCapture:
    """Capture click position for page turn button"""
    
    def __init__(self):
        self.clickPosition = None
        self.capturing = False
        
    def show(self) -> Optional[Tuple[int, int]]:
        """
        Display instruction and capture single click
        
        Returns:
            Tuple[int, int]: (x, y) click position or None if cancelled
        """
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        
        # Create instruction label
        label = tk.Label(
            self.root,
            text="👆 「次へ」ボタン（またはページ右端）を1回クリックしてください",
            font=('Arial', 16, 'bold'),
            fg='yellow',
            bg='black'
        )
        label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Bind click event
        self.root.bind('<Button-1>', self._onClick)
        
        self.root.mainloop()
        
        return self.clickPosition
    
    def _onClick(self, event):
        """Handle click event"""
        # Get absolute screen coordinates
        self.clickPosition = (event.x_root, event.y_root)
        
        # Close overlay
        self.root.quit()
        self.root.destroy()
    
    def confirmClick(self, position: Tuple[int, int]) -> bool:
        """
        Show confirmation dialog for click position
        
        Args:
            position: (x, y) click coordinates
            
        Returns:
            bool: True if user confirms, False otherwise
        """
        root = tk.Tk()
        root.withdraw()
        
        result = messagebox.askyesno(
            "クリック位置確認",
            f"このクリック位置で正しいですか？\n\n"
            f"座標: ({position[0]}, {position[1]})",
            icon='question'
        )
        
        root.destroy()
        return result


class CaptureEngine:
    """Core capture logic for screenshots and auto-capture loop"""
    
    def __init__(self, tempDir: str = None):
        self.tempDir = tempDir or tempfile.mkdtemp(prefix="kindle_capture_")
        self.capturedImages = []
        self.pageCount = 0
        
    def takeScreenshot(self, area: Tuple[int, int, int, int]) -> str:
        """
        Capture screenshot of specified area
        
        Args:
            area: (x, y, width, height)
            
        Returns:
            str: Path to saved screenshot
        """
        x, y, width, height = area
        
        # Capture screenshot
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        
        # Save to temp directory
        self.pageCount += 1
        filename = f"page_{self.pageCount:04d}.png"
        filepath = os.path.join(self.tempDir, filename)
        screenshot.save(filepath)
        
        self.capturedImages.append(filepath)
        
        return filepath
    
    def compareImages(self, img1Path: str, img2Path: str, threshold: float = 0.99) -> bool:
        """
        Compare two images for similarity
        
        Args:
            img1Path: Path to first image
            img2Path: Path to second image
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            bool: True if images are similar (>= threshold), False otherwise
        """
        try:
            img1 = Image.open(img1Path)
            img2 = Image.open(img2Path)
            
            # Calculate difference
            diff = ImageChops.difference(img1, img2)
            
            # Get histogram
            histogram = diff.histogram()
            
            # Calculate total pixels
            totalPixels = sum(histogram)
            
            # Count identical pixels (first bin in histogram for each channel)
            identicalPixels = histogram[0] + histogram[256] + histogram[512]
            
            # Calculate similarity
            similarity = identicalPixels / totalPixels if totalPixels > 0 else 0
            
            return similarity >= threshold
            
        except Exception as e:
            print(f"⚠️ 画像比較エラー: {e}")
            return False
    
    def performPageTurn(self, clickPos: Tuple[int, int]):
        """
        Click at specified position to turn page
        
        Args:
            clickPos: (x, y) click coordinates
        """
        pyautogui.click(clickPos[0], clickPos[1])
        time.sleep(0.5)  # Wait for page turn animation
    
    def testRun(self, area: Tuple[int, int, int, int], clickPos: Tuple[int, int]) -> bool:
        """
        Perform test run: capture one page, turn page, show screenshot
        
        Args:
            area: Capture area (x, y, width, height)
            clickPos: Click position (x, y)
            
        Returns:
            bool: True if test successful, False otherwise
        """
        try:
            print("\n🧪 テスト実行中...")
            
            # Capture first page
            print("   📸 ページ1を撮影...")
            img1Path = self.takeScreenshot(area)
            
            # Turn page
            print("   👆 ページをめくります...")
            self.performPageTurn(clickPos)
            
            # Capture second page
            print("   📸 ページ2を撮影...")
            img2Path = self.takeScreenshot(area)
            
            # Show screenshot to user
            self._showTestResult(img1Path)
            
            print("✅ テスト実行完了")
            return True
            
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            return False
    
    def _showTestResult(self, imagePath: str):
        """Show test screenshot to user"""
        root = tk.Tk()
        root.title("テスト撮影結果")
        
        # Load and display image
        img = Image.open(imagePath)
        
        # Resize if too large
        maxWidth = 800
        maxHeight = 1000
        if img.width > maxWidth or img.height > maxHeight:
            ratio = min(maxWidth / img.width, maxHeight / img.height)
            newSize = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(newSize, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        label = tk.Label(root, image=photo)
        label.image = photo  # Keep reference
        label.pack()
        
        # Add instruction
        infoLabel = tk.Label(
            root,
            text="このスクリーンショットを確認してください。\nウィンドウを閉じて続行します。",
            font=('Arial', 12),
            pady=10
        )
        infoLabel.pack()
        
        root.mainloop()
    
    def autoCapture(
        self,
        area: Tuple[int, int, int, int],
        clickPos: Tuple[int, int],
        stopEvent: threading.Event,
        statusCallback=None
    ) -> List[str]:
        """
        Main auto-capture loop
        
        Args:
            area: Capture area (x, y, width, height)
            clickPos: Click position (x, y)
            stopEvent: Threading event to signal stop
            statusCallback: Optional callback for status updates
            
        Returns:
            List[str]: List of captured image paths
        """
        print("\n🚀 自動撮影開始!")
        print("   ⏸️  停止するにはEscキーを2秒間長押ししてください\n")
        
        previousImage = None
        
        try:
            while not stopEvent.is_set():
                # Capture current page
                currentImage = self.takeScreenshot(area)
                
                # Update status
                if statusCallback:
                    statusCallback(self.pageCount)
                else:
                    print(f"📸 ページ {self.pageCount} を撮影中...")
                
                # Check if this is the last page
                if previousImage and self.compareImages(previousImage, currentImage):
                    print(f"\n✅ 最終ページを検出しました (ページ {self.pageCount})")
                    # Remove duplicate last page
                    os.remove(currentImage)
                    self.capturedImages.pop()
                    self.pageCount -= 1
                    break
                
                # Turn page
                self.performPageTurn(clickPos)
                
                # Store current as previous for next iteration
                previousImage = currentImage
                
                # Check stop event
                if stopEvent.is_set():
                    print("\n⏸️  ユーザーによって停止されました")
                    break
            
            print(f"\n📊 撮影完了: 合計 {self.pageCount} ページ")
            return self.capturedImages
            
        except Exception as e:
            print(f"\n❌ 撮影エラー: {e}")
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            for imgPath in self.capturedImages:
                if os.path.exists(imgPath):
                    os.remove(imgPath)
            
            if os.path.exists(self.tempDir):
                os.rmdir(self.tempDir)
                
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")
