"""CLI エントリポイント"""
import argparse
import sys
from pathlib import Path

from src.config import (
    APP_NAME,
    OUTPUT_DIR,
    DEFAULT_STYLE,
    DEFAULT_COLOR_TONE,
    DEFAULT_TONE,
)
from src.gemini_client import create_client, test_connection


def build_parser() -> argparse.ArgumentParser:
    """引数パーサーを構築"""
    parser = argparse.ArgumentParser(
        prog="slide-gen",
        description=f"{APP_NAME} - ドキュメントからAIでスライドを自動生成",
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # generate コマンド
    gen = subparsers.add_parser("generate", help="スライドを生成")
    gen.add_argument("input_file", type=str, help="入力ファイル（PDF/テキスト）")
    gen.add_argument("--output", "-o", type=str, default=None, help="出力ディレクトリ")
    gen.add_argument("--style", type=str, default=DEFAULT_STYLE,
                     choices=["business", "casual", "academic"],
                     help="スタイル（デフォルト: business）")
    gen.add_argument("--color", type=str, default=DEFAULT_COLOR_TONE,
                     choices=["dark", "light", "colorful"],
                     help="色調（デフォルト: dark）")
    gen.add_argument("--tone", type=str, default=DEFAULT_TONE,
                     choices=["formal", "friendly"],
                     help="トーン（デフォルト: formal）")

    # rewrite コマンド
    rw = subparsers.add_parser("rewrite", help="特定スライドを再生成")
    rw.add_argument("session_dir", type=str, help="セッションディレクトリ")
    rw.add_argument("--slide", type=int, required=True, help="再生成するスライド番号")

    # test-connection コマンド
    subparsers.add_parser("test-connection", help="Gemini API 接続テスト")

    return parser


def cmd_test_connection() -> None:
    """API接続テストを実行"""
    print(f"[{APP_NAME}] Gemini API 接続テスト...")
    client = create_client()
    try:
        test_connection(client)
        print("接続成功！ Gemini API が利用可能です。")
    except ConnectionError as e:
        print(f"接続失敗: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_generate(args: argparse.Namespace) -> None:
    """スライド生成を実行"""
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"エラー: ファイルが見つかりません: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    taste = {
        "style": args.style,
        "color_tone": args.color,
        "tone": args.tone,
    }

    print(f"[{APP_NAME}] スライド生成を開始します")
    print(f"  入力: {input_path}")
    print(f"  出力: {output_dir}")
    print(f"  テイスト: {taste}")

    # F2〜F5 の実装後にここを繋ぎ込む
    from src.document_reader import read_document
    from src.slide_planner import generate_slide_plan
    from src.image_generator import generate_images
    from src.pptx_builder import build_pptx

    client = create_client()

    # F2: 資料読み込み
    print("\n[1/4] 資料を読み込み中...")
    doc = read_document(input_path)
    print(f"  {doc['pages']}ページ, {len(doc['text'])}文字を抽出")

    # F3: スライド構成生成
    print("\n[2/4] スライド構成を生成中...")
    plan = generate_slide_plan(client, doc["text"], taste, input_path)
    print(f"  {len(plan['slides'])}枚のスライド構成を生成")

    # F4: 背景画像生成
    print("\n[3/4] 背景画像を生成中...")
    image_paths = generate_images(client, plan, output_dir)
    print(f"  {len(image_paths)}枚の背景画像を生成")

    # F5: PPTX出力
    print("\n[4/4] PPTXを組み立て中...")
    pptx_path = build_pptx(plan, image_paths, output_dir, taste)
    print(f"\n完了！ PPTX を保存しました: {pptx_path}")


def cmd_rewrite(args: argparse.Namespace) -> None:
    """スライドリライトを実行"""
    session_dir = Path(args.session_dir)
    if not session_dir.exists():
        print(f"エラー: セッションディレクトリが見つかりません: {session_dir}", file=sys.stderr)
        sys.exit(1)
    # F6 の実装後にここを繋ぎ込む
    print(f"[{APP_NAME}] スライド #{args.slide} をリライトします（未実装）")


def main() -> None:
    """メインエントリポイント"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "test-connection":
        cmd_test_connection()
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "rewrite":
        cmd_rewrite(args)


if __name__ == "__main__":
    main()
