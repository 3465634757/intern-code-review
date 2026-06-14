#!/usr/bin/env bash
# fetch-commits.sh - 拉取指定实习生本周的代码变更
#
# 用法:
#   ./scripts/fetch-commits.sh <github_id> <since_date> <repo_path> [output_dir]
#
# 示例:
#   ./scripts/fetch-commits.sh zhangsan-dev 2026-06-09 /path/to/web-app reports/2026-W24/raw

set -euo pipefail

GITHUB_ID="${1:?用法: $0 <github_id> <since_date> <repo_path> [output_dir]}"
SINCE="${2:?请指定起始日期, 如 2026-06-09}"
REPO_PATH="${3:?请指定仓库路径}"
OUTPUT_DIR="${4:-./raw-commits}"

mkdir -p "$OUTPUT_DIR"

REPO_NAME=$(basename "$REPO_PATH")
COMMITS_FILE="$OUTPUT_DIR/${REPO_NAME}-commits.txt"
DIFF_FILE="$OUTPUT_DIR/${REPO_NAME}-diff.txt"

echo "📥 正在从 $REPO_PATH 拉取 $GITHUB_ID 自 $SINCE 以来的提交..."

cd "$REPO_PATH"

# 拉取最新代码
git pull --quiet 2>/dev/null || true

# 获取提交记录
git log \
    --author="$GITHUB_ID" \
    --since="$SINCE" \
    --pretty=format:"%h|%s|%ai|%an" \
    --no-merges \
    > "$COMMITS_FILE" 2>/dev/null || true

# 获取代码变更
git log \
    --author="$GITHUB_ID" \
    --since="$SINCE" \
    --no-merges \
    -p --stat \
    > "$DIFF_FILE" 2>/dev/null || true

COMMIT_COUNT=$(wc -l < "$COMMITS_FILE" | tr -d ' ')
DIFF_SIZE=$(wc -c < "$DIFF_FILE" | tr -d ' ')

echo "  ✅ 提交记录: $COMMIT_COUNT 条 → $COMMITS_FILE"
echo "  ✅ 代码变更: $DIFF_SIZE 字节 → $DIFF_FILE"
