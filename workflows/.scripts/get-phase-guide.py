#!/usr/bin/env python3
"""通用工作流 — 获取当前阶段提示词

用法: python3 get-phase-guide.py <instance-dir> [phase_id] [--readonly]

不传 phase_id: 自动找当前 pending/running 的节点
传 phase_id: 返回指定节点的提示词
--readonly: 不修改状态（面板查看用）
"""
import json, os, sys, datetime


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("用法: python3 get-phase-guide.py <instance-dir> [phase_id] [--readonly]")
        sys.exit(0)

    instance_dir = sys.argv[1]
    phase_id_arg = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else ''
    readonly = '--readonly' in sys.argv

    status_file = os.path.join(instance_dir, 'status.json')
    if not os.path.exists(status_file):
        print(f"❌ 错误: status.json 不存在: {status_file}")
        sys.exit(1)

    with open(status_file, 'r', encoding='utf-8') as f:
        status = json.load(f)

    # Determine target phase
    if phase_id_arg:
        target_id = phase_id_arg
    else:
        target_id = find_next_pending(status.get('phases', []))
        if not target_id:
            print("✅ 所有阶段已完成！工作流执行结束。")
            # Mark completed
            if not readonly:
                status['status'] = 'completed'
                status['lastUpdated'] = datetime.datetime.now().isoformat()
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(status, f, ensure_ascii=False, indent=2)
            sys.exit(0)

    # Mark phase as running
    if not readonly:
        mark_running(status['phases'], target_id)
        status['currentPhase'] = target_id
        status['lastUpdated'] = datetime.datetime.now().isoformat()
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    # Find template directory (look for workflow.json up from instance dir)
    template_dir = find_template_dir(instance_dir)
    if not template_dir:
        print(f"❌ 错误: 无法定位模板目录")
        sys.exit(1)

    # Load workflow.json to get phase definition
    wf_path = os.path.join(template_dir, 'workflow.json')
    with open(wf_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    phase_def = find_phase_def(workflow.get('phases', []), target_id)
    if not phase_def:
        print(f"❌ 错误: 找不到阶段定义 {target_id}")
        sys.exit(1)

    # Load reference file
    ref_file = phase_def.get('ref', '')
    ref_content = ''
    if ref_file:
        ref_path = os.path.join(template_dir, 'references', ref_file)
        if os.path.exists(ref_path):
            with open(ref_path, 'r', encoding='utf-8') as f:
                ref_content = f.read()

    # Load previous phase output (inject context)
    prev_output = get_previous_output(instance_dir, status['phases'], target_id)

    # Load user message (if any)
    user_message = status.get('note', '')

    # Build guide output
    output = []
    output.append(f"# 阶段 {target_id}: {phase_def.get('name', '')}")
    output.append(f"\n> {phase_def.get('description', '')}")
    output.append(f"\n**节点类型**: {phase_def.get('nodeType', 'cli')}")

    if phase_def.get('dependsOn'):
        output.append(f"**依赖阶段**: {', '.join(phase_def['dependsOn'])}")

    if user_message:
        output.append(f"\n## 📝 人工指令\n\n{user_message}")

    if prev_output:
        output.append(f"\n## 上一步产出（自动注入）\n\n```json\n{prev_output[:3000]}\n```")

    if ref_content:
        output.append(f"\n## 执行指南\n\n{ref_content}")

    output.append(f"\n## 产出要求\n")
    output.append(f"- 产出文件写入: `{instance_dir}/outputs/`")
    output.append(f"- 必须产出: {', '.join(phase_def.get('requiredArtifacts', []))}")

    if phase_def.get('outputSchema', {}).get('requiredFields'):
        output.append(f"- JSON 必填字段: {', '.join(phase_def['outputSchema']['requiredFields'])}")

    # Parameters
    params = status.get('params', {})
    if params:
        output.append(f"\n## 参数\n")
        for k, v in params.items():
            output.append(f"- **{k}**: {v}")

    print('\n'.join(output))


def find_next_pending(phases, parent_done=False):
    """深度优先找第一个 pending 节点"""
    for p in phases:
        sub = p.get('subPhases', [])
        if sub:
            result = find_next_pending(sub)
            if result:
                return result
            # All sub done → parent done
            if all(s.get('status') in ('done', 'skipped') for s in sub):
                if p.get('status') != 'done':
                    p['status'] = 'done'
                continue
        if p.get('status') == 'pending':
            return p['id']
    return None


def mark_running(phases, target_id):
    """标记目标阶段为 running"""
    for p in phases:
        if p['id'] == target_id:
            p['status'] = 'running'
            p['startedAt'] = datetime.datetime.now().isoformat()
            return True
        if p.get('subPhases'):
            if mark_running(p['subPhases'], target_id):
                return True
    return False


def find_template_dir(instance_dir):
    """从实例目录定位模板目录。
    新路径: workspace/workflow-instances/{template}/{id}
    模板在: workspace/workflows/{template}/
    """
    parts = instance_dir.rstrip('/').split('/')
    # instance_dir = .../workflow-instances/template_name/instance_id
    if len(parts) >= 2:
        template_name = parts[-2]
        # Go up to workspace level, then into workflows/
        workspace_dir = '/'.join(parts[:-3])  # remove workflow-instances/name/id
        template_dir = os.path.join(workspace_dir, 'workflows', template_name)
        if os.path.exists(os.path.join(template_dir, 'workflow.json')):
            return template_dir
    # Fallback: old path (instances inside template dir)
    if len(parts) >= 2:
        template_dir = '/'.join(parts[:-2])
        if os.path.exists(os.path.join(template_dir, 'workflow.json')):
            return template_dir
    # Fallback: search parent dirs
    current = instance_dir
    for _ in range(6):
        current = os.path.dirname(current)
        if os.path.exists(os.path.join(current, 'workflow.json')):
            return current
    return None


def find_phase_def(phases, target_id):
    """递归查找阶段定义"""
    for p in phases:
        if p['id'] == target_id:
            return p
        if p.get('subPhases'):
            found = find_phase_def(p['subPhases'], target_id)
            if found:
                return found
    return None


def get_previous_output(instance_dir, phases, target_id):
    """获取上一个已完成阶段的 JSON 输出"""
    done_ids = []
    collect_done(phases, done_ids)
    if not done_ids:
        return ''

    # Get the last done phase's output
    last_id = done_ids[-1]
    output_path = os.path.join(instance_dir, 'outputs', f'phase-{last_id}.json')
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


def collect_done(phases, result):
    """收集所有已完成的阶段 ID（按顺序）"""
    for p in phases:
        if p.get('subPhases'):
            collect_done(p['subPhases'], result)
        if p.get('status') == 'done':
            result.append(p['id'])


if __name__ == '__main__':
    main()
