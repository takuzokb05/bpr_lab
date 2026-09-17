# Claude Code Hooks vs Skills vs Subagents: Three Ways to Extend the Agent and When Each Backfires

- URL: https://ainexusdaily.vercel.app/article/2026-09-13-claude-code-hooks-vs-skills-vs-subagents-three-ways-to-extend-the-agent-and-when
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-17

## 要約
2026年9月13日公開。Claude Code の3つの拡張メカニズム（Hooks / Skills / Subagents）を判断軸付きで徹底比較。核心は「Hooks は決定をモデルから取り除く、Skills は決定を追加する、Subagents は決定を隔離する」というフレーム。Hooks はライフサイクルイベント（PreToolUse, Stop等）で必ず発火する決定論的処理に使用、exit code 2 の無限ループに注意。Skills は確率的プロシージャでモデルが関連性を判断して呼び出す（セッション開始時に数十トークンのみ）、説明文の肥大化に注意。Subagents はコンテキスト汚染を防ぐため隔離実行（約2万トークンオーバーヘッド）、フォローアップ質問ができない点に注意。「always」要件を「when relevant」として実装するのが最大の信頼性ミスと指摘。
