"""
高度な画像生成の例
異なる解像度とアスペクト比を使用した画像生成を実演します。
"""

import sys
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import initialize_gemini
from image_generator import ImageGenerator


def main():
    print("="*70)
    print("  Gemini 3 Pro Image - 高度な画像生成")
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
    
    # 異なる設定での画像生成
    configurations = [
        {
            "prompt": "A professional product photo of a luxury watch on a marble surface",
            "aspect_ratio": "1:1",
            "resolution": "4K",
            "description": "正方形・4K解像度 (商品写真向け)"
        },
        {
            "prompt": "A cinematic landscape of an alien planet with two suns setting",
            "aspect_ratio": "16:9",
            "resolution": "2K",
            "description": "ワイドスクリーン・2K解像度 (映画風)"
        },
        {
            "prompt": "A vertical portrait of a cyberpunk character in neon-lit streets",
            "aspect_ratio": "9:16",
            "resolution": "2K",
            "description": "縦長・2K解像度 (スマホ壁紙向け)"
        },
        {
            "prompt": "An infographic showing the solar system with detailed planet information",
            "aspect_ratio": "4:3",
            "resolution": "2K",
            "description": "4:3・2K解像度 (インフォグラフィック)"
        }
    ]
    
    print("Step 3: 異なる設定で画像を生成中...")
    print()
    
    for i, config in enumerate(configurations, 1):
        print(f"\n{'='*70}")
        print(f"設定 {i}/{len(configurations)}: {config['description']}")
        print(f"{'='*70}")
        
        try:
            images = generator.generate_image(
                prompt=config["prompt"],
                aspect_ratio=config["aspect_ratio"],
                resolution=config["resolution"],
                num_images=1,
                filename_prefix=f"advanced_example_{i}"
            )
            
            if images:
                img = images[0]
                print(f"\n✓ 成功!")
                print(f"  画像サイズ: {img.width} x {img.height} pixels")
                print(f"  アスペクト比: {config['aspect_ratio']}")
                print(f"  解像度: {config['resolution']}")
            else:
                print(f"\n⚠ 失敗: 画像が生成されませんでした")
                
        except Exception as e:
            print(f"\n✗ エラー: {e}")
    
    print("\n" + "="*70)
    print("  完了!")
    print(f"  生成された画像は output フォルダに保存されています")
    print("="*70)
    
    # サポートされている設定の表示
    print("\n" + "="*70)
    print("  サポートされている設定")
    print("="*70)
    print(f"\nアスペクト比: {', '.join(ImageGenerator.SUPPORTED_ASPECT_RATIOS)}")
    print(f"解像度: {', '.join(ImageGenerator.SUPPORTED_RESOLUTIONS)}")


if __name__ == "__main__":
    main()
