"""
基本的な画像生成の例
Gemini 3 Pro Image を使用してテキストから画像を生成します。
"""

import sys
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import initialize_gemini
from image_generator import ImageGenerator


def main():
    print("="*70)
    print("  Gemini 3 Pro Image - 基本的な画像生成")
    print("="*70)
    print()
    
    # API初期化
    print("Step 1: API初期化中...")
    initialize_gemini()
    print()
    
    # ImageGenerator インスタンス作成
    print("Step 2: ImageGenerator を初期化中...")
    generator = ImageGenerator()
    print()
    
    # 画像生成プロンプト
    prompts = [
        "A futuristic cityscape at night with neon lights and flying cars",
        "A peaceful mountain landscape with a crystal clear lake reflecting snow-capped peaks",
        "A cute robot playing with a cat in a cozy living room"
    ]
    
    print("Step 3: 画像を生成中...")
    print()
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- 画像 {i}/{len(prompts)} ---")
        try:
            images = generator.generate_image(
                prompt=prompt,
                aspect_ratio="1:1",
                resolution="2K",
                num_images=1,
                filename_prefix=f"basic_example_{i}"
            )
            
            if images:
                print(f"✓ 成功: {prompt[:50]}...")
            else:
                print(f"⚠ 失敗: 画像が生成されませんでした")
                
        except Exception as e:
            print(f"✗ エラー: {e}")
    
    print("\n" + "="*70)
    print("  完了!")
    print(f"  生成された画像は output フォルダに保存されています")
    print("="*70)


if __name__ == "__main__":
    main()
