"""
Check available Gemini models
"""
import google.generativeai as genai

# Load API key
with open("API_KEY.txt", 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]
    api_key = lines[1]

genai.configure(api_key=api_key)

print("Available Gemini Models:")
print("="*60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\nModel: {model.name}")
        print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'input_token_limit'):
            print(f"  Input Tokens: {model.input_token_limit:,}")
        if hasattr(model, 'output_token_limit'):
            print(f"  Output Tokens: {model.output_token_limit:,}")
