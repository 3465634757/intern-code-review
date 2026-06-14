# 🎓 实习生周度代码审查系统

基于 AI 的实习生每周代码自动评审系统，为不同岗位提供专属评审标准和周度报告。

灵感来源：[keba2503/ai-pr-review-prompts](https://github.com/keba2503/ai-pr-review-prompts)

## 🏗️ 项目结构

```
intern-code-review/
├── .github/workflows/
│   └── weekly-review.yml          # GitHub Actions 定时审查
├── prompts/                       # 岗位专属审查提示词
│   ├── _base-template.md          # 通用基础模板（所有岗位共享）
│   ├── frontend-intern.md         # 前端实习生
│   ├── backend-intern.md          # 后端实习生
│   ├── mobile-intern.md           # 移动端实习生
│   ├── qa-intern.md               # 测试实习生
│   ├── devops-intern.md           # 运维实习生
│   └── data-intern.md             # 数据/算法实习生
├── config/
│   ├── interns.yml                # 实习生名单 + 岗位映射
│   └── scoring-rubric.yml         # 统一评分标准
├── scripts/
│   ├── fetch-commits.sh           # 拉取本周代码变更
│   ├── generate-report.py         # 调用 AI 生成报告
│   └── aggregate-scores.py        # 汇总所有人分数
├── reports/                       # 生成的周度报告
│   └── 2026-W24/
│       ├── frontend-张三.md
│       ├── backend-李四.md
│       ├── summary.csv
│       └── summary.md
├── examples/
│   └── frontend-intern-zhangsan.md  # 示例报告
├── run.sh                         # 本地一键运行脚本
├── requirements.txt               # Python 依赖
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 二选一
export ANTHROPIC_API_KEY="sk-ant-xxx"    # Claude（推荐）
export OPENAI_API_KEY="sk-xxx"           # GPT-4o
```

### 3. 修改配置

编辑 `config/interns.yml`，填入你的实习生信息：

```yaml
interns:
  - name: "张三"
    github_id: "zhangsan-dev"    # GitHub/GitLab 用户名
    role: "frontend"              # 岗位：frontend/backend/mobile/qa/devops/data
    team: "用户端"
    mentor: "李导师"
    repos:
      - "company/web-app"         # 仓库名
```

### 4. 运行审查

```bash
# 本地运行 - 审查所有实习生（本周）
./run.sh

# 只审查某个人
./run.sh --intern "张三"

# 指定周次
./run.sh --week 2026-W24

# 试运行（只收集数据，不调用AI，用于验证流程）
./run.sh --dry-run
```

### 5. 查看报告

```bash
ls reports/2026-W24/
# frontend-张三.md    ← 个人报告
# backend-李四.md     ← 个人报告
# summary.csv         ← 汇总表格
# summary.md          ← 汇总看板
```

## 🔄 自动化部署（GitHub Actions）

### 配置 Secrets

在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 说明 |
|-------------|------|
| `ANTHROPIC_API_KEY` | Claude API Key（推荐） |
| `OPENAI_API_KEY` | GPT API Key（备选） |
| `WECOM_WEBHOOK` | 企业微信机器人 Webhook（可选） |
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook（可选） |

### 触发方式

1. **定时触发**：每周五 17:00（UTC+8）自动运行
2. **手动触发**：Actions → 实习生周度代码审查 → Run workflow

## 📝 自定义岗位提示词

### 添加新岗位

1. 复制 `_base-template.md` 作为基础
2. 创建 `prompts/{role}-intern.md`，编写岗位专项评审标准
3. 在 `config/interns.yml` 中使用新 role 名称

### 修改评分标准

编辑 `config/scoring-rubric.yml`：

```yaml
scoring:
  levels:
    A: { min: 90, label: "优秀" }    # 调整等级阈值
    B: { min: 75, label: "良好" }
    C: { min: 60, label: "合格" }
    D: { min: 0,  label: "需改进" }
```

### 调整权重

在 `_base-template.md` 的评审维度表格中修改权重：

```markdown
| 维度 | 权重 | 评审要点 |
|------|------|----------|
| 代码规范 | 15% | ... |
| 逻辑正确性 | 25% | ... |
```

## 📊 评分规则

### 等级说明

| 等级 | 分数范围 | 含义 | 建议动作 |
|------|---------|------|----------|
| 🟢 A | 90-100 | 优秀 | 推荐转正评估 |
| 🔵 B | 75-89 | 良好 | 符合预期，继续培养 |
| 🟡 C | 60-74 | 合格 | 需要更多指导 |
| 🔴 D | 0-59 | 需改进 | 触发导师1v1辅导 |

### 评分铁律

1. **正态分布**：不允许所有维度都在 70-85 之间
2. **零容忍**：硬编码密码、SQL注入、未处理空指针 → 该维度 0-40 分
3. **扣分有据**：每个扣分点必须指出具体文件和代码

## 🔧 进阶用法

### 手动传入代码数据（不依赖 Git）

```bash
# 1. 准备数据
echo "abc123|feat: 新增用户列表|2026-06-10" > commits.txt
git diff HEAD~5 > diff.txt

# 2. 生成报告
python scripts/generate-report.py \
  --intern "张三" \
  --commits-file commits.txt \
  --diff-file diff.txt \
  --output report.md
```

### 接入企业微信/飞书

在 GitHub Secrets 中配置 `WECOM_WEBHOOK` 或 `FEISHU_WEBHOOK`，每次审查完成后自动推送汇总到群。

### 接入 GitLab CI

将 `.github/workflows/weekly-review.yml` 的逻辑转换为 `.gitlab-ci.yml`，使用 `rules: - if: $CI_PIPELINE_SOURCE == "schedule"` 定时触发。

## ❓ FAQ

**Q: 评分偏高/偏低怎么办？**
A: 修改 `_base-template.md` 中的"评分铁律"章节，调整正态分布的约束。

**Q: 如何加入历史趋势对比？**
A: 保持 `reports/` 目录结构不变，每周报告会自动归档到对应周目录，`aggregate-scores.py` 会自动对比历史。

**Q: 实习生代码量很少怎么办？**
A: AI 会对少量代码做深度审查。也可以合并 PR review 数据作为补充输入。

**Q: 如何横向比较不同岗位的实习生？**
A: 通用维度（85%）统一标准，岗位专项（15%）差异化，总分可直接比较。

## 📄 License

MIT
