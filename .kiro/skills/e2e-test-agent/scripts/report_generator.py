#!/usr/bin/env python3
"""
HTML 测试报告生成器

生成各阶段的 HTML 报告。供 LLM 通过 shell 调用。

使用方式:
    # 生成阶段报告
    python scripts/report_generator.py --stage requirement_analysis --op OP-123456 \
        --title "阶段 1: 需求分析报告" \
        --data '{"knowledge_doc": "https://...", "test_cases": "https://...", "case_count": 15}'

    # 生成测试报告（含用例结果）
    python scripts/report_generator.py --stage first_test --op OP-123456 \
        --title "第一轮测试报告" \
        --results-file "docs/recordings/OP-123456/test_results.json"

    # 生成最终报告
    python scripts/report_generator.py --stage final --op OP-123456 \
        --title "最终测试报告" \
        --context-file "docs/recordings/OP-123456/pipeline-context.json"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 30px; }}
        h1 {{ color: #1a1a1a; margin-bottom: 8px; font-size: 24px; }}
        h2 {{ color: #333; margin: 25px 0 12px; padding-bottom: 8px; border-bottom: 2px solid #f0f0f0; font-size: 18px; }}
        .meta {{ color: #666; margin-bottom: 25px; font-size: 13px; }}
        .meta span {{ margin-right: 15px; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 25px; }}
        .card {{ background: #f8f9fa; border-radius: 6px; padding: 15px; text-align: center; }}
        .card .num {{ font-size: 28px; font-weight: bold; }}
        .card .label {{ color: #666; font-size: 12px; margin-top: 4px; }}
        .card.success .num {{ color: #52c41a; }}
        .card.error .num {{ color: #ff4d4f; }}
        .card.warning .num {{ color: #faad14; }}
        .card.info .num {{ color: #1890ff; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; font-size: 13px; }}
        th {{ background: #fafafa; font-weight: 600; }}
        .pass {{ color: #52c41a; font-weight: bold; }}
        .fail {{ color: #ff4d4f; font-weight: bold; }}
        .skip {{ color: #999; }}
        .warn {{ color: #faad14; font-weight: bold; }}
        .section {{ margin-bottom: 20px; }}
        .link {{ color: #1890ff; text-decoration: none; }}
        .link:hover {{ text-decoration: underline; }}
        .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #f0f0f0; color: #999; font-size: 11px; text-align: center; }}
        .risk {{ background: #fff2f0; border: 1px solid #ffccc7; border-radius: 4px; padding: 12px; margin: 10px 0; }}
        .risk-title {{ color: #ff4d4f; font-weight: bold; margin-bottom: 5px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>{title}</h1>
    <div class="meta">
        <span>OP: {op_number}</span>
        <span>阶段: {stage}</span>
        <span>生成时间: {timestamp}</span>
    </div>
    <div class="meta" style="margin-top:-15px;">
        <span>开始时间: {start_time}</span>
        <span>结束时间: {end_time}</span>
        <span>耗时: {duration}</span>
    </div>
    {content}
    <div class="footer">E2E Test Agent · 自动生成于 {timestamp}</div>
</div>
</body>
</html>"""


def build_cards(data: dict) -> str:
    """构建统计卡片"""
    card_map = {
        "total": ("总计", "info"),
        "passed": ("通过", "success"),
        "failed": ("失败", "error"),
        "skipped": ("跳过", "warning"),
        "case_count": ("用例数", "info"),
        "bug_count": ("Bug数", "error"),
        "bug_fix_rounds": ("修复轮次", "warning"),
        "automation_cases": ("自动化用例", "info"),
    }
    cards = []
    for key, value in data.items():
        if key in card_map:
            label, css = card_map[key]
            cards.append(f'<div class="card {css}"><div class="num">{value}</div><div class="label">{label}</div></div>')
    if not cards:
        return ""
    return f'<div class="cards">{"".join(cards)}</div>'


def build_table(rows: list, columns: list = None) -> str:
    """构建表格"""
    if not rows:
        return ""
    if not columns:
        columns = list(rows[0].keys())
    headers = "".join(f"<th>{c}</th>" for c in columns)
    body_rows = []
    for row in rows:
        cells = []
        for col in columns:
            val = row.get(col, "")
            if col in ("状态", "status", "result"):
                css = "pass" if str(val).lower() in ("pass", "passed", "通过", "✅") else \
                      "fail" if str(val).lower() in ("fail", "failed", "失败", "❌") else \
                      "skip" if str(val).lower() in ("skip", "skipped", "跳过") else ""
                cells.append(f'<td class="{css}">{val}</td>')
            elif str(val).startswith("http"):
                cells.append(f'<td><a class="link" href="{val}" target="_blank">链接</a></td>')
            else:
                cells.append(f"<td>{val}</td>")
        body_rows.append(f'<tr>{"".join(cells)}</tr>')
    return f'<table><thead><tr>{headers}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'


def generate_report(stage: str, op_number: str, title: str, content: str,
                    start_time: str = "", end_time: str = "", duration: str = "") -> str:
    """生成完整 HTML"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return REPORT_TEMPLATE.format(
        title=title,
        op_number=op_number,
        stage=stage,
        timestamp=timestamp,
        start_time=start_time or timestamp,
        end_time=end_time or timestamp,
        duration=duration or "-",
        content=content
    )


def stage_requirement_analysis(args):
    """阶段 1 报告"""
    data = {}
    if args.data_file:
        with open(args.data_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    elif args.data:
        data = json.loads(args.data)
    cards = build_cards({"case_count": data.get("case_count", 0)})

    # 产出物表格（从 data 中读取，不硬编码）
    outputs = data.get("outputs", [
        {"项目": "功能知识库", "状态": "✅", "链接": data.get("knowledge_doc", ""), "说明": "基于需求文档自动生成"},
        {"项目": "测试用例", "状态": "✅", "链接": data.get("test_cases", ""), "说明": f"共 {data.get('case_count', 0)} 条"},
    ])
    table = build_table(outputs)

    # 执行步骤详情
    steps_html = '<h2>执行步骤</h2><table><thead><tr><th>步骤</th><th>操作</th><th>结果</th></tr></thead><tbody>'
    steps = data.get("steps", [
        {"step": "1.1", "action": "读取 OP 信息", "result": f"OP-{data.get('op_number', '').replace('OP-', '')} | platform={data.get('platform', '')} | channel={data.get('channel', '')}"},
        {"step": "1.2", "action": "生成功能知识库", "result": f"推送到 Outline: {data.get('knowledge_doc', '')}"},
        {"step": "1.3a", "action": "创建 Google Sheet", "result": f"Sheet 创建成功"},
        {"step": "1.3b", "action": "写入测试用例到 Sheet", "result": f"{data.get('case_count', 0)} 条用例写入"},
        {"step": "1.3c", "action": "合并 A 列模块单元格", "result": "合并完成"},
        {"step": "1.3d", "action": "导入自动化测试平台", "result": f"{data.get('case_count', 0)} 条导入成功"},
        {"step": "1.4", "action": "生成阶段报告", "result": "HTML 报告生成"},
        {"step": "1.5", "action": "更新 pipeline-context", "result": "current_phase = requirement_analyzed"},
    ])
    for s in steps:
        steps_html += f'<tr><td>{s["step"]}</td><td>{s["action"]}</td><td>{s["result"]}</td></tr>'
    steps_html += '</tbody></table>'

    coverage_html = '<h2>覆盖度自审</h2><table><thead><tr><th>维度</th><th>状态</th><th>说明</th></tr></thead><tbody>'
    coverage = data.get("coverage", [
        {"维度": "正常流程", "状态": "✅ 已覆盖", "说明": "照片正常展示、照片过期展示"},
        {"维度": "边界条件", "状态": "✅ 已覆盖", "说明": "89天、90天、91天"},
        {"维度": "异常流程", "状态": "✅ 已覆盖", "说明": "无照片数据"},
        {"维度": "必填校验", "状态": "N/A", "说明": "本功能无表单输入"},
        {"维度": "状态流转", "状态": "N/A", "说明": "本功能无状态流转"},
        {"维度": "权限控制", "状态": "N/A", "说明": "本功能无权限差异"},
    ])
    for c in coverage:
        steps_html_class = "pass" if "✅" in c["状态"] else "skip" if "N/A" in c["状态"] else ""
        coverage_html += f'<tr><td>{c["维度"]}</td><td class="{steps_html_class}">{c["状态"]}</td><td>{c["说明"]}</td></tr>'
    coverage_html += '</tbody></table>'

    content = f"{cards}<h2>产出物</h2>{table}{steps_html}{coverage_html}"
    return generate_report(
        "requirement_analysis", args.op,
        args.title or "阶段 1: 需求分析报告", content,
        start_time=data.get("start_time", ""),
        end_time=data.get("end_time", ""),
        duration=data.get("duration", "")
    )


def stage_test_report(args):
    """测试报告（阶段 3/4/5/6）— first_test, bug_fix_verify, bug_fix_risk, second_test, automation_error"""
    results = []
    data = {}
    if args.data_file:
        path = Path(args.data_file)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results = data.get("results", [])
    elif args.results_file:
        path = Path(args.results_file)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                results = json.load(f)

    # 统计
    total = len(results)
    passed = sum(1 for r in results if r.get("status") in ("pass", "passed", "通过"))
    failed = sum(1 for r in results if r.get("status") in ("fail", "failed", "失败"))
    skipped = total - passed - failed

    cards = build_cards({"total": total, "passed": passed, "failed": failed, "skipped": skipped})
    table = build_table(results, ["case_number", "case_name", "status", "note"]) if results else ""

    content = f"{cards}"
    if table:
        content += f"<h2>用例详情</h2>{table}"

    # 额外信息（仓库、CDN 报告链接等）
    extra_html = ""
    test_report_cdn = data.get("test_report_cdn", "")
    automation_repo = data.get("automation_repo", "")
    automation_branch = data.get("automation_branch", "")

    if test_report_cdn or automation_repo:
        extra_html += '<h2>🔗 相关链接</h2><table><thead><tr><th>资源</th><th>链接</th></tr></thead><tbody>'
        if test_report_cdn:
            extra_html += f'<tr><td>自动化测试执行报告（含截图）</td><td><a class="link" href="{test_report_cdn}" target="_blank">CDN 报告</a></td></tr>'
        if automation_repo:
            repo_url = f"{automation_repo}/tree/{automation_branch}" if automation_branch else automation_repo
            extra_html += f'<tr><td>自动化代码仓库</td><td><a class="link" href="{repo_url}" target="_blank">GitHub (分支: {automation_branch})</a></td></tr>'
        extra_html += '</tbody></table>'

    content += extra_html

    return generate_report(args.stage, args.op, args.title or f"测试报告 - {args.op}", content,
                           start_time=getattr(args, 'start_time', '') or '',
                           end_time=getattr(args, 'end_time', '') or '',
                           duration=getattr(args, 'duration', '') or '')


def stage_final(args):
    """最终报告（阶段 7）— 给所有关注项目的人看"""
    data = {}
    if args.data_file:
        path = Path(args.data_file)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    elif args.context_file:
        path = Path(args.context_file)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

    stats = data.get("stats", {})
    conclusion = data.get("conclusion", "未知")
    conclusion_detail = data.get("conclusion_detail", "")

    # 结论样式
    conclusion_color = "#52c41a" if "全部通过" in conclusion else "#faad14" if "风险" in conclusion else "#ff4d4f"
    conclusion_icon = "✅" if "全部通过" in conclusion else "⚠️" if "风险" in conclusion else "❌"

    # 板块 1: 结论摘要
    section1 = f'''
    <div style="margin-bottom:15px; font-size:13px; color:#666;">
        <span style="margin-right:15px;"><strong>功能:</strong> {data.get("unit", "")}</span>
        <span style="margin-right:15px;"><strong>平台:</strong> {data.get("platform", "")}</span>
        <span><strong>环境:</strong> {data.get("env", "")}</span>
    </div>
    <div style="text-align:center; padding:20px 0; margin-bottom:20px; background:{conclusion_color}10; border:2px solid {conclusion_color}; border-radius:8px;">
        <div style="font-size:36px; margin-bottom:8px;">{conclusion_icon}</div>
        <div style="font-size:22px; font-weight:bold; color:{conclusion_color};">{conclusion}</div>
        <div style="color:#666; margin-top:8px; font-size:14px;">{conclusion_detail}</div>
    </div>'''

    # 板块 2: 统计卡片
    section2 = build_cards({
        "total": stats.get("total_cases", 0),
        "passed": stats.get("passed", 0),
        "failed": stats.get("failed", 0),
        "skipped": stats.get("skipped", 0),
        "bug_fix_rounds": stats.get("bug_fix_rounds", 0),
        "automation_cases": stats.get("automation_executable", 0),
    })

    # 板块 3: 各阶段执行情况
    stages = data.get("stages", [])
    section3 = ""
    if stages:
        section3 = '<h2>📋 各阶段执行情况</h2><table><thead><tr><th>阶段</th><th>状态</th><th>耗时</th><th>产出</th><th>报告</th></tr></thead><tbody>'
        for s in stages:
            status = s.get("status", "")
            status_class = "pass" if "✅" in status else "fail" if "❌" in status else "warn" if "⚠️" in status else ""
            report_url = s.get("report_url", "-")
            report_cell = f'<a class="link" href="{report_url}" target="_blank">查看</a>' if report_url.startswith("http") else report_url
            section3 += f'<tr><td>{s.get("name", "")}</td><td class="{status_class}">{status}</td><td>{s.get("duration", "-")}</td><td>{s.get("output", "-")}</td><td>{report_cell}</td></tr>'
        section3 += '</tbody></table>'

    # 板块 4: 测试用例执行结果
    test_results = data.get("test_results", [])
    section4 = ""
    if test_results:
        section4 = '<h2>🧪 测试用例执行结果</h2><table><thead><tr><th>用例编号</th><th>用例名称</th><th>状态</th><th>备注</th></tr></thead><tbody>'
        for r in test_results:
            status = r.get("status", "")
            if status in ("passed", "pass"):
                status_display = "✅ 通过"
                status_class = "pass"
            elif status in ("failed", "fail"):
                status_display = "❌ 失败"
                status_class = "fail"
            else:
                status_display = "⏭️ 跳过"
                status_class = "skip"
            section4 += f'<tr><td>{r.get("case_number", "")}</td><td>{r.get("case_name", "")}</td><td class="{status_class}">{status_display}</td><td>{r.get("note", "")}</td></tr>'
        section4 += '</tbody></table>'

    # 板块 5: Bug 列表
    bugs = data.get("bugs", [])
    section5 = '<h2>🐛 Bug 列表</h2>'
    if bugs:
        for bug in bugs:
            section5 += f'''<div class="risk">
                <div class="risk-title">{bug.get("case_number", "")} - {bug.get("title", "")}</div>
                <p><strong>问题描述：</strong>{bug.get("description", "")}</p>
                <p><strong>根因分析：</strong>{bug.get("root_cause", "")}</p>
                <p><strong>相关代码：</strong><code>{bug.get("related_code", "")}</code></p>
                <p><strong>修复建议：</strong>{bug.get("suggestion", "")}</p>
                <p><strong>修复状态：</strong><span class="fail">{bug.get("fix_status", "")}</span></p>
            </div>'''
    else:
        section5 += '<div style="text-align:center; padding:20px; color:#52c41a; font-size:16px;">🎉 无 Bug</div>'

    # 板块 6: 自动化代码
    automation = data.get("automation", {})
    section6 = '<h2>🤖 自动化代码</h2>'
    if automation:
        files_html = "".join(f"<li><code>{f}</code></li>" for f in automation.get("files", []))
        skip_reasons_html = "".join(f"<li>{r}</li>" for r in automation.get("skip_reasons", []))
        pr_html = f'<p><strong>PR：</strong><a class="link" href="{automation["pr_url"]}" target="_blank">{automation["pr_url"]}</a></p>' if automation.get("pr_url") else ""
        section6 += f'''<div style="background:#e6f7ff; border:1px solid #91d5ff; border-radius:4px; padding:12px; margin:10px 0;">
            <p><strong>仓库：</strong><a class="link" href="{automation.get("repo", "")}" target="_blank">{automation.get("repo", "")}</a></p>
            <p><strong>分支：</strong><code>{automation.get("branch", "")}</code></p>
            {pr_html}
            <p><strong>生成文件：</strong></p><ul style="margin-left:20px;">{files_html}</ul>
            <p style="margin-top:8px;"><strong>可执行用例：</strong>{automation.get("executable", 0)}个 | <strong>跳过用例：</strong>{automation.get("skipped", 0)}个</p>
            <p><strong>跳过原因：</strong></p><ul style="margin-left:20px;">{skip_reasons_html}</ul>
        </div>'''
    else:
        section6 += '<p style="color:#999;">未生成自动化代码</p>'

    # 板块 7: 风险项
    risks = data.get("risks", [])
    section7 = '<h2>⚠️ 风险项</h2>'
    if risks:
        for risk in risks:
            # 兼容两种格式: {level, title, detail} 或 {severity, description}
            severity = risk.get("severity", "")
            level = risk.get("level", "")
            if not level:
                level_map = {"critical": "高", "high": "高", "medium": "中", "low": "低"}
                level = level_map.get(severity, "中")
            title = risk.get("title", "")
            detail = risk.get("detail", "") or risk.get("description", "")
            if not title and detail:
                title = detail[:30] + ("..." if len(detail) > 30 else "")
            if level == "高":
                border_color = "#ff4d4f"
                bg_color = "#fff2f0"
                label_bg = "#ff4d4f"
            elif level == "低":
                border_color = "#91d5ff"
                bg_color = "#e6f7ff"
                label_bg = "#1890ff"
            else:
                border_color = "#faad14"
                bg_color = "#fffbe6"
                label_bg = "#faad14"
            section7 += f'''<div style="background:{bg_color}; border-left:4px solid {border_color}; border-radius:4px; padding:12px 12px 12px 16px; margin:10px 0;">
                <div style="margin-bottom:5px;"><span style="background:{label_bg}; color:#fff; padding:2px 8px; border-radius:3px; font-size:11px; font-weight:bold;">{level}</span> <strong style="margin-left:6px;">{title}</strong></div>
                <p style="color:#333; font-size:13px;">{detail}</p>
            </div>'''
    else:
        section7 += '<div style="text-align:center; padding:20px; color:#52c41a; font-size:16px;">✅ 无风险项</div>'

    # 板块 8: 关键链接
    links = data.get("links", [])
    section8 = ""
    if links:
        section8 = '<h2>🔗 关键链接</h2><table><thead><tr><th>资源</th><th>链接</th></tr></thead><tbody>'
        for link in links:
            label = link.get("label", link.get("name", "链接"))
            section8 += f'<tr><td>{link.get("name", "")}</td><td><a class="link" href="{link.get("url", "")}" target="_blank">{label}</a></td></tr>'
        section8 += '</tbody></table>'

    content = f"{section1}{section2}{section3}{section4}{section5}{section6}{section7}{section8}"
    return generate_report("final", args.op, args.title or f"最终测试报告 - {args.op}", content,
                           start_time=data.get("start_time", ""),
                           end_time=data.get("end_time", ""),
                           duration=data.get("duration", ""))


def main():
    parser = argparse.ArgumentParser(description='HTML 测试报告生成器')
    parser.add_argument('--stage', required=True, help='阶段名称')
    parser.add_argument('--op', required=True, help='OP 编号')
    parser.add_argument('--title', help='报告标题')
    parser.add_argument('--data', help='JSON 数据字符串')
    parser.add_argument('--data-file', help='JSON 数据文件路径（优先于 --data）')
    parser.add_argument('--results-file', help='测试结果 JSON 文件路径')
    parser.add_argument('--context-file', help='pipeline-context.json 路径')
    parser.add_argument('--output', help='输出文件路径（不指定则输出到 stdout）')
    parser.add_argument('--start-time', help='开始时间')
    parser.add_argument('--end-time', help='结束时间')
    parser.add_argument('--duration', help='耗时')

    args = parser.parse_args()

    # 根据阶段生成报告
    if args.stage == "requirement_analysis":
        html = stage_requirement_analysis(args)
    elif args.stage in ("first_test", "bug_fix_verify", "bug_fix_risk", "second_test", "automation_error"):
        html = stage_test_report(args)
    elif args.stage == "final":
        html = stage_final(args)
    else:
        # 通用报告
        data = {}
        if args.data_file:
            with open(args.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif args.data:
            data = json.loads(args.data)
        cards = build_cards(data)
        content = cards
        html = generate_report(args.stage, args.op, args.title or f"报告 - {args.op}", content,
                               start_time=getattr(args, 'start_time', '') or '',
                               end_time=getattr(args, 'end_time', '') or '',
                               duration=getattr(args, 'duration', '') or '')

    # 输出
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(json.dumps({"success": True, "path": str(output_path)}))
    else:
        print(html)


if __name__ == '__main__':
    main()
