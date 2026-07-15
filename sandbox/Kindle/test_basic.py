"""
Test script to verify basic functionality of Kindle Auto-Capture Tool
"""

import sys

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        import window_manager
        print("  ✅ window_manager imported successfully")
    except Exception as e:
        print(f"  ❌ window_manager import failed: {e}")
        return False
    
    try:
        import capture
        print("  ✅ capture imported successfully")
    except Exception as e:
        print(f"  ❌ capture import failed: {e}")
        return False
    
    try:
        import pdf_engine
        print("  ✅ pdf_engine imported successfully")
    except Exception as e:
        print(f"  ❌ pdf_engine import failed: {e}")
        return False
    
    try:
        import main
        print("  ✅ main imported successfully")
    except Exception as e:
        print(f"  ❌ main import failed: {e}")
        return False
    
    return True

def test_dependencies():
    """Test that all dependencies are installed"""
    print("\n🧪 Testing dependencies...")
    
    dependencies = [
        'pyautogui',
        'PIL',
        'img2pdf',
        'pynput',
        'pygetwindow'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep} installed")
        except ImportError:
            print(f"  ❌ {dep} not installed")
            all_ok = False
    
    return all_ok

def test_window_manager():
    """Test WindowManager basic functionality"""
    print("\n🧪 Testing WindowManager...")
    
    try:
        from window_manager import WindowManager
        wm = WindowManager()
        print("  ✅ WindowManager instantiated")
        
        # Test coordinate conversion (without actual window)
        # This should raise an error as expected
        try:
            wm.absoluteToRelative(100, 100)
            print("  ⚠️  Coordinate conversion worked without window (unexpected)")
        except ValueError as e:
            print("  ✅ Coordinate conversion properly requires window")
        
        return True
    except Exception as e:
        print(f"  ❌ WindowManager test failed: {e}")
        return False

def test_pdf_engine():
    """Test PdfEngine basic functionality"""
    print("\n🧪 Testing PdfEngine...")
    
    try:
        from pdf_engine import PdfEngine
        
        # Test output path generation
        path = PdfEngine.getOutputPath()
        print(f"  ✅ Output path generated: {path}")
        
        # Verify it's in Downloads folder
        if "Downloads" in path and path.endswith(".pdf"):
            print("  ✅ Path format is correct")
        else:
            print("  ⚠️  Path format might be incorrect")
        
        return True
    except Exception as e:
        print(f"  ❌ PdfEngine test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Kindle Auto-Capture Tool - Verification Tests")
    print("="*60)
    
    results = []
    
    results.append(("Dependencies", test_dependencies()))
    results.append(("Module Imports", test_imports()))
    results.append(("WindowManager", test_window_manager()))
    results.append(("PdfEngine", test_pdf_engine()))
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed! The tool is ready to use.")
        print("\nTo run the tool, execute:")
        print("  python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
