# flash-study — project guide for Claude Code

A study tool for qualification exams. Text is shown one phrase at a time (RSVP "flash" reading) to hold focus, then a 4-choice "summary quiz" checks retention. NotebookLM-style: paste study material (or a PDF), AI builds the flash text and the quiz.

Full spec: see `docs/flash-study-spec.md` (import it into the repo).

## The backbone: one deck = one JSON
Everything flows through a single shape. Do not create a second source of truth.
```json
{ "id":"", "title":"", "source":"", "flashMode":"original|ai",
  "flashText":"", "quiz":[{"q":"","o":["","","",""],"a":0,"e":""}],
  "quizStatus":"ready|unset", "category":"" }
```
- AI auto-generation, work-mode JSON paste-import, and save/reuse all produce or consume this shape.
- In-browser session: keep in memory + file export/import. PWA: persist the same shape in IndexedDB.

## LLM access
- All model calls go through ONE function `callLLM(prompt, opts)` that branches by provider.
- `genQuiz()`, `reconstruct()`, `categorize()` stay provider-agnostic and call `callLLM`.
- Providers (BYOK, standalone/PWA only): Anthropic (x-api-key + version + dangerous-direct-browser-access header), OpenAI (Authorization: Bearer), Google Gemini (key as query param). Enforce JSON output where the provider supports it.
- Robust parsing: salvage complete JSON objects even if the response is truncated.

## Security (non-negotiable)
- API keys are BYOK and live ONLY in browser storage at runtime.
- Never log, print, hardcode, or commit a key. The commit hook in `.claude/scripts/check-no-secrets.sh` is a backstop, not a license to be careless.

## Product principle
Flash reading is the entry point; the quiz (active recall) is the real retention mechanism. Never trade away quiz quality for speed. The top risk is plausible-but-wrong AI quizzes — the `quiz-evaluator` agent gates this.

## Phases
- Phase 1 (done, prototype): flash UI, 4-choice quiz flow, deck JSON export/import, manual categories. (Prototype is a single HTML file: `prototype/index.html`.)
- Phase 2: PDF intake (pdf.js), work-mode JSON paste import, settings screen, AI auto-categorize.
- Phase 3: PWA build, 3-provider BYOK via callLLM, IndexedDB deck library.

## How to work here
- Plan before non-trivial edits (use the `architect` agent / plan mode).
- After code changes, run `reviewer`; after any quiz-generation change, run `quiz-evaluator`.
- Keep changes small and named clearly.
