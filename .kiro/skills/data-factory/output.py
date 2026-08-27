# -*- coding: utf-8 -*-
"""
输出格式化模块
处理结果打印、汇总和进度显示
"""

import sys
from core.logger import output


def print_progress(current: int, total: int, action: str, width: int = 30) -> None:
    """
    打印进度条（覆盖式更新）。
    
    Args:
        current: 当前进度（从 1 开始）
        total: 总数
        action: 当前操作描述
        width: 进度条宽度（字符数），默认 30
    
    Example:
        for i, item in enumerate(items, 1):
            print_progress(i, len(items), f"处理 {item}")
            process(item)
        print()  # 完成后换行
    """
    if total <= 0:
        return
    
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    
    # 截断过长的 action 描述
    max_action_len = 30
    if len(action) > max_action_len:
        action = action[:max_action_len - 3] + "..."
    
    # \r 回到行首，覆盖上一次输出
    sys.stdout.write(f"\r  [{bar}] {current}/{total} {action}")
    sys.stdout.flush()
    
    # 完成时换行
    if current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()


def print_results(results: list):
    """
    打印并记录所有结果
    
    Args:
        results: 结果列表，每个元素是包含 success 字段的字典
    """
    for r in results:
        output(r)
    
    # 汇总统计
    total = len(results)
    passed = sum(1 for r in results if r.get("success"))
    
    print(f"\n{'─'*50}")
    print(f"  汇总: {passed}/{total} 成功")
    if passed < total:
        print("  ⚠️  部分操作失败，请查看上方详情或检查测试环境服务状态")
    print(f"{'─'*50}\n")
