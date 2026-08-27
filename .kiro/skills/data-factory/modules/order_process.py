# -*- coding: utf-8 -*-
"""
订单处理模块（兼容性重导出）

此文件保留用于向后兼容，实际实现已拆分到 modules/order/ 子模块：
  - modules/order/helpers.py    - 辅助函数
  - modules/order/resolve.py    - 订单ID解析
  - modules/order/process.py    - 订单处理流程（FP审核、结算、发货）
  - modules/order/status.py     - 订单状态变更（送达、取消）

新代码请直接从 modules.order 导入。
"""

# 从子模块重导出所有公开函数
from modules.order import (
    # 解析
    resolve_order_ids,
    # 处理流程
    action_fp_verify,
    action_settlement,
    action_shipping,
    action_process_orders,
    # 状态变更
    action_delivered,
    action_cancel_orders,
)

__all__ = [
    "resolve_order_ids",
    "action_fp_verify",
    "action_settlement",
    "action_shipping",
    "action_process_orders",
    "action_delivered",
    "action_cancel_orders",
]
