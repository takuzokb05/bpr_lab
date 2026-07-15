"""
Gemini API Configuration Module
親フォルダのAPI_KEY.txtからAPIキーを読み込み、Gemini APIを初期化します。
"""

import os
import google.generativeai as genai
from pathlib import Path


def get_api_key():
    """
    親フォルダのAPI_KEY.txtからAPIキーを読み込む
    
    Returns:
        str: APIキー
        
    Raises:
        FileNotFoundError: API_KEY.txtが見つからない場合
        ValueError: APIキーが空の場合
    """
    # 現在のファイルの親の親ディレクトリ(PDFをOCRフォルダ)を取得
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    api_key_path = parent_dir / "API_KEY.txt"
    
    if not api_key_path.exists():
        raise FileNotFoundError(
            f"API_KEY.txt が見つかりません: {api_key_path}\n"
            f"親フォルダ({parent_dir})にAPI_KEY.txtを配置してください。"
        )
    
    with open(api_key_path, 'r', encoding='utf-8') as f:
        api_key = f.read().strip()
    
    if not api_key:
        raise ValueError("API_KEY.txtが空です。有効なAPIキーを設定してください。")
    
    return api_key


def initialize_gemini():
    """
    Gemini APIを初期化する
    
    Returns:
        str: 使用されたAPIキー
        
    Raises:
        Exception: API初期化に失敗した場合
    """
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)
        print("✓ Gemini API の初期化に成功しました")
        return api_key
    except Exception as e:
        print(f"✗ Gemini API の初期化に失敗しました: {e}")
        raise


def list_available_models():
    """
    利用可能なGeminiモデルをリストアップする
    
    Returns:
        list: 利用可能なモデル名のリスト
    """
    try:
        models = []
        print("\n--- 利用可能なモデル ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
                print(f"  • {m.name}")
        print(f"\n合計 {len(models)} 個のモデルが利用可能です\n")
        return models
    except Exception as e:
        print(f"モデルリストの取得に失敗しました: {e}")
        return []


if __name__ == "__main__":
    # テスト実行
    print("=== Gemini API Configuration Test ===\n")
    
    try:
        # API初期化
        api_key = initialize_gemini()
        print(f"APIキー: {api_key[:10]}...{api_key[-4:]}\n")
        
        # モデルリスト取得
        models = list_available_models()
        
        # 画像生成モデルの確認
        image_models = [m for m in models if 'image' in m.lower()]
        if image_models:
            print("--- 画像生成モデル ---")
            for model in image_models:
                print(f"  • {model}")
        else:
            print("⚠ 画像生成モデルが見つかりませんでした")
            
    except Exception as e:
        print(f"\n✗ エラーが発生しました:\n{e}")
