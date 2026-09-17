# Claude Fable 5.1 公式ドキュメント: 変更点・破壊的変更・新機能一覧

- URL: https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-17

## 要約
Claude Fable 5.1（2026-09-01 GA）の一次情報。API開発者向けの移行必須知識。

**モデルID**: claude-fable-5-1 / claude-mythos-5-1（Project Glasswing限定）
**コンテキスト**: 1Mトークン（デフォルト兼最大）、max output 128kトークン

**破壊的変更3件**:
1. **forced tool use廃止**: tool_choice: any/tool が400エラー（tool_choice: auto または strict tool useに移行）
2. **thinking blockのモデル固有化**: Fable 5.1のthinking blockは旧モデルで読み取り不可、会話履歴をまたぐモデル切り替え時に注意
3. **turn編集でthinking無効化**: 過去ターンを編集するとthinking blockが失効、append-onlyで管理が必須

**新機能5件（いずれもbeta）**:
1. ターン毎のeffort変更（mid-conversation-output-config-2026-07-01 betaヘッダー）
2. turn-scoped system messages（clear_at: next_user_message、キャッシュを温めたまま一時的指示追加）
3. ツール呼び出し間のprogress updates（thinking.display: "updates"でユーザー向けステータス行を取得）
4. cache reads 75%値下げ → $0.25/MTok（Fable 5の$1.00/MTokから）
5. content provenance（statistical text watermark + C2PA署名付きメディア）

**Fable 5からの挙動変化**（コード変更なしで発生）:
- 並列ツール呼び出し減少（1ターン1ツールになりやすい）
- progress update数減少（高effort時）
- 低effortで検索ツールを呼ばずメモリ回答が増加
- 散文が密になる（長文・段落少）
- チャットでの書式設定（太字・ヘッダー・リスト）が減少

**価格**: 入力$10/出力$50/MTok（Fable 5と同額）、cache reads $0.25/MTok（75%減）
**利用可能**: Claude API（claude-fable-5-1）、Amazon Bedrock、Google Cloud、Microsoft Foundry

**移行手順**: (1)model IDをclause-fable-5-1に更新 (2)forced tool useを削除 (3)thinking blockをappend-onlyで管理 (4)effortを再調整 (5)eval再実施
