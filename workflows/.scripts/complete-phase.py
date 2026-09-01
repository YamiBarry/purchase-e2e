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
import json, os, sys, datetime, re


def main():
    if len(sys.argv) < 3 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0)

    instance_dir = sys.argv[1]
    action = sys.argv[2]

    status_file = os.path.join(instance_dir, "status.json")
    if not os.path.exists(status_file):
        print(f"❌ 错误: status.json 不存在: {status_file}")
        sys.exit(1)

    with open(status_file, "r", encoding="utf-8") as f:
        status = json.load(f)

    now = datetime.datetime.now().isoformat()

    # ─── Special commands ───
    if action == "rollback":
        target = sys.argv[3] if len(sys.argv) > 3 else ""
        reason = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else "Rollback requested"
        if not target:
            print("❌ rollback 需要指定目标阶段 ID")
            sys.exit(1)
        rollback_to(status, target)
        status["currentPhase"] = target
        status["status"] = "running"
        save_status(status_file, status, now)
        append_log(instance_dir, now, "rollback", status.get("currentPhase", ""), f"→ {target}: {reason}")
        print(f"↩️ 已回退到阶段 {target}。原因: {reason}")
        print("STOP")
        sys.exit(0)

    if action in ("block", "pause", "fail"):
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else f"{action} by agent"
        status_map = {"block": "blocked", "pause": "paused", "fail": "failed"}
        emoji_map = {"block": "🚫", "pause": "⏸️", "fail": "❌"}
        action_label = {"block": "挂起", "pause": "暂停", "fail": "标记失败"}
        new_status = status_map[action]
        status["status"] = new_status
        status["lastError"] = reason
        save_status(status_file, status, now)
        append_log(instance_dir, now, action, status.get("currentPhase", ""), reason)
        append_session_summary_on_interrupt(instance_dir, new_status, reason, status.get("currentPhase", ""), now)
        print(f"{emoji_map[action]} 已{action_label[action]}。原因: {reason}")
        print("STOP")
        sys.exit(0)

    if action == "message":
        text = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        status["note"] = text
        save_status(status_file, status, now)
        append_log(instance_dir, now, "message", "-", text[:80])
        print(f"📝 指令已记录，下次执行时 agent 将看到此消息。")
        sys.exit(0)

    # ─── Normal completion: validate and advance ───
    phase_id = action
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    template_dir = find_template_dir(instance_dir)
    if not template_dir:
        print("❌ 无法定位模板目录")
        sys.exit(1)

    wf_path = os.path.join(template_dir, "workflow.json")
    with open(wf_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    phase_def = find_phase_def(workflow.get("phases", []), phase_id)
    if not phase_def:
        print(f"❌ 找不到阶段定义: {phase_id}")
        sys.exit(1)

    outputs_dir = os.path.join(instance_dir, "outputs")

    # ─── Check 1: Required artifacts exist ───
    missing = []
    for artifact in phase_def.get("requiredArtifacts", []):
        if not os.path.exists(os.path.join(outputs_dir, artifact)):
            missing.append(artifact)
    if missing:
        print(f"❌ 产出文件缺失: {', '.join(missing)}")
        print(f"请确保以下文件存在于 {outputs_dir}/:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # ─── Check 2: JSON schema validation ───
    output_schema = phase_def.get("outputSchema", {})
    if output_schema:
        validate_schema(phase_id, outputs_dir, phase_def, template_dir, instance_dir)

    # ─── All checks passed — advance state ───
    mark_done(status["phases"], phase_id, now)
    append_checklist_to_md(instance_dir, phase_id, outputs_dir)

    # ─── Parse output for DAG routing ───
    parsed_output = None
    json_path = os.path.join(outputs_dir, f"phase-{phase_id}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                parsed_output = json.load(f)
        except Exception:
            pass

    # ─── Standard DAG routing ───
    next_phase = route_by_dag(workflow, phase_id, parsed_output, status)

    if next_phase:
        phase_status = get_phase_status(status["phases"], next_phase)
        if phase_status in ("done", "failed"):
            reset_phase_to_pending(status["phases"], next_phase)
            append_log(instance_dir, now, "loop-back", phase_id, f"→ {next_phase}")

    if next_phase:
        status["currentPhase"] = next_phase
    else:
        status["status"] = "completed"
        status["currentPhase"] = ""

    if status.get("note"):
        status["note"] = ""

    save_status(status_file, status, now)
    write_current_phase_file(instance_dir, status.get("currentPhase", ""))
    append_log(instance_dir, now, "complete", phase_id, f"→ {next_phase or 'DONE'}")
    sync_to_db(instance_dir)

    print(f"✅ 阶段 {phase_id}「{phase_def.get('name', '')}」已完成。")
    if next_phase:
        print(f"下一阶段: {next_phase}")
    else:
        print("🎉 所有阶段已完成！")
    print("STOP")


# ─── Schema Validation ───

def validate_schema(phase_id, outputs_dir, phase_def, template_dir, instance_dir):
    """Complete schema validation with fieldValidations support."""
    output_schema = phase_def.get("outputSchema", {})
    required_fields = output_schema.get("requiredFields", [])
    field_types = output_schema.get("fieldTypes", {})
    field_validations = output_schema.get("fieldValidations", {})

    json_file = os.path.join(outputs_dir, f"phase-{phase_id}.json")
    if not os.path.exists(json_file):
        for af in phase_def.get("requiredArtifacts", []):
            if af.endswith(".json"):
                candidate = os.path.join(outputs_dir, af)
                if os.path.exists(candidate):
                    json_file = candidate
                    break
        else:
            return

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ phase-{phase_id}.json 不是有效 JSON: {e}")
        sys.exit(1)

    missing = [f for f in required_fields if f not in data or data[f] is None]
    if missing:
        print(f"❌ phase-{phase_id}.json 缺少必填字段: {', '.join(missing)}")
        print(f"  要求: {required_fields}")
        print(f"  实际: {list(data.keys())}")
        sys.exit(1)

    type_map = {
        "string": str, "str": str, "number": (int, float), "int": (int, float),
        "boolean": bool, "bool": bool, "object": dict, "dict": dict, "array": list, "list": list
    }
    for field, expected in field_types.items():
        if field not in data:
            continue
        expected_types = type_map.get(expected)
        if expected_types and not isinstance(data[field], expected_types):
            actual = type(data[field]).__name__
            print(f"❌ 字段 {field} 类型不匹配: 期望 {expected}, 实际 {actual}")
            sys.exit(1)

    validation_errors = []
    for field, rule in field_validations.items():
        if field not in data:
            continue
        value = data[field]

        if rule == "checklist_required":
            if not isinstance(value, list) or len(value) == 0:
                validation_errors.append(f"{field}: 必须是非空数组，每条包含 item 和 status 字段")
            else:
                bad_items = []
                for i, entry in enumerate(value):
                    if not isinstance(entry, dict):
                        bad_items.append(f"第{i+1}条不是对象")
                    elif not entry.get("item") or not entry.get("status"):
                        bad_items.append(f"第{i+1}条缺少 item 或 status 字段")
                if bad_items:
                    validation_errors.append(f"{field}: checklist 格式错误 - " + "; ".join(bad_items))
                else:
                    ref_count = count_reference_checklist(template_dir, phase_def)
                    if ref_count > 0 and len(value) < ref_count:
                        validation_errors.append(
                            f"{field}: checklist 条目数不足（JSON 有 {len(value)} 条，reference 有 {ref_count} 条，必须 >= {ref_count}）"
                        )
        else:
            error = validate_field_rule(field, rule, value, instance_dir, outputs_dir)
            if error:
                validation_errors.append(error)

    cond_errors = validate_conditional_required(data, output_schema, instance_dir, outputs_dir)
    validation_errors.extend(cond_errors)

    if phase_id == "pm":
        tracking_errors = validate_tracking_for_pm(data, instance_dir, outputs_dir)
        validation_errors.extend(tracking_errors)
    elif phase_id == "arch":
        tracking_errors = validate_tracking_for_arch(data, instance_dir, outputs_dir)
        validation_errors.extend(tracking_errors)

    if validation_errors:
        print(f"❌ Phase {phase_id} 验证失败:")
        for e in validation_errors:
            print(f"  - {e}")
        print("\n请修复后重新调用本脚本。")
        sys.exit(1)


# ─── Extended Field Validation Rules ───

def validate_field_rule(field, rule, value, instance_dir, outputs_dir):
    """扩展的字段验证规则"""
    if not value:
        return None

    if rule == "file_exists":
        workspace_dir = find_workspace_dir(instance_dir)
        full_path = os.path.join(workspace_dir, value)
        if not os.path.exists(full_path):
            return f"{field}: 文件不存在 - {value}（完整路径: {full_path}）"
        return None

    if rule == "file_exists_in_outputs":
        full_path = os.path.join(outputs_dir, value)
        if not os.path.exists(full_path):
            return f"{field}: 产出文件不存在 - {value}"
        return None

    if rule == "url_format":
        if not value.startswith("http://") and not value.startswith("https://"):
            return f"{field}: 必须是有效 URL，当前值: {value}"
        return None

    if rule == "sheet_url_with_gid":
        if not value.startswith("https://docs.google.com/spreadsheets/"):
            return f"{field}: 必须是 Google Sheets URL"
        if "#gid=" not in value:
            return f"{field}: URL 必须包含 #gid=（指向具体 tab），当前值: {value}"
        return None

    if rule.startswith("enum:"):
        allowed = rule.split(":")[1].split(",")
        if value not in allowed:
            return f"{field}: 值 '{value}' 不在允许范围 {allowed}"
        return None

    if rule.startswith("array_min_length:"):
        min_len = int(rule.split(":")[1])
        if not isinstance(value, list):
            return f"{field}: 必须是数组"
        if len(value) < min_len:
            return f"{field}: 数组长度不足，要求至少 {min_len} 项，实际 {len(value)} 项"
        return None

    if rule.startswith("array_items_have:"):
        required_fields = rule.split(":")[1].split(",")
        if not isinstance(value, list):
            return f"{field}: 必须是数组"
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                return f"{field}[{i}]: 必须是对象"
            missing = [fld for fld in required_fields if fld not in item]
            if missing:
                return f"{field}[{i}]: 缺少必填字段 {missing}"
        return None

    return None


def find_workspace_dir(instance_dir):
    """从实例目录定位 workspace 根目录"""
    parts = instance_dir.rstrip("/").split("/")
    if len(parts) >= 3:
        return "/".join(parts[:-3])
    return instance_dir


def validate_conditional_required(data, output_schema, instance_dir, outputs_dir):
    """条件必填验证"""
    cond_config = output_schema.get("conditionalRequired", {})
    if not cond_config:
        return []

    condition = cond_config.get("when", "")
    fields = cond_config.get("fields", [])

    if not condition or not fields:
        return []

    if evaluate_condition(condition, data, instance_dir, outputs_dir):
        missing = [f for f in fields if f not in data or data[f] is None or data[f] == "" or data[f] == []]
        if missing:
            return [f"条件 '{condition}' 满足时，以下字段必填但缺失: {missing}"]

    return []


def evaluate_condition(condition, data, instance_dir, outputs_dir):
    """解析并评估条件表达式"""
    def replace_ref(match):
        ref = match.group(1)
        parts = ref.split(".")
        if len(parts) >= 2:
            phase_id = parts[0]
            field_path = ".".join(parts[1:])
            json_path = os.path.join(outputs_dir, f"{phase_id}.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path) as f:
                        phase_data = json.load(f)
                    value = get_nested_field(phase_data, field_path)
                    return f"'{value or ''}'"
                except Exception:
                    pass
        return "''"

    resolved = re.sub(r"\{\{([^}]+)\}\}", replace_ref, condition)

    # 解析 field == 'value'
    match = re.match(r"(\w+)\s*==\s*['\"]([^'\"]*)['\"]", resolved)
    if match:
        field, expected = match.groups()
        actual = data.get(field, "")
        return str(actual) == expected

    # 解析 'actual' == 'expected'
    match = re.match(r"['\"]([^'\"]*)['\"]\\s*==\\s*['\"]([^'\"]*)['\"]", resolved)
    if match:
        actual, expected = match.groups()
        return actual == expected

    return False


# ─── 埋点专项验证 ───

def validate_tracking_for_pm(data, instance_dir, outputs_dir):
    """PM 阶段埋点专项验证"""
    errors = []

    if data.get("need_tracking") != "yes":
        return []

    spec_path = data.get("tracking_spec_path", "")
    if not spec_path:
        errors.append("need_tracking=yes 时，tracking_spec_path 必填")
    else:
        workspace_dir = find_workspace_dir(instance_dir)
        full_path = os.path.join(workspace_dir, spec_path)
        if not os.path.exists(full_path):
            errors.append(f"tracking_spec_path 指向的文件不存在: {spec_path}（请先创建 requirements/OP-XXXXX/tracking-spec.md）")

    count = data.get("tracking_events_count", 0)
    if not count or count <= 0:
        errors.append("need_tracking=yes 时，tracking_events_count 必须 > 0")

    return errors


def validate_tracking_for_arch(data, instance_dir, outputs_dir):
    """Arch 阶段埋点专项验证"""
    errors = []

    pm_json = os.path.join(outputs_dir, "phase-pm.json")
    if not os.path.exists(pm_json):
        return []

    try:
        with open(pm_json) as f:
            pm_data = json.load(f)
    except Exception:
        return []

    if pm_data.get("need_tracking") != "yes":
        return []

    spec_path = data.get("tracking_spec_path", "")
    if not spec_path:
        errors.append("need_tracking=yes 时，tracking_spec_path 必填")
    else:
        workspace_dir = find_workspace_dir(instance_dir)
        full_path = os.path.join(workspace_dir, spec_path)
        if not os.path.exists(full_path):
            errors.append(f"tracking_spec_path 指向的文件不存在: {spec_path}")

    sheet_url = data.get("tracking_sheet_url", "")
    if not sheet_url:
        errors.append("need_tracking=yes 时，tracking_sheet_url 必填（必须实际调用 add_sheet_tab 创建 tab）")
    elif "#gid=" not in sheet_url:
        errors.append("tracking_sheet_url 必须包含 #gid=xxx（指向你创建的 tab）。只填 tracking_sheet_tab 名字是不够的，必须实际调用 @google-workspace 的 add_sheet_tab 创建 tab 后获取 URL。")

    events = data.get("tracking_events", [])
    if not events:
        errors.append("need_tracking=yes 时，tracking_events 必填且非空")
    else:
        for i, evt in enumerate(events):
            if not isinstance(evt, dict):
                errors.append(f"tracking_events[{i}] 必须是对象")
            else:
                required = ["name", "sensor_name", "trigger"]
                missing_fields = [fld for fld in required if not evt.get(fld)]
                if missing_fields:
                    errors.append(f"tracking_events[{i}] 缺少必填字段: {missing_fields}")

    return errors


def count_reference_checklist(template_dir, phase_def):
    """Count checklist items in the reference markdown file."""
    ref_file = phase_def.get("ref", "")
    if not ref_file or not template_dir:
        return 0
    ref_path = os.path.join(template_dir, "references", ref_file)
    if not os.path.exists(ref_path):
        return 0
    try:
        count = 0
        in_checklist = False
        with open(ref_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if "checklist" in stripped.lower() and stripped.startswith("##"):
                    in_checklist = True
                    continue
                if in_checklist:
                    if stripped.startswith("##"):
                        break
                    if stripped.startswith("- ["):
                        count += 1
        return count
    except Exception:
        return 0


# ─── Loop Detection ───

def check_loop(phase_def, instance_dir):
    """Check if a loop node still has pending batches."""
    phase_id = phase_def.get("id", "")
    output_path = os.path.join(instance_dir, "outputs", f"phase-{phase_id}.json")
    if os.path.exists(output_path):
        try:
            data = json.load(open(output_path))
            if "pending_batches" in data:
                return len(data.get("pending_batches", [])) > 0
            if "all_batches_done" in data:
                return not data.get("all_batches_done", False)
        except Exception:
            pass

    check_file = phase_def.get("loopCompletionCheck")
    if not check_file:
        return False
    check_path = os.path.join(instance_dir, "outputs", check_file)
    if not os.path.exists(check_path):
        return False
    try:
        data = json.load(open(check_path))
        status_field = phase_def.get("loopStatusField", "status")
        batches = data.get("batches", [])
        return any(b.get(status_field) == "pending" for b in batches)
    except Exception:
        return False


# ─── Checklist → MD Append ───

def append_checklist_to_md(instance_dir, phase_id, outputs_dir):
    """Read checklist from phase-X.json and append to phase-X.md."""
    json_path = os.path.join(outputs_dir, f"phase-{phase_id}.json")
    md_path = os.path.join(outputs_dir, f"phase-{phase_id}.md")
    if not os.path.exists(json_path) or not os.path.exists(md_path):
        return
    try:
        data = json.load(open(json_path))
        checklist = data.get("checklist", [])
        if not isinstance(checklist, list) or not checklist:
            return
        lines = ["\n\n## Checklist 执行结果\n"]
        for entry in checklist:
            if isinstance(entry, dict):
                status = entry.get("status", "?")
                item = entry.get("item", "?")
                icon = {"done": "✅", "skipped": "⏭️", "failed": "❌"}.get(status, "⬜")
                note = f" — {entry['note']}" if entry.get("note") else ""
                lines.append(f"- {icon} {item}{note}")
        with open(md_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"[WARN] checklist 追加到 md 失败: {e}", file=sys.stderr)


# ─── Session Summary on Interrupt ───

def append_session_summary_on_interrupt(instance_dir, new_status, reason, current_phase, now):
    """Auto-append interruption info to session-summary.md."""
    labels = {"blocked": "🚫 已阻塞", "paused": "⏸️ 已暂停", "failed": "❌ 已失败"}
    label = labels.get(new_status, new_status)
    entry = f'\n## {label}（{now[:16]}）\n\n**中断阶段**: Phase {current_phase}\n**原因**: {reason}\n**恢复方式**: 通过 API 或面板点击"继续"按钮恢复\n'
    summary_path = os.path.join(instance_dir, "session-summary.md")
    try:
        with open(summary_path, "a", encoding="utf-8") as f:
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
    status["lastUpdated"] = now
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def write_current_phase_file(instance_dir, phase):
    try:
        with open(os.path.join(instance_dir, ".current-phase"), "w") as f:
            f.write(phase)
    except Exception:
        pass


def mark_done(phases, target_id, now):
    for p in phases:
        if p["id"] == target_id:
            p["status"] = "done"
            p["finishedAt"] = now
            return True
        if p.get("subPhases"):
            if mark_done(p["subPhases"], target_id, now):
                if all(s.get("status") in ("done", "skipped") for s in p["subPhases"]):
                    p["status"] = "done"
                    p["finishedAt"] = now
                return True
    return False


def save_parsed_output(phases, target_id, parsed_output):
    """将解析的 JSON 输出保存到 phase state 中"""
    for p in phases:
        if p["id"] == target_id:
            p["parsedOutput"] = parsed_output
            return True
        if p.get("subPhases"):
            if save_parsed_output(p["subPhases"], target_id, parsed_output):
                return True
    return False


def rollback_to(status, target_id):
    found_ref = [False]
    reset_phases(status["phases"], target_id, found_ref)


def reset_phases(phases, target_id, found_ref):
    for p in phases:
        if p["id"] == target_id:
            found_ref[0] = True
        if found_ref[0]:
            p["status"] = "pending"
            p.pop("startedAt", None)
            p.pop("finishedAt", None)
        if p.get("subPhases"):
            reset_phases(p["subPhases"], target_id, found_ref)


def find_next_pending(phases):
    """线性模式下查找下一个 pending 阶段"""
    for p in phases:
        sub = p.get("subPhases", [])
        if sub:
            result = find_next_pending(sub)
            if result:
                return result
            if all(s.get("status") in ("done", "skipped") for s in sub):
                continue
        if p.get("status") == "pending":
            return p["id"]
    return None


def route_by_dag(workflow, current_phase_id, parsed_output, status):
    """标准 DAG 路由：根据 flow.edges 决定下一阶段。"""
    flow = workflow.get("flow", {})
    edges = flow.get("edges", [])

    if not edges:
        return find_next_pending(status.get("phases", []))

    outgoing = [e for e in edges if e.get("source") == current_phase_id]
    if not outgoing:
        return None

    for edge in outgoing:
        condition = edge.get("condition")
        if condition and parsed_output:
            field = condition.get("field", "")
            expected = condition.get("equals", "")
            actual = get_nested_field(parsed_output, field)
            if str(actual) == str(expected):
                return edge.get("target")

    for edge in outgoing:
        if not edge.get("condition"):
            return edge.get("target")

    return None


def get_nested_field(data, field_path):
    """获取嵌套字段值，支持点号路径如 "result.status" """
    if not data or not field_path:
        return None
    parts = field_path.split(".")
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
        if p["id"] == target_id:
            return p.get("status", "pending")
        if p.get("subPhases"):
            result = get_phase_status(p["subPhases"], target_id)
            if result:
                return result
    return None


def reset_phase_to_pending(phases, target_id):
    """将目标阶段重置为 pending（用于回环）"""
    for p in phases:
        if p["id"] == target_id:
            p["status"] = "pending"
            p.pop("startedAt", None)
            p.pop("finishedAt", None)
            p["loopCount"] = p.get("loopCount", 0) + 1
            return True
        if p.get("subPhases"):
            if reset_phase_to_pending(p["subPhases"], target_id):
                return True
    return False


def find_template_dir(instance_dir):
    """从实例目录定位模板目录。"""
    parts = instance_dir.rstrip("/").split("/")
    if len(parts) >= 2:
        template_name = parts[-2]
        workspace_dir = "/".join(parts[:-3])
        template_dir = os.path.join(workspace_dir, "workflows", template_name)
        if os.path.exists(os.path.join(template_dir, "workflow.json")):
            return template_dir
    if len(parts) >= 2:
        template_dir = "/".join(parts[:-2])
        if os.path.exists(os.path.join(template_dir, "workflow.json")):
            return template_dir
    current = instance_dir
    for _ in range(6):
        current = os.path.dirname(current)
        if os.path.exists(os.path.join(current, "workflow.json")):
            return current
    return None


def find_phase_def(phases, target_id):
    for p in phases:
        if p["id"] == target_id:
            return p
        sub = p.get("subPhases") or p.get("phases", [])
        if sub:
            found = find_phase_def(sub, target_id)
            if found:
                return found
    return None


def append_log(instance_dir, now, action, phase, result):
    log_path = os.path.join(instance_dir, "execution-log.md")
    line = f"| {now[:16]} | {action} | {phase} | {result} |\n"
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# 执行日志\n\n| 时间 | 操作 | 阶段 | 结果 |\n|------|------|------|------|\n")
            f.write(line)
    else:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)


if __name__ == "__main__":
    main()
