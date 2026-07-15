"""
Main Controller for Kindle Auto-Capture Tool
Entry point and workflow orchestration
"""

import json
import os
import time
import threading
from tkinter import messagebox
import tkinter as tk
from pynput import keyboard

from window_manager import WindowManager
from capture import AreaSelector, ClickPositionCapture, CaptureEngine
from pdf_engine import PdfEngine


class EmergencyStopListener:
    """Monitor Esc key hold for emergency stop"""
    
    def __init__(self, stopEvent: threading.Event, holdDuration: float = 2.0):
        self.stopEvent = stopEvent
        self.holdDuration = holdDuration
        self.escPressed = False
        self.pressStartTime = None
        self.listener = None
        
    def start(self):
        """Start listening for Esc key"""
        self.listener = keyboard.Listener(
            on_press=self._onPress,
            on_release=self._onRelease
        )
        self.listener.start()
        print("🛑 緊急停止: Escキーを2秒間長押しで停止します")
    
    def stop(self):
        """Stop listening"""
        if self.listener:
            self.listener.stop()
    
    def _onPress(self, key):
        """Handle key press"""
        try:
            if key == keyboard.Key.esc:
                if not self.escPressed:
                    self.escPressed = True
                    self.pressStartTime = time.time()
                    
                    # Start monitoring thread
                    threading.Thread(target=self._monitorHold, daemon=True).start()
        except AttributeError:
            pass
    
    def _onRelease(self, key):
        """Handle key release"""
        try:
            if key == keyboard.Key.esc:
                self.escPressed = False
                self.pressStartTime = None
        except AttributeError:
            pass
    
    def _monitorHold(self):
        """Monitor if Esc is held long enough"""
        while self.escPressed:
            if self.pressStartTime:
                elapsed = time.time() - self.pressStartTime
                if elapsed >= self.holdDuration:
                    print("\n🛑 緊急停止が発動されました!")
                    self.stopEvent.set()
                    break
            time.sleep(0.1)


class ConfigManager:
    """Manage configuration save/load"""
    
    CONFIG_FILE = "config.json"
    
    @staticmethod
    def exists() -> bool:
        """Check if config file exists"""
        return os.path.exists(ConfigManager.CONFIG_FILE)
    
    @staticmethod
    def save(captureArea: tuple, clickPosition: tuple, windowInfo: dict):
        """
        Save configuration to file
        
        Args:
            captureArea: (relX, relY, width, height)
            clickPosition: (relX, relY)
            windowInfo: Window information dict
        """
        config = {
            "captureArea": {
                "relativeX": captureArea[0],
                "relativeY": captureArea[1],
                "width": captureArea[2],
                "height": captureArea[3]
            },
            "clickPosition": {
                "relativeX": clickPosition[0],
                "relativeY": clickPosition[1]
            },
            "windowReference": windowInfo
        }
        
        with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"💾 設定を保存しました: {ConfigManager.CONFIG_FILE}")
    
    @staticmethod
    def load() -> dict:
        """
        Load configuration from file
        
        Returns:
            dict: Configuration data
        """
        with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📂 設定を読み込みました: {ConfigManager.CONFIG_FILE}")
        return config


def runSetupWorkflow(windowManager: WindowManager) -> tuple:
    """
    Run initial setup workflow
    
    Args:
        windowManager: WindowManager instance
        
    Returns:
        tuple: (captureArea, clickPosition) in relative coordinates
    """
    print("\n" + "="*60)
    print("📋 初期セットアップを開始します")
    print("="*60)
    
    # Step 1: Area Selection
    print("\n【ステップ 1/2】 撮影範囲の指定")
    areaSelector = AreaSelector()
    
    while True:
        area = areaSelector.show()
        if area is None:
            print("❌ 範囲選択がキャンセルされました")
            return None, None
        
        if areaSelector.confirmSelection(area):
            break
        else:
            print("🔄 範囲を再選択してください")
    
    # Convert to relative coordinates
    relArea = (
        windowManager.absoluteToRelative(area[0], area[1])[0],
        windowManager.absoluteToRelative(area[0], area[1])[1],
        area[2],
        area[3]
    )
    
    print(f"✅ 撮影範囲を設定しました: {area[2]}x{area[3]} px")
    
    # Step 2: Click Position Capture
    print("\n【ステップ 2/2】 クリック位置の指定")
    clickCapture = ClickPositionCapture()
    
    while True:
        clickPos = clickCapture.show()
        if clickPos is None:
            print("❌ クリック位置の指定がキャンセルされました")
            return None, None
        
        if clickCapture.confirmClick(clickPos):
            break
        else:
            print("🔄 クリック位置を再指定してください")
    
    # Convert to relative coordinates
    relClickPos = windowManager.absoluteToRelative(clickPos[0], clickPos[1])
    
    print(f"✅ クリック位置を設定しました: ({clickPos[0]}, {clickPos[1]})")
    
    return relArea, relClickPos


def runTestAndConfirm(captureEngine: CaptureEngine, area: tuple, clickPos: tuple) -> bool:
    """
    Run test capture and get user confirmation
    
    Args:
        captureEngine: CaptureEngine instance
        area: Capture area (absolute coordinates)
        clickPos: Click position (absolute coordinates)
        
    Returns:
        bool: True if user confirms to continue
    """
    print("\n" + "="*60)
    print("🧪 テスト実行")
    print("="*60)
    
    # Run test
    if not captureEngine.testRun(area, clickPos):
        return False
    
    # Ask for confirmation
    root = tk.Tk()
    root.withdraw()
    
    result = messagebox.askyesno(
        "続行確認",
        "テスト実行が完了しました。\n\nこのまま全ページの撮影を開始しますか？",
        icon='question'
    )
    
    root.destroy()
    
    return result


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("📚 Kindle Auto-Capture to PDF Tool")
    print("="*60)
    
    # Initialize window manager
    windowManager = WindowManager()
    
    # Find Kindle window
    if not windowManager.findKindleWindow():
        print("\n❌ Kindle for PCが見つかりません。起動してから再実行してください。")
        input("\nEnterキーを押して終了...")
        return
    
    # Activate Kindle window
    if not windowManager.activateWindow():
        print("\n❌ Kindleウィンドウをアクティブ化できませんでした。")
        input("\nEnterキーを押して終了...")
        return
    
    time.sleep(1)  # Wait for window activation
    
    # Check if config exists
    if ConfigManager.exists():
        print("\n💾 前回の設定が見つかりました")
        
        root = tk.Tk()
        root.withdraw()
        useExisting = messagebox.askyesno(
            "設定の再利用",
            "前回の設定を使用しますか？\n\n「いいえ」を選択すると、新しく設定を行います。",
            icon='question'
        )
        root.destroy()
        
        if useExisting:
            # Load existing config
            config = ConfigManager.load()
            
            # Convert relative to absolute coordinates
            relArea = (
                config["captureArea"]["relativeX"],
                config["captureArea"]["relativeY"],
                config["captureArea"]["width"],
                config["captureArea"]["height"]
            )
            
            relClickPos = (
                config["clickPosition"]["relativeX"],
                config["clickPosition"]["relativeY"]
            )
            
            # Convert to absolute
            absAreaTopLeft = windowManager.relativeToAbsolute(relArea[0], relArea[1])
            area = (absAreaTopLeft[0], absAreaTopLeft[1], relArea[2], relArea[3])
            clickPos = windowManager.relativeToAbsolute(relClickPos[0], relClickPos[1])
            
        else:
            # Run setup
            relArea, relClickPos = runSetupWorkflow(windowManager)
            if relArea is None or relClickPos is None:
                print("\n❌ セットアップがキャンセルされました")
                input("\nEnterキーを押して終了...")
                return
            
            # Convert to absolute
            absAreaTopLeft = windowManager.relativeToAbsolute(relArea[0], relArea[1])
            area = (absAreaTopLeft[0], absAreaTopLeft[1], relArea[2], relArea[3])
            clickPos = windowManager.relativeToAbsolute(relClickPos[0], relClickPos[1])
            
            # Save config
            windowPos = windowManager.getWindowPosition()
            windowInfo = {
                "title": windowManager.windowTitle,
                "lastX": windowPos[0],
                "lastY": windowPos[1]
            }
            ConfigManager.save(relArea, relClickPos, windowInfo)
    else:
        # First run - setup required
        relArea, relClickPos = runSetupWorkflow(windowManager)
        if relArea is None or relClickPos is None:
            print("\n❌ セットアップがキャンセルされました")
            input("\nEnterキーを押して終了...")
            return
        
        # Convert to absolute
        absAreaTopLeft = windowManager.relativeToAbsolute(relArea[0], relArea[1])
        area = (absAreaTopLeft[0], absAreaTopLeft[1], relArea[2], relArea[3])
        clickPos = windowManager.relativeToAbsolute(relClickPos[0], relClickPos[1])
        
        # Save config
        windowPos = windowManager.getWindowPosition()
        windowInfo = {
            "title": windowManager.windowTitle,
            "lastX": windowPos[0],
            "lastY": windowPos[1]
        }
        ConfigManager.save(relArea, relClickPos, windowInfo)
    
    # Initialize capture engine
    captureEngine = CaptureEngine()
    
    # Run test and get confirmation
    if not runTestAndConfirm(captureEngine, area, clickPos):
        print("\n❌ ユーザーによってキャンセルされました")
        captureEngine.cleanup()
        input("\nEnterキーを押して終了...")
        return
    
    # Reset capture engine for actual run
    captureEngine = CaptureEngine()
    
    # Setup emergency stop
    stopEvent = threading.Event()
    emergencyStop = EmergencyStopListener(stopEvent)
    emergencyStop.start()
    
    try:
        # Run auto-capture
        print("\n" + "="*60)
        print("📸 自動撮影開始")
        print("="*60)
        
        capturedImages = captureEngine.autoCapture(area, clickPos, stopEvent)
        
        if not capturedImages:
            print("\n⚠️ 撮影された画像がありません")
            return
        
        # Generate PDF
        print("\n" + "="*60)
        print("📄 PDF生成")
        print("="*60)
        
        pdfPath = PdfEngine.convertToPdf(capturedImages)
        
        print("\n" + "="*60)
        print("✅ 完了!")
        print("="*60)
        print(f"\n📁 PDFファイル: {pdfPath}")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        
    finally:
        # Cleanup
        emergencyStop.stop()
        captureEngine.cleanup()
        
        input("\nEnterキーを押して終了...")


if __name__ == "__main__":
    main()
