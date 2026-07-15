"""
WebSocket Server for OCR UI
HTMLフロントエンドと既存のOCRコードを接続するWebSocketサーバー
"""

import asyncio
import websockets
import json
import threading
import os
from pathlib import Path
from datetime import datetime
import yaml

# 既存モジュールのインポート
from pdf_processor import PDFProcessor
from ocr_engine import OCREngine, load_api_key
from state_manager import StateManager
from error_handler import ErrorHandler, OCRError


class OCRWebSocketServer:
    """WebSocketサーバークラス"""
    
    def __init__(self):
        self.clients = set()
        self.config = self.load_config()
        self.pdf_processor = None
        self.ocr_engine = None
        self.state_manager = StateManager()
        self.error_handler = None
        self.processing = False
        self.paused = False
        self.stop_requested = False
        
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
    
    async def broadcast(self, message):
        """全クライアントにメッセージを送信"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    async def send_log(self, level, message):
        """ログメッセージを送信"""
        await self.broadcast({
            'type': 'log',
            'level': level,
            'message': message
        })
    
    async def send_progress(self, processed, total):
        """進捗を送信"""
        await self.broadcast({
            'type': 'progress',
            'processed': processed,
            'total': total
        })
    
    async def send_status(self, **kwargs):
        """ステータスを送信"""
        await self.broadcast({
            'type': 'status',
            **kwargs
        })
    
    async def send_file_list(self):
        """ファイルリストを送信"""
        temp_dir = Path(self.config["output"]["temp_dir"])
        files = []
        
        if temp_dir.exists():
            for file in sorted(temp_dir.glob("*.png")):
                files.append({
                    'name': file.name,
                    'status': '待機中',
                    'processing': False
                })
        
        await self.broadcast({
            'type': 'file_list',
            'files': files
        })
    
    async def handle_client(self, websocket):
        """クライアント接続ハンドラ"""
        self.clients.add(websocket)
        await self.send_log('INFO', f'クライアント接続: {len(self.clients)}台')
        
        # 初期状態を送信
        await self.send_file_list()
        
        # 保存された状態があれば読み込む
        if self.state_manager.load():
            total = self.state_manager.get("total_pages", 0)
            processed = self.state_manager.get("last_processed_page", 0)
            await self.send_progress(processed, total)
            await self.send_status(
                chapter=self.state_manager.get("current_chapter", "--"),
                last_tail=self.state_manager.get("last_tail_text", "--")[:50] + "..."
            )
        
        try:
            async for message in websocket:
                data = json.parse(message)
                await self.handle_command(data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            await self.send_log('INFO', f'クライアント切断: {len(self.clients)}台')
    
    async def handle_command(self, data):
        """コマンドハンドラ"""
        command = data.get('command')
        
        if command == 'upload_pdf':
            asyncio.create_task(self.handle_pdf_upload(data))
        elif command == 'start':
            asyncio.create_task(self.start_processing(data.get('pdf_path')))
        elif command == 'pause':
            self.paused = not self.paused
            await self.send_log('WARN', '処理を一時停止しました' if self.paused else '処理を再開しました')
        elif command == 'stop':
            self.stop_requested = True
            await self.send_log('WARN', '停止リクエストを受信しました')
        elif command == 'refresh_files':
            await self.send_file_list()
        elif command == 'open_output':
            output_file = self.config["output"]["markdown_file"]
            if Path(output_file).exists():
                os.startfile(output_file)
                await self.send_log('INFO', f'{output_file} を開きました')
    
    async def handle_pdf_upload(self, data):
        """PDFアップロード処理"""
        try:
            import base64
            
            filename = data.get('filename')
            file_data = data.get('data')
            
            await self.send_log('INFO', f'PDFアップロード開始: {filename}')
            
            # Base64デコード
            await self.send_log('INFO', 'ファイルをデコード中...')
            pdf_bytes = base64.b64decode(file_data)
            file_size_mb = len(pdf_bytes) / 1024 / 1024
            await self.send_log('INFO', f'ファイルサイズ: {file_size_mb:.2f} MB')
            
            # 一時ファイルに保存
            temp_pdf_path = Path("temp_upload.pdf")
            await self.send_log('INFO', '一時ファイルに保存中...')
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            await self.send_log('SUCCESS', 'PDFファイル保存完了')
            
            # PDF Processor初期化
            await self.send_log('INFO', 'PDF Processorを初期化中...')
            self.pdf_processor = PDFProcessor(
                output_dir=self.config["output"]["temp_dir"],
                dpi=self.config["processing"]["dpi"],
                image_format=self.config["processing"]["image_format"]
            )
            
            # PDFを画像に変換
            await self.send_log('INFO', 'PDF→画像変換を開始します (時間がかかる場合があります)...')
            await self.broadcast({
                'type': 'upload_progress',
                'percent': 40,
                'status': 'PDF変換中... (大きなファイルの場合、数分かかることがあります)'
            })
            
            # 変換を別スレッドで実行（ブロッキングを避ける）
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            def convert_pdf_sync():
                return self.pdf_processor.convert_pdf(str(temp_pdf_path), force=True)
            
            with concurrent.futures.ThreadPoolExecutor() as pool:
                total_pages = await loop.run_in_executor(pool, convert_pdf_sync)
            
            await self.send_log('SUCCESS', f'PDF変換完了: {total_pages}ページ')
            await self.broadcast({
                'type': 'upload_progress',
                'percent': 80,
                'status': 'ステート初期化中...'
            })
            
            # ステート初期化
            self.state_manager.update(
                total_pages=total_pages,
                batch_size=self.config["processing"]["batch_size"],
                overlap=self.config["processing"]["overlap"]
            )
            self.state_manager.save()
            
            await self.send_log('SUCCESS', 'ステート初期化完了')
            await self.broadcast({
                'type': 'upload_progress',
                'percent': 100,
                'status': '完了！'
            })
            
            await self.send_progress(0, total_pages)
            await self.send_status(
                filename=filename,
                job_status='待機中'
            )
            await self.send_file_list()
            
            # アップロード完了を通知
            await self.broadcast({
                'type': 'upload_complete',
                'total_pages': total_pages
            })
            
            # 一時ファイル削除
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
                await self.send_log('INFO', '一時ファイルを削除しました')
            
            # 自動的に処理を開始
            await self.send_log('INFO', 'OCR処理を自動開始します...')
            await asyncio.sleep(1)  # UIが更新されるまで少し待つ
            asyncio.create_task(self.start_processing())
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            await self.send_log('ERROR', f'PDFアップロードエラー: {e}')
            await self.send_log('DEBUG', f'詳細: {error_detail}')
            await self.broadcast({
                'type': 'upload_error',
                'error': str(e)
            })
            
            # 一時ファイルがあれば削除
            temp_pdf_path = Path("temp_upload.pdf")
            if temp_pdf_path.exists():
                temp_pdf_path.unlink()
    
    async def start_processing(self, pdf_path=None):
        """OCR処理を開始"""
        if self.processing:
            await self.send_log('WARN', '既に処理中です')
            return
        
        self.processing = True
        self.stop_requested = False
        self.paused = False
        
        try:
            # OCRエンジン初期化
            await self.send_log('INFO', 'OCRエンジンを初期化中...')
            api_key = load_api_key()
            self.ocr_engine = OCREngine(
                api_key=api_key,
                model_name=self.config["api"]["model"],
                fallback_model=self.config["api"]["fallback_model"],
                timeout=self.config["api"]["timeout"]
            )
            
            if not self.ocr_engine.test_connection():
                await self.send_log('ERROR', 'API接続テスト失敗')
                self.processing = False
                return
            
            await self.send_log('SUCCESS', 'API接続成功')
            
            # PDF Processor初期化
            self.pdf_processor = PDFProcessor(
                output_dir=self.config["output"]["temp_dir"],
                dpi=self.config["processing"]["dpi"],
                image_format=self.config["processing"]["image_format"]
            )
            
            # エラーハンドラー初期化
            self.error_handler = ErrorHandler(
                max_retries=self.config["api"]["max_retries"],
                log_dir=self.config["output"]["log_dir"]
            )
            
            # ステート確認
            if not self.state_manager.load():
                await self.send_log('ERROR', '保存された状態が見つかりません。PDFを最初から処理してください。')
                self.processing = False
                return
            
            # ページ検証
            total_pages = self.state_manager.get("total_pages")
            valid, missing = self.pdf_processor.validate_pages(total_pages)
            if not valid:
                await self.send_log('ERROR', f'ページ画像が見つかりません: {missing}')
                self.processing = False
                return
            
            # ステータス更新
            await self.send_status(job_status='処理中ジョブ')
            await self.send_log('INFO', f'OCR処理開始 (総ページ: {total_pages})')
            
            # 出力ファイル
            output_file = self.config["output"]["markdown_file"]
            last_page = self.state_manager.get("last_processed_page", 0)
            mode = "a" if last_page > 0 else "w"
            
            # バッチ処理
            with open(output_file, mode, encoding='utf-8') as f:
                while True:
                    # 停止チェック
                    if self.stop_requested:
                        await self.send_log('WARN', '処理が中断されました')
                        break
                    
                    # 一時停止チェック
                    while self.paused:
                        await asyncio.sleep(1)
                    
                    # 次のバッチ取得
                    batch_info = self.state_manager.get_next_batch()
                    if not batch_info:
                        break
                    
                    input_start, input_end, output_start, output_end = batch_info
                    
                    # 進捗更新
                    await self.send_progress(output_start - 1, total_pages)
                    
                    # ファイルリスト更新 (処理中のファイルをハイライト)
                    await self.send_file_list()
                    
                    # ページ画像取得
                    image_paths = self.pdf_processor.get_page_paths(input_start, input_end)
                    
                    await self.send_log('INFO', f'バッチ処理中: P{output_start}-{output_end}')
                    
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
                        
                        # UI更新
                        await self.send_progress(output_end, total_pages)
                        await self.send_status(
                            chapter=chapter or self.state_manager.get("current_chapter", "--"),
                            last_tail=(last_tail[:50] + "...") if last_tail else "--"
                        )
                        
                        await self.send_log('SUCCESS', f'バッチ完了: P{output_start}-{output_end}')
                        
                    except OCRError as e:
                        self.error_handler.handle_api_error(e, output_start)
                        await self.send_log('ERROR', f'OCRエラー: {e}')
                        break
                    
                    # 少し待機
                    await asyncio.sleep(0.1)
            
            self.processing = False
            
            # 完了チェック
            processed = self.state_manager.get("last_processed_page", 0)
            if processed >= total_pages:
                await self.send_log('SUCCESS', '✅ 全ページの処理が完了しました')
                await self.send_status(job_status='完了')
            else:
                await self.send_log('WARN', f'⚠️ 処理中断 ({processed}/{total_pages}ページ完了)')
                await self.send_status(job_status='一時停止')
                
        except Exception as e:
            self.processing = False
            await self.send_log('ERROR', f'予期しないエラー: {e}')
            await self.send_status(job_status='エラー')
    
    async def start_server(self):
        """サーバー起動"""
        print("="*70)
        print("  🎨 Gemini OCR Studio - WebSocket Server")
        print("="*70)
        print()
        print("  WebSocket: ws://localhost:8765")
        print("  UI: ocr_ui.html をブラウザで開いてください")
        print()
        print("  Ctrl+C で終了")
        print("="*70)
        print()
        
        async with websockets.serve(self.handle_client, "localhost", 8765):
            await asyncio.Future()  # 永続実行


if __name__ == "__main__":
    server = OCRWebSocketServer()
    asyncio.run(server.start_server())
