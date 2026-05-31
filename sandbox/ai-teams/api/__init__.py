"""AI Teams v3 — HTTP API（FastAPI + SSE）。

core エンジンは UI 非依存なので、`council.run()` の yield を Server-Sent Events で
そのまま流すだけで「途中経過が見える」ストリーミング討論になる（v2 の積年のバグを構造的に解消）。
"""
