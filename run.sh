#!/usr/bin/env bash
# run.sh - 本地一键运行周度代码审查
#
# 用法:
#   ./run.sh                    # 审查所有实习生（本周）
#   ./run.sh --intern "张三"     # 只审查指定实习生
#   ./run.sh --week 2026-W24    # 指定周次
#   ./run.sh --since 2026-06-01 # 指定起始日期（自由时间段）
#   ./run.sh --since 2026-06-01 --week 2026-W24  # 指定日期+周次归档名
#   ./run.sh --dry-run          # 试运行（只收集数据，不调用AI）
#   ./run.sh --provider deepseek # 指定 AI Provider（默认 sfkey）
#
# 支持的 AI Provider（按优先级自动检测）:
#   gemini        - Google Gemini（免费，推荐）
#   sfkey         - SFKey OpenAI Compatible
#   zai           - Z.AI GLM-5.1（OpenAI 兼容）
#   deepseek      - DeepSeek（国内可用）
#   siliconflow   - 硅基流动（国内平台）
#   anthropic     - Claude（收费）
#   openai        - GPT-4o（收费）
#
# 前置条件:
#   1. pip install -r requirements.txt
#   2. 设置环境变量（任选一个）:
#      export GEMINI_API_KEY="your-key"       # 推荐
#      export ZAI_API_KEY="your-key"       # SFKey / Z.AI
#      export DEEPSEEK_API_KEY="your-key"
#      export SILICONFLOW_API_KEY="your-key"
#   3. 默认仓库父目录为 /d/qt/repos，可用 --repo-base 覆盖

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 解析参数
INTERN=""
WEEK=""
SINCE=""
DRY_RUN=""
REPO_BASE=""
PROVIDER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --intern) INTERN="$2"; shift 2 ;;
        --week) WEEK="$2"; shift 2 ;;
        --since) SINCE="$2"; shift 2 ;;
        --dry-run) DRY_RUN="--dry-run"; shift ;;
        --repo-base) REPO_BASE="$2"; shift 2 ;;
        --provider) PROVIDER="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# 确定周次
if [ -z "$WEEK" ]; then
    WEEK=$(date +%Y-W%V)
fi
echo "📅 审查周: $WEEK"

# 确定日期范围（优先使用 --since 指定的日期）
if [ -n "$SINCE" ]; then
    echo "📅 起始日期: $SINCE（手动指定）"
else
    SINCE=$(date -d "last monday" +%Y-%m-%d 2>/dev/null || date -v-monday +%Y-%m-%d 2>/dev/null || echo "")
    echo "📅 起始日期: $SINCE（自动计算）"
fi

# 创建输出目录
OUTPUT_DIR="reports/$WEEK"
mkdir -p "$OUTPUT_DIR"

# 检测可用的 AI Provider（国内无需翻墙的优先）
if [ -z "$PROVIDER" ]; then
    if [ -n "${ZAI_API_KEY:-}" ]; then
        PROVIDER="sfkey"
        echo "🤖 自动选择 Provider: SFKey OpenAI Compatible（ZAI_API_KEY）"
    elif [ -n "${DEEPSEEK_API_KEY:-}" ]; then
        PROVIDER="deepseek"
        echo "🤖 自动选择 Provider: DeepSeek（国内直连）"
    elif [ -n "${SILICONFLOW_API_KEY:-}" ]; then
        PROVIDER="siliconflow"
        echo "🤖 自动选择 Provider: SiliconFlow（国内直连）"
    elif [ -n "${GEMINI_API_KEY:-}" ]; then
        PROVIDER="gemini"
        echo "🤖 自动选择 Provider: Google Gemini"
    elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
        PROVIDER="anthropic"
        echo "🤖 自动选择 Provider: Anthropic Claude"
    elif [ -n "${OPENAI_API_KEY:-}" ]; then
        PROVIDER="openai"
        echo "🤖 自动选择 Provider: OpenAI GPT"
    else
        echo "❌ 错误: 未检测到可用的 AI API Key"
        echo ""
        echo "请设置以下任一环境变量（推荐 DeepSeek，国内直连免费）:"
        echo "  export ZAI_API_KEY=\"your-key\"           # SFKey / Z.AI"
        echo "  export DEEPSEEK_API_KEY=\"your-key\"      # https://platform.deepseek.com"
        echo "  export SILICONFLOW_API_KEY=\"your-key\"   # https://cloud.siliconflow.cn"
        echo "  export GEMINI_API_KEY=\"your-key\"        # https://aistudio.google.com/apikey（需翻墙）"
        exit 1
    fi
else
    echo "🤖 指定 Provider: $PROVIDER"
fi

# 解析 interns.yml 获取实习生列表
if [ -n "$INTERN" ]; then
    INTERNS=("$INTERN")
else
    INTERNS=$(grep '^\s*-\s*name:' config/interns.yml | sed 's/.*name:\s*"//;s/".*//' | tr -d ' ')
fi

TOTAL=0
SUCCESS=0
FAILED=0

for NAME in $INTERNS; do
    TOTAL=$((TOTAL + 1))
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "👤 [$TOTAL] 审查: $NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 从配置文件获取岗位
    ROLE=$(grep -A5 "\"$NAME\"" config/interns.yml | grep 'role:' | head -1 | sed 's/.*role:\s*"//;s/".*//' | tr -d ' ')

    if [ -z "$ROLE" ]; then
        echo "  ❌ 未找到 $NAME 的岗位配置"
        FAILED=$((FAILED + 1))
        continue
    fi

    OUTPUT_FILE="$OUTPUT_DIR/${ROLE}-${NAME}.md"

    # 构建命令
    CMD="python scripts/generate-report.py"
    CMD="$CMD --config config/interns.yml"
    CMD="$CMD --intern \"$NAME\""
    CMD="$CMD --week \"$WEEK\""
    CMD="$CMD --output \"$OUTPUT_FILE\""
    CMD="$CMD --provider \"$PROVIDER\""

    if [ -n "$SINCE" ]; then
        CMD="$CMD --since \"$SINCE\""
    fi

    if [ -n "$DRY_RUN" ]; then
        CMD="$CMD --dry-run"
    fi

    if [ -n "$REPO_BASE" ]; then
        CMD="$CMD --repo-path \"$REPO_BASE\""
    fi

    # 执行
    if eval $CMD; then
        SUCCESS=$((SUCCESS + 1))
        echo "  ✅ $NAME 审查完成"
    else
        FAILED=$((FAILED + 1))
        echo "  ❌ $NAME 审查失败"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 审查完成"
echo "  总计: $TOTAL | 成功: $SUCCESS | 失败: $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 汇总
if [ -z "$DRY_RUN" ] && [ $SUCCESS -gt 0 ]; then
    echo ""
    echo "📈 正在生成汇总报告..."
    python scripts/aggregate-scores.py --reports-dir "$OUTPUT_DIR" --history
    echo ""
    echo "📁 报告目录: $OUTPUT_DIR/"
    ls -la "$OUTPUT_DIR/"
fi
