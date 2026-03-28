#!/bin/bash
# ============================================================
# デプロイパッケージ作成スクリプト
# VPSに転送するzipアーカイブを作成する
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/deploy"
ARCHIVE_NAME="fx_auto_trading_deploy.zip"

echo "=== デプロイパッケージ作成 ==="
echo "プロジェクト: $PROJECT_DIR"

# 出力ディレクトリ作成
mkdir -p "$OUTPUT_DIR"

# 既存のアーカイブがあれば削除
rm -f "$OUTPUT_DIR/$ARCHIVE_NAME"

# zipアーカイブ作成（除外: .env, data/, venv/, __pycache__/, .git/, .claude/, deploy/）
cd "$PROJECT_DIR"
zip -r "$OUTPUT_DIR/$ARCHIVE_NAME" . \
    -x ".env" \
    -x "data/*" \
    -x "venv/*" \
    -x ".git/*" \
    -x ".claude/*" \
    -x "deploy/*" \
    -x "*/__pycache__/*" \
    -x "__pycache__/*" \
    -x "*.pyc"

echo ""
echo "=== 完了 ==="
echo "アーカイブ: $OUTPUT_DIR/$ARCHIVE_NAME"
echo "サイズ: $(du -h "$OUTPUT_DIR/$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "次のステップ:"
echo "  1. RDPでVPSに接続"
echo "  2. $OUTPUT_DIR/$ARCHIVE_NAME をVPSにコピー"
echo "  3. scripts/vps_setup.ps1 もVPSにコピー"
echo "  4. VPS上でPowerShellを開いて vps_setup.ps1 を実行"
