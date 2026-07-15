"""
Gemini OCR Studio - Web UI
既存のOCRコードをWebUIから操作できるようにするGradioアプリケーション
"""

import gradio as gr
import sys
import os
import threading
import queue
from pathlib import Path
from datetime import datetime
from io import StringIO
import yaml

# 既存モジュールのインポート
from pdf_processor import PDFProcessor
from ocr_engine import OCREngine, load_api_key
from state_manager import StateManager
from error_handler import ErrorHandler, OCRError


class OCRWebUI:
    """OCR Web UIクラス"""
    
    def __init__(self):
        self.config = self.load_config()
        self.pdf_processor = None
        self.ocr_engine = None
        self.state_manager = StateManager()
        self.error_handler = None
        self.processing = False
        self.stop_requested = False
        self.log_queue = queue.Queue()
        
    def load_config(self):
        """設定ファイルを読み込む"""
        try:
            with open("config.yaml", 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {
                "api": {
                    "model": "gemini-3-flash",
                    "fallback_model": "gemini-3-pro",
                    "max_retries": 3,
                    "timeout": 60
                },
                "processing": {
                    "batch_size": 10,
                    "overlap": 1,
                    "dpi": 300,
                    "image_format": "png"
                },
                "output": {
                    "markdown_file": "output.md",
                    "log_dir": "logs",
                    "temp_dir": "temp_pages"
                }
            }
    
    def log(self, level, message):
        """ログメッセージを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_queue.put(log_entry)
        return log_entry
    
    def get_logs(self):
        """ログを取得"""
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except:
                break
        return "\n".join(logs)
    
    def initialize_ocr(self, model_name):
        """OCRエンジンを初期化"""
        try:
            api_key = load_api_key()
            self.ocr_engine = OCREngine(
                api_key=api_key,
                model_name=model_name,
                fallback_model=self.config["api"]["fallback_model"],
                timeout=self.config["api"]["timeout"]
            )
            
            if self.ocr_engine.test_connection():
                self.log("SUCCESS", "API接続成功")
                return True, "✅ API接続成功"
            else:
                self.log("ERROR", "API接続失敗")
                return False, "❌ API接続失敗"
                
        except Exception as e:
            self.log("ERROR", f"OCRエンジン初期化エラー: {e}")
            return False, f"❌ エラー: {e}"
    
    def process_pdf_upload(self, pdf_file, batch_size, overlap, model, force_reconvert):
        """PDFアップロード処理"""
        if not pdf_file:
            return "PDFファイルを選択してください", "", ""
        
        try:
            # PDF Processorを初期化
            self.pdf_processor = PDFProcessor(
                output_dir=self.config["output"]["temp_dir"],
                dpi=self.config["processing"]["dpi"],
                image_format=self.config["processing"]["image_format"]
            )
            
            # PDFを画像に変換
            self.log("INFO", f"PDF変換開始: {pdf_file.name}")
            total_pages = self.pdf_processor.convert_pdf(pdf_file.name, force=force_reconvert)
            
            # ステート初期化
            self.state_manager.update(
                total_pages=total_pages,
                batch_size=batch_size,
                overlap=overlap
            )
            self.state_manager.save()
            
            self.log("SUCCESS", f"PDF変換完了: {total_pages}ページ")
            
            status = f"✅ PDF読み込み完了\n📄 総ページ数: {total_pages}\n📦 バッチサイズ: {batch_size}"
            
            return status, self.get_logs(), gr.update(interactive=True)
            
        except Exception as e:
            self.log("ERROR", f"PDF処理エラー: {e}")
            return f"❌ エラー: {e}", self.get_logs(), gr.update(interactive=False)
    
    def start_ocr_processing(self, model, progress=gr.Progress()):
        """OCR処理を開始"""
        if self.processing:
            return "⚠️ 既に処理中です", self.get_logs()
        
        self.processing = True
        self.stop_requested = False
        
        try:
            # OCRエンジン初期化
            success, msg = self.initialize_ocr(model)
            if not success:
                self.processing = False
                return msg, self.get_logs()
            
            # エラーハンドラー初期化
            self.error_handler = ErrorHandler(
                max_retries=self.config["api"]["max_retries"],
                log_dir=self.config["output"]["log_dir"]
            )
            
            # ページ検証
            total_pages = self.state_manager.get("total_pages")
            valid, missing = self.pdf_processor.validate_pages(total_pages)
            if not valid:
                self.processing = False
                return f"❌ ページ画像が見つかりません: {missing}", self.get_logs()
            
            # 出力ファイル
            output_file = self.config["output"]["markdown_file"]
            last_page = self.state_manager.get("last_processed_page", 0)
            mode = "a" if last_page > 0 else "w"
            
            self.log("INFO", f"OCR処理開始 (総ページ: {total_pages})")
            
            # バッチ処理
            with open(output_file, mode, encoding='utf-8') as f:
                processed = last_page
                
                while True:
                    if self.stop_requested:
                        self.log("WARN", "処理が中断されました")
                        break
                    
                    # 次のバッチ取得
                    batch_info = self.state_manager.get_next_batch()
                    if not batch_info:
                        break
                    
                    input_start, input_end, output_start, output_end = batch_info
                    
                    # 進捗更新
                    progress(processed / total_pages, desc=f"処理中: {output_start}-{output_end}")
                    
                    # ページ画像取得
                    image_paths = self.pdf_processor.get_page_paths(input_start, input_end)
                    
                    self.log("INFO", f"バッチ処理中: P{output_start}-{output_end}")
                    
                    # OCR処理
                    try:
                        markdown_text = self.ocr_engine.process_batch(
                            image_paths=image_paths,
                            output_start=output_start,
                            output_end=output_end,
                            last_tail_text=self.state_manager.get("last_tail_text", ""),
                            current_chapter=self.state_manager.get("current_chapter", "")
                        )
                        
                        # 出力書き込み
                        f.write(markdown_text)
                        f.write("\n\n")
                        f.flush()
                        
                        # メタデータ抽出
                        last_tail, chapter = self.ocr_engine.extract_metadata(markdown_text)
                        
                        # ステート更新
                        self.state_manager.update(
                            last_processed_page=output_end,
                            last_tail_text=last_tail,
                            current_chapter=chapter or self.state_manager.get("current_chapter", "")
                        )
                        self.state_manager.save()
                        
                        processed = output_end
                        self.log("SUCCESS", f"バッチ完了: P{output_start}-{output_end}")
                        
                    except OCRError as e:
                        self.error_handler.handle_api_error(e, output_start)
                        self.log("ERROR", f"OCRエラー: {e}")
                        break
            
            self.processing = False
            
            if processed >= total_pages:
                self.log("SUCCESS", "✅ 全ページの処理が完了しました")
                return f"✅ 処理完了！\n📄 出力: {output_file}", self.get_logs()
            else:
                return f"⚠️ 処理中断 ({processed}/{total_pages}ページ完了)", self.get_logs()
                
        except Exception as e:
            self.processing = False
            self.log("ERROR", f"予期しないエラー: {e}")
            return f"❌ エラー: {e}", self.get_logs()
    
    def resume_processing(self, model, progress=gr.Progress()):
        """処理を再開"""
        if not self.state_manager.load():
            return "❌ 保存された状態が見つかりません", self.get_logs()
        
        self.log("INFO", "保存された状態から再開します")
        return self.start_ocr_processing(model, progress)
    
    def stop_processing(self):
        """処理を停止"""
        self.stop_requested = True
        self.log("WARN", "停止リクエスト送信")
        return "⛔ 停止リクエスト送信", self.get_logs()
    
    def cleanup_files(self):
        """一時ファイルをクリーンアップ"""
        try:
            if self.pdf_processor:
                self.pdf_processor.cleanup()
            
            if Path("progress.json").exists():
                Path("progress.json").unlink()
                self.log("INFO", "progress.json を削除")
            
            self.log("SUCCESS", "クリーンアップ完了")
            return "✅ クリーンアップ完了", self.get_logs()
            
        except Exception as e:
            self.log("ERROR", f"クリーンアップエラー: {e}")
            return f"❌ エラー: {e}", self.get_logs()
    
    def get_status(self):
        """現在の状態を取得"""
        if self.state_manager.load():
            total = self.state_manager.get("total_pages", 0)
            processed = self.state_manager.get("last_processed_page", 0)
            chapter = self.state_manager.get("current_chapter", "不明")
            
            status = f"""
📊 **処理状態**
- 総ページ数: {total}
- 処理済み: {processed}/{total} ({processed/total*100:.1f}%)
- 現在の章: {chapter}
"""
            return status
        else:
            return "ℹ️ 保存された状態がありません"


def create_ui():
    """UIを作成"""
    ui = OCRWebUI()
    
    # カスタムCSS (stitch.zipのデザインを参考)
    custom_css = """
    .gradio-container {
        font-family: 'Inter', sans-serif !important;
        max-width: 1400px !important;
    }
    .primary-btn {
        background: linear-gradient(135deg, #13a4ec 0%, #0f8cc9 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .danger-btn {
        background: #ef4444 !important;
        color: white !important;
    }
    .log-box {
        font-family: 'JetBrains Mono', monospace !important;
        background: #0f172a !important;
        color: #e2e8f0 !important;
        font-size: 12px !important;
        line-height: 1.6 !important;
    }
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"),
        css=custom_css,
        title="Gemini OCR Studio"
    ) as app:
        
        # ヘッダー
        gr.Markdown(
            """
            # 🎨 Gemini OCR Studio
            ### ステートフル・スライディングウィンドウ OCRシステム
            """
        )
        
        with gr.Tabs():
            # OCR処理タブ
            with gr.Tab("📄 OCR処理"):
                with gr.Row():
                    with gr.Column(scale=2):
                        pdf_upload = gr.File(
                            label="PDFファイルをアップロード",
                            file_types=[".pdf"],
                            type="filepath"
                        )
                        
                        with gr.Row():
                            batch_size = gr.Slider(1, 20, value=10, step=1, label="バッチサイズ")
                            overlap = gr.Slider(0, 5, value=1, step=1, label="重複ページ数")
                        
                        model_select = gr.Dropdown(
                            choices=["gemini-3-flash", "gemini-3-pro", "gemini-2.5-flash"],
                            value="gemini-3-flash",
                            label="モデル選択"
                        )
                        
                        force_reconvert = gr.Checkbox(label="強制再変換", value=False)
                        
                        upload_btn = gr.Button("📤 PDFを読み込む", elem_classes="primary-btn")
                    
                    with gr.Column(scale=1):
                        status_display = gr.Markdown("待機中...")
                
                gr.Markdown("### 処理制御")
                with gr.Row():
                    start_btn = gr.Button("🚀 新規処理開始", elem_classes="primary-btn", scale=2)
                    resume_btn = gr.Button("▶️ 再開", scale=1)
                    stop_btn = gr.Button("⛔ 停止", elem_classes="danger-btn", scale=1)
                
                gr.Markdown("### 📊 リアルタイムログ")
                log_display = gr.Textbox(
                    label="実行ログ",
                    lines=15,
                    max_lines=20,
                    elem_classes="log-box",
                    interactive=False
                )
                
                # イベントハンドラ
                upload_btn.click(
                    fn=ui.process_pdf_upload,
                    inputs=[pdf_upload, batch_size, overlap, model_select, force_reconvert],
                    outputs=[status_display, log_display, start_btn]
                )
                
                start_btn.click(
                    fn=ui.start_ocr_processing,
                    inputs=[model_select],
                    outputs=[status_display, log_display]
                )
                
                resume_btn.click(
                    fn=ui.resume_processing,
                    inputs=[model_select],
                    outputs=[status_display, log_display]
                )
                
                stop_btn.click(
                    fn=ui.stop_processing,
                    outputs=[status_display, log_display]
                )
            
            # 結果タブ
            with gr.Tab("📝 結果"):
                gr.Markdown("### 出力ファイル")
                output_file = gr.File(
                    label="output.md",
                    value="output.md" if Path("output.md").exists() else None
                )
                
                gr.Markdown("### プレビュー")
                preview_display = gr.Textbox(
                    label="Markdown プレビュー",
                    lines=20,
                    interactive=False
                )
                
                def load_output():
                    if Path("output.md").exists():
                        with open("output.md", 'r', encoding='utf-8') as f:
                            return f.read()
                    return "出力ファイルがまだ生成されていません"
                
                refresh_btn = gr.Button("🔄 更新")
                refresh_btn.click(fn=load_output, outputs=preview_display)
            
            # 設定・管理タブ
            with gr.Tab("⚙️ 設定・管理"):
                gr.Markdown("### 処理状態")
                status_info = gr.Markdown(ui.get_status())
                
                status_refresh_btn = gr.Button("🔄 状態を更新")
                status_refresh_btn.click(fn=ui.get_status, outputs=status_info)
                
                gr.Markdown("### ファイル管理")
                cleanup_btn = gr.Button("🗑️ 一時ファイルをクリーンアップ", elem_classes="danger-btn")
                cleanup_status = gr.Textbox(label="クリーンアップ結果", interactive=False)
                cleanup_log = gr.Textbox(label="ログ", interactive=False, elem_classes="log-box")
                
                cleanup_btn.click(
                    fn=ui.cleanup_files,
                    outputs=[cleanup_status, cleanup_log]
                )
        
        # フッター
        gr.Markdown(
            """
            ---
            **Gemini OCR Studio** | Powered by Google Gemini API  
            © 2026 - ステートフル・スライディングウィンドウ OCRシステム
            """
        )
    
    return app


if __name__ == "__main__":
    print("="*70)
    print("  🎨 Gemini OCR Studio - Web UI")
    print("="*70)
    print()
    
    app = create_ui()
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
