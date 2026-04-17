# Claude Opus 4.7 on Amazon Bedrock GA: 次世代推論エンジン＋ゼロオペレータデータアクセス

- URL: https://aws.amazon.com/blogs/aws/introducing-anthropics-claude-opus-4-7-model-in-amazon-bedrock/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-17

## 要約
AWSが2026年4月16日にClaude Opus 4.7をAmazon Bedrockで一般提供開始。技術的特徴：(1)次世代推論エンジンによる高スループット・低レイテンシでのエンタープライズグレードスケーラビリティ；(2)ゼロオペレータデータアクセス—顧客のプロンプト・レスポンスはAnthropic/AWSオペレーターから不可視；(3)1Mトークンコンテキスト＋最大128K出力；(4)2026年1月ナレッジカットオフ。パフォーマンス：SWE-bench Verified 87.6%（Opus 4.6比+6.8pt）、長時間自律タスクでの精度向上が顕著。API移行注意点：新tokenizer採用でOpus 4.6比1.0〜1.35倍のトークン数になる破壊的変更あり（Migrating to Claude Opus 4.7 参照必須）。価格：$5/$25（入力/出力/百万トークン）で据え置き。xhigh effort・タスクバジェット（ベータ）サポート。Bedrock Guardrailsや既存のAWS IAM・VPCエンドポイント統合は継続。
