#!/bin/bash
# VPS日次収集スクリプト
# collect_x.py を実行し、結果JSONをGitHub APIでリポジトリにpush
# cron: 0 21 * * * /root/vps_collect_and_push.sh >> /root/collect.log 2>&1

set -euo pipefail

# 環境変数読み込み
set -a
source /root/.env.collect
set +a

# 設定
REPO="takuzokb05/bpr_lab"
BRANCH="main"
WORK_DIR="/root/collect_output"
SCRIPT="/root/collect_x.py"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"

echo "${LOG_PREFIX} === 日次収集開始 ==="

# 作業ディレクトリ準備（collect_x.pyはスクリプト相対でinbox/x/に保存する）
# /root/collect_x.py → parent.parent = /root → /root/inbox/x/
INBOX_DIR="/root/inbox/x"
mkdir -p "${INBOX_DIR}"

# collect_x.py実行（JSON出力のみ、articles生成はトリガー側で実施）
echo "${LOG_PREFIX} collect_x.py 実行中..."
python3 "${SCRIPT}" --domain all --days 1 --json-only --output-dir "${INBOX_DIR}" 2>&1 | tail -30

# 生成されたJSONファイルを検索
JSON_FILES=$(find "${INBOX_DIR}" -name "x_collect_*.json" -mmin -30 2>/dev/null)

if [ -z "${JSON_FILES}" ]; then
    echo "${LOG_PREFIX} 収集結果なし。終了"
    exit 0
fi

# 各JSONファイルをGitHub APIでリポジトリにpush
for JSON_FILE in ${JSON_FILES}; do
    # URLエンコード対応
    export PYTHONIOENCODING=utf-8
    FILENAME=$(basename "${JSON_FILE}")
    # リポジトリ内のパス
    REPO_PATH="sandbox/タスクマネージャー/library/inbox/x/${FILENAME}"

    echo "${LOG_PREFIX} アップロード: ${REPO_PATH}"

    # ファイル内容をbase64エンコード
    CONTENT_B64=$(base64 -w 0 "${JSON_FILE}")

    # GitHub Contents APIでファイルを作成
    HTTP_CODE=$(curl -s -o /tmp/gh_response.json -w "%{http_code}" \
        -X PUT \
        -H "Authorization: token ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/${REPO}/contents/${REPO_PATH}" \
        -d "{
            \"message\": \"docs(library): VPS日次収集 ${FILENAME}\",
            \"content\": \"${CONTENT_B64}\",
            \"branch\": \"${BRANCH}\"
        }")

    if [ "${HTTP_CODE}" = "201" ]; then
        echo "${LOG_PREFIX} OK: ${FILENAME}"
        rm -f "${JSON_FILE}"
    else
        echo "${LOG_PREFIX} ERROR (HTTP ${HTTP_CODE}): ${FILENAME}"
        cat /tmp/gh_response.json
    fi
done

echo "${LOG_PREFIX} === 日次収集完了 ==="
