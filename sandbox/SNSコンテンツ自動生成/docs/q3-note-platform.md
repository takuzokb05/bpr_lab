## Q3: Note プラットフォームのデータ取得方法

### 主要な発見

1. **公式APIは存在しない**
   - noteは公式にAPIを公開しておらず、今後の公開予定も未定
   - ソース: [noteヘルプセンター — 公式API](https://www.help-note.com/hc/ja/articles/46643492548121)

2. **非公式APIが2026年2月に仕様変更で利用不可に**
   - 以前は `https://note.com/api/v2/creators/{userId}` 等で記事情報・スキ数（likeCount）・プロフィール等が取得可能だった
   - 2026年2月の仕様変更により、プログラミング経由での記事情報取得が不可能に
   - ソース: [Note非公式APIでできること整理](https://note.com/ktcrs1107/n/n3ab972786aa0)
   - ソース: [Noteの非公式APIの調べ方](https://nomad-dev-life.net/blog/2025-04-19-note-unofficial-api)
   - ソース: [2025年7月 非公式API整理](https://note.com/fuji1080/n/n0b22ae25a97b)

3. **RSSフィードは利用可能**
   - URL形式: `https://note.com/{ユーザー名}/rss`
   - マガジン別: `https://note.com/{ユーザー名}/m/{マガジンID}/rss`
   - 取得可能データ: タイトル、description（冒頭部分）、サムネイル、公開日、リンク
   - **制限**: スキ数は取得不可。本文全文は note pro のみ対応
   - ソース: [noteヘルプ — 全文RSS設定](https://www.help-note.com/hc/ja/articles/900001001246)
   - ソース: [noteのRSSフィード活用方法](https://note.com/koukichi_t/n/n15a5148cbe86)

4. **代替手段: Webスクレイピング**
   - note.comの利用規約ではスクレイピングの明示的な禁止条項は確認できていないが、過度なアクセスは問題になる可能性
   - Python + BeautifulSoup / Playwright でHTMLから記事本文・スキ数を抽出する方法
   - ただし非公式APIの変更と同様、HTML構造の変更で壊れるリスクあり

### 実用的なアプローチ（2026年2月時点）

| 方法 | 取得可能データ | スキ数 | 本文全文 | 安定性 |
|------|-------------|--------|---------|--------|
| RSS | タイトル、概要、日付、リンク | 不可 | note pro のみ | 高（公式機能） |
| Webスクレイピング | すべて | 可能 | 可能 | 低（HTML変更で壊れる） |
| 非公式API | — | — | — | **2026年2月に利用不可** |

### 推奨

- **短期**: RSS でタイトル・概要を取得 + 必要に応じてスクレイピングでスキ数・本文を補完
- **長期**: note の仕様変更リスクを考慮し、手動エクスポート（noteダッシュボードからCSV等）も検討
- **本プロジェクトへの影響**: Note記事の文体分析には本文が必要。RSS だけでは不足するため、スクレイピングか手動コピーが必要

### 情報の信頼性評価

- 一次ソース（公式）: 2件（noteヘルプセンター）
- 二次ソース（開発者ブログ・コミュニティ）: 5件
- 注意: 非公式APIの仕様変更は2026年2月報告。最新状態は要確認

### ソース一覧

1. [noteヘルプ — 公式API有無](https://www.help-note.com/hc/ja/articles/46643492548121) - 公式
2. [noteヘルプ — RSS全文配信](https://www.help-note.com/hc/ja/articles/900001001246) - 公式
3. [Noteの非公式APIの調べ方](https://nomad-dev-life.net/blog/2025-04-19-note-unofficial-api) - 開発者ブログ
4. [2025年7月 非公式API整理](https://note.com/fuji1080/n/n0b22ae25a97b) - コミュニティ
5. [Note非公式APIでできること整理](https://note.com/ktcrs1107/n/n3ab972786aa0) - コミュニティ
6. [note非公式API活用アイディア](https://note.com/manochi/n/n4f57e7ae7b9b) - コミュニティ
7. [noteのRSSフィード活用](https://note.com/koukichi_t/n/n15a5148cbe86) - コミュニティ
