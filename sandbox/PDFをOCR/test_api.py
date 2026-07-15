"""
Test script to verify API connection and model availability
"""

from ocr_engine import load_api_key, OCREngine

try:
    print("Loading API key...")
    api_key = load_api_key()
    print("✓ API key loaded successfully")
    
    print("\nInitializing OCR engine...")
    engine = OCREngine(api_key, model_name="gemini-2.0-flash")
    
    print("\nTesting API connection...")
    if engine.test_connection():
        print("✓ API connection successful!")
        print("\n" + "="*60)
        print("System is ready to use!")
        print("="*60)
    else:
        print("❌ API connection failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
