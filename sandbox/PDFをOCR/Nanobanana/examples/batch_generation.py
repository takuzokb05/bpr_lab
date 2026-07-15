"""
バッチ画像生成の例
複数のプロンプトから一括で画像を生成します。
"""

import sys
from pathlib import Path
from typing import List, Dict

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import initialize_gemini
from image_generator import ImageGenerator


def batch_generate(
    generator: ImageGenerator,
    prompts: List[str],
    aspect_ratio: str = "1:1",
    resolution: str = "2K"
) -> Dict[str, bool]:
    """
    複数のプロンプトから一括で画像を生成
    
    Args:
        generator: ImageGenerator インスタンス
        prompts: プロンプトのリスト
        aspect_ratio: アスペクト比
        resolution: 解像度
        
    Returns:
        各プロンプトの成功/失敗を示す辞書
    """
    results = {}
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'='*70}")
        print(f"画像 {i}/{len(prompts)}")
        print(f"{'='*70}")
        
        try:
            images = generator.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                num_images=1,
                filename_prefix=f"batch_{i}"
            )
            
            results[prompt] = len(images) > 0
            
        except Exception as e:
            print(f"✗ エラー: {e}")
            results[prompt] = False
    
    return results


def main():
    print("="*70)
    print("  Gemini 3 Pro Image - バッチ画像生成")
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
    
    # バッチ生成するプロンプトリスト
    prompts = [
        # 自然風景
        "A serene Japanese garden with cherry blossoms in full bloom",
        "Northern lights dancing over a frozen lake in Iceland",
        "A tropical beach at sunset with palm trees swaying",
        
        # 都市風景
        "Tokyo street at night with neon signs and rain reflections",
        "New York City skyline at golden hour",
        "A cozy European cafe on a cobblestone street",
        
        # ファンタジー
        "A magical forest with glowing mushrooms and fairy lights",
        "A dragon flying over a medieval castle",
        "An underwater city with bioluminescent creatures",
        
        # 抽象・アート
        "Abstract geometric patterns in vibrant colors",
        "Watercolor painting of a mountain landscape",
        "Minimalist design with bold shapes and pastel colors"
    ]
    
    print(f"Step 3: {len(prompts)} 枚の画像を一括生成中...")
    print(f"設定: アスペクト比 16:9, 解像度 2K")
    
    # バッチ生成実行
    results = batch_generate(
        generator=generator,
        prompts=prompts,
        aspect_ratio="16:9",
        resolution="2K"
    )
    
    # 結果サマリー
    print("\n" + "="*70)
    print("  生成結果サマリー")
    print("="*70)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"\n成功: {success_count}/{total_count} 枚")
    print(f"失敗: {total_count - success_count}/{total_count} 枚")
    
    if success_count < total_count:
        print("\n失敗したプロンプト:")
        for prompt, success in results.items():
            if not success:
                print(f"  ✗ {prompt[:60]}...")
    
    print("\n" + "="*70)
    print("  完了!")
    print(f"  生成された画像は output フォルダに保存されています")
    print("="*70)


if __name__ == "__main__":
    main()
