#!/usr/bin/env python3
"""drop_fetch — drop.md の X 投稿を adhx で取得し inbox/drop-fetched/ に保存する。

クラウドセッションからは Anthropic egress プロキシで adhx.com が 403 になるため、
ネット取得工程だけを GitHub Actions（または adhx に到達できる環境）に逃がすためのスクリプト。
取得済み JSON は curate の Phase 1 がローカル読みして記事化する（ネット不要）。

使い方:
    python3 drop_fetch.py            # drop.md の未取得 X URL を adhx から取得して保存
    python3 drop_fetch.py --dry-run  # 取得はせず対象 URL の一覧だけ表示（ネット不要・検証用）

依存: 標準ライブラリのみ（Windows/Linux 両対応）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# tools/ の1つ上が「タスクマネージャー」。その下の library/inbox を使う。
BASE = Path(__file__).resolve().parent.parent
INBOX = BASE / "library" / "inbox"
DROP_MD = INBOX / "drop.md"
FETCHED_DIR = INBOX / "drop-fetched"

# x.com / twitter.com の /{user}/status/{id} を拾う（クエリ ?s=12 等は無視）
TWEET_RE = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/(\d+)",
    re.IGNORECASE,
)
ADHX_API = "https://adhx.com/api/share/tweet/{user}/{status_id}"
USER_AGENT = "Mozilla/5.0 (compatible; drop-fetch/1.0)"
TIMEOUT = 20


HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def extract_targets(text: str) -> list[tuple[str, str]]:
    """drop.md 本文から (username, status_id) の重複なしリストを返す。

    テンプレの HTML コメント（<!-- 例: ... -->）内の例 URL は除外する。
    """
    text = HTML_COMMENT_RE.sub("", text)
    seen: set[str] = set()
    targets: list[tuple[str, str]] = []
    for user, status_id in TWEET_RE.findall(text):
        if status_id in seen:
            continue
        seen.add(status_id)
        targets.append((user, status_id))
    return targets


def fetch_tweet(user: str, status_id: str) -> dict:
    url = ADHX_API.format(user=user, status_id=status_id)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="drop.md の X 投稿を adhx で取得")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="取得せず対象 URL の一覧だけ表示（ネット不要）",
    )
    args = parser.parse_args()

    if not DROP_MD.exists():
        print(f"drop.md が見つかりません: {DROP_MD}", file=sys.stderr)
        return 1

    text = DROP_MD.read_text(encoding="utf-8")
    targets = extract_targets(text)
    FETCHED_DIR.mkdir(parents=True, exist_ok=True)

    fetched = skipped = errors = 0
    for user, status_id in targets:
        out = FETCHED_DIR / f"{status_id}.json"
        if out.exists():
            skipped += 1
            continue
        if args.dry_run:
            print(f"[would fetch] @{user} / {status_id}")
            continue
        try:
            data = fetch_tweet(user, status_id)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            print(f"[error] @{user}/{status_id}: {e}", file=sys.stderr)
            errors += 1
            continue
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        likes = (data.get("engagement") or {}).get("likes", "?")
        print(f"[fetched] @{user}/{status_id} (likes={likes}) -> {out.name}")
        fetched += 1

    print(
        f"=== drop_fetch 完了: 対象 {len(targets)}件 / "
        f"取得 {fetched} / 既取得スキップ {skipped} / エラー {errors} ==="
    )
    # 部分失敗でジョブ全体を落とさない（ログに残す方針）
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
