#!/usr/bin/env python3
"""
generate-report.py - 调用 AI 生成实习生周度评审报告

用法:
  python generate-report.py \
    --config config/interns.yml \
    --intern "张三" \
    --week "2026-W24" \
    --output reports/2026-W24/frontend-张三.md

  或者手动传入数据:
  python generate-report.py \
    --prompt-file prompts/_base-template.md \
    --role-file prompts/frontend-intern.md \
    --commits-file commits.txt \
    --diff-file diff.txt \
    --intern "张三" \
    --role "frontend" \
    --week "2026-W24" \
    --output report.md
"""

import argparse
import os
import sys
import subprocess
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path


def load_config(config_path):
    """加载实习生配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def find_intern(config, name):
    """根据姓名查找实习生信息"""
    for intern in config['interns']:
        if intern['name'] == name:
            return intern
    raise ValueError(f"未找到实习生: {name}")


def get_week_range(week_str):
    """解析 '2026-W24' 格式，返回起止日期"""
    year = int(week_str.split('-W')[0])
    week_num = int(week_str.split('-W')[1])
    # ISO week: Monday = day 1
    jan1 = datetime(year, 1, 1)
    # 找到该年的第一个周一
    if jan1.weekday() <= 3:
        start = jan1 - timedelta(days=jan1.weekday())
    else:
        start = jan1 + timedelta(days=7 - jan1.weekday())
    week_start = start + timedelta(weeks=week_num - 1)
    week_end = week_start + timedelta(days=4)  # 到周五
    return week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')


def fetch_commits(intern, since, until, repo_path=None):
    """从 Git 仓库拉取指定实习生的本周提交"""
    github_id = intern['github_id']
    repos = intern.get('repos', [])

    all_commits = []
    all_diffs = []

    for repo in repos:
        # 如果本地有仓库路径，直接用 git 命令
        repo_dir = repo_path / repo.split('/')[-1] if repo_path else None
        if repo_dir and repo_dir.exists():
            try:
                # 获取提交记录
                result = subprocess.run(
                    ['git', 'log',
                     f'--author={github_id}',
                     f'--since={since}',
                     f'--until={until}',
                     '--pretty=format:%h|%s|%ai|%an',
                     '--no-merges'],
                    capture_output=True, text=True, cwd=str(repo_dir)
                )
                if result.stdout.strip():
                    all_commits.append(f"## 仓库: {repo}\n{result.stdout}")

                # 获取 diff 统计
                result = subprocess.run(
                    ['git', 'log',
                     f'--author={github_id}',
                     f'--since={since}',
                     f'--until={until}',
                     '--no-merges',
                     '-p', '--stat'],
                    capture_output=True, text=True, cwd=str(repo_dir)
                )
                if result.stdout.strip():
                    all_diffs.append(f"## 仓库: {repo}\n{result.stdout}")
            except Exception as e:
                print(f"  警告: 无法访问仓库 {repo}: {e}", file=sys.stderr)

    return '\n\n'.join(all_commits), '\n\n'.join(all_diffs)


def load_prompt(base_file, role_file):
    """加载并合并提示词"""
    prompts_dir = Path(__file__).parent.parent / 'prompts'

    with open(prompts_dir / base_file, 'r', encoding='utf-8') as f:
        base = f.read()

    with open(prompts_dir / role_file, 'r', encoding='utf-8') as f:
        role = f.read()

    return f"{base}\n\n---\n\n{role}"


def call_ai(prompt, commits, diff, intern_name, role, model="claude-sonnet-4-20250514"):
    """调用 AI API 生成报告"""
    # 截断 diff 避免超 token 限制
    max_diff = 50000
    if len(diff) > max_diff:
        diff = diff[:max_diff] + f"\n\n... [diff 已截断，原始长度 {len(diff)} 字符] ..."

    full_prompt = f"""{prompt}

---

## 待审查数据

### 实习生：{intern_name}
### 岗位：{role}

### 本周提交记录
{commits if commits else "（本周无提交记录）"}

### 代码变更详情
```
{diff if diff else "（本周无代码变更）"}
```

请严格按照上方评审模板格式，输出完整的周度评审报告。
注意：即使代码量很少，也必须按模板完整输出，对少量代码做深度审查。
"""

    # 尝试使用 anthropic SDK
    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )
        return message.content[0].text
    except ImportError:
        pass

    # 尝试使用 openai SDK
    try:
        import openai
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )
        return response.choices[0].message.content
    except ImportError:
        pass

    # 如果都没有安装，输出 prompt 供手动使用
    print("警告: 未安装 anthropic 或 openai SDK，请先 pip install anthropic 或 pip install openai", file=sys.stderr)
    return None


def main():
    parser = argparse.ArgumentParser(description='生成实习生周度评审报告')
    parser.add_argument('--config', default='config/interns.yml', help='实习生配置文件')
    parser.add_argument('--intern', required=True, help='实习生姓名')
    parser.add_argument('--week', help='审查周，格式: 2026-W24（默认本周）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--model', default='claude-sonnet-4-20250514', help='AI 模型')
    parser.add_argument('--repo-path', help='仓库本地路径（可选）')
    parser.add_argument('--dry-run', action='store_true', help='只输出 prompt，不调用 AI')

    # 也支持手动传入数据（不从 Git 拉取）
    parser.add_argument('--commits-file', help='手动指定提交记录文件')
    parser.add_argument('--diff-file', help='手动指定 diff 文件')

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    intern = find_intern(config, args.intern)
    role = intern['role']

    # 确定周次
    if args.week:
        week = args.week
    else:
        today = datetime.now()
        week = f"{today.year}-W{today.isocalendar()[1]:02d}"

    since, until = get_week_range(week)
    print(f"📋 生成评审报告: {args.intern} ({role}) | {week} ({since} ~ {until})")

    # 加载提示词
    prompt = load_prompt('_base-template.md', f'{role}-intern.md')

    # 获取代码变更
    if args.commits_file and args.diff_file:
        with open(args.commits_file, 'r', encoding='utf-8') as f:
            commits = f.read()
        with open(args.diff_file, 'r', encoding='utf-8') as f:
            diff = f.read()
    else:
        repo_path = Path(args.repo_path) if args.repo_path else None
        commits, diff = fetch_commits(intern, since, until, repo_path)

    print(f"  提交记录: {len(commits)} 字符")
    print(f"  代码变更: {len(diff)} 字符")

    # 调用 AI 或输出 prompt
    if args.dry_run:
        # dry-run 模式：直接组装并输出 prompt
        max_diff = 50000
        truncated_diff = diff[:max_diff] + f"\n\n... [diff 已截断] ..." if len(diff) > max_diff else diff
        full_prompt = f"""{prompt}

---

## 待审查数据

### 实习生：{args.intern}
### 岗位：{role}

### 本周提交记录
{commits if commits else "（本周无提交记录）"}

### 代码变更详情
```
{truncated_diff if truncated_diff else "（本周无代码变更）"}
```

请严格按照上方评审模板格式，输出完整的周度评审报告。
"""
        print("\n" + "=" * 60)
        print("PROMPT (可复制到 AI 工具中):")
        print("=" * 60)
        print(full_prompt)
        return

    report = call_ai(prompt, commits, diff, args.intern, role, args.model)

    if report is None:
        # AI 调用失败，输出 prompt 到文件
        max_diff = 50000
        truncated_diff = diff[:max_diff] + f"\n\n... [diff 已截断] ..." if len(diff) > max_diff else diff
        full_prompt = f"""{prompt}\n\n---\n\n## 待审查数据\n\n### 实习生：{args.intern}\n### 岗位：{role}\n\n### 本周提交记录\n{commits}\n\n### 代码变更详情\n```\n{truncated_diff}\n```\n\n请严格按照上方评审模板格式，输出完整的周度评审报告。"""
        prompt_output = args.output.replace('.md', '.prompt.txt') if args.output else 'prompt.txt'
        with open(prompt_output, 'w', encoding='utf-8') as f:
            f.write(full_prompt)
        print(f"  提示词已保存到: {prompt_output}，请手动粘贴到 AI 工具中")
        return

    # 保存报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  ✅ 报告已保存: {output_path}")
    else:
        print("\n" + "=" * 60)
        print(report)


if __name__ == '__main__':
    main()
