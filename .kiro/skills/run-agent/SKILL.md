---
name: run-agent
description: 调度子 Agent 执行任务。当需要将子任务派发给其他 agent（如 coder-agent、qa-agent、reviewer-agent 等）时使用。支持同步等待结果和异步提交+轮询两种模式。触发词：subagent, 子任务, 派发, 调度agent, run-agent
---

# 子 Agent 调度

通过 `run-agent` 脚本调度其他 kiro agent 执行子任务。基于 ACP 协议通信，稳定可靠。

## 安装

1. 将 `run-agent.py` 放到你的 workspace 的 `bin/` 目录下（或任意 PATH 目录）
2. 赋予执行权限：`chmod +x bin/run-agent.py`
3. 将本 `SKILL.md` 放到 `.kiro/skills/run-agent/SKILL.md`
4. 确保系统已安装 `kiro-cli` 并可在命令行调用

## 前置条件

- Python 3.10+（需要 `tuple[...]` 语法和 `match` 支持）
- `kiro-cli` 已安装并在 PATH 中
- 目标 agent 已在 workspace 或 global 中注册

## 脚本路径

安装后根据你的实际路径修改，例如：`~/workspace/bin/run-agent.py`

## 操作

### 同步执行（等待完成后返回结果）

适用于预计 < 5 分钟的任务。主 agent 会阻塞等待。

```bash
python3 bin/run-agent.py --agent <agent-name> --query "<任务描述>" [--context "<上下文>"] [--working-dir <路径>] [--timeout <秒>]
```

参数说明：
- `--agent`: 目标 agent 名称（必填）
- `--query`: 任务指令（必填）
- `--context`: 可选，额外上下文信息，会拼接到 query 前面
- `--working-dir`: 可选，指定执行目录（决定 agent 发现和代码操作目录），不传则用当前 cwd
- `--timeout`: 可选，超时秒数，默认 600

示例：
```bash
python3 bin/run-agent.py \
  --agent coder-agent \
  --query "实现 OrderNoteService" \
  --context "$(cat ai-workspace/OP-34000/03_architecture/arch.md)" \
  --working-dir /path/to/your/repo \
  --timeout 300
```

### 异步执行（立即返回 task_id，后续轮询结果）

适用于长时间任务，或需要并行派发多个子任务的场景。

```bash
# 提交任务（立即返回 task_id）
TASK_ID=$(python3 bin/run-agent.py --async --agent <agent-name> --query "<任务描述>")

# 查询状态
python3 bin/run-agent.py status $TASK_ID

# 阻塞等待完成（带超时）
python3 bin/run-agent.py wait $TASK_ID --timeout 600
```

status/wait 返回 JSON：
```json
{
  "task_id": "task-1778120194-619c01",
  "status": "completed",
  "agent": "coder-agent",
  "cwd": "/path/to/repo",
  "exit_code": 0,
  "reply": "agent 的完整回复内容",
  "created_at": "2026-05-07T10:16:34+0800",
  "completed_at": "2026-05-07T10:16:52+0800"
}
```

status 字段值：`running` | `completed` | `failed` | `timeout`

### 并行派发多个任务

```bash
T1=$(python3 bin/run-agent.py --async --agent coder-agent --query "实现模块A")
T2=$(python3 bin/run-agent.py --async --agent qa-agent --query "编写模块B测试")

# 等待全部完成
python3 bin/run-agent.py wait $T1
python3 bin/run-agent.py wait $T2
```

### 列出所有任务

```bash
python3 bin/run-agent.py list
```

### 列出可用 agent

```bash
python3 bin/run-agent.py agents [--working-dir <路径>]
```

## 注意事项

1. `--working-dir` 决定了子 agent 能发现哪些 workspace agent 和 steering rules
2. 同步模式下 stdout 直接是 agent 的回复文本；异步模式下 stdout 是 task_id
3. 子 agent 拥有完整的工具能力（fs_read, fs_write, execute_bash, code, grep 等）
4. context 内容过长时建议写入临时文件，用 `$(cat file)` 传入
5. 任务状态默认存储在 `/tmp/kiro-tasks/`，可通过环境变量 `TASK_CENTER_DIR` 自定义
