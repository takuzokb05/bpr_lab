# VPSセットアップ引き継ぎ書

## 目的
ConoHa Windows Server にFX自動取引システムをデプロイし、スマホ（Telegram Bot）のみで運用可能にする。

## VPS情報
- **IP**: 160.251.221.43
- **ユーザー**: Administrator
- **パスワード**: `.env` の `VPS_PASSWORD` を参照
- **プラン**: メモリ2GB / CPU 3Core / SSD 100GB
- **OS**: Windows Server（ConoHa Windows Server）

## 完了済み
- [x] ConoHa Windows Server 契約・起動
- [x] OpenSSH Server インストール・起動・自動起動設定済み
- [x] Windowsファイアウォール ポート22開放済み
- [x] ConoHaセキュリティグループ: IPv4v6-RDP + IPv4v6-SSH 追加済み
- [x] SSH接続確認（VPS内部から: `Get-Service sshd` = Running, `:22` LISTENING）
- [x] Telegram Bot 実装済み・動作確認済み（ローカルPC）
- [x] デプロイガイド作成済み: `docs/vps_deployment_guide.md`
- [x] 自動起動スクリプト作成済み: `scripts/start_trading.bat`, `scripts/stop_trading.bat`

## 未完了（これをやる）

### Step 1: SSH接続テスト
```bash
ssh -o StrictHostKeyChecking=no Administrator@160.251.221.43 "hostname"
```
パスワードを聞かれたら `.env` の `VPS_PASSWORD` の値を入力。

> **注意**: VSCode版Claudeではネットワーク制限でポート22に到達できなかった。CLI版で再試行。

### Step 2: Pythonインストール
```powershell
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"
Start-Process -Wait -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"
python --version
```

### Step 3: プロジェクトファイル転送
ローカルからVPSへSCP:
```bash
scp -r "c:/Users/takuz/プロジェクト/bpr_lab/sandbox/FX自動取引" Administrator@160.251.221.43:"C:/Users/Administrator/FX自動取引"
```
転送対象: `src/`, `tests/`, `scripts/`, `docs/`, `main.py`, `requirements.txt`, `.env.example`
**除外**: `.env`（VPS側で別途作成）、`data/`、`venv/`、`__pycache__`

### Step 4: VPS上で環境構築
```cmd
cd C:\Users\Administrator\FX自動取引
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 5: .env作成
```cmd
copy .env.example .env
notepad .env
```
設定値:
```
TELEGRAM_BOT_TOKEN=（.envから取得）
TELEGRAM_CHAT_ID=（.envから取得）
```

### Step 6: MetaTrader 5 インストール
- https://www.metatrader5.com/ja/download からダウンロード・インストール
- デモ口座ログイン: サーバー `GaitameFinest-Demo`, 口座 `22005467`
- **MT5は常時起動が必要**（最小化OK）

### Step 7: 動作確認
```cmd
cd C:\Users\Administrator\FX自動取引
venv\Scripts\activate
python main.py --dry-run
```
6ペア全てOKが出れば成功。

### Step 8: 自動起動設定
- `scripts/start_trading.bat` をタスクスケジューラに登録
- MT5をスタートアップフォルダに追加
- 詳細: `docs/vps_deployment_guide.md` のセクション3参照

## ファイル構成（主要）
```
FX自動取引/
├── main.py                 ← エントリポイント
├── src/
│   ├── mt5_client.py       ← MT5 API接続
│   ├── config.py           ← 設定（env読み込み含む）
│   ├── telegram_notifier.py← Telegram Bot（通知・コマンド）
│   ├── risk_manager.py     ← リスク管理・キルスイッチ
│   ├── position_manager.py ← ポジション管理
│   ├── trading_loop.py     ← トレーディングループ
│   └── strategy/
│       └── ma_crossover.py ← MA+RSI+ADX戦略
├── scripts/
│   ├── start_trading.bat   ← 自動起動用
│   └── stop_trading.bat    ← 停止用
├── .env                    ← 秘匿情報（Git除外）
├── .env.example            ← テンプレート
└── requirements.txt        ← 依存パッケージ
```

## SSH接続できない場合の代替手段
RDPで接続し、PowerShellで手動実行。手順は `docs/vps_deployment_guide.md` に記載。
