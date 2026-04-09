# Claude Code 2.1.7 最新アップデート：新フックイベント・--resume改善・権限制御強化

- URL: https://www.issoh.co.jp/tech/details/10625/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-04-09

## 要約
株式会社一創によるClaude Code v2.1.7アップデートの詳解記事。主要変更点：①--resumeフローの高速化、②新フックイベント追加（TeammateIdle・TaskCompleted・PermissionDenied）、③Windows/MCP/長期セッション安定性改善、④typeahead補完とツールサマリー表示改善。PermissionDeniedフックでは{retry: true}を返すことでモデルに再試行を指示できる新機能を紹介。Auto ModeのClassifier拒否後にフックで介入できるようになったことで細かい権限制御が可能に。--resumeのキャッシュミス問題（v2.1.69以降のリグレッション）の修正についても詳述。公式CHANGELOGに基づく信頼性の高い日本語解説。
