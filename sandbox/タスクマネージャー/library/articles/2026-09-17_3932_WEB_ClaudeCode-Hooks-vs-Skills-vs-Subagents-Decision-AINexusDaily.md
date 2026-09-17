# Claude Code Hooks vs Skills vs Subagents: Three Ways to Extend and When Each Backfires

- URL: https://ainexusdaily.vercel.app/article/2026-09-13-claude-code-hooks-vs-skills-vs-subagents-three-ways-to-extend-the-agent-and-when
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-17

## 要約
2026年9月13日公開。Claude Codeの3大拡張メカニズムを判断軸付きで徹底比較した実践記事。

**核心フレーム**: 「Hooks はモデルから決定を取り除く、Skills は決定を追加する、Subagents は決定を隔離する」

**Hooks**（決定論的）: PreToolUse/Stop等のライフサイクルイベントで必ず発火。「必ず起こること」に使用（常にリンターを走らせる、.envファイルへのアクセスをブロックする等）。落とし穴: exit code 2 の誤用で無限ループ。

**Skills**（確率的）: セッション開始時に説明文のみロード（数十トークン）し、関連性をモデルが判断して呼び出し。コードレビューやリリースノート草案等のオプションワークフローに最適。落とし穴: 説明文の肥大化が全ターンを圧迫し誤ルーティングを招く。

**Subagents**（隔離実行）: 独自コンテキストウィンドウを持つ分離実行、最終サマリーのみ返却。コードベース横断検索やログ分析に最適。落とし穴: タスク途中でのフォローアップ質問不可、サマリーで詳細が失われる。約2万トークンのオーバーヘッド。

**最大の信頼性ミス**: 「always（常に）」要件を「when relevant（関連する場合）」として実装すること。両者は実行時に正反対の挙動をする。

拡張メカニズム選択の優先順序: 強制→Hooks、contextual知識→Skills、委譲境界→Subagents、常時稼働プロジェクト指針→CLAUDE.md（短く）。
