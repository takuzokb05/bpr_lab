# Claude Managed Agents: Dreaming, Outcomes, Multi-Agent Orchestration Explained

- URL: https://www.developersdigest.tech/blog/claude-managed-agents-dreaming-outcomes-multi-agent
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-07

## 投稿内容
Detailed explanation of Anthropic's May 6, 2026 release: three new capabilities — Dreaming (research preview), Outcomes (public beta), and Multi-Agent Orchestration (public beta). Claude Agent SDK (TypeScript/Python) lets developers define agents as code, with Anthropic managing the loop: model call, tool dispatch, context compaction, retries. Orchestrator agent breaks down tasks, routes subtasks to specialist agents, synthesizes results. Agents act in parallel in isolated contexts. Three orchestration approaches: subagents within single session, built-in Agent Teams (one "team lead" coordinating via shared task list, teammates in own context windows), external orchestrators across repos. Dreaming enables offline background research; Outcomes tracks agent goal completion metrics.

## 要約
Anthropicが2026年5月6日に発表した3大新機能の詳細解説。①Dreaming（研究プレビュー）: オフライン中のバックグラウンド調査実行、②Outcomes（パブリックベータ）: エージェントの目標達成率をトラッキングするメトリクス基盤、③Multi-Agent Orchestration（パブリックベータ）: 複数エージェントの協調実行フレームワーク。Claude Agent SDK（TS/Python）でエージェントをコード定義し、Anthropic側がモデル呼び出し・ツールディスパッチ・コンテキスト圧縮・リトライを管理。オーケストレーション方式は3種: 単一セッション内サブエージェント、Agent Teams（リードエージェント+並列チームメイト）、外部オーケストレーター（複数リポジトリ横断）。Claude Codeを超えた自律エージェント構築への公式経路として重要な一次情報。
