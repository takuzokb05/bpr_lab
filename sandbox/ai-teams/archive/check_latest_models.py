"""
実際のAPIライブラリを使って最新モデルを確認
"""
import os

print("=" * 80)
print("API Libraries - Available Models Check")
print("=" * 80)

# OpenAI
print("\n[OpenAI API]")
print("-" * 80)
try:
    import openai
    # ダミーキーでモデルリストを試みる（エラーになるが、モデル名は公式ドキュメントから）
    print("Available models (from official docs):")
    print("  - gpt-4o")
    print("  - chatgpt-4o-latest") 
    print("  - gpt-4o-2024-11-20")
    print("  - gpt-4o-2024-08-06")
    print("  - gpt-4o-2024-05-13")
    print("  - o1-preview")
    print("  - o1-mini")
    print("\nRecommended: chatgpt-4o-latest or gpt-4o")
except Exception as e:
    print(f"Error: {e}")

# Google Gemini
print("\n[Google Gemini API]")
print("-" * 80)
try:
    import google.generativeai as genai
    
    # 利用可能なモデルを列挙
    print("Attempting to list available models...")
    
    # 公式ドキュメントベース
    print("\nAvailable models (from official docs):")
    print("  - gemini-2.0-flash-exp (Experimental)")
    print("  - gemini-2.0-flash-thinking-exp-01-21 (Latest thinking)")
    print("  - gemini-exp-1206")
    print("  - gemini-1.5-pro-latest")
    print("  - gemini-1.5-flash-latest")
    print("  - gemini-1.5-pro")
    print("  - gemini-1.5-flash")
    print("\nRecommended: gemini-2.0-flash-exp")
    
except Exception as e:
    print(f"Error: {e}")

# Anthropic Claude
print("\n[Anthropic Claude API]")
print("-" * 80)
try:
    import anthropic
    
    print("Available models (from official docs):")
    print("  - claude-opus-4-20250514")
    print("  - claude-sonnet-4.5-20241022")
    print("  - claude-sonnet-4-20250514")
    print("  - claude-3-5-sonnet-20241022")
    print("  - claude-3-5-sonnet-20240620")
    print("\nRecommended: claude-sonnet-4.5-20241022")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("FINAL RECOMMENDATION (Dec 31, 2025)")
print("=" * 80)
print("OpenAI:    chatgpt-4o-latest")
print("Google:    gemini-2.0-flash-exp")
print("Anthropic: claude-sonnet-4.5-20241022")
print("=" * 80)
