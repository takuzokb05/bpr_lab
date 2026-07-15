# 🚨 BREAKING: AI coding agents hallucinate because they can't actually read your c...

- URL: https://x.com/eng_khairallah1/status/2037439420530594284
- ソース: x
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-29
- いいね: 357 / RT: 42 / リプライ: 53
- 投稿者: @eng_khairallah1 / フォロワー 17,579

## 投稿内容

🚨 BREAKING: AI coding agents hallucinate because they can't actually read your codebase. This MCP server fixes that.

It's called Context+.

Bookmark it for later.

It builds a real semantic map of your entire codebase before your AI touches a single line of code. 17 tools. 43 file extensions. Actual syntax trees, not regex.

Here's what it does that nothing else does:

→ Tree-sitter AST parsing across 43 file extensions. Real syntax trees with function signatures, class methods, and symbol ranges
→ Spectral Clustering that groups semantically related files into labeled clusters
→ Obsidian-style wikilinks that map high-level features to their corresponding code files
→ Blast radius tracing. Before any change, it shows every file and line where a symbol is imported or used
→ Semantic search by meaning. Ask what something does, not what it's called. Uses Ollama vector embeddings with disk cache
→ Identifier-level retrieval for functions, classes, and variables with ranked call sites and line numbers
→ In-memory property graph with decay scoring that tracks how your codebase actually connects

Here's the part that changes how AI writes code:

The propose_commit tool. It validates changes against strict rules, creates a shadow restore point, and only then writes to disk. If something goes wrong, one command undoes any AI change without touching your git history.

Your AI can't just freestyle your production code anymore.

Works with Claude Code, Cursor, VS Code, Windsurf, and OpenCode.

Powered by Ollama locally. No external API calls needed for embeddings.

100% Open Source. MIT License.

(Link in the comments)

## 要約

（要約は次回 /curate 時に追記）
