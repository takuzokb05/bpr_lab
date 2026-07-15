"""
Gemini 3 Pro Image (Nano Banana Pro) 画像生成モジュール
gemini-3-pro-image-preview モデルを使用した画像生成機能を提供します。
"""

import os
import google.generativeai as genai
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from PIL import Image
import io


class ImageGenerator:
    """
    Gemini 3 Pro Image を使用した画像生成クラス
    """
    
    # サポートされているアスペクト比
    SUPPORTED_ASPECT_RATIOS = [
        "1:1", "3:2", "2:3", "3:4", "4:3", 
        "4:5", "5:4", "9:16", "16:9"
    ]
    
    # サポートされている解像度
    SUPPORTED_RESOLUTIONS = ["1K", "2K", "4K"]
    
    def __init__(self, model_name: str = "gemini-3-pro-image-preview"):
        """
        ImageGenerator の初期化
        
        Args:
            model_name: 使用するモデル名 (デフォルト: gemini-3-pro-image-preview)
        """
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"✓ ImageGenerator initialized with model: {model_name}")
        print(f"✓ Output directory: {self.output_dir}")
    
    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
        num_images: int = 1,
        save: bool = True,
        filename_prefix: str = "generated"
    ) -> List[Image.Image]:
        """
        テキストプロンプトから画像を生成
        
        Args:
            prompt: 画像生成のためのテキストプロンプト
            aspect_ratio: アスペクト比 (例: "1:1", "16:9")
            resolution: 解像度 ("1K", "2K", "4K")
            num_images: 生成する画像の数
            save: 画像を保存するかどうか
            filename_prefix: 保存ファイル名のプレフィックス
            
        Returns:
            生成された画像のリスト (PIL.Image)
            
        Raises:
            ValueError: サポートされていないアスペクト比または解像度の場合
        """
        # バリデーション
        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            raise ValueError(
                f"サポートされていないアスペクト比: {aspect_ratio}\n"
                f"サポート: {', '.join(self.SUPPORTED_ASPECT_RATIOS)}"
            )
        
        if resolution not in self.SUPPORTED_RESOLUTIONS:
            raise ValueError(
                f"サポートされていない解像度: {resolution}\n"
                f"サポート: {', '.join(self.SUPPORTED_RESOLUTIONS)}"
            )
        
        print(f"\n{'='*60}")
        print(f"画像生成を開始...")
        print(f"プロンプト: {prompt}")
        print(f"アスペクト比: {aspect_ratio} | 解像度: {resolution} | 枚数: {num_images}")
        print(f"{'='*60}\n")
        
        try:
            # 画像生成の設定
            generation_config = {
                "temperature": 1.0,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # プロンプトに解像度とアスペクト比の指示を追加
            enhanced_prompt = f"{prompt}\n\n[Technical requirements: aspect ratio {aspect_ratio}, {resolution} resolution]"
            
            # 画像生成
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config=generation_config
            )
            
            images = []
            
            # レスポンスから画像を抽出
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates[:num_images]:
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data'):
                                # バイナリデータから画像を作成
                                image_data = part.inline_data.data
                                image = Image.open(io.BytesIO(image_data))
                                images.append(image)
                                
                                if save:
                                    self._save_image(
                                        image, 
                                        filename_prefix, 
                                        aspect_ratio, 
                                        resolution
                                    )
            
            if not images:
                print("⚠ 画像が生成されませんでした。レスポンスを確認してください。")
                print(f"Response: {response}")
            else:
                print(f"✓ {len(images)} 枚の画像を生成しました")
            
            return images
            
        except Exception as e:
            print(f"✗ 画像生成エラー: {e}")
            raise
    
    def generate_from_image(
        self,
        prompt: str,
        input_image_path: str,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
        save: bool = True,
        filename_prefix: str = "edited"
    ) -> List[Image.Image]:
        """
        画像とテキストプロンプトから新しい画像を生成 (image-to-image)
        
        Args:
            prompt: 画像編集のためのテキストプロンプト
            input_image_path: 入力画像のパス
            aspect_ratio: アスペクト比
            resolution: 解像度
            save: 画像を保存するかどうか
            filename_prefix: 保存ファイル名のプレフィックス
            
        Returns:
            生成された画像のリスト (PIL.Image)
        """
        print(f"\n{'='*60}")
        print(f"画像編集を開始...")
        print(f"入力画像: {input_image_path}")
        print(f"プロンプト: {prompt}")
        print(f"{'='*60}\n")
        
        try:
            # 入力画像を読み込む
            input_image = Image.open(input_image_path)
            
            # プロンプトと画像を組み合わせて生成
            enhanced_prompt = f"{prompt}\n\n[Technical requirements: aspect ratio {aspect_ratio}, {resolution} resolution]"
            
            response = self.model.generate_content([enhanced_prompt, input_image])
            
            images = []
            
            # レスポンスから画像を抽出
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data'):
                                image_data = part.inline_data.data
                                image = Image.open(io.BytesIO(image_data))
                                images.append(image)
                                
                                if save:
                                    self._save_image(
                                        image, 
                                        filename_prefix, 
                                        aspect_ratio, 
                                        resolution
                                    )
            
            if not images:
                print("⚠ 画像が生成されませんでした")
            else:
                print(f"✓ {len(images)} 枚の画像を生成しました")
            
            return images
            
        except Exception as e:
            print(f"✗ 画像編集エラー: {e}")
            raise
    
    def _save_image(
        self, 
        image: Image.Image, 
        prefix: str, 
        aspect_ratio: str, 
        resolution: str
    ) -> Path:
        """
        画像をファイルに保存
        
        Args:
            image: 保存する画像
            prefix: ファイル名のプレフィックス
            aspect_ratio: アスペクト比
            resolution: 解像度
            
        Returns:
            保存されたファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        aspect_str = aspect_ratio.replace(":", "x")
        filename = f"{prefix}_{aspect_str}_{resolution}_{timestamp}.png"
        filepath = self.output_dir / filename
        
        image.save(filepath, "PNG")
        print(f"  → 保存: {filepath}")
        
        return filepath


if __name__ == "__main__":
    # テスト実行
    from config import initialize_gemini
    
    print("=== Gemini 3 Pro Image Generator Test ===\n")
    
    try:
        # API初期化
        initialize_gemini()
        
        # ImageGenerator インスタンス作成
        generator = ImageGenerator()
        
        # テスト画像生成
        test_prompt = "A serene Japanese garden with cherry blossoms, koi pond, and traditional stone lanterns at sunset"
        
        images = generator.generate_image(
            prompt=test_prompt,
            aspect_ratio="16:9",
            resolution="2K",
            num_images=1,
            filename_prefix="test"
        )
        
        print(f"\n✓ テスト完了: {len(images)} 枚の画像を生成しました")
        
    except Exception as e:
        print(f"\n✗ テストエラー: {e}")
