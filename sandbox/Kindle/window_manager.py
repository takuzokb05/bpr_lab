"""
Window Manager for Kindle Auto-Capture Tool
Handles Kindle window detection, activation, and coordinate translation
"""

import pygetwindow as gw
from typing import Optional, Tuple


class WindowManager:
    """Manages Kindle for PC window operations and coordinate transformations"""
    
    def __init__(self):
        self.kindleWindow = None
        self.windowTitle = None
        
    def findKindleWindow(self) -> bool:
        """
        Find and store reference to Kindle for PC window
        
        Returns:
            bool: True if Kindle window found, False otherwise
        """
        try:
            # Search for windows with "Kindle" in title
            windows = gw.getWindowsWithTitle("Kindle")
            
            if not windows:
                print("❌ Kindleウィンドウが見つかりません。Kindle for PCを起動してください。")
                return False
            
            # Use the first Kindle window found
            self.kindleWindow = windows[0]
            self.windowTitle = self.kindleWindow.title
            print(f"✅ Kindleウィンドウを検出: {self.windowTitle}")
            return True
            
        except Exception as e:
            print(f"❌ ウィンドウ検出エラー: {e}")
            return False
    
    def activateWindow(self) -> bool:
        """
        Bring Kindle window to foreground
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.kindleWindow:
                if not self.findKindleWindow():
                    return False
            
            # Restore if minimized
            if self.kindleWindow.isMinimized:
                self.kindleWindow.restore()
            
            # Bring to front
            self.kindleWindow.activate()
            print("✅ Kindleウィンドウをアクティブ化しました")
            return True
            
        except Exception as e:
            print(f"❌ ウィンドウアクティブ化エラー: {e}")
            return False
    
    def getWindowPosition(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Get current window position and size
        
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) or None if error
        """
        try:
            if not self.kindleWindow:
                if not self.findKindleWindow():
                    return None
            
            return (
                self.kindleWindow.left,
                self.kindleWindow.top,
                self.kindleWindow.width,
                self.kindleWindow.height
            )
            
        except Exception as e:
            print(f"❌ ウィンドウ位置取得エラー: {e}")
            return None
    
    def absoluteToRelative(self, absX: int, absY: int) -> Tuple[int, int]:
        """
        Convert absolute screen coordinates to window-relative coordinates
        
        Args:
            absX: Absolute X coordinate on screen
            absY: Absolute Y coordinate on screen
            
        Returns:
            Tuple[int, int]: (relativeX, relativeY)
        """
        if not self.kindleWindow:
            raise ValueError("Kindleウィンドウが設定されていません")
        
        relX = absX - self.kindleWindow.left
        relY = absY - self.kindleWindow.top
        
        return (relX, relY)
    
    def relativeToAbsolute(self, relX: int, relY: int) -> Tuple[int, int]:
        """
        Convert window-relative coordinates to absolute screen coordinates
        
        Args:
            relX: Relative X coordinate within window
            relY: Relative Y coordinate within window
            
        Returns:
            Tuple[int, int]: (absoluteX, absoluteY)
        """
        if not self.kindleWindow:
            raise ValueError("Kindleウィンドウが設定されていません")
        
        absX = self.kindleWindow.left + relX
        absY = self.kindleWindow.top + relY
        
        return (absX, absY)
    
    def isWindowValid(self) -> bool:
        """
        Check if the stored window reference is still valid
        
        Returns:
            bool: True if window exists and is valid
        """
        try:
            if not self.kindleWindow:
                return False
            
            # Try to access window properties to verify it's still valid
            _ = self.kindleWindow.title
            return True
            
        except Exception:
            return False
