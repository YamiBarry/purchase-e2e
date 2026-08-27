#!/usr/bin/env python3
"""后台启动 smoke_order.py，解决 nohup & 在非交互式 shell 不生效的问题"""
import subprocess
import sys
import os

log_file = "/tmp/smoke_order.log"
script = r"D:\workspace\autoqa-agent\.kiro\skills\smoke-order-test\smoke_order.py"

# 透传所有参数给 smoke_order.py，明确用 python3 确保环境一致
args = [sys.executable, script] + sys.argv[1:]

with open(log_file, "w") as f:
    proc = subprocess.Popen(
        args,
        stdout=f,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # 脱离父进程，真正后台运行
    )

print(f"已在后台启动，pid={proc.pid}，日志: {log_file}")
