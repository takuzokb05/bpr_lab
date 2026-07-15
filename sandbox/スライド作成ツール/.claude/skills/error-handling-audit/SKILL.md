---
name: error-handling-audit
description: エラーハンドリングの監査・改善（6カテゴリ監査 + 改善パターン集）
---

# Error Handling Audit - エラーハンドリング監査

## 概要

既存コードのエラーハンドリングを6つのカテゴリで体系的に監査し、重大度分類と改善パターンを用いて具体的な修正計画を提示するスキル。

**対象**: Python, JavaScript/TypeScript, その他主要言語のプロジェクト
**キーワード**: エラーハンドリング, 例外処理, 信頼性, 監査, リカバリー

## 監査チェックリスト

### カテゴリ1: 例外の握りつぶし（Silent Failures）

意図せず例外が無視されているケースを検出する。

- [ ] 空の `except` / `catch` ブロック
- [ ] `pass` のみの例外ハンドラ
- [ ] ログも通知もなく例外を握りつぶしている箇所
- [ ] 広すぎる例外キャッチ（`except Exception` / `catch(e)`）
- [ ] 戻り値で `None` / `null` を返して失敗を隠蔽

```python
# 問題: 握りつぶし
try:
    result = api_call()
except Exception:
    pass  # 何が起きたか分からない

# 改善: 適切なログ + リカバリー
try:
    result = api_call()
except requests.Timeout:
    logger.warning("API呼び出しタイムアウト、リトライします")
    result = api_call_with_retry()
except requests.RequestException as e:
    logger.error(f"API呼び出し失敗: {e}")
    raise
```

### カテゴリ2: 不適切な例外粒度（Wrong Granularity）

例外の種類を区別せず一括処理しているケースを検出する。

- [ ] 複数の異なる例外を同じハンドラで処理
- [ ] ビジネスロジックエラーとシステムエラーの混同
- [ ] HTTP ステータスコードの不適切なマッピング
- [ ] カスタム例外クラスの不足

### カテゴリ3: ユーザー通知不足（Poor User Feedback）

エラー発生時にユーザーに適切な情報が伝わらないケースを検出する。

- [ ] 技術的なエラーメッセージがそのままユーザーに表示される
- [ ] エラー時にUIが無反応（ローディング状態のまま等）
- [ ] 「エラーが発生しました」のみで原因や対処法がない
- [ ] エラー後の復帰方法が示されない

### カテゴリ4: リソースリーク（Resource Leaks）

エラー発生時にリソースが適切に解放されないケースを検出する。

- [ ] `try` 内でオープンしたファイル/接続が `finally` で閉じられない
- [ ] コンテキストマネージャ（`with` / `using`）の未使用
- [ ] DB トランザクションの未ロールバック
- [ ] 一時ファイルの未削除
- [ ] イベントリスナー / タイマーの未解除

```python
# 問題: リソースリーク
def process_file(path):
    f = open(path)
    data = json.load(f)  # ここで例外→ファイル閉じられない
    f.close()
    return data

# 改善: with文で確実にクローズ
def process_file(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)
```

### カテゴリ5: リカバリー戦略の不在（No Recovery Strategy）

エラー発生後のリカバリーが考慮されていないケースを検出する。

- [ ] リトライ機構のない外部API呼び出し
- [ ] フォールバック値 / デフォルト値の未定義
- [ ] 部分的な失敗時のロールバック未実装
- [ ] グレースフルデグラデーションの欠如

### カテゴリ6: セキュリティ上のエラー処理問題（Security Issues）

エラー処理がセキュリティリスクになっているケースを検出する。

- [ ] スタックトレースの外部公開
- [ ] エラーメッセージに内部パス / DB構造 / APIキーが含まれる
- [ ] エラー時の認証バイパス（例外で認証チェックがスキップされる）
- [ ] エラーレート制限の欠如（ブルートフォース対策）

## 改善パターン集

### パターン1: APIリトライ
```python
import time

def api_call_with_retry(func, max_retries=3, base_delay=1.0):
    """指数バックオフ付きリトライ"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.Timeout:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

### パターン2: トランザクション管理
```python
def update_records(db, records):
    """トランザクション付きDB更新"""
    try:
        db.execute("BEGIN")
        for record in records:
            db.execute("UPDATE ...", record)
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
```

### パターン3: エラーメッセージ変換
```python
# 内部エラー → ユーザー向けメッセージの変換マップ
ERROR_MESSAGES = {
    "ConnectionError": "サーバーに接続できません。ネットワーク接続を確認してください。",
    "TimeoutError": "処理に時間がかかっています。しばらく待ってから再度お試しください。",
    "ValidationError": "入力内容に問題があります。{details}",
}

def get_user_message(error):
    error_type = type(error).__name__
    template = ERROR_MESSAGES.get(error_type, "予期しないエラーが発生しました。")
    return template.format(details=str(error)) if "{details}" in template else template
```

### パターン4: 構造化ログ
```python
import logging

logger = logging.getLogger(__name__)

def safe_operation(data):
    try:
        result = process(data)
        return result
    except ValueError as e:
        logger.warning("入力データ不正", extra={
            "error_type": "validation",
            "input_summary": str(data)[:100],
            "detail": str(e),
        })
        raise
    except Exception as e:
        logger.error("予期しないエラー", extra={
            "error_type": "unexpected",
            "detail": str(e),
        }, exc_info=True)
        raise
```

## ルール

1. **全6カテゴリをチェック** - 部分的な監査はしない。全カテゴリを走査した上で該当なしのカテゴリも報告する
2. **重大度を付ける** - 各指摘にCritical/High/Medium/Lowの重大度を付与する
3. **改善パターンを引用** - 指摘には上記パターン集または同等の具体的修正例を添える
4. **既存の良い実装を壊さない** - 適切にエラー処理されている箇所はそのまま維持。過剰な修正提案をしない
5. **プロジェクトの文脈を考慮** - プロトタイプと本番コードでは求められるレベルが異なる

## 出力フォーマット

```markdown
# エラーハンドリング監査レポート

## 監査対象
- ファイル: (対象一覧)
- プロジェクト種別: (本番 / プロトタイプ / PoC)

## 監査結果サマリー

| カテゴリ | 件数 | Critical | High | Medium | Low |
|----------|------|----------|------|--------|-----|
| 1. 握りつぶし | 3 | 1 | 2 | 0 | 0 |
| 2. 不適切な粒度 | 1 | 0 | 0 | 1 | 0 |
| 3. ユーザー通知不足 | 2 | 0 | 1 | 1 | 0 |
| 4. リソースリーク | 0 | - | - | - | - |
| 5. リカバリー不在 | 2 | 0 | 2 | 0 | 0 |
| 6. セキュリティ | 1 | 1 | 0 | 0 | 0 |

## 指摘詳細

### [Critical] カテゴリ1: APIエラーの握りつぶし
- **場所**: `api_client.py:58`
- **問題**: requests例外をcatchして `return None` しており、呼び出し元がエラーを検知できない
- **改善**: パターン1（APIリトライ）を適用
- **修正例**:
  ```python
  (修正コード)
  ```

...

## 改善計画（優先順）
1. [Critical] (即座に対応)
2. [High] (今週中に対応)
3. [Medium] (次スプリントで対応)
```

## 使用例

### ケース1: リリース前監査
```
ユーザー: リリース前にエラー処理を点検したい

→ 主要ファイルを全6カテゴリで走査
→ Critical/High を重点的に報告
→ リリースブロッカーとなる項目を明示
```

### ケース2: 障害後の原因分析
```
ユーザー: 本番で例外が握りつぶされてて障害になった。他にも同じ問題がないか調べたい

→ カテゴリ1（握りつぶし）を重点的に全ファイル走査
→ 同パターンの問題を洗い出し
→ 改善パターンを適用した修正PRを提案
```

## 注意事項

- 監査対象が大きい場合は、ディレクトリ単位で分割して実施する
- カテゴリ6（セキュリティ）の指摘は公開PRのコメントに書かず、別途報告する
- 「全部直す」より「Critical→High→Medium」の優先順で段階的に改善する
- プロトタイプ段階のコードにCritical以外の過度な指摘は控える
