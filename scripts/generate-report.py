#!/usr/bin/env python3
"""
generate-report.py - 调用 AI 生成实习生周度评审报告
支持的 AI Provider（按推荐顺序）:
  1. gemini      - Google Gemini（免费，推荐）
  2. deepseek    - DeepSeek（国内可用，注册送额度）
  3. siliconflow - 硅基流动（国内平台，免费额度）
  4. anthropic   - Claude（收费）
  5. openai      - GPT-4o（收费）
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
  指定 provider:
  python generate-report.py \
    --provider deepseek \
    --intern "张三" \
    ...
"""
import argparse
import os
import sys
import subprocess
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# Provider 配置
# ============================================================
PROVIDERS = {
    "gemini": {
        "name": "Google Gemini",
        "env_key": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
        "description": "免费额度充足，推荐首选",
    },
    "deepseek": {
        "name": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "description": "国内可用，推理能力强",
    },
    "siliconflow": {
        "name": "SiliconFlow (硅基流动)",
        "env_key": "SILICONFLOW_API_KEY",
        "default_model": "Qwen/Qwen2.5-72B-Instruct",
        "description": "国内平台，支持多种开源模型",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "env_key": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-20250514",
        "description": "收费，质量高",
    },
    "openai": {
        "name": "OpenAI GPT",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
        "description": "收费，通用能力强",
    },
    "zai": {
        "name": "Z.AI GLM",
        "env_key": "ZAI_API_KEY",
        "default_model": "glm-5.1",
        "description": "GLM-5.1，OpenAI 兼容接口",
    },
    "sfkey": {
        "name": "SFKey OpenAI Compatible",
        "env_key": "ZAI_API_KEY",
        "default_model": "glm-5.1",
        "description": "SFKey OpenAI 兼容接口（使用 ZAI_API_KEY）",
    },
}

# Provider 优先级（自动检测时按此顺序尝试，国内无需翻墙的排前面）
PROVIDER_PRIORITY = ["sfkey", "zai", "deepseek", "siliconflow", "gemini", "anthropic", "openai"]


def detect_provider():
    """自动检测可用的 provider（按优先级）"""
    for provider_id in PROVIDER_PRIORITY:
        config = PROVIDERS[provider_id]
        if os.environ.get(config["env_key"]):
            return provider_id
    return None


# ============================================================
# 各 Provider 的 API 调用实现
# ============================================================
def call_gemini(prompt, model, api_key):
    """调用 Google Gemini API"""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text
    except ImportError:
        # fallback: 使用 REST API
        import urllib.request
        import urllib.error
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 8192}
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Gemini API 错误 ({e.code}): {error_body}")


def call_deepseek(prompt, model, api_key):
    """调用 DeepSeek API（兼容 OpenAI 格式）"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except ImportError:
        # fallback: 使用 REST API
        import urllib.request
        import urllib.error
        url = "https://api.deepseek.com/chat/completions"
        payload = json.dumps({
            "model": model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"DeepSeek API 错误 ({e.code}): {error_body}")


def call_siliconflow(prompt, model, api_key):
    """调用 SiliconFlow API（兼容 OpenAI 格式）"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except ImportError:
        import urllib.request
        import urllib.error
        url = "https://api.siliconflow.cn/v1/chat/completions"
        payload = json.dumps({
            "model": model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"SiliconFlow API 错误 ({e.code}): {error_body}")


def call_anthropic(prompt, model, api_key):
    """调用 Anthropic Claude API"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except ImportError:
        raise RuntimeError("请先安装 anthropic SDK: pip install anthropic")


def call_openai(prompt, model, api_key):
    """调用 OpenAI GPT API"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except ImportError:
        raise RuntimeError("请先安装 openai SDK: pip install openai")


def call_zai(prompt, model, api_key):
    """调用 Z.AI GLM API（兼容 OpenAI 格式）"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.z.ai/api/paas/v4/",
        )
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except ImportError:
        raise RuntimeError("请先安装 openai SDK: pip install openai")


def call_sfkey(prompt, model, api_key):
    """调用 SFKey OpenAI 兼容 API"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.sfkey.cn/v1/",
        )
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except ImportError:
        raise RuntimeError("请先安装 openai SDK: pip install openai")


# Provider 调用映射
PROVIDER_CALLERS = {
    "gemini": call_gemini,
    "deepseek": call_deepseek,
    "siliconflow": call_siliconflow,
    "anthropic": call_anthropic,
    "openai": call_openai,
    "zai": call_zai,
    "sfkey": call_sfkey,
}


# ============================================================
# 核心逻辑
# ============================================================
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
    jan1 = datetime(year, 1, 1)
    if jan1.weekday() <= 3:
        start = jan1 - timedelta(days=jan1.weekday())
    else:
        start = jan1 + timedelta(days=7 - jan1.weekday())
    week_start = start + timedelta(weeks=week_num - 1)
    week_end = week_start + timedelta(days=4)
    return week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')


def fetch_commits(intern, since, until, repo_path=None):
    """从 Git 仓库拉取指定实习生的本周提交"""
    github_id = intern['github_id']
    repos = intern.get('repos', [])
    all_commits = []
    all_diffs = []
    for repo in repos:
        repo_dir = repo_path / repo.split('/')[-1] if repo_path else None
        if repo_dir and repo_dir.exists():
            try:
                result = subprocess.run(
                    ['git', 'log',
                     f'--author={github_id}',
                     f'--since={since}',
                     f'--until={until}',
                     '--pretty=format:%h|%s|%ai|%an',
                     '--no-merges'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=str(repo_dir)
                )
                if result.stdout.strip():
                    all_commits.append(f"## 仓库: {repo}\n{result.stdout}")
                result = subprocess.run(
                    ['git', 'log',
                     f'--author={github_id}',
                     f'--since={since}',
                     f'--until={until}',
                     '--no-merges',
                     '-p', '--stat'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=str(repo_dir)
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


def call_ai(prompt, commits, diff, intern_name, role, provider, model, api_key):
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

    caller = PROVIDER_CALLERS.get(provider)
    if not caller:
        raise ValueError(f"不支持的 provider: {provider}")

    print(f"  🤖 调用 {PROVIDERS[provider]['name']} ({model})...")
    return caller(full_prompt, model, api_key)


def main():
    parser = argparse.ArgumentParser(
        description='生成实习生周度评审报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的 AI Provider:
  gemini        Google Gemini（免费，推荐首选）
  deepseek      DeepSeek（国内可用，推理能力强）
  siliconflow   硅基流动（国内平台，多模型可选）
  anthropic     Claude（收费）
  openai        GPT-4o（收费）

示例:
  # 使用 Gemini（默认，自动检测 API Key）
  export GEMINI_API_KEY="your-key"
  python generate-report.py --intern "张三"

  # 指定 provider
  python generate-report.py --provider deepseek --intern "张三"

  # 指定模型
  python generate-report.py --provider gemini --model gemini-2.5-pro --intern "张三"
""",
    )
    parser.add_argument('--config', default='config/interns.yml', help='实习生配置文件')
    parser.add_argument('--intern', required=True, help='实习生姓名')
    parser.add_argument('--week', help='审查周，格式: 2026-W24（默认本周）')
    parser.add_argument('--since', help='起始日期，格式: 2026-06-01（覆盖 week 计算的日期）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--provider', default='sfkey', help='AI provider（默认 sfkey）')
    parser.add_argument('--model', help='AI 模型（默认使用 provider 推荐模型）')
    parser.add_argument('--repo-path', default='D:/qt/repos', help='仓库本地路径（默认: D:/qt/repos）')
    parser.add_argument('--dry-run', action='store_true', help='只输出 prompt，不调用 AI')
    parser.add_argument('--list-providers', action='store_true', help='列出所有支持的 provider')
    # 也支持手动传入数据（不从 Git 拉取）
    parser.add_argument('--commits-file', help='手动指定提交记录文件')
    parser.add_argument('--diff-file', help='手动指定 diff 文件')

    args = parser.parse_args()

    # 列出 provider
    if args.list_providers:
        print("\n支持的 AI Provider:\n")
        for pid in PROVIDER_PRIORITY:
            pc = PROVIDERS[pid]
            has_key = "✅" if os.environ.get(pc["env_key"]) else "❌"
            print(f"  {pid:15s} {pc['name']:25s} Key: {has_key}  {pc['description']}")
        env_keys = list(dict.fromkeys(PROVIDERS[p]['env_key'] for p in PROVIDER_PRIORITY))
        print(f"\n环境变量: {', '.join(env_keys)}")
        return

    # ==============================================
    # ✅ 修复：DRY_RUN 模式放在最前面，跳过 API Key 检查
    # ==============================================
    if args.dry_run:
        print("🔧 试运行模式：不调用 AI，只输出 Prompt")
        print("   （无需配置 API Key）")

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

        # 确定日期范围
        if args.since:
            since = args.since
            until = (datetime.strptime(since, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
            print(f"📋 试运行: {args.intern} ({role}) | {since} ~ {until}")
        else:
            since, until = get_week_range(week)
            print(f"📋 试运行: {args.intern} ({role}) | {week} ({since} ~ {until})")

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

        # 输出完整 Prompt
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
        print("\n✅ 试运行完成！")
        return

    # ==============================================
    # 以下是正常模式（需要 API Key）
    # ==============================================

    # 确定 provider
    provider = args.provider
    if not provider:
        provider = detect_provider()
        if not provider:
            print("错误: 未检测到可用的 AI API Key。请设置以下任一环境变量:", file=sys.stderr)
            for pid in PROVIDER_PRIORITY:
                pc = PROVIDERS[pid]
                print(f"  export {pc['env_key']}=\"your-key\"  # {pc['name']} - {pc['description']}", file=sys.stderr)
            print(f"\n或使用 --list-providers 查看所有选项", file=sys.stderr)
            sys.exit(1)
        print(f"  🔍 自动检测到 provider: {PROVIDERS[provider]['name']}")

    if provider not in PROVIDERS:
        print(f"错误: 不支持的 provider '{provider}'", file=sys.stderr)
        print(f"支持的: {', '.join(PROVIDER_PRIORITY)}", file=sys.stderr)
        sys.exit(1)

    # 获取 API Key
    pc = PROVIDERS[provider]
    api_key = os.environ.get(pc["env_key"])
    if not api_key:
        print(f"错误: 未设置 {pc['env_key']}", file=sys.stderr)
        print(f"  export {pc['env_key']}=\"your-key\"", file=sys.stderr)
        sys.exit(1)

    # 确定模型
    model = args.model or pc["default_model"]

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

    # 确定日期范围（--since 优先，否则根据 week 计算）
    if args.since:
        since = args.since
        until = (datetime.strptime(since, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        print(f"📋 生成评审报告: {args.intern} ({role}) | {since} ~ {until}（手动指定）")
    else:
        since, until = get_week_range(week)
        print(f"📋 生成评审报告: {args.intern} ({role}) | {week} ({since} ~ {until})")

    print(f"  Provider: {pc['name']} | 模型: {model}")

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

    # 调用 AI
    try:
        report = call_ai(prompt, commits, diff, args.intern, role, provider, model, api_key)
    except Exception as e:
        print(f"  ❌ AI 调用失败: {e}", file=sys.stderr)
        # 输出 prompt 到文件供手动使用
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
