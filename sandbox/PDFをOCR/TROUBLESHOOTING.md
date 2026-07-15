# Gemini OCR Studio - トラブルシューティングガイド

## 問題: PDFアップロード後に処理が進まない

### 症状
- PDFファイルをアップロードした
- ログに「PDFファイル: xxx.pdf」と表示される
- その後、何も起きない（2分以上経過）

### 原因
1. **大きなPDFファイル**: 48MBのような大きなファイルは変換に時間がかかる
2. **Popplerの問題**: PDF→画像変換ツールが正しく動作していない
3. **メモリ不足**: 大きなPDFの変換にメモリが足りない

### 解決方法

#### 1. サーバーログを確認

サーバーのターミナルを確認してください。エラーメッセージが表示されているはずです。

#### 2. Popplerの確認

```powershell
python find_poppler.py
```

Popplerが見つからない場合:
```powershell
# POPPLER_SETUP.md の手順に従ってインストール
```

#### 3. 小さなPDFでテスト

まず小さなPDF (1-2MB) でテストしてください:
```powershell
# 小さなPDFファイルをアップロード
# 正常に動作するか確認
```

#### 4. コマンドラインで直接変換

WebUIを使わず、コマンドラインで変換してみる:
```powershell
python main.py --input "イシューから始めよ.pdf"
```

エラーメッセージが表示されれば、それが原因です。

#### 5. DPI設定を下げる

`config.yaml` を編集:
```yaml
processing:
  dpi: 150  # 300から150に下げる
```

これで画像サイズが小さくなり、処理が速くなります。

## 問題: WebSocket接続が切断される

### 症状
```
[23:02:53] WARN WebSocket接続切断
```

### 原因
- 大きなファイルの処理中にタイムアウト
- サーバーがクラッシュ

### 解決方法

#### 1. サーバーを再起動

```powershell
# Ctrl+C でサーバーを停止
.\start_server.bat
```

#### 2. ブラウザをリロード

F5キーでページをリロードしてください。

## 問題: 「保存された状態が見つかりません」エラー

### 解決方法

最初にコマンドラインでPDFを変換:
```powershell
python main.py --input "your_file.pdf"
```

その後、UIから再開できます。

## デバッグモード

詳細なログを見るには、`ocr_server.py` を直接実行:
```powershell
python ocr_server.py
```

ターミナルに詳細なログが表示されます。

## よくある問題

### 1. 「Cannot find empty port in range: 7860-7860」

古い `launch_ui.bat` が実行されています。正しくは:
```powershell
.\start_server.bat  # サーバー起動
# ブラウザで ocr_ui.html を開く
```

### 2. 「ModuleNotFoundError: No module named 'websockets'」

```powershell
pip install websockets
```

### 3. PDFが大きすぎる

- 500MB以上のPDFは処理できません
- PDFを分割してください

## サポート

それでも解決しない場合:
1. サーバーのターミナル出力をコピー
2. ブラウザのコンソール (F12) のエラーをコピー
3. 両方を報告してください
