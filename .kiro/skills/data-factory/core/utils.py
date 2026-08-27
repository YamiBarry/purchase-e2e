# -*- coding: utf-8 -*-
"""
通用工具函数模块。

提供时间处理、类型转换、SQL 构建、统一错误处理、轮询等待等通用功能。

Example:
    from core.utils import (
        get_timestamp,
        build_error_result,
        wait_for_condition
    )
    
    ts = get_timestamp()
    result = build_error_result(env, action, error, elapsed)
"""

import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

from core.types import ActionResult


T = TypeVar('T')


def get_timestamp() -> int:
    """
    获取当前时间戳（秒）。
    
    Returns:
        当前 Unix 时间戳，单位秒。
    """
    return int(time.time())


def get_timestamp_ms() -> int:
    """
    获取当前时间戳（毫秒）。
    
    Returns:
        当前 Unix 时间戳，单位毫秒。
    """
    return int(time.time() * 1000)


def format_datetime(ts: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    时间戳转格式化字符串。
    
    Args:
        ts: Unix 时间戳（秒）。
        fmt: 日期格式字符串，默认 "%Y-%m-%d %H:%M:%S"。
    
    Returns:
        格式化后的日期时间字符串。
    """
    return datetime.fromtimestamp(ts).strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> int:
    """
    格式化字符串转时间戳。
    
    Args:
        dt_str: 日期时间字符串。
        fmt: 日期格式字符串，默认 "%Y-%m-%d %H:%M:%S"。
    
    Returns:
        Unix 时间戳（秒）。
    """
    return int(datetime.strptime(dt_str, fmt).timestamp())


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数。
    
    Args:
        value: 待转换的值。
        default: 转换失败时的默认值。
    
    Returns:
        转换后的整数，或默认值。
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数。
    
    Args:
        value: 待转换的值。
        default: 转换失败时的默认值。
    
    Returns:
        转换后的浮点数，或默认值。
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def truncate_str(s: str, max_len: int = 100) -> str:
    """
    截断字符串。
    
    Args:
        s: 原始字符串。
        max_len: 最大长度，默认 100。
    
    Returns:
        截断后的字符串，超长时末尾添加 "..."。
    """
    if not s or len(s) <= max_len:
        return s
    return s[:max_len] + "..."


def build_in_clause(items: list) -> Tuple[str, Tuple[Any, ...]]:
    """
    构建 SQL IN 子句的占位符和参数。
    
    Args:
        items: 值列表。
    
    Returns:
        (placeholders, params) 元组，placeholders 为占位符字符串，params 为参数元组。
    
    Example:
        placeholders, params = build_in_clause(['A', 'B', 'C'])
        # placeholders = '%s, %s, %s'
        # params = ('A', 'B', 'C')
        sql = f"SELECT * FROM t WHERE col IN ({placeholders})"
        db.execute(sql, params)
    """
    if not items:
        return "", ()
    placeholders = ", ".join(["%s"] * len(items))
    return placeholders, tuple(items)


# ==================== 统一错误处理 ====================

def build_error_result(
    env: str,
    action: str,
    error: Exception,
    elapsed: float,
    data: Optional[Dict[str, Any]] = None
) -> ActionResult:
    """
    构建统一的错误返回结果。
    
    Args:
        env: 环境标识（UAT/GQC/DEV）。
        action: 操作名称。
        error: 异常对象。
        elapsed: 耗时（秒）。
        data: 附加数据（可选）。
    
    Returns:
        包含错误信息的 ActionResult 字典。
    
    Example:
        try:
            # ... 业务逻辑
        except Exception as e:
            return build_error_result(env, "my_action", e, time.time() - start)
    """
    # 延迟导入避免循环依赖
    from core.exceptions import DataFactoryError
    
    result: ActionResult = {
        "success": False,
        "env": env,
        "action": action,
        "error": str(error),
        "elapsed": elapsed,
    }
    
    # 添加附加数据
    if data:
        result["data"] = data
    
    # 对自定义异常添加类型信息，便于调试
    if isinstance(error, DataFactoryError):
        result["error_type"] = type(error).__name__
        if error.details:
            result["error_details"] = error.details
    
    return result


def build_success_result(
    env: str,
    action: str,
    data: Dict[str, Any],
    elapsed: float,
    message: Optional[str] = None,
    validation: Optional[Dict[str, Any]] = None
) -> ActionResult:
    """
    构建统一的成功返回结果。
    
    Args:
        env: 环境标识（UAT/GQC/DEV）。
        action: 操作名称。
        data: 返回数据。
        elapsed: 耗时（秒）。
        message: 成功消息（可选）。
        validation: 验证结果（可选）。
    
    Returns:
        包含成功信息的 ActionResult 字典。
    """
    result: ActionResult = {
        "success": True,
        "env": env,
        "action": action,
        "data": data,
        "elapsed": elapsed,
    }
    
    if message:
        result["message"] = message
    
    if validation:
        result["validation"] = validation
    
    return result


# ==================== 轮询等待工具 ====================

def wait_for_condition(
    check_fn: Callable[[], T],
    timeout: float = 10.0,
    interval: float = 0.5,
    description: str = "condition"
) -> Optional[T]:
    """
    轮询等待条件满足。
    
    Args:
        check_fn: 检查函数，返回 truthy 值表示条件满足。
        timeout: 超时时间（秒），默认 10 秒。
        interval: 检查间隔（秒），默认 0.5 秒。
        description: 条件描述（用于日志）。
    
    Returns:
        check_fn 的返回值（条件满足时），或 None（超时时）。
    
    Example:
        result = wait_for_condition(
            lambda: db.query_one(
                "SELECT * FROM orders WHERE id=%s AND status='shipped'",
                (order_id,)
            ),
            timeout=30,
            description="订单发货"
        )
        if result:
            print("订单已发货")
        else:
            print("等待超时")
    """
    start = time.time()
    while time.time() - start < timeout:
        result = check_fn()
        if result:
            return result
        time.sleep(interval)
    return None


def wait_for_db_condition(
    db: Any,
    sql: str,
    params: Tuple[Any, ...],
    timeout: float = 10.0,
    interval: float = 0.5
) -> Optional[Dict[str, Any]]:
    """
    轮询等待数据库条件满足。
    
    Args:
        db: 数据库客户端实例。
        sql: SQL 查询语句。
        params: SQL 参数元组。
        timeout: 超时时间（秒），默认 10 秒。
        interval: 检查间隔（秒），默认 0.5 秒。
    
    Returns:
        查询结果（条件满足时），或 None（超时时）。
    
    Example:
        row = wait_for_db_condition(
            db,
            "SELECT * FROM mkt_promotion_schedule WHERE ps_id = %s AND status = 30",
            (ps_id,),
            timeout=10
        )
    """
    return wait_for_condition(
        lambda: db.query_one(sql, params),
        timeout=timeout,
        interval=interval,
        description=f"SQL: {sql[:50]}..."
    )
