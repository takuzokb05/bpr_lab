# VentureBeat: Anthropic がOpenClaw・サードパーティAgentのサブスク利用を再開 — 条件付き

- URL: https://venturebeat.com/technology/anthropic-reinstates-openclaw-and-third-party-agent-usage-on-claude-subscriptions-with-a-catch
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-04

## 投稿内容
VentureBeats独立報道：Anthropicが一時停止していたOpenClaw・サードパーティAIエージェントのClaude Subscriptionでの利用を「条件付き」で再開（2026年6月初旬）。

**背景経緯**
5月中旬：「サブスク価格でAPIコストを無制限吸収できる抜け穴」を塞ぐためAnthropicがOpenClaw等の利用を一時遮断
→ ユーザーからの強い反発
→ クレジット制限付きで再開

**再開の条件**
6月15日以降の Agent SDK呼び出しは専用クレジットプールから引き落とし：
- Pro ($20/月): $20クレジット
- Max 5x ($100/月): $100クレジット  
- Max 20x ($200/月): $200クレジット
クレジットは月次リセット（繰越不可）。超過分は標準API価格（Pay-As-You-Go）で課金。

**コスト試算（MagnaCapax GitHub Gist）**
特定ワークロードでは実質12〜175倍のコスト増に相当するケースあり。

**対象**
OpenClaw、Windsurf、Cursor等のサードパーティエージェント、claude -p、Claude Code GitHub Actions。

**施行日**: 2026年6月15日（記事公開時点で11日前）

## 要約
VentureBeat独立報道：AnthropicがOpenClaw等サードパーティエージェントのサブスク利用を条件付き再開。6月15日から専用クレジットプール（Pro $20、Max 5x $100、Max 20x $200）から引き落とし。コスト試算では特定ワークロードで実質12〜175倍増のケースあり。
