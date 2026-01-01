import os

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def strip_imports(content, modules_to_remove):
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        # 指定モジュールのimportを除去 (from X import Y, import X)
        if any(line.strip().startswith(f"from {m}") or line.strip().startswith(f"import {m}") for m in modules_to_remove):
            continue
        new_lines.append(line)
    return "\n".join(new_lines)

def main():
    print("Building standalone app...")
    
    # 1. 依存モジュールの読み込み
    db_code = read_file("database.py")
    llm_code = read_file("llm_client.py")
    app_code = read_file("app.py")
    
    # 2. コードの整形 (重複importの削除など簡易的な処理)
    # database.py, llm_client.py の import は標準ライブラリばかりなので残すが、
    # 相互依存はないのでそのまま結合でOK。
    # ただし app.py からはローカルモジュールのimportを消す。
    
    app_code_clean = strip_imports(app_code, ["database", "llm_client"])
    
    # 3. 結合
    # ヘッダー
    final_code = "# AI Teams Standalone Version\n"
    final_code += "# Generated automatically\n\n"
    
    # 必要な標準ライブラリのimportをなるべく先頭に集めたいが、
    # 簡易的に各ファイルのimportをそのまま残し、app.pyだけ調整する。
    
    final_code += "# ==========================\n"
    final_code += "# MODULE: database.py\n"
    final_code += "# ==========================\n"
    final_code += db_code + "\n\n"
    
    final_code += "# ==========================\n"
    final_code += "# MODULE: llm_client.py\n"
    final_code += "# ==========================\n"
    final_code += llm_code + "\n\n"
    
    final_code += "# ==========================\n"
    final_code += "# MODULE: app.py\n"
    final_code += "# ==========================\n"
    final_code += app_code_clean
    
    # 4. 書き出し
    os.makedirs("dist", exist_ok=True)
    with open("dist/ai_teams_standalone.py", "w", encoding="utf-8") as f:
        f.write(final_code)
        
    print("Done! Created dist/ai_teams_standalone.py")

if __name__ == "__main__":
    main()
