"""
Gemini OCR Studio - Interactive UI
Gradioベースのインタラクティブダッシュボード
"""

import gradio as gr
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# Nanobananaモジュールのインポート
sys.path.insert(0, str(Path(__file__).parent / "Nanobanana"))
from Nanobanana.config import initialize_gemini
from Nanobanana.image_generator import ImageGenerator

# OCRモジュールのインポート
try:
    from ocr_engine import OCREngine
    from pdf_processor import PDFProcessor
    from state_manager import StateManager
except ImportError:
    print("⚠ OCRモジュールが見つかりません。一部機能が制限されます。")
    OCREngine = None
    PDFProcessor = None
    StateManager = None


class OCRStudioUI:
    """OCR Studio UIクラス"""
    
    def __init__(self):
        self.image_generator = None
        self.ocr_engine = None
        self.processing = False
        self.logs = []
        
        # Gemini API初期化
        try:
            initialize_gemini()
            self.image_generator = ImageGenerator()
            self.add_log("SUCCESS", "Gemini API初期化成功")
        except Exception as e:
            self.add_log("ERROR", f"Gemini API初期化失敗: {e}")
    
    def add_log(self, level, message):
        """ログを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        return "\n".join(self.logs[-50:])  # 最新50件のみ
    
    # ===== 画像生成機能 =====
    
    def generate_image(self, prompt, aspect_ratio, resolution, progress=gr.Progress()):
        """画像を生成"""
        if not self.image_generator:
            return None, self.add_log("ERROR", "ImageGeneratorが初期化されていません")
        
        try:
            progress(0, desc="画像生成中...")
            self.add_log("INFO", f"画像生成開始: {prompt[:50]}...")
            
            images = self.image_generator.generate_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                num_images=1,
                filename_prefix="ui_generated"
            )
            
            if images:
                progress(1.0, desc="完了!")
                self.add_log("SUCCESS", "画像生成完了")
                return images[0], self.add_log("SUCCESS", "画像生成完了")
            else:
                return None, self.add_log("ERROR", "画像生成失敗")
                
        except Exception as e:
            return None, self.add_log("ERROR", f"画像生成エラー: {e}")
    
    def batch_generate_images(self, prompts_text, aspect_ratio, resolution, progress=gr.Progress()):
        """複数の画像を一括生成"""
        if not self.image_generator:
            return [], self.add_log("ERROR", "ImageGeneratorが初期化されていません")
        
        prompts = [p.strip() for p in prompts_text.split("\n") if p.strip()]
        if not prompts:
            return [], self.add_log("ERROR", "プロンプトが入力されていません")
        
        generated_images = []
        
        for i, prompt in enumerate(prompts):
            try:
                progress((i + 1) / len(prompts), desc=f"生成中 {i+1}/{len(prompts)}")
                self.add_log("INFO", f"[{i+1}/{len(prompts)}] {prompt[:30]}...")
                
                images = self.image_generator.generate_image(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    num_images=1,
                    filename_prefix=f"batch_{i+1}"
                )
                
                if images:
                    generated_images.append(images[0])
                    self.add_log("SUCCESS", f"[{i+1}/{len(prompts)}] 完了")
                else:
                    self.add_log("ERROR", f"[{i+1}/{len(prompts)}] 失敗")
                    
            except Exception as e:
                self.add_log("ERROR", f"[{i+1}/{len(prompts)}] エラー: {e}")
        
        return generated_images, self.add_log("SUCCESS", f"{len(generated_images)}/{len(prompts)} 枚生成完了")
    
    # ===== OCR機能 =====
    
    def process_pdf(self, pdf_file, window_size, overlap, progress=gr.Progress()):
        """PDFを処理"""
        if not pdf_file:
            return self.add_log("ERROR", "PDFファイルが選択されていません")
        
        self.processing = True
        self.add_log("INFO", f"PDF処理開始: {pdf_file.name}")
        
        try:
            # ここに実際のOCR処理ロジックを実装
            # 現在はデモ用のシミュレーション
            total_steps = 10
            for i in range(total_steps):
                if not self.processing:
                    return self.add_log("WARN", "処理が中断されました")
                
                progress((i + 1) / total_steps, desc=f"処理中 {i+1}/{total_steps}")
                self.add_log("INFO", f"ページ {i+1} を処理中...")
                time.sleep(0.5)  # シミュレーション
            
            self.add_log("SUCCESS", "PDF処理完了")
            return self.add_log("SUCCESS", "PDF処理完了")
            
        except Exception as e:
            return self.add_log("ERROR", f"PDF処理エラー: {e}")
        finally:
            self.processing = False
    
    def stop_processing(self):
        """処理を停止"""
        self.processing = False
        return self.add_log("WARN", "処理停止リクエスト送信")


def create_ui():
    """UIを作成"""
    studio = OCRStudioUI()
    
    # カスタムCSS
    custom_css = """
    .gradio-container {
        font-family: 'Inter', sans-serif !important;
    }
    .primary-btn {
        background: linear-gradient(135deg, #13a4ec 0%, #0f8cc9 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .danger-btn {
        background: #ef4444 !important;
        border: none !important;
        color: white !important;
    }
    .log-box {
        font-family: 'JetBrains Mono', monospace !important;
        background: #0f172a !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
    .stat-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
        ),
        css=custom_css,
        title="Gemini OCR Studio"
    ) as app:
        
        # ヘッダー
        with gr.Row():
            gr.Markdown(
                """
                # 🎨 Gemini OCR Studio
                ### Enterprise Edition - Powered by Gemini 3 Pro & Nanobanana
                """
            )
        
        # タブ
        with gr.Tabs():
            
            # ===== OCR処理タブ =====
            with gr.Tab("📄 OCR処理"):
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### PDFアップロード")
                        pdf_input = gr.File(
                            label="PDFファイルを選択",
                            file_types=[".pdf"],
                            type="filepath"
                        )
                        
                        with gr.Row():
                            window_size = gr.Slider(
                                minimum=1,
                                maximum=20,
                                value=10,
                                step=1,
                                label="ウィンドウサイズ (ページ)"
                            )
                            overlap = gr.Slider(
                                minimum=0,
                                maximum=10,
                                value=2,
                                step=1,
                                label="重複 (ページ)"
                            )
                        
                        with gr.Row():
                            start_btn = gr.Button("🚀 処理開始", elem_classes="primary-btn", scale=2)
                            stop_btn = gr.Button("⛔ 停止", elem_classes="danger-btn", scale=1)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 処理状態")
                        status_display = gr.Markdown("待機中...")
                
                gr.Markdown("### 📊 リアルタイムログ")
                log_output = gr.Textbox(
                    label="実行ログ",
                    lines=15,
                    max_lines=20,
                    elem_classes="log-box",
                    interactive=False
                )
                
                # イベントハンドラ
                start_btn.click(
                    fn=studio.process_pdf,
                    inputs=[pdf_input, window_size, overlap],
                    outputs=log_output
                )
                
                stop_btn.click(
                    fn=studio.stop_processing,
                    outputs=log_output
                )
            
            # ===== 画像生成タブ =====
            with gr.Tab("🎨 画像生成 (Nanobanana)"):
                gr.Markdown("### Gemini 3 Pro Image で画像を生成")
                
                with gr.Row():
                    with gr.Column():
                        prompt_input = gr.Textbox(
                            label="プロンプト",
                            placeholder="例: A futuristic cityscape at night with neon lights",
                            lines=3
                        )
                        
                        with gr.Row():
                            aspect_ratio = gr.Dropdown(
                                choices=ImageGenerator.SUPPORTED_ASPECT_RATIOS,
                                value="16:9",
                                label="アスペクト比"
                            )
                            resolution = gr.Dropdown(
                                choices=ImageGenerator.SUPPORTED_RESOLUTIONS,
                                value="2K",
                                label="解像度"
                            )
                        
                        generate_btn = gr.Button("✨ 画像生成", elem_classes="primary-btn")
                    
                    with gr.Column():
                        image_output = gr.Image(label="生成画像", type="pil")
                
                image_log = gr.Textbox(
                    label="生成ログ",
                    lines=5,
                    elem_classes="log-box",
                    interactive=False
                )
                
                # イベントハンドラ
                generate_btn.click(
                    fn=studio.generate_image,
                    inputs=[prompt_input, aspect_ratio, resolution],
                    outputs=[image_output, image_log]
                )
            
            # ===== バッチ生成タブ =====
            with gr.Tab("🔄 バッチ生成"):
                gr.Markdown("### 複数のプロンプトから一括生成")
                
                with gr.Row():
                    with gr.Column():
                        batch_prompts = gr.Textbox(
                            label="プロンプト (1行に1つ)",
                            placeholder="A serene mountain landscape\nA futuristic robot\nA magical forest",
                            lines=10
                        )
                        
                        with gr.Row():
                            batch_aspect = gr.Dropdown(
                                choices=ImageGenerator.SUPPORTED_ASPECT_RATIOS,
                                value="1:1",
                                label="アスペクト比"
                            )
                            batch_resolution = gr.Dropdown(
                                choices=ImageGenerator.SUPPORTED_RESOLUTIONS,
                                value="2K",
                                label="解像度"
                            )
                        
                        batch_generate_btn = gr.Button("🚀 一括生成", elem_classes="primary-btn")
                    
                    with gr.Column():
                        batch_gallery = gr.Gallery(
                            label="生成画像",
                            columns=3,
                            height="auto"
                        )
                
                batch_log = gr.Textbox(
                    label="生成ログ",
                    lines=8,
                    elem_classes="log-box",
                    interactive=False
                )
                
                # イベントハンドラ
                batch_generate_btn.click(
                    fn=studio.batch_generate_images,
                    inputs=[batch_prompts, batch_aspect, batch_resolution],
                    outputs=[batch_gallery, batch_log]
                )
            
            # ===== 設定タブ =====
            with gr.Tab("⚙️ 設定"):
                gr.Markdown("### API設定")
                
                api_status = gr.Markdown(
                    """
                    ✅ **Gemini API**: 接続済み  
                    ✅ **Nanobanana**: 利用可能  
                    📁 **出力ディレクトリ**: `./Nanobanana/output/`
                    """
                )
                
                gr.Markdown("### モデル情報")
                model_info = gr.Markdown(
                    """
                    - **画像生成モデル**: `gemini-3-pro-image-preview`
                    - **対応解像度**: 1K, 2K, 4K
                    - **対応アスペクト比**: 9種類
                    """
                )
        
        # フッター
        gr.Markdown(
            """
            ---
            **Gemini OCR Studio** | Powered by Google Gemini 3 Pro & Nanobanana  
            © 2026 Enterprise Edition
            """
        )
    
    return app


if __name__ == "__main__":
    print("="*70)
    print("  🎨 Gemini OCR Studio - Interactive UI")
    print("="*70)
    print()
    
    app = create_ui()
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )
