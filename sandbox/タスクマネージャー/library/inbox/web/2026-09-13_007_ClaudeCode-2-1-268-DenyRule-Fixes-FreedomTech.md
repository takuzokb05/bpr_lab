# Claude Code 2.1.268: Deny-Rule Bypass Fixes and WebFetch Timeout

- URL: https://freedom.tech/posts/2026-09-10-claude-code-2-1-268/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-13

## 要約
Claude Code 2.1.268 (September 10, 2026) fixes two critical security issues: (1) deny rules starting with ! were leaking scope beyond their settings source, and (2) Edit/Write/Read deny rules on symlinked directories weren't applying when using real (non-symlink) paths. Additionally: /mcp and claude mcp list no longer print secrets resolved from ${VAR} placeholders—preventing accidental secret exposure in output. WebFetch now enforces a 300-second timeout (overridable via CLAUDE_CODE_WEBFETCH_DEADLINE_MS). CPU pinning in idle sessions is fixed. These are security-relevant fixes for anyone using deny rules in CLAUDE.md or settings.json.
