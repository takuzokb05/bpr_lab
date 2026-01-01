import google.generativeai as genai
import os

def list_models():
    # Load API key from file
    try:
        with open("API_KEY.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) > 1:
                api_key = lines[1].strip()
                genai.configure(api_key=api_key)
            else:
                print("API Key not found in line 2.")
                return
    except Exception as e:
        print(f"Error reading API_KEY.txt: {e}")
        return

    print("Listing available Gemini models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
