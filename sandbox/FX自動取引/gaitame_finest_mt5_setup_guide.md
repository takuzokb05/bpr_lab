# 外為ファイネスト + MT5 セットアップガイド

> Phase 2 準備用 — 作成日: 2026-02-14

---

## Step 1: MT5 デモ口座の開設

### 1-1. 申込みページにアクセス

URL: https://www.gaitamefinest.com/demo-account-MT5-individual

### 1-2. フォームに入力

必要な情報は以下のみ（本人確認書類は不要）:

- **名前**: アルファベットで入力（例: Takumi Yamada）
- **Eメールアドレス**: ログイン情報の送付先

### 1-3. ログイン情報を受け取る

送信後、入力したメールアドレスに **ログインID** と **パスワード** が届く。これが MT5 にログインするための認証情報になる。

### 1-4. デモ口座の仕様

| 項目 | 値 |
|------|-----|
| 仮想資金 | 100万円 |
| レバレッジ | 25倍 |
| 有効期限 | 申込日から **90日間** |
| 期限切れ後 | 再申請すれば何度でも利用可能 |
| 複数口座 | 同時利用可能 |

> **注意**: デモ口座のスプレッドやレートはライブ口座と同じ配信元だが、サーバーが異なるため約定に差が出る場合がある。Python API での接続テストやロジック検証には十分だが、実取引のパフォーマンス検証はライブ口座で行う必要がある。

---

## Step 2: MT5 のインストール（Windows）

### 2-1. ダウンロード

公式ページからインストーラーを取得:
https://www.gaitamefinest.com/how_to_use_mt5

「MT5取引システムのダウンロード」リンクをクリック。

### 2-2. インストール

1. ダウンロードした `.exe` ファイルを実行
2. インストールウィザードに従って進める
3. **「Open MQL5 Community ウェブサイト」のチェックを外す**（外為ファイネストのサービスではない）
4. インストール完了を待つ

### 2-3. 初回起動時の注意

MT5 起動直後に **「デモ口座申請」画面** が自動表示されるが、これは MT5 内蔵の汎用機能であり外為ファイネストのデモ口座とは別物。**「キャンセル」で閉じる**。

---

## Step 3: MT5 へのログイン

### 3-1. ログイン画面を開く

メニューバー → **「ファイル」** → **「取引口座にログイン」**

### 3-2. ログイン情報を入力

| 項目 | 入力値 |
|------|--------|
| ログインID | メールで届いた ID |
| パスワード | メールで届いたパスワード |
| サーバー | **`GaitameFinest-Demo`** |

> サーバー名が表示されない場合: 検索欄に `gaitamefinest` と入力 → 「会社を探す」 → 「Gaitame Finest Company Limited」を選択

### 3-3. 接続確認

ログイン成功の確認ポイント:

- 画面右下のステータスバーに **通信速度（例: 52 ms）** が表示される
- 「気配値表示」に通貨ペアのレートが流れ始める
- 「ナビゲータ」ウィンドウに口座情報が表示される

**「回線不通」「無効な口座」と表示された場合**:
- サーバー名が `GaitameFinest-Demo` になっているか確認
- ログインID・パスワードを再入力
- それでも接続できない場合、デモ口座を再申請

---

## Step 4: Python API 接続の準備（Phase 2 向け）

MT5 の Python API（`MetaTrader5` パッケージ）を使用するための前提条件:

### 4-1. 前提

- **OS**: Windows のみ（MT5 ターミナルがバックグラウンドで起動している必要がある）
- **Python**: 3.8 以上
- **MT5 ターミナル**: ログイン済みの状態で起動しておく

### 4-2. パッケージインストール

```bash
pip install MetaTrader5
```

### 4-3. 接続テスト（動作確認用）

```python
import MetaTrader5 as mt5

# MT5ターミナルに接続
if not mt5.initialize():
    print(f"initialize() failed: {mt5.last_error()}")
    quit()

# 口座情報を表示
account_info = mt5.account_info()
print(f"口座番号: {account_info.login}")
print(f"サーバー: {account_info.server}")
print(f"残高: {account_info.balance}")
print(f"通貨: {account_info.currency}")

# USDJPY のレートを取得
tick = mt5.symbol_info_tick("USDJPY")
if tick:
    print(f"USDJPY Bid: {tick.bid}, Ask: {tick.ask}")

# 切断
mt5.shutdown()
```

### 4-4. BrokerClient 実装のマッピング（Phase 1 の抽象レイヤーとの対応）

| BrokerClient メソッド | MT5 Python API |
|----------------------|----------------|
| `get_account_info()` | `mt5.account_info()` |
| `get_positions()` | `mt5.positions_get()` |
| `place_order()` | `mt5.order_send()` |
| `close_position()` | `mt5.order_send()` (close) |
| `get_candles()` | `mt5.copy_rates_from_pos()` |
| `get_tick()` | `mt5.symbol_info_tick()` |

---

## トラブルシューティング

### デモ口座が開設できない

- 毎週土曜 23:00 〜 日曜 11:00 の間にメンテナンスが入り、申請ページにアクセスできない場合がある
- 時間をおいて再試行

### MT5 にログインできない

- サーバー名を `GaitameFinest-Demo`（デモ）か `GaitameFinest-Live`（ライブ）か確認
- パスワードの大文字/小文字を確認
- ファイアウォールやプロキシでポートがブロックされていないか確認

### Python API で `initialize()` が失敗する

- MT5 ターミナルが起動してログイン済みであることを確認
- Python が 64bit 版であることを確認（32bit 版では動作しない）
- `MetaTrader5` パッケージのバージョンを確認: `pip show MetaTrader5`

### デモ口座の期限が切れた

- 90日で期限切れになるが、同じメールアドレスで何度でも再申請可能
- 再申請するとログインID・パスワードが新しく発行される

---

## チェックリスト

- [ ] 外為ファイネストの MT5 デモ口座を申込み
- [ ] メールでログインID・パスワードを受け取り
- [ ] MT5 をダウンロード・インストール
- [ ] MT5 にデモ口座でログイン（サーバー: `GaitameFinest-Demo`）
- [ ] 気配値表示でレートが流れていることを確認
- [ ] Python の `MetaTrader5` パッケージをインストール
- [ ] 接続テストスクリプトを実行して口座情報が表示されることを確認
- [ ] `mt5_client.py` の BrokerClient 実装を開始（Phase 2）
