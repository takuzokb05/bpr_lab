
import openai
import os

# Use environment variable or local file only
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    try:
        with open("API_KEY.txt", "r") as f:
            OPENAI_API_KEY = f.read().strip()
    except:
        pass

if not OPENAI_API_KEY:
    print("Warning: No API Key found.")
else:
    print(f"Using API Key: {OPENAI_API_KEY[:5]}...")

try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("Fetching ALL available GPT models from OpenAI API...")
    models = client.models.list()
    
    # Get all models containing 'gpt'
    all_gpt_models = [m.id for m in models.data if "gpt" in m.id]
    all_gpt_models.sort()
    
    print(f"\nFound {len(all_gpt_models)} GPT models. Listing ALL:")
    print("-" * 40)
    for m in all_gpt_models:
        print(m)
    print("-" * 40)
    
except Exception as e:
    print(f"Error: {e}")
