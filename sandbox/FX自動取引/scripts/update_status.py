"""STATUS.md を自動生成・更新するスクリプト。

データソース:
- git log: 直近7日のマージ済PR
- src/config.py: DEFAULT_INSTRUMENTS（稼働ペア）
- (任意) VPS sqlite: 取引数・postmortem率
- (任意) VPS process: Python PID・起動時刻
- (任意) VPS file: trading.log サイズ

使い方:
    python scripts/update_status.py                # ローカル分のみ更新
    python scripts/update_status.py --with-vps    # VPS データも取得（ssh 必要）
    python scripts/update_status.py --dry-run     # 出力プレビューのみ

VPS データ取得には `ssh vps` が事前設定されている必要あり。

注意:
- 手動でメンテしている課題リストは保持する（テンプレートで上書きしない）
- 「観察中の課題」「振り返り起点リンク」「メンテナンス方針」セクションは
  既存ファイルから引き継ぐ（ない場合のみテンプレートを書く）
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_PATH = PROJECT_ROOT / "STATUS.md"
CONFIG_PATH = PROJECT_ROOT / "src" / "config.py"


# ============================================================
# データ収集
# ============================================================


def get_recent_prs(days: int = 7) -> list[dict]:
    """直近 N 日のmainマージ PR を git log から取得する。"""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    cmd = [
        "git", "log", "--oneline", "--first-parent", "main",
        f"--since={since}",
    ]
    try:
        result = subprocess.run(
            cmd, cwd=PROJECT_ROOT, capture_output=True, text=True,
            check=True, encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        print(f"git log失敗: {e}", file=sys.stderr)
        return []

    prs = []
    for line in result.stdout.strip().splitlines():
        # "<sha> <title> (#NN)" の形式から PR# 抽出
        match = re.match(r"^([0-9a-f]+)\s+(.+?)\s+\(#(\d+)\)\s*$", line)
        if match:
            sha, title, pr_num = match.groups()
            prs.append({"sha": sha, "title": title, "pr": pr_num})
    return prs


def get_default_instruments() -> list[str]:
    """src/config.py から DEFAULT_INSTRUMENTS を抽出する。"""
    text = CONFIG_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"DEFAULT_INSTRUMENTS:\s*list\[str\]\s*=\s*\[([^\]]+)\]",
        text,
    )
    if not match:
        return []
    items = re.findall(r'"([^"]+)"', match.group(1))
    return items


def get_vps_python_status() -> dict | None:
    """ssh vps で Python プロセス情報を取得する（任意）。

    Windowsの ssh + リモート cmd.exe 経由ではPowerShellパイプ `|` の引用が
    剥がれて `Select-Object` が cmd.exe に渡って失敗する。
    `-EncodedCommand` (Base64 UTF-16LE) を使えばクオート/パイプ/$ 全て無害化される。
    """
    import base64
    ps_cmd = (
        "Get-Process python -ErrorAction SilentlyContinue "
        "| Select-Object Id, StartTime, WorkingSet64 "
        "| ConvertTo-Json -Compress"
    )
    encoded = base64.b64encode(ps_cmd.encode("utf-16-le")).decode("ascii")
    cmd = ["ssh", "vps", "powershell", "-EncodedCommand", encoded]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        import json
        data = json.loads(result.stdout.strip())
        if isinstance(data, list):
            data = data[0] if data else None
        if data and "WorkingSet64" in data:
            data["RAMmb"] = int(data["WorkingSet64"] / 1024 / 1024)
        return data
    except Exception as e:
        print(f"VPS Python取得失敗: {e}", file=sys.stderr)
        return None


def get_vps_db_stats() -> dict:
    """ssh vps で取引DB統計を取得する（任意）。失敗時は空dict。

    Python ワンライナーをPowerShell `-EncodedCommand` 経由で実行することで、
    クオート・パイプ・日本語パス全てを安全に渡す。
    """
    import base64
    # PowerShell 内で python -c "..." を実行する形にする。
    # 日本語パスを含むため UTF-16LE エンコードが安全。
    pyscript = (
        "import sqlite3,json;"
        r"c=sqlite3.connect(r'C:\bpr_lab\sandbox\FX自動取引\data\fx_trading.db');"
        "cur=c.cursor();"
        "out={};"
        "cur.execute('SELECT COUNT(*) FROM trades');out['trades']=cur.fetchone()[0];"
        "cur.execute('SELECT COUNT(*) FROM trade_postmortems');out['postmortems']=cur.fetchone()[0];"
        "cur.execute('SELECT COUNT(*) FROM kill_switch_log');out['kill_switch']=cur.fetchone()[0];"
        "print(json.dumps(out))"
    )
    # PowerShell側で python.exe -c を呼ぶラッパー。シングルクオートで囲み、PowerShellに引数として渡す
    ps_wrapper = f"python -c '{pyscript}'"
    encoded = base64.b64encode(ps_wrapper.encode("utf-16-le")).decode("ascii")
    cmd = ["ssh", "vps", "powershell", "-EncodedCommand", encoded]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        import json
        return json.loads(result.stdout.strip())
    except Exception as e:
        print(f"VPS DB stats取得失敗: {e}", file=sys.stderr)
        return {}


# ============================================================
# セクション生成
# ============================================================


def render_meta(next_update_days: int = 7) -> str:
    now = datetime.now(timezone(timedelta(hours=9)))
    next_update = now + timedelta(days=next_update_days)
    return (
        "| メタ | 値 |\n"
        "|---|---|\n"
        f"| **最終更新** | {now.strftime('%Y-%m-%d %H:%M JST')} |\n"
        f"| **次回更新予定** | {next_update.strftime('%Y-%m-%d')}（{next_update_days}日後）または重要変更時 |\n"
        "| **更新方法** | `python scripts/update_status.py [--with-vps]` / 手動編集（緊急時） |\n"
    )


def render_runtime(instruments: list[str], vps_python: dict | None) -> str:
    inst_str = " / ".join(instruments) if instruments else "(未設定)"
    if vps_python:
        pid = vps_python.get("Id", "?")
        ram = vps_python.get("RAMmb", "?")
        start_raw = vps_python.get("StartTime", "?")
        # PowerShell ConvertTo-Json の "/Date(NNN)/" 形式を JST に変換
        start_str = start_raw
        if isinstance(start_raw, str) and start_raw.startswith("/Date("):
            try:
                ms = int(re.search(r"/Date\((\d+)\)/", start_raw).group(1))
                dt_jst = datetime.fromtimestamp(
                    ms / 1000, tz=timezone(timedelta(hours=9))
                )
                start_str = dt_jst.strftime("%Y-%m-%d %H:%M JST")
            except Exception:
                pass
        process_line = f"PID {pid}、起動 {start_str}、RAM {ram}MB"
    else:
        process_line = "(VPS未取得 — `--with-vps` で取得)"
    return (
        "| 項目 | 値 |\n"
        "|---|---|\n"
        "| **本番VPS** | ConoHa Windows Server (160.251.221.43) |\n"
        f"| **Pythonプロセス** | {process_line} |\n"
        f"| **稼働ペア** | {inst_str} |\n"
        "| **timeframe** | M15、60秒間隔ループ |\n"
        "| **ブローカー** | 外為ファイネスト MT5 デモ口座 |\n"
    )


def render_stats(db: dict) -> str:
    if not db:
        return "(VPS DB未取得 — `--with-vps` で取得。手動更新時は前回値を保持)\n"
    return (
        "| 項目 | 値 |\n"
        "|---|---|\n"
        f"| **総取引数** | {db.get('trades', '?')} |\n"
        f"| **postmortem 件数** | {db.get('postmortems', '?')} |\n"
        f"| **kill_switch ログ** | {db.get('kill_switch', '?')} |\n"
    )


def render_recent_prs(prs: list[dict]) -> str:
    if not prs:
        return "(直近7日にmainマージなし)\n"
    lines = ["| PR | タイトル |", "|---|---|"]
    for p in prs[:15]:
        # mainマージは常に "(#NN)" suffix を持つはず
        lines.append(f"| **#{p['pr']}** | {p['title']} |")
    return "\n".join(lines) + "\n"


# ============================================================
# 既存セクション保持（手動メンテ部分）
# ============================================================


PRESERVE_HEADERS = (
    "## ⚠️ 観察中の課題",
    "## 🚪 振り返り起点リンク",
    "## 📝 メンテナンス",
)


def extract_preserved_sections(existing: str) -> dict[str, str]:
    """既存 STATUS.md から手動メンテ部分のセクションを抽出する。"""
    if not existing:
        return {}
    sections: dict[str, str] = {}
    for header in PRESERVE_HEADERS:
        # 該当ヘッダから次の `## ` または末尾まで
        pattern = re.escape(header) + r".*?(?=\n## |\Z)"
        match = re.search(pattern, existing, re.DOTALL)
        if match:
            sections[header] = match.group(0).rstrip() + "\n"
    return sections


def default_section(header: str) -> str:
    """既存ファイルになかった場合のテンプレートデフォルト。"""
    if header == "## ⚠️ 観察中の課題":
        return (
            "## ⚠️ 観察中の課題（高優先度のみ）\n\n"
            "(自動取得対象外。`memory/project_fx_pending_items.md` から手動転記)\n"
        )
    if header == "## 🚪 振り返り起点リンク":
        return (
            "## 🚪 振り返り起点リンク\n\n"
            "| 用途 | リンク |\n"
            "|---|---|\n"
            "| ドキュメント全体マップ | `docs/INDEX.md` |\n"
            "| コード全体マップ | `src/INDEX.md` |\n"
            "| メモリインデックス | `~/.claude/projects/.../memory/MEMORY.md` |\n"
            "| 未対応リスト | `memory/project_fx_pending_items.md` |\n"
            "| GitHub | https://github.com/takuzokb05/bpr_lab |\n"
        )
    if header == "## 📝 メンテナンス":
        return (
            "## 📝 メンテナンス\n\n"
            "### 更新トリガー\n"
            "- 週次: `python scripts/update_status.py --with-vps`\n"
            "- 大きなPRマージ時 / 構成変更時: 手動更新\n\n"
            "### stale警告\n"
            "最終更新から **14日経過** したら、AIは「STATUS.md が stale」と警告する。\n"
        )
    return ""


# ============================================================
# 統合
# ============================================================


def build_status(with_vps: bool) -> str:
    instruments = get_default_instruments()
    prs = get_recent_prs(days=7)
    vps_python = get_vps_python_status() if with_vps else None
    db = get_vps_db_stats() if with_vps else {}

    existing = STATUS_PATH.read_text(encoding="utf-8") if STATUS_PATH.exists() else ""
    preserved = extract_preserved_sections(existing)

    parts = [
        "# STATUS — FX自動取引 運用ダッシュボード\n",
        "> **「いま」のスナップショット。** ふわっと指示を受けたAI/未来の自分が**最初に見る**ファイル。\n"
        "> 過去判断や根拠は `docs/INDEX.md` / `memory/MEMORY.md` / git log を参照。\n",
        render_meta(),
        "---\n",
        "## 🟢 いま稼働中の構成\n",
        render_runtime(instruments, vps_python),
        "---\n",
        "## 📊 最新 statistics\n",
        render_stats(db),
        "---\n",
        "## 🔄 直近7日のマージ済PR\n",
        render_recent_prs(prs),
        "完全な履歴: `git log --oneline --since=\"7 days ago\"`\n",
        preserved.get("## ⚠️ 観察中の課題", default_section("## ⚠️ 観察中の課題")),
        preserved.get("## 🚪 振り返り起点リンク", default_section("## 🚪 振り返り起点リンク")),
        preserved.get("## 📝 メンテナンス", default_section("## 📝 メンテナンス")),
    ]
    return "\n".join(parts)


def main() -> int:
    # Windows console の cp932 で em dash 等が出力できない問題を回避
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="STATUS.md 自動更新")
    parser.add_argument(
        "--with-vps", action="store_true",
        help="VPS データ（プロセス・DB統計）も ssh 経由で取得",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="STATUS.md に書かず標準出力にプレビュー",
    )
    args = parser.parse_args()

    content = build_status(with_vps=args.with_vps)

    if args.dry_run:
        print(content)
        return 0

    STATUS_PATH.write_text(content, encoding="utf-8")
    print(f"OK: {STATUS_PATH} を更新しました ({len(content)} 文字)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
