#!/usr/bin/env python3
"""
Pipeline 状态管理器

管理 pipeline-context.json 的读写和状态流转。
供 LLM 通过 shell 调用。

使用方式:
    # 初始化
    python scripts/state_manager.py --op OP-123456 --action init \
        --trigger requirement_ready \
        --requirement-doc "https://..." \
        --platform PC --channel Purchase --unit "地址管理" --env UAT

    # 更新阶段
    python scripts/state_manager.py --op OP-123456 --action update_phase \
        --phase requirement_analyzed

    # 更新字段
    python scripts/state_manager.py --op OP-123456 --action set \
        --key knowledge_doc_url --value "https://docs.yamibuy.net/doc/xxx"

    # 添加报告
    python scripts/state_manager.py --op OP-123456 --action add_report \
        --stage first_test --url "https://cdn.yamibuy.com/..."

    # 添加 Bug
    python scripts/state_manager.py --op OP-123456 --action add_bug \
        --case-number PC_ADDRESS_003 --case-name "编辑地址失败" --error "省份下拉为空"

    # 清除 Bug 列表
    python scripts/state_manager.py --op OP-123456 --action clear_bugs

    # 增加轮次
    python scripts/state_manager.py --op OP-123456 --action increment \
        --counter bug_fix_round

    # 查看状态
    python scripts/state_manager.py --op OP-123456 --action status

    # 输出完整 JSON
    python scripts/state_manager.py --op OP-123456 --action dump
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def get_context_path(op_number: str) -> Path:
    """获取 pipeline-context.json 路径"""
    return Path(f"docs/recordings/{op_number}/pipeline-context.json")


def load_context(op_number: str) -> dict:
    """加载上下文"""
    path = get_context_path(op_number)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_context(op_number: str, context: dict):
    """保存上下文"""
    path = get_context_path(op_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    context["updated_at"] = datetime.now().isoformat()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(context, f, ensure_ascii=False, indent=2)


def action_init(args):
    """初始化 pipeline context"""
    context = {
        "pipeline_id": f"{args.op}_{datetime.now().strftime('%Y%m%dT%H%M%S')}",
        "op_number": args.op,
        "trigger": args.trigger or "requirement_ready",
        "current_phase": "idle",
        "platform": args.platform or "",
        "project_type": args.project_type or "EC",
        "channel": args.channel or "",
        "unit": args.unit or "",
        "env": args.env or "UAT",
        "requirement_doc": args.requirement_doc or "",
        "design_doc": args.design_doc or "",
        "branch": args.branch or "",
        "tracking_doc": args.tracking_doc or "",
        "knowledge_doc_url": "",
        "knowledge_doc_id": "",
        "test_cases_url": "",
        "spreadsheet_id": "",
        "bug_fix_round": 0,
        "second_test_round": 0,
        "bug_list": [],
        "test_results": [],
        "reports": {},
        "risks": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    save_context(args.op, context)
    print(json.dumps(context, ensure_ascii=False, indent=2))


def action_update_phase(args):
    """更新当前阶段"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    context["current_phase"] = args.phase
    save_context(args.op, context)
    print(json.dumps({"success": True, "current_phase": args.phase}))


def action_set(args):
    """设置字段值"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)

    # 尝试解析 JSON 值
    try:
        value = json.loads(args.value)
    except (json.JSONDecodeError, TypeError):
        value = args.value

    context[args.key] = value
    save_context(args.op, context)
    print(json.dumps({"success": True, "key": args.key, "value": value}))


def action_add_report(args):
    """添加报告链接"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    if "reports" not in context:
        context["reports"] = {}
    context["reports"][args.stage] = args.url
    save_context(args.op, context)
    print(json.dumps({"success": True, "stage": args.stage, "url": args.url}))


def action_add_bug(args):
    """添加 Bug"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    if "bug_list" not in context:
        context["bug_list"] = []
    bug = {
        "case_number": args.case_number,
        "case_name": args.case_name,
        "error": args.error,
        "timestamp": datetime.now().isoformat()
    }
    if args.screenshot:
        bug["screenshot"] = args.screenshot
    context["bug_list"].append(bug)
    save_context(args.op, context)
    print(json.dumps({"success": True, "bug": bug}))


def action_clear_bugs(args):
    """清除 Bug 列表"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    context["bug_list"] = []
    save_context(args.op, context)
    print(json.dumps({"success": True, "message": "bug_list cleared"}))


def action_increment(args):
    """增加计数器"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    counter = args.counter
    context[counter] = context.get(counter, 0) + 1
    save_context(args.op, context)
    print(json.dumps({"success": True, "counter": counter, "value": context[counter]}))


def action_status(args):
    """查看状态摘要"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    summary = {
        "op_number": context.get("op_number"),
        "current_phase": context.get("current_phase"),
        "bug_fix_round": context.get("bug_fix_round", 0),
        "second_test_round": context.get("second_test_round", 0),
        "bug_count": len(context.get("bug_list", [])),
        "reports": context.get("reports", {}),
        "risks_count": len(context.get("risks", [])),
        "updated_at": context.get("updated_at")
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def action_dump(args):
    """输出完整 JSON"""
    context = load_context(args.op)
    if not context:
        print(json.dumps({"error": "context not found"}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(context, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Pipeline 状态管理器')
    parser.add_argument('--op', required=True, help='OP 编号')
    parser.add_argument('--action', required=True,
                        choices=['init', 'update_phase', 'set', 'add_report',
                                 'add_bug', 'clear_bugs', 'increment', 'status', 'dump'],
                        help='操作类型')

    # init 参数
    parser.add_argument('--trigger', help='触发类型')
    parser.add_argument('--requirement-doc', help='需求文档 URL')
    parser.add_argument('--design-doc', help='设计稿 URL')
    parser.add_argument('--platform', help='平台')
    parser.add_argument('--project-type', help='项目类型')
    parser.add_argument('--channel', help='Channel')
    parser.add_argument('--unit', help='功能模块')
    parser.add_argument('--env', help='测试环境')
    parser.add_argument('--branch', help='开发分支')
    parser.add_argument('--tracking-doc', help='埋点文档')

    # update_phase 参数
    parser.add_argument('--phase', help='阶段名称')

    # set 参数
    parser.add_argument('--key', help='字段名')
    parser.add_argument('--value', help='字段值')

    # add_report 参数
    parser.add_argument('--stage', help='阶段名称')
    parser.add_argument('--url', help='报告 URL')

    # add_bug 参数
    parser.add_argument('--case-number', help='用例编号')
    parser.add_argument('--case-name', help='用例名称')
    parser.add_argument('--error', help='错误信息')
    parser.add_argument('--screenshot', help='截图路径')

    # increment 参数
    parser.add_argument('--counter', help='计数器名称')

    args = parser.parse_args()

    actions = {
        'init': action_init,
        'update_phase': action_update_phase,
        'set': action_set,
        'add_report': action_add_report,
        'add_bug': action_add_bug,
        'clear_bugs': action_clear_bugs,
        'increment': action_increment,
        'status': action_status,
        'dump': action_dump,
    }

    actions[args.action](args)


if __name__ == '__main__':
    main()
