#!/usr/bin/env python3
"""
aggregate-scores.py - 汇总所有实习生的周度评审分数

用法:
  python aggregate-scores.py --reports-dir reports/2026-W24 --output reports/2026-W24/summary.csv

输出:
  - CSV 汇总表（姓名、岗位、各维度分数、总分、等级）
  - Markdown 汇总表（可直接嵌入报告）
  - 趋势对比（如果有历史数据）
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_report(filepath):
    """从 Markdown 报告中提取分数"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'file': str(filepath),
        'intern': '',
        'role': '',
        'week': '',
        'total_score': 0,
        'level': '',
        'dimensions': {},
        'highlights': [],
        'improvements': []
    }

    # 提取基本信息
    name_match = re.search(r'\*\*实习生姓名\*\*[：:]\s*(.+)', content)
    if name_match:
        result['intern'] = name_match.group(1).strip()

    role_match = re.search(r'\*\*岗位\*\*[：:]\s*(.+)', content)
    if role_match:
        result['role'] = role_match.group(1).strip()

    week_match = re.search(r'\*\*审查周期\*\*[：:]\s*(\d{4}-W\d{2})', content)
    if week_match:
        result['week'] = week_match.group(1).strip()

    # 提取总分
    total_match = re.search(r'\*\*总分\*\*.*?\|\s*\*\*([\d.]+)\*\*', content)
    if total_match:
        result['total_score'] = float(total_match.group(1))

    # 提取等级（支持 "A"、"A（优秀）"、"🟡 C" 等格式）
    level_match = re.search(r'\*\*等级\*\*[：:]\s*.*?([A-D])', content)
    if level_match:
        result['level'] = level_match.group(1).strip()

    # 提取各维度分数（只从评分总览表格中，排除成长趋势表）
    # 找到"评分总览"表格区域，在"等级"行之前
    scoring_section = content.split('### 📊 评分总览')
    if len(scoring_section) > 1:
        scoring_area = scoring_section[1].split('**等级**')[0] if '**等级**' in scoring_section[1] else scoring_section[1]
        dim_pattern = re.compile(
            r'\|\s*(代码规范|逻辑正确性|学习成长|工程实践|沟通协作|岗位专项)\s*\|\s*(\d+)\s*\|'
        )
        for match in dim_pattern.finditer(scoring_area):
            dim_name = match.group(1)
            dim_score = int(match.group(2))
            result['dimensions'][dim_name] = dim_score

    return result


def load_previous_scores(reports_base_dir, current_week, intern_name):
    """加载历史分数用于趋势对比"""
    history = []
    base = Path(reports_base_dir)

    # 遍历所有周目录
    for week_dir in sorted(base.iterdir()):
        if not week_dir.is_dir():
            continue
        week_name = week_dir.name
        if week_name >= current_week:
            continue

        # 查找该实习生的历史报告
        for report_file in week_dir.glob('*.md'):
            if report_file.name == 'summary.md' or report_file.name == 'summary.csv':
                continue
            report = parse_report(report_file)
            if report['intern'] == intern_name and report['total_score'] > 0:
                history.append({
                    'week': week_name,
                    'score': report['total_score'],
                    'level': report['level'],
                    'dimensions': report['dimensions']
                })

    return history


def calculate_trend(current_score, previous_score):
    """计算趋势"""
    if previous_score is None:
        return "🆕"
    diff = current_score - previous_score
    if diff > 3:
        return "📈"
    elif diff < -3:
        return "📉"
    else:
        return "➡️"


def generate_csv(reports, output_path):
    """生成 CSV 汇总表"""
    if not reports:
        print("警告: 没有找到任何报告", file=sys.stderr)
        return

    # 维度列
    dim_names = ['代码规范', '逻辑正确性', '学习成长', '工程实践', '沟通协作', '岗位专项']

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        header = ['姓名', '岗位', '团队'] + dim_names + ['总分', '等级', '趋势']
        writer.writerow(header)

        for r in sorted(reports, key=lambda x: x['total_score'], reverse=True):
            row = [r['intern'], r['role'], r.get('team', '')]
            for dim in dim_names:
                row.append(r['dimensions'].get(dim, '-'))
            row.append(r['total_score'])
            row.append(r['level'])
            row.append(r.get('trend', ''))
            writer.writerow(row)

    print(f"  ✅ CSV 汇总已保存: {output_path}")


def generate_markdown_summary(reports, week, output_path):
    """生成 Markdown 汇总表"""
    if not reports:
        return

    lines = [
        f"# 实习生周度评审汇总 - {week}",
        "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总览",
        "",
        "| 排名 | 姓名 | 岗位 | 总分 | 等级 | 趋势 | 亮点 | 待改进 |",
        "|------|------|------|------|------|------|------|--------|",
    ]

    for i, r in enumerate(sorted(reports, key=lambda x: x['total_score'], reverse=True), 1):
        level_emoji = {'A': '🟢', 'B': '🔵', 'C': '🟡', 'D': '🔴'}.get(r['level'], '⚪')
        lines.append(
            f"| {i} | {r['intern']} | {r['role']} | {r['total_score']} | "
            f"{level_emoji} {r['level']} | {r.get('trend', '')} | "
            f"{len(r.get('highlights', []))}条 | {len(r.get('improvements', []))}条 |"
        )

    # 统计
    scores = [r['total_score'] for r in reports if r['total_score'] > 0]
    if scores:
        lines.extend([
            "",
            "## 统计",
            "",
            f"- **人数**: {len(reports)}",
            f"- **平均分**: {sum(scores)/len(scores):.1f}",
            f"- **最高分**: {max(scores):.1f}",
            f"- **最低分**: {min(scores):.1f}",
            f"- **等级分布**:",
        ])
        for level in ['A', 'B', 'C', 'D']:
            count = sum(1 for r in reports if r['level'] == level)
            if count:
                emoji = {'A': '🟢', 'B': '🔵', 'C': '🟡', 'D': '🔴'}[level]
                lines.append(f"  - {emoji} {level}: {count}人")

    lines.append("")
    lines.append("---")
    lines.append(f"*本报告由 AI 代码审查系统自动生成*")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  ✅ Markdown 汇总已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='汇总实习生周度评审分数')
    parser.add_argument('--reports-dir', default=None, help='报告目录（默认自动检测最新周）')
    parser.add_argument('--output', '-o', help='输出路径（默认在报告目录下生成 summary）')
    parser.add_argument('--config', default='config/interns.yml', help='实习生配置文件')
    parser.add_argument('--history', action='store_true', help='是否包含历史趋势对比')

    args = parser.parse_args()

    reports_base = Path('reports')

    if args.reports_dir:
        reports_dir = Path(args.reports_dir)
    else:
        # 找最新的周目录
        if not reports_base.exists():
            print("错误: reports/ 目录不存在", file=sys.stderr)
            sys.exit(1)
        week_dirs = sorted([d for d in reports_base.iterdir() if d.is_dir()], reverse=True)
        if not week_dirs:
            print("错误: 没有找到任何周报告目录", file=sys.stderr)
            sys.exit(1)
        reports_dir = week_dirs[0]

    week = reports_dir.name
    print(f"📊 汇总报告: {week}")

    # 解析所有报告
    reports = []
    for report_file in reports_dir.glob('*.md'):
        if report_file.name.startswith('summary'):
            continue
        try:
            report = parse_report(report_file)
            if report['total_score'] > 0:
                # 加载历史数据计算趋势
                if args.history:
                    history = load_previous_scores(reports_base, week, report['intern'])
                    if history:
                        last_score = history[-1]['score']
                        report['trend'] = calculate_trend(report['total_score'], last_score)
                        report['prev_score'] = last_score
                    else:
                        report['trend'] = '🆕'
                reports.append(report)
        except Exception as e:
            print(f"  警告: 解析 {report_file} 失败: {e}", file=sys.stderr)

    print(f"  找到 {len(reports)} 份报告")

    # 生成汇总
    if args.output:
        output_base = Path(args.output).stem
        output_dir = Path(args.output).parent
    else:
        output_base = 'summary'
        output_dir = reports_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    generate_csv(reports, output_dir / f'{output_base}.csv')
    generate_markdown_summary(reports, week, output_dir / f'{output_base}.md')


if __name__ == '__main__':
    main()
