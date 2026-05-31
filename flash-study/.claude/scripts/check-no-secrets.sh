#!/usr/bin/env bash
# Backstop: block `git commit` if staged changes look like they contain an API key.
# Starting point — tighten the patterns for your providers as needed.
# Requires git + jq. Fails OPEN (exit 0) if it cannot inspect, so it never blocks unrelated work.
INPUT="$(cat 2>/dev/null || true)"
CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"

case "$CMD" in
  *"git commit"*) : ;;
  *) exit 0 ;;
esac

STAGED="$(git diff --cached -U0 2>/dev/null || true)"
[ -z "$STAGED" ] && exit 0

# Likely key shapes: Anthropic (sk-ant-...), OpenAI (sk-...), Google (AIza...), or apiKey="<long>"
if printf '%s' "$STAGED" | grep -Eiq 'sk-ant-[a-z0-9_-]{20,}|sk-[a-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|api[_-]?key["'"'"' ]*[:=][ ]*["'"'"'][A-Za-z0-9_-]{20,}'; then
  echo "Blocked commit: a staged change looks like it contains an API key." >&2
  echo "BYOK keys must never be committed — they belong only in browser storage at runtime." >&2
  exit 2
fi
exit 0
