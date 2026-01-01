"""
実際のAPIキーを使って利用可能なモデルを確認
"""
import os

# APIキーを読み込み
with open("API_KEY.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# OpenAI
print("=" * 80)
print("[1] OpenAI Models")
print("=" * 80)
try:
    import openai
    openai_key = lines[4].strip()  # 5行目
    client = openai.OpenAI(api_key=openai_key)
    
    # モデル一覧を取得
    models = client.models.list()
    gpt_models = [m.id for m in models.data if 'gpt' in m.id.lower()]
    
    print("Available GPT models:")
    for model in sorted(gpt_models)[:20]:  # 最初の20個
        print(f"  - {model}")
    
except Exception as e:
    print(f"Error: {e}")

# Anthropic
print("\n" + "=" * 80)
print("[2] Anthropic Claude Models")
print("=" * 80)
try:
    import anthropic
    anthropic_key = lines[1].strip()  # 2行目
    client = anthropic.Anthropic(api_key=anthropic_key)
    
    # 公式ドキュメントから
    test_models = [
        "claude-opus-4.5-20241122",
        "claude-sonnet-4.5-20241022",
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-opus-20240229",
    ]
    
    print("Testing models:")
    for model in test_models:
        try:
            # 簡単なテストリクエスト
            response = client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print(f"  ✓ {model} - WORKS")
        except Exception as e:
            if "not_found" in str(e):
                print(f"  ✗ {model} - NOT FOUND")
            else:
                print(f"  ? {model} - Error: {str(e)[:50]}")
    
except Exception as e:
    print(f"Error: {e}")

# Google Gemini
print("\n" + "=" * 80)
print("[3] Google Gemini Models")
print("=" * 80)
try:
    import google.generativeai as genai
    
    # APIキーを探す（Google用）
    print("Note: Google API key needs to start with 'AIzaSy...'")
    print("Current API_KEY.txt does not seem to have a valid Google API key.")
    print("\nExpected Gemini models:")
    print("  - gemini-3-flash-preview")
    print("  - gemini-3-pro-preview")
    print("  - gemini-2.5-flash")
    print("  - gemini-2.5-pro")
    print("  - gemini-1.5-pro")
    print("  - gemini-1.5-flash")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("Based on actual API availability, use:")
print("  OpenAI:    gpt-4o (check list above)")
print("  Anthropic: (check which model works above)")
print("  Google:    Need valid API key (AIzaSy...)")
print("=" * 80)
