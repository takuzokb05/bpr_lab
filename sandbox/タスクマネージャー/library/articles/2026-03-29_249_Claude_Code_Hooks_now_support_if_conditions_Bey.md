# Claude Code Hooks now support "if" conditions

- URL: https://x.com/dani_avila7/status/2037598893157032421
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 110 / RT: 5 / リプライ: 7
- 投稿者: @dani_avila7 / フォロワー 27,092

## 投稿内容

Claude Code Hooks now support "if" conditions

Beyond matching on tool_name, you can now add a second filter that runs only when a specific condition is met, same syntax you already use in your settings.json rules

"PreToolUse": [{  
     "matcher": "Bash",  
     "hooks": [{  
         "type": "command",  
         "if": "Bash(rm *)",  
         "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-rm.sh"  
       }]  
}]

This hook only fires when Claude runs a Bash command that matches rm *. Not every Bash call, just that one pattern.

Works with: PreToolUse, PostToolUse, PostToolUseFailure, and PermissionRequest

This unlocks more surgical hooks for project-specific workflows, no more hooks firing on every tool call when you only care about one

My hooks article is going to need another rewrite 😅

## 要約

（要約は次回 /curate 時に追記）
