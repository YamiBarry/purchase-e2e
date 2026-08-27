#!/usr/bin/env python3
"""run-agent: Spawn a kiro-cli subagent task via ACP protocol (sync or async).

Usage:
  run-agent --agent <name> --query "..." [--context "..."] [--working-dir /path] [--timeout 600]
  run-agent --async --agent <name> --query "..." [--context "..."] [--working-dir /path] [--timeout 600]
  run-agent status <task_id>
  run-agent wait <task_id> [--timeout 600]
  run-agent list
  run-agent agents [--working-dir /path]
"""
import argparse, asyncio, json, os, subprocess, sys, time, uuid

TASK_DIR = os.environ.get("TASK_CENTER_DIR", "/tmp/kiro-tasks")
os.makedirs(TASK_DIR, exist_ok=True)

# 确保 kiro-cli 在 PATH 中
_sep = ";" if sys.platform == "win32" else ":"
_local_bin = os.path.expanduser("~/.local/bin")
if _local_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{_local_bin}{_sep}{os.environ.get('PATH', '')}"
if sys.platform == "win32":
    _win_bin = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Kiro-Cli")
    if os.path.isdir(_win_bin) and _win_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{_win_bin}{_sep}{os.environ.get('PATH', '')}"


# ---- ACP client ----

async def run_acp(agent: str, query: str, cwd: str, timeout: float) -> tuple[int, str]:
    """Spawn kiro-cli acp, send prompt, collect reply. Returns (exit_code, reply)."""
    cmd = ["kiro-cli", "acp", "--trust-all-tools"]
    if agent:
        cmd += ["--agent", agent]

    # 使用自定义 limit 避免超长行报错
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE, cwd=cwd,
    )
    # 替换 stdout 的 StreamReader 以增大 buffer limit
    if hasattr(proc.stdout, '_limit'):
        proc.stdout._limit = 50 * 1024 * 1024  # 50MB

    msg_id = 0

    async def send_rpc(method, params):
        nonlocal msg_id
        msg_id += 1
        line = json.dumps({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})
        proc.stdin.write((line + "\n").encode())
        await proc.stdin.drain()
        return msg_id

    async def wait_result(mid, deadline):
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for RPC response")
            raw = await asyncio.wait_for(proc.stdout.readline(), timeout=max(remaining, 0.1))
            if not raw:
                raise RuntimeError("ACP process exited unexpectedly")
            try:
                msg = json.loads(raw.decode().strip())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(str(msg["error"]))
                return msg.get("result")
        raise TimeoutError("Timed out waiting for RPC response")

    try:
        deadline = time.time() + timeout

        # initialize
        mid = await send_rpc("initialize", {
            "protocolVersion": 1, "clientCapabilities": {},
            "clientInfo": {"name": "run-agent", "version": "1.0"},
        })
        await wait_result(mid, deadline)

        # session/new
        mid = await send_rpc("session/new", {"cwd": cwd, "mcpServers": []})
        result = await wait_result(mid, deadline)
        session_id = result.get("sessionId", "") if isinstance(result, dict) else ""

        # session/prompt
        mid = await send_rpc("session/prompt", {
            "sessionId": session_id,
            "prompt": [{"type": "text", "text": query}],
        })

        # collect chunks until end_turn
        full_text = ""
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for agent response")
            try:
                raw = await asyncio.wait_for(proc.stdout.readline(), timeout=min(remaining, 30))
            except asyncio.TimeoutError:
                if time.time() >= deadline:
                    raise TimeoutError("Timed out waiting for agent response")
                continue  # 30s内无输出但总超时未到，继续等待
            if not raw:
                break
            try:
                msg = json.loads(raw.decode().strip())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if msg.get("method") == "session/update":
                update = msg.get("params", {}).get("update", {})
                if update.get("sessionUpdate") == "agent_message_chunk":
                    full_text += update.get("content", {}).get("text", "")
            elif msg.get("id") == mid and "result" in msg:
                r = msg["result"]
                if isinstance(r, dict) and r.get("stopReason") == "end_turn":
                    break

        proc.stdin.close()
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

        return (0, full_text)

    except (TimeoutError, asyncio.TimeoutError):
        proc.kill()
        await proc.wait()
        return (124, "timeout")
    except Exception as e:
        proc.kill()
        await proc.wait()
        return (1, f"error: {e}")


# ---- task management ----

def gen_id():
    return f"task-{int(time.time())}-{uuid.uuid4().hex[:6]}"


def build_query(query: str, context: str | None) -> str:
    if context:
        return f"## Context\n\n{context}\n\n## Task\n\n{query}"
    return query


def cmd_run_sync(args):
    full_query = build_query(args.query, args.context)
    cwd = args.working_dir or os.getcwd()
    exit_code, reply = asyncio.run(run_acp(args.agent, full_query, cwd, args.timeout))
    sys.stdout.buffer.write(reply.encode('utf-8', errors='replace'))
    sys.stdout.buffer.write(b'\n')
    sys.stdout.buffer.flush()
    sys.exit(0 if exit_code == 0 else 1)


def cmd_run_async(args):
    task_id = gen_id()
    task_dir = os.path.join(TASK_DIR, task_id)
    os.makedirs(task_dir)

    full_query = build_query(args.query, args.context)
    cwd = args.working_dir or os.getcwd()

    # Write task metadata
    meta = {"agent": args.agent, "cwd": cwd, "timeout": args.timeout, "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    with open(os.path.join(task_dir, "meta.json"), "w") as f:
        json.dump(meta, f)
    with open(os.path.join(task_dir, "status"), "w") as f:
        f.write("running")

    # Spawn background worker
    worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run-agent")
    subprocess.Popen(
        [sys.executable, worker, "_worker", task_id, args.agent, cwd, str(args.timeout), full_query],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    print(task_id)


def cmd_worker(args):
    """Background worker process — runs ACP and writes result to task dir."""
    _, task_id, agent, cwd, timeout_str, query = args
    task_dir = os.path.join(TASK_DIR, task_id)
    timeout = float(timeout_str)

    exit_code, reply = asyncio.run(run_acp(agent, query, cwd, timeout))

    with open(os.path.join(task_dir, "output"), "w") as f:
        f.write(reply)
    with open(os.path.join(task_dir, "exit_code"), "w") as f:
        f.write(str(exit_code))
    status = "completed" if exit_code == 0 else ("timeout" if exit_code == 124 else "failed")
    with open(os.path.join(task_dir, "status"), "w") as f:
        f.write(status)
    with open(os.path.join(task_dir, "completed_at"), "w") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%S%z"))


def cmd_status(task_id: str):
    task_dir = os.path.join(TASK_DIR, task_id)
    if not os.path.isdir(task_dir):
        print(json.dumps({"error": "task not found"}))
        sys.exit(1)

    status = open(os.path.join(task_dir, "status")).read().strip()
    meta = json.load(open(os.path.join(task_dir, "meta.json")))
    result = {"task_id": task_id, "status": status, **meta}

    if status != "running":
        result["exit_code"] = int(open(os.path.join(task_dir, "exit_code")).read().strip())
        result["reply"] = open(os.path.join(task_dir, "output")).read()
        result["completed_at"] = open(os.path.join(task_dir, "completed_at")).read().strip()

    print(json.dumps(result, ensure_ascii=False))


def cmd_wait(task_id: str, timeout: float):
    task_dir = os.path.join(TASK_DIR, task_id)
    if not os.path.isdir(task_dir):
        print(json.dumps({"error": "task not found"}))
        sys.exit(1)

    elapsed = 0
    while elapsed < timeout:
        status = open(os.path.join(task_dir, "status")).read().strip()
        if status != "running":
            break
        time.sleep(2)
        elapsed += 2

    cmd_status(task_id)


def cmd_list():
    tasks = []
    for name in sorted(os.listdir(TASK_DIR), reverse=True):
        task_dir = os.path.join(TASK_DIR, name)
        if not os.path.isdir(task_dir) or not os.path.exists(os.path.join(task_dir, "meta.json")):
            continue
        status = open(os.path.join(task_dir, "status")).read().strip()
        meta = json.load(open(os.path.join(task_dir, "meta.json")))
        tasks.append({"task_id": name, "status": status, "agent": meta.get("agent", "")})
    print(json.dumps(tasks, ensure_ascii=False))


def cmd_agents(working_dir: str | None):
    cwd = working_dir or os.getcwd()
    result = subprocess.run(["kiro-cli", "agent", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    import re
    output = re.sub(r'\x1b\[[0-9;]*m', '', (result.stdout or '') + (result.stderr or ''))
    agents = []
    for line in output.splitlines():
        m = re.match(r'\s*\*?\s*(\S+)\s+(Workspace|Global)\s*(.*)', line)
        if m and '(Built-in)' not in line:
            agents.append({"name": m.group(1), "scope": m.group(2).lower(), "description": m.group(3).strip()})
    print(json.dumps(agents, ensure_ascii=False))


# ---- main ----

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_worker":
        cmd_worker(sys.argv[1:])
        return

    parser = argparse.ArgumentParser(prog="run-agent", description="Kiro subagent task runner")
    sub = parser.add_subparsers(dest="command")

    # status
    p_status = sub.add_parser("status", help="Get task status")
    p_status.add_argument("task_id")

    # wait
    p_wait = sub.add_parser("wait", help="Wait for task completion")
    p_wait.add_argument("task_id")
    p_wait.add_argument("--timeout", type=float, default=600)

    # list
    sub.add_parser("list", help="List all tasks")

    # agents
    p_agents = sub.add_parser("agents", help="List available agents")
    p_agents.add_argument("--working-dir", default=None)

    # Default: run mode (no subcommand)
    parser.add_argument("--agent", default=None)
    parser.add_argument("--query", default=None)
    parser.add_argument("--context", default=None)
    parser.add_argument("--working-dir", default=None, dest="working_dir")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--async", action="store_true", dest="is_async")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args.task_id)
    elif args.command == "wait":
        cmd_wait(args.task_id, args.timeout)
    elif args.command == "list":
        cmd_list()
    elif args.command == "agents":
        cmd_agents(args.working_dir)
    elif args.agent and args.query:
        if args.is_async:
            cmd_run_async(args)
        else:
            cmd_run_sync(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
