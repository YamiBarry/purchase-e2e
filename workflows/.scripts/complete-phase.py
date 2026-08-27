#!/usr/bin/env python3
"""通用工作流 — 完成阶段校验与推进

用法:
  python3 complete-phase.py <instance-dir> <phase_id> [output_file]
  python3 complete-phase.py <instance-dir> rollback <target_phase_id> [reason]
  python3 complete-phase.py <instance-dir> block [reason]
  python3 complete-phase.py <instance-dir> pause [reason]
  python3 complete-phase.py <instance-dir> fail [reason]
  python3 complete-phase.py <instance-dir> message <text>
"""
import json, os, sys, datetime


def main():
    if len(sys.argv) < 3 or sys.argv[1] in ('--help', '-h'):
        print(__doc__)
        sys.exit(0)

    instance_dir = sys.argv[1]
    action = sys.argv[2]

    status_file = os.path.join(instance_dir, 'status.json')
    if not os.path.exists(status_file):
        print(f"❌ 错误: status.json 不存在: {status_file}")
        sys.exit(1)

    with open(status_file, 'r', encoding='utf-8') as f:
        status = json.load(f)

    now = datetime.datetime.now().isoformat()

    # ─── Special commands ───
    if action == 'rollback':
        target = sys.argv[3] if len(sys.argv) > 3 else ''
        reason = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else 'Rollback requested'
        if not target:
            print("❌ rollback 需要指定目标阶段 ID")
            sys.exit(1)
        rollback_to(status, target)
        status['currentPhase'] = target
        status['status'] = 'running'
        save_status(status_file, status, now)
        append_log(instance_dir, now, 'rollback', status.get('currentPhase', ''), f'→ {target}: {reason}')
        print(f"↩️ 已回退到阶段 {target}。原因: {reason}")
        print("STOP")
        sys.exit(0)

    if action in ('block', 'pause', 'fail'):
        reason = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else f'{action} by agent'
        status_map = {'block': 'blocked', 'pause': 'paused', 'fail': 'failed'}
        emoji_map = {'block': '🚫', 'pause': '⏸️', 'fail': '❌'}
        action_label = {'block': '挂起', 'pause': '暂停', 'fail': '标记失败'}
        new_status = status_map[action]
        status['status'] = new_status
        status['lastError'] = reason
        save_status(status_file, status, now)
        append_log(instance_dir, now, action, status.get('currentPhase', ''), reason)
        # Auto-append to session-summary.md
        append_session_summary_on_interrupt(instance_dir, new_status, reason, status.get('currentPhase', ''), now)
        print(f"{emoji_map[action]} 已{action_label[action]}。原因: {reason}")
        print("STOP")
        sys.exit(0)

    if action == 'message':
        text = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else ''
        status['note'] = text
        save_status(status_file, status, now)
        append_log(instance_dir, now, 'message', '-', text[:80])
        print(f"📝 指令已记录，下次执行时 agent 将看到此消息。")
        sys.exit(0)

    # ─── Normal completion: validate and advance ───
    phase_id = action
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Find template
    template_dir = find_template_dir(instance_dir)
    if not template_dir:
        print("❌ 无法定位模板目录")
        sys.exit(1)

    wf_path = os.path.join(template_dir, 'workflow.json')
    with open(wf_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    phase_def = find_phase_def(workflow.get('phases', []), phase_id)
    if not phase_def:
        print(f"❌ 找不到阶段定义: {phase_id}")
        sys.exit(1)

    outputs_dir = os.path.join(instance_dir, 'outputs')

    # ─── Check 1: Required artifacts exist ───
    missing = []
    for artifact in phase_def.get('requiredArtifacts', []):
        if not os.path.exists(os.path.join(outputs_dir, artifact)):
            missing.append(artifact)
    if missing:
        print(f"❌ 产出文件缺失: {', '.join(missing)}")
        print(f"请确保以下文件存在于 {outputs_dir}/:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # ─── Check 2: JSON schema validation ───
    output_schema = phase_def.get('outputSchema', {})
    if output_schema:
        validate_schema(phase_id, outputs_dir, phase_def, template_dir)

    # ─── All checks passed — advance state ───
    mark_done(status['phases'], phase_id, now)

    # Append checklist to phase-X.md
    append_checklist_to_md(instance_dir, phase_id, outputs_dir)

    # ─── Parse output for DAG routing ───
    parsed_output = None
    json_path = os.path.join(outputs_dir, f'phase-{phase_id}.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                parsed_output = json.load(f)
        except Exception:
            pass

    # ─── Standard DAG routing ───
    next_phase = route_by_dag(workflow, phase_id, parsed_output, status)
    
    # Handle loop-back: reset target phase to pending
    if next_phase:
        phase_status = get_phase_status(status['phases'], next_phase)
        if phase_status in ('done', 'failed'):
            # This is a loop-back edge, reset the target phase
            reset_phase_to_pending(status['phases'], next_phase)
            append_log(instance_dir, now, 'loop-back', phase_id, f'→ {next_phase}')
    
    # Update status
    if next_phase:
        status['currentPhase'] = next_phase
    else:
        status['status'] = 'completed'
        status['currentPhase'] = ''

    # Clear note after use
    if status.get('note'):
        status['note'] = ''

    save_status(status_file, status, now)
    write_current_phase_file(instance_dir, status.get('currentPhase', ''))
    append_log(instance_dir, now, 'complete', phase_id, f'→ {next_phase or "DONE"}')

    # Sync to DB via HTTP (non-blocking, failure OK)
    sync_to_db(instance_dir)

    print(f"✅ 阶段 {phase_id}「{phase_def.get('name', '')}」已完成。")
    if next_phase:
        print(f"下一阶段: {next_phase}")
    else:
        print("🎉 所有阶段已完成！")
    print("STOP")


# ─── Schema Validation ───

def validate_schema(phase_id, outputs_dir, phase_def, template_dir):
    """Complete schema validation with fieldValidations support."""
    output_schema = phase_def.get('outputSchema', {})
    required_fields = output_schema.get('requiredFields', [])
    field_types = output_schema.get('fieldTypes', {})
    field_validations = output_schema.get('fieldValidations', {})

    # Find the JSON artifact
    json_file = os.path.join(outputs_dir, f'phase-{phase_id}.json')
    if not os.path.exists(json_file):
        # Try other JSON artifacts
        for af in phase_def.get('requiredArtifacts', []):
            if af.endswith('.json'):
                candidate = os.path.join(outputs_dir, af)
                if os.path.exists(candidate):
                    json_file = candidate
                    break
        else:
            return  # No JSON to validate

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ phase-{phase_id}.json 不是有效 JSON: {e}")
        sys.exit(1)

    # Required fields check
    missing = [f for f in required_fields if f not in data or data[f] is None]
    if missing:
        print(f"❌ phase-{phase_id}.json 缺少必填字段: {', '.join(missing)}")
        print(f"  要求: {required_fields}")
        print(f"  实际: {list(data.keys())}")
        sys.exit(1)

    # Type check
    type_map = {'string': str, 'str': str, 'number': (int, float), 'int': (int, float),
                'boolean': bool, 'bool': bool, 'object': dict, 'dict': dict, 'array': list, 'list': list}
    for field, expected in field_types.items():
        if field not in data:
            continue
        expected_types = type_map.get(expected)
        if expected_types and not isinstance(data[field], expected_types):
            actual = type(data[field]).__name__
            print(f"❌ 字段 {field} 类型不匹配: 期望 {expected}, 实际 {actual}")
            sys.exit(1)

    # Field validations (advanced rules)
    validation_errors = []
    for field, rule in field_validations.items():
        if field not in data:
            continue
        value = data[field]

        if rule == 'checklist_required':
            # checklist must be non-empty array, each item has 'item' and 'status'
            if not isinstance(value, list) or len(value) == 0:
                validation_errors.append(f'{field}: 必须是非空数组，每条包含 item 和 status 字段')
            else:
                bad_items = []
                for i, entry in enumerate(value):
                    if not isinstance(entry, dict):
                        bad_items.append(f'第{i+1}条不是对象')
                    elif not entry.get('item') or not entry.get('status'):
                        bad_items.append(f'第{i+1}条缺少 item 或 status 字段')
                if bad_items:
                    validation_errors.append(f'{field}: checklist 格式错误 — {"; ".join(bad_items)}')
                else:
                    # Check count >= reference checklist count
                    ref_count = count_reference_checklist(template_dir, phase_def)
                    if ref_count > 0 and len(value) < ref_count:
                        validation_errors.append(
                            f'{field}: checklist 条目数不足（JSON 有 {len(value)} 条，reference 有 {ref_count} 条，必须 >= {ref_count}）'
                        )

    if validation_errors:
        print(f"❌ Phase {phase_id} fieldValidations 校验失败:")
        for e in validation_errors:
            print(f"  - {e}")
        print("\n请补全后重新调用本脚本。")
        sys.exit(1)


def count_reference_checklist(template_dir, phase_def):
    """Count checklist items in the reference markdown file."""
    ref_file = phase_def.get('ref', '')
    if not ref_file or not template_dir:
        return 0
    ref_path = os.path.join(template_dir, 'references', ref_file)
    if not os.path.exists(ref_path):
        return 0
    try:
        count = 0
        in_checklist = False
        with open(ref_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if 'checklist' in stripped.lower() and stripped.startswith('##'):
                    in_checklist = True
                    continue
                if in_checklist:
                    if stripped.startswith('##'):
                        break  # Next section
                    if stripped.startswith('- ['):
                        count += 1
        return count
    except Exception:
        return 0


# ─── Loop Detection ───

def check_loop(phase_def, instance_dir):
    """Check if a loop node still has pending batches."""
    phase_id = phase_def.get('id', '')
    output_path = os.path.join(instance_dir, 'outputs', f'phase-{phase_id}.json')
    if os.path.exists(output_path):
        try:
            data = json.load(open(output_path))
            if 'pending_batches' in data:
                return len(data.get('pending_batches', [])) > 0
            if 'all_batches_done' in data:
                return not data.get('all_batches_done', False)
        except Exception:
            pass

    check_file = phase_def.get('loopCompletionCheck')
    if not check_file:
        return False
    check_path = os.path.join(instance_dir, 'outputs', check_file)
    if not os.path.exists(check_path):
        return False
    try:
        data = json.load(open(check_path))
        status_field = phase_def.get('loopStatusField', 'status')
        batches = data.get('batches', [])
        return any(b.get(status_field) == 'pending' for b in batches)
    except Exception:
        return False


# ─── Checklist → MD Append ───

def append_checklist_to_md(instance_dir, phase_id, outputs_dir):
    """Read checklist from phase-X.json and append to phase-X.md."""
    json_path = os.path.join(outputs_dir, f'phase-{phase_id}.json')
    md_path = os.path.join(outputs_dir, f'phase-{phase_id}.md')
    if not os.path.exists(json_path) or not os.path.exists(md_path):
        return
    try:
        data = json.load(open(json_path))
        checklist = data.get('checklist', [])
        if not isinstance(checklist, list) or not checklist:
            return
        lines = ['\n\n## Checklist 执行结果\n']
        for entry in checklist:
            if isinstance(entry, dict):
                status = entry.get('status', '?')
                item = entry.get('item', '?')
                icon = {'done': '✅', 'skipped': '⏭️', 'failed': '❌'}.get(status, '⬜')
                note = f" — {entry['note']}" if entry.get('note') else ''
                lines.append(f'- {icon} {item}{note}')
        with open(md_path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except Exception as e:
        print(f'[WARN] checklist 追加到 md 失败: {e}', file=sys.stderr)


# ─── Session Summary on Interrupt ───

def append_session_summary_on_interrupt(instance_dir, new_status, reason, current_phase, now):
    """Auto-append interruption info to session-summary.md."""
    labels = {'blocked': '🚫 已阻塞', 'paused': '⏸️ 已暂停', 'failed': '❌ 已失败'}
    label = labels.get(new_status, new_status)
    entry = f'\n## {label}（{now[:16]}）\n\n**中断阶段**: Phase {current_phase}\n**原因**: {reason}\n**恢复方式**: 通过 API 或面板点击"继续"按钮恢复\n'
    summary_path = os.path.join(instance_dir, 'session-summary.md')
    try:
        with open(summary_path, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass


# ─── DB Sync ───

def sync_to_db(instance_dir):
    """Sync file-system state to SQLite via HTTP."""
    try:
        import urllib.request
        parts = instance_dir.rstrip("/").split("/")
        instance_id = parts[-1]
        template_name = parts[-2]
        if not template_name or not instance_id:
            return
        for port in [os.environ.get("PORT", "8900"), "9999"]:
            try:
                url = f"http://localhost:{port}/api/workflow/instances/{template_name}/{instance_id}/sync"
                req = urllib.request.Request(url, method="POST", data=b"{}")
                req.add_header("Content-Type", "application/json")
                urllib.request.urlopen(req, timeout=3)
                return
            except Exception:
                continue
    except Exception:
        pass


# ─── Helper Functions ───

def save_status(path, status, now):
    status['lastUpdated'] = now
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def write_current_phase_file(instance_dir, phase):
    try:
        with open(os.path.join(instance_dir, '.current-phase'), 'w') as f:
            f.write(phase)
    except Exception:
        pass


def mark_done(phases, target_id, now):
    for p in phases:
        if p['id'] == target_id:
            p['status'] = 'done'
            p['finishedAt'] = now
            return True
        if p.get('subPhases'):
            if mark_done(p['subPhases'], target_id, now):
                if all(s.get('status') in ('done', 'skipped') for s in p['subPhases']):
                    p['status'] = 'done'
                    p['finishedAt'] = now
                return True
    return False


def save_parsed_output(phases, target_id, parsed_output):
    """将解析的 JSON 输出保存到 phase state 中"""
    for p in phases:
        if p['id'] == target_id:
            p['parsedOutput'] = parsed_output
            return True
        if p.get('subPhases'):
            if save_parsed_output(p['subPhases'], target_id, parsed_output):
                return True
    return False


def rollback_to(status, target_id):
    found_ref = [False]
    reset_phases(status['phases'], target_id, found_ref)


def reset_phases(phases, target_id, found_ref):
    for p in phases:
        if p['id'] == target_id:
            found_ref[0] = True
        if found_ref[0]:
            p['status'] = 'pending'
            p.pop('startedAt', None)
            p.pop('finishedAt', None)
        if p.get('subPhases'):
            reset_phases(p['subPhases'], target_id, found_ref)


def find_next_pending(phases):
    """线性模式下查找下一个 pending 阶段"""
    for p in phases:
        sub = p.get('subPhases', [])
        if sub:
            result = find_next_pending(sub)
            if result:
                return result
            if all(s.get('status') in ('done', 'skipped') for s in sub):
                continue
        if p.get('status') == 'pending':
            return p['id']
    return None


def route_by_dag(workflow, current_phase_id, parsed_output, status):
    """
    标准 DAG 路由：根据 flow.edges 决定下一阶段。
    
    路由规则：
    1. 找出从当前节点出发的所有边
    2. 优先检查条件边（有 condition 的），字段值匹配则走该边
    3. 条件都不匹配，走默认边（无 condition 的第一条边）
    4. 没有出边或 edges 为空，退回线性顺序
    
    返回: 下一阶段 ID，或 None 表示流程结束
    """
    flow = workflow.get('flow', {})
    edges = flow.get('edges', [])
    
    # 没有 edges → 退回线性模式
    if not edges:
        return find_next_pending(status.get('phases', []))
    
    # 找出从当前节点出发的所有边
    outgoing = [e for e in edges if e.get('source') == current_phase_id]
    if not outgoing:
        return None  # 没有出边，流程结束
    
    # 先检查条件边
    for edge in outgoing:
        condition = edge.get('condition')
        if condition and parsed_output:
            field = condition.get('field', '')
            expected = condition.get('equals', '')
            actual = get_nested_field(parsed_output, field)
            if str(actual) == str(expected):
                return edge.get('target')
    
    # 走默认边（无 condition 的第一条）
    for edge in outgoing:
        if not edge.get('condition'):
            return edge.get('target')
    
    # 都是条件边但没命中 → 流程结束
    return None


def get_nested_field(data, field_path):
    """获取嵌套字段值，支持点号路径如 "result.status" """
    if not data or not field_path:
        return None
    parts = field_path.split('.')
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def get_phase_status(phases, target_id):
    """获取阶段状态"""
    for p in phases:
        if p['id'] == target_id:
            return p.get('status', 'pending')
        if p.get('subPhases'):
            result = get_phase_status(p['subPhases'], target_id)
            if result:
                return result
    return None


def reset_phase_to_pending(phases, target_id):
    """将目标阶段重置为 pending（用于回环）"""
    for p in phases:
        if p['id'] == target_id:
            p['status'] = 'pending'
            p.pop('startedAt', None)
            p.pop('finishedAt', None)
            p['loopCount'] = p.get('loopCount', 0) + 1
            return True
        if p.get('subPhases'):
            if reset_phase_to_pending(p['subPhases'], target_id):
                return True
    return False


def find_template_dir(instance_dir):
    """从实例目录定位模板目录。
    新路径: workspace/workflow-instances/{template}/{id}
    模板在: workspace/workflows/{template}/
    """
    parts = instance_dir.rstrip('/').split('/')
    if len(parts) >= 2:
        template_name = parts[-2]
        workspace_dir = '/'.join(parts[:-3])
        template_dir = os.path.join(workspace_dir, 'workflows', template_name)
        if os.path.exists(os.path.join(template_dir, 'workflow.json')):
            return template_dir
    # Fallback: old path
    if len(parts) >= 2:
        template_dir = '/'.join(parts[:-2])
        if os.path.exists(os.path.join(template_dir, 'workflow.json')):
            return template_dir
    current = instance_dir
    for _ in range(6):
        current = os.path.dirname(current)
        if os.path.exists(os.path.join(current, 'workflow.json')):
            return current
    return None


def find_phase_def(phases, target_id):
    for p in phases:
        if p['id'] == target_id:
            return p
        sub = p.get('subPhases') or p.get('phases', [])
        if sub:
            found = find_phase_def(sub, target_id)
            if found:
                return found
    return None


def append_log(instance_dir, now, action, phase, result):
    log_path = os.path.join(instance_dir, 'execution-log.md')
    line = f'| {now[:16]} | {action} | {phase} | {result} |\n'
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('# 执行日志\n\n| 时间 | 操作 | 阶段 | 结果 |\n|------|------|------|------|\n')
            f.write(line)
    else:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(line)


if __name__ == '__main__':
    main()
