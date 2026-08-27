# -*- coding: utf-8 -*-
"""
验证器基础模块
提供通用的验证辅助函数
"""

from typing import Any, Dict, List, Optional


def make_check(field: str, expected: Any, actual: Any) -> Dict[str, Any]:
    """
    创建单个验证检查项
    
    Args:
        field: 字段名
        expected: 期望值
        actual: 实际值
    
    Returns:
        检查项字典 {"field": str, "expected": Any, "actual": Any, "ok": bool}
    """
    if expected is not None:
        ok = str(actual) == str(expected)
    else:
        ok = actual is not None
    return {"field": field, "expected": expected, "actual": actual, "ok": ok}


def build_validation(checks: List[Dict], suggestion: str = "") -> Dict[str, Any]:
    """
    构建验证结果
    
    Args:
        checks: 检查项列表
        suggestion: 失败时的建议（可选）
    
    Returns:
        验证结果字典 {"passed": bool, "checks": list, "failed_checks": list, "suggestion": str}
    """
    failed = [c for c in checks if not c["ok"]]
    return {
        "passed": len(failed) == 0,
        "checks": checks,
        "failed_checks": failed,
        "suggestion": suggestion if failed else "",
    }
