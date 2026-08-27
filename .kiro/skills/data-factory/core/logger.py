# -*- coding: utf-8 -*-
"""
日志模块。

提供统一的日志记录和 Action 结果输出功能。

日志级别:
    DEBUG: 调试信息
    INFO: 一般信息
    WARN: 警告信息
    ERROR: 错误信息
    SILENT: 静默模式（不输出任何日志）

Example:
    from core.logger import info, error, output
    
    info("开始处理订单", context="order")
    error("订单处理失败", context="order")
    output(result)  # 打印并写入日志文件
"""

import os
import sys
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional


class LogLevel(IntEnum):
    """日志级别枚举。"""
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    SILENT = 100


# 全局日志级别
_log_level: LogLevel = LogLevel.INFO

# 是否输出到文件
_log_to_file: bool = True

# 默认 log 文件路径（写到工作区 docs 目录）
_DEFAULT_LOG_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "docs"
)
_DEFAULT_LOG_FILENAME: str = "data-factory-log.md"

# 当前 log 文件路径
_log_file: str = os.path.join(_DEFAULT_LOG_DIR, _DEFAULT_LOG_FILENAME)


def set_log_level(level: LogLevel) -> None:
    """
    设置全局日志级别。
    
    Args:
        level: 日志级别枚举值。
    """
    global _log_level
    _log_level = level


def set_log_to_file(enabled: bool) -> None:
    """
    设置是否输出到文件。
    
    Args:
        enabled: True 启用文件输出，False 禁用。
    """
    global _log_to_file
    _log_to_file = enabled


def set_log_file(path: str) -> None:
    """
    设置日志文件路径。
    
    Args:
        path: 日志文件完整路径，或仅文件名（使用默认目录）。
    """
    global _log_file
    if os.path.isabs(path) or os.path.dirname(path):
        _log_file = path
    else:
        _log_file = os.path.join(_DEFAULT_LOG_DIR, path)


def get_log_file() -> str:
    """
    获取当前日志文件路径。
    
    Returns:
        日志文件完整路径。
    """
    return _log_file


def get_log_level() -> LogLevel:
    """
    获取当前日志级别。
    
    Returns:
        当前日志级别枚举值。
    """
    return _log_level


# ==================== 通用日志函数 ====================

def _format_message(level: str, message: str, context: Optional[str] = None) -> str:
    """
    格式化日志消息。
    
    Args:
        level: 日志级别标签（如 DEBUG、INFO）。
        message: 日志消息内容。
        context: 上下文标签（可选）。
    
    Returns:
        格式化后的日志字符串。
    """
    ts = datetime.now().strftime("%H:%M:%S")
    ctx = f"[{context}] " if context else ""
    return f"{ts} {level} {ctx}{message}"


def debug(message: str, context: Optional[str] = None) -> None:
    """
    输出调试日志。
    
    Args:
        message: 日志消息。
        context: 上下文标签（可选）。
    """
    if _log_level <= LogLevel.DEBUG:
        print(_format_message("DEBUG", message, context), file=sys.stderr)


def info(message: str, context: Optional[str] = None) -> None:
    """
    输出信息日志。
    
    Args:
        message: 日志消息。
        context: 上下文标签（可选）。
    """
    if _log_level <= LogLevel.INFO:
        print(_format_message("INFO ", message, context))


def warn(message: str, context: Optional[str] = None) -> None:
    """
    输出警告日志。
    
    Args:
        message: 日志消息。
        context: 上下文标签（可选）。
    """
    if _log_level <= LogLevel.WARN:
        print(_format_message("WARN ", message, context), file=sys.stderr)


def error(message: str, context: Optional[str] = None) -> None:
    """
    输出错误日志。
    
    Args:
        message: 日志消息。
        context: 上下文标签（可选）。
    """
    if _log_level <= LogLevel.ERROR:
        print(_format_message("ERROR", message, context), file=sys.stderr)


# ==================== Action 结果输出 ====================

def _check_symbol(ok: bool) -> str:
    """
    返回成功/失败符号。
    
    Args:
        ok: 是否成功。
    
    Returns:
        ✅ 或 ❌。
    """
    return "✅" if ok else "❌"


def print_result(result: Dict[str, Any]) -> None:
    """
    终端打印 Action 结果。
    
    Args:
        result: Action 返回的结果字典，包含 env、action、success、data、validation 等字段。
    """
    env = result.get("env", "")
    action = result.get("action", "")
    success = result.get("success", False)
    data = result.get("data", {})
    validation = result.get("validation", {})
    elapsed = result.get("elapsed", 0)
    err = result.get("error", "")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symbol = _check_symbol(success)

    print(f"\n{symbol} [{env}] {action}  {ts}")

    # 打印数据
    if data:
        for k, v in data.items():
            if k == "items_promote_price" and isinstance(v, list):
                # 促销活动商品价格，每行一个
                print(f"   {k}:")
                for item in v:
                    item_num = item.get("item_number", item.get("goods_id", ""))
                    if item.get("类型") == "本地化":
                        areas = "  ".join(item.get("区域促销价", []))
                        print(f"     {item_num}  [本地化]  {areas}  ({item.get('ratio','')})")
                    else:
                        unit = item.get("unit_price", "")
                        promote = item.get("promote_price", "")
                        ratio = item.get("ratio", "")
                        if unit:
                            print(f"     {item_num}  unit_price={unit}  促销价={promote}  ({ratio})")
                        else:
                            print(f"     {item_num}  促销价={promote}")
            else:
                print(f"   {k}: {v}")

    # 打印验证结果
    if validation:
        checks = validation.get("checks", [])
        failed = validation.get("failed_checks", [])
        if checks:
            check_line = "  ".join(
                f"{'✅' if c['ok'] else '❌'} {c['field']}={c['actual']}"
                for c in checks
            )
            print(f"   验证: {check_line}")
        if failed:
            print(f"   验证失败:")
            for c in failed:
                expected = c.get('expected', '')
                actual = c.get('actual', '')
                field = c.get('field', '')
                if expected:
                    print(f"     ✗ {field}: 期望 {expected}，实际 {actual}")
                else:
                    print(f"     ✗ {field}: 实际 {actual}")
        suggestion = validation.get("suggestion", "")
        if suggestion:
            print(f"   建议: {suggestion}")

    # 打印错误
    if err:
        print(f"   错误: {err}")

    # 打印提示信息
    hint = result.get("hint", "")
    if hint:
        print(f"   提示: {hint}")

    print(f"   耗时: {elapsed:.1f}s")


def write_log(result: dict) -> None:
    """追加写入 log 文件"""
    if not _log_to_file:
        return
    
    log_file = _log_file
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    env = result.get("env", "")
    action = result.get("action", "")
    success = result.get("success", False)
    data = result.get("data", {})
    validation = result.get("validation", {})
    elapsed = result.get("elapsed", 0)
    err = result.get("error", "")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symbol = _check_symbol(success)

    lines = [f"\n## {symbol} [{env}] {action} — {ts}\n"]

    if data:
        for k, v in data.items():
            lines.append(f"- {k}: `{v}`")

    if validation:
        failed = validation.get("failed_checks", [])
        if not failed:
            lines.append("- 验证: 通过")
        else:
            lines.append("- 验证失败:")
            for c in failed:
                expected = c.get('expected', '')
                actual = c.get('actual', '')
                field = c.get('field', '')
                if expected:
                    lines.append(f"  - ✗ {field}: 期望 `{expected}`，实际 `{actual}`")
                else:
                    lines.append(f"  - ✗ {field}: 实际 `{actual}`")
        suggestion = validation.get("suggestion", "")
        if suggestion:
            lines.append(f"- 建议: {suggestion}")

    if err:
        lines.append(f"- 错误: {err}")

    lines.append(f"- 耗时: {elapsed:.1f}s\n")

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        pass  # log 写失败不影响主流程


def output(result: dict) -> None:
    """打印 + 写 log，统一入口"""
    print_result(result)
    write_log(result)
