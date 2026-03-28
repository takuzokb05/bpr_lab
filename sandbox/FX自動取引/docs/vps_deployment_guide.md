# Windows VPS デプロイガイド

ConoHa Windows Server にFX自動取引システムをデプロイする手順。

## 前提条件

- ConoHa Windows Server 2GB プラン契約済み
- RDPクライアント（スマホ: Microsoft Remote Desktop / PC: mstsc）
- 手元に `.env` ファイルの内容を控えている

## 1. VPS初期セットアップ

### 1.1 RDP接続

```
ホスト: <ConoHaから払い出されるIPアドレス>
ユーザー: Administrator
パスワード: <契約時に設定したもの>
```

### 1.2 必要ソフトのインストール

RDPでVPSに接続後、以下を順にインストール。

#### Python 3.11+

1. https://www.python.org/downloads/ からインストーラをダウンロード
2. **「Add python.exe to PATH」にチェック** を入れてインストール
3. 確認:
```cmd
python --version
pip --version
```

#### Git

1. https://git-scm.com/download/win からインストール
2. デフォルト設定でOK
3. 確認:
```cmd
git --version
```

#### MetaTrader 5

1. https://www.metatrader5.com/ja/download からダウンロード
2. インストール後、起動
3. 外為ファイネストのデモ口座にログイン:
   - サーバー: `GaitameFinest-Demo`
   - 口座番号: `22005467`
   - パスワード: <デモ口座のパスワード>
4. **MT5は常時起動しておく**（最小化OK）

## 2. プロジェクトデプロイ

### 2.1 コード配置

```cmd
cd C:\Users\Administrator
git clone <リポジトリURL> FX自動取引
cd FX自動取引
```

> **Git未使用の場合**: ローカルPCからフォルダごとSCP/RDPファイル転送でコピーしてもOK。

### 2.2 依存パッケージインストール

```cmd
cd C:\Users\Administrator\FX自動取引
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2.3 環境変数ファイル作成

```cmd
copy .env.example .env
notepad .env
```

以下を入力して保存:
```
TELEGRAM_BOT_TOKEN=<Botトークン>
TELEGRAM_CHAT_ID=<チャットID>
```

### 2.4 動作確認

```cmd
venv\Scripts\activate
python main.py --dry-run
```

6ペア全てOKが出ればデプロイ成功。

## 3. 自動起動設定

VPS再起動後もシステムが自動で立ち上がるようにする。

### 3.1 起動スクリプト

`scripts\start_trading.bat` が用意済み。内容:
- MT5ターミナルの起動確認
- Python仮想環境のアクティベート
- main.py の実行（ログをファイル出力）

### 3.2 タスクスケジューラ登録

1. Windowsキー → 「タスク スケジューラ」を検索して開く
2. 右ペイン → 「タスクの作成」
3. 設定:

| タブ | 項目 | 値 |
|------|------|-----|
| 全般 | 名前 | `FX自動取引` |
| 全般 | 最上位の特権で実行 | チェック |
| 全般 | ユーザーがログオンしているかどうかにかかわらず実行する | 選択 |
| トリガー | タスクの開始 | スタートアップ時 |
| トリガー | 遅延時間 | 30秒 |
| 操作 | プログラム | `C:\Users\Administrator\FX自動取引\scripts\start_trading.bat` |
| 操作 | 開始 | `C:\Users\Administrator\FX自動取引` |
| 設定 | タスクを停止するまでの時間 | チェックを外す（無制限） |
| 設定 | 要求時に実行中のタスクが強制的に停止されない | チェック |

4. OK → Administratorパスワード入力

### 3.3 MT5の自動起動

MT5ターミナルもスタートアップに登録:
1. `Win + R` → `shell:startup` → Enter
2. MT5のショートカットをスタートアップフォルダにコピー

## 4. 運用

### 4.1 日常の監視（スマホのみ）

| 操作 | 方法 |
|------|------|
| ステータス確認 | Telegram: `/status` |
| ポジション確認 | Telegram: `/positions` |
| 残高確認 | Telegram: `/balance` |
| 緊急停止 | Telegram: `/stop` |
| 再開 | Telegram: `/start` |
| メンテナンス | RDPアプリでVPS接続 |

### 4.2 ログ確認

RDP接続して:
```cmd
cd C:\Users\Administrator\FX自動取引
type data\trading.log | more
```

またはTelegram Bot経由で WARNING以上のログは自動通知。

### 4.3 VPSメンテナンス

- **Windows Update**: 自動再起動で取引中断の可能性あり → アクティブ時間を設定して深夜のみ許可
- **MT5デモ口座**: 90日で期限切れ → 要更新
- **ディスク容量**: ログファイルの肥大化に注意

## 5. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| Telegramから応答なし | main.pyが停止 | RDPで接続し `start_trading.bat` を手動実行 |
| MT5接続失敗 | MT5が落ちている | RDPでMT5を再起動 |
| VPSに接続できない | VPS停止/ネットワーク障害 | ConoHaコンパネからVPS状態を確認・再起動 |
| Windows Update再起動 | 自動更新 | タスクスケジューラで自動復帰するはず |
| デモ口座期限切れ | 90日経過 | 新しいデモ口座を開設しMT5を再設定 |
