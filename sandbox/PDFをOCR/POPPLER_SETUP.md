# Poppler セットアップガイド (Windows)

## 手順

### 1. ダウンロードしたファイルを解凍
ダウンロードしたZIPファイル（例: `poppler-24.08.0.zip`）を解凍してください。

推奨場所: `C:\Program Files\poppler` または `C:\poppler`

### 2. PATHに追加

#### 方法A: 環境変数を手動で設定（推奨）

1. **Windowsキー**を押して「環境変数」と入力
2. 「システム環境変数の編集」を選択
3. 「環境変数」ボタンをクリック
4. 「システム環境変数」の「Path」を選択して「編集」
5. 「新規」をクリック
6. Popplerの`bin`フォルダのパスを追加（例: `C:\Program Files\poppler\Library\bin`）
7. 「OK」を3回クリックして閉じる
8. **PowerShellを再起動**

#### 方法B: PowerShellで一時的に設定（今回のみ）

PowerShellで以下を実行:
```powershell
# Popplerのbinフォルダのパスを設定（実際のパスに変更してください）
$env:Path += ";C:\Program Files\poppler\Library\bin"
```

### 3. 確認

PowerShellで以下を実行して、Popplerが認識されているか確認:
```powershell
pdftoppm -v
```

バージョン情報が表示されればOKです！

## トラブルシューティング

### 「pdftoppm が認識されません」と表示される場合

1. Popplerの`bin`フォルダの正確なパスを確認
2. そのフォルダに`pdftoppm.exe`があることを確認
3. PowerShellを再起動
4. 環境変数が正しく設定されているか確認

### よくあるパス例

- `C:\Program Files\poppler\Library\bin`
- `C:\poppler\Library\bin`
- `C:\Users\<ユーザー名>\Downloads\poppler-xx.xx.x\Library\bin`

## 次のステップ

Popplerの設定が完了したら、以下でPDF OCRシステムをテストできます:
```bash
python main.py --input <your_pdf_file>.pdf
```
