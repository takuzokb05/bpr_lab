try:
    with open("models.txt", "r", encoding="utf-16") as f:
        for line in f:
            if "gemini" in line.lower():
                print(line.strip())
except:
    try:
        with open("models.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "gemini" in line.lower():
                    print(line.strip())
    except Exception as e:
        print(f"Error: {e}")
