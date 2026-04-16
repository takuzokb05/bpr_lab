#!/usr/bin/env python3
"""
X投稿収集スクリプト (SocialData API)
Layer 1: API検索
Layer 2: ルールフィルタ
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional

API_KEY = os.environ.get("SOCIALDATA_API_KEY", "")
BASE_URL = "https://api.socialdata.tools/twitter/search"

# ドメイン別検索クエリ定義
DOMAIN_QUERIES = {
    "claude-code": [
        '"Claude Code" -is:retweet lang:ja',
        '"Claude Code" -is:retweet lang:en',
        '"claude code" (skill OR hook OR subagent OR MCP) -is:retweet',
    ],
    "claude-ecosystem": [
        '(Anthropic OR "Claude API" OR "Agent SDK" OR "Claude Managed") -is:retweet lang:en',
        '(Anthropic OR "Claude API" OR "Agent SDK") -is:retweet lang:ja',
        '("MCP server" OR "Model Context Protocol") Anthropic -is:retweet',
    ],
    "ai-trading": [
        '(AI OR LLM OR GPT) (trading OR "algorithmic trading" OR "algo trading") -is:retweet lang:en',
        '(AI OR LLM) (MT5 OR MetaTrader OR "forex trading" OR FX自動) -is:retweet',
        'AI (トレーディング OR 自動売買 OR アルゴリズム) -is:retweet lang:ja',
    ],
    "ai-news": [
        '(AI OR LLM OR "language model") (release OR launch OR announced) -is:retweet lang:en min_faves:50',
        '(AI OR 生成AI OR LLM) (リリース OR 発表 OR 新機能) -is:retweet lang:ja min_faves:20',
    ],
}

# Layer 2: ルールフィルタ
NOISE_KEYWORDS = [
    "giveaway", "follow back", "followback", "airdrop",
    "crypto pump", "買います", "売ります", "フォロバ",
    "NFT mint", "win a", "retweet to win",
]

SIGNAL_MIN_ENGAGEMENT = {
    "claude-code": 5,
    "claude-ecosystem": 10,
    "ai-trading": 10,
    "ai-news": 20,
}


def search_tweets(query: str, days: int, max_results: int = 50) -> list:
    """SocialData API で検索実行 (Latestタイプ)"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
    }

    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    since_str = since_dt.strftime("%Y-%m-%d")
    full_query = f"{query} since:{since_str}"

    params = {
        "query": full_query,
        "type": "Latest",
    }

    tweets = []
    cursor = None
    fetched = 0

    while fetched < max_results:
        if cursor:
            params["next_cursor"] = cursor

        try:
            resp = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
            if resp.status_code == 429:
                print(f"  [rate-limit] waiting 60s...", file=sys.stderr)
                time.sleep(60)
                continue
            if resp.status_code != 200:
                print(f"  [error] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
                break

            data = resp.json()
            batch = data.get("tweets", [])
            if not batch:
                break

            tweets.extend(batch)
            fetched += len(batch)

            cursor = data.get("next_cursor")
            if not cursor:
                break

            time.sleep(1)  # rate limit courtesy

        except requests.RequestException as e:
            print(f"  [error] {e}", file=sys.stderr)
            break

    return tweets


def apply_layer2_filter(tweets: list, domain: str) -> list:
    """Layer 2: ルールベースフィルタ"""
    min_eng = SIGNAL_MIN_ENGAGEMENT.get(domain, 10)
    result = []
    for tw in tweets:
        text = (tw.get("full_text") or tw.get("text") or "").lower()

        # NOISEキーワード除外
        if any(kw.lower() in text for kw in NOISE_KEYWORDS):
            continue

        # エンゲージメント最低ライン
        likes = tw.get("favorite_count", 0) or 0
        rts = tw.get("retweet_count", 0) or 0
        eng = likes + rts
        if eng < min_eng:
            continue

        result.append(tw)
    return result


def deduplicate(tweets: list) -> list:
    """IDで重複除去"""
    seen = set()
    result = []
    for tw in tweets:
        tid = tw.get("id_str") or str(tw.get("id", ""))
        if tid and tid not in seen:
            seen.add(tid)
            result.append(tw)
    return result


def collect_domain(domain: str, days: int, output_dir: Path) -> dict:
    """1ドメインの収集実行"""
    queries = DOMAIN_QUERIES.get(domain, [])
    all_tweets = []

    print(f"\n[{domain}] 検索開始 ({len(queries)}クエリ)")
    for i, q in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] {q[:80]}...")
        tweets = search_tweets(q, days, max_results=100)
        print(f"  → {len(tweets)}件取得")
        all_tweets.extend(tweets)
        time.sleep(2)

    # 重複除去
    all_tweets = deduplicate(all_tweets)
    print(f"  重複除去後: {len(all_tweets)}件")

    # Layer 2 フィルタ
    filtered = apply_layer2_filter(all_tweets, domain)
    print(f"  Layer2フィルタ後: {len(filtered)}件")

    # 保存
    now = datetime.now(timezone.utc)
    filename = f"{now.strftime('%Y-%m-%d')}_{domain}.json"
    out_path = output_dir / filename

    payload = {
        "domain": domain,
        "collected_at": now.isoformat(),
        "days": days,
        "total_fetched": len(all_tweets),
        "total_filtered": len(filtered),
        "tweets": filtered,
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  保存: {out_path}")

    return {
        "domain": domain,
        "fetched": len(all_tweets),
        "saved": len(filtered),
        "file": str(out_path),
    }


def main():
    parser = argparse.ArgumentParser(description="X投稿収集スクリプト (SocialData API)")
    parser.add_argument("--domain", default="all",
                        help="ドメイン指定: all / claude-code / claude-ecosystem / ai-trading / ai-news")
    parser.add_argument("--days", type=int, default=1, help="収集対象日数 (default: 1)")
    parser.add_argument("--output-dir", default="library/inbox/x/", help="出力ディレクトリ")
    parser.add_argument("--json-only", action="store_true", help="JSONのみ保存 (Markdownは生成しない)")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: SOCIALDATA_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.domain == "all":
        domains = list(DOMAIN_QUERIES.keys())
    else:
        domains = [args.domain]

    results = []
    errors = []

    for domain in domains:
        try:
            r = collect_domain(domain, args.days, output_dir)
            results.append(r)
        except Exception as e:
            print(f"[ERROR] {domain}: {e}", file=sys.stderr)
            errors.append({"domain": domain, "error": str(e)})

    # サマリー出力
    print("\n=== 収集完了 ===")
    total_fetched = sum(r["fetched"] for r in results)
    total_saved = sum(r["saved"] for r in results)
    print(f"ドメイン数: {len(results)}")
    print(f"総取得: {total_fetched}件 / フィルタ後保存: {total_saved}件")
    for r in results:
        print(f"  [{r['domain']}] {r['fetched']}件取得 → {r['saved']}件保存")
    if errors:
        print(f"\nエラー ({len(errors)}件):")
        for e in errors:
            print(f"  [{e['domain']}] {e['error']}")


if __name__ == "__main__":
    main()
