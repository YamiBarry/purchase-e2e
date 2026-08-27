# -*- coding: utf-8 -*-
"""
订单处理模块
支持：FP审核 → 结算 → 发货 → 送达 → 取消

接口来源：
  FP审核: POST /fp/validation/{purchase_id}/approve
  结算: POST /so/order/settlement/{order_id}
  发货: POST /so/deliver/shipping
  取消: POST /so/order/cancel_batch/
  RMA拒收: POST /rma/order/orderReject/{order_sn}
"""

# 订单ID解析
from modules.order.resolve import resolve_order_ids

# 订单处理流程
from modules.order.process import (
    action_fp_verify,
    action_settlement,
    action_shipping,
    action_process_orders,
)

# 订单状态变更
from modules.order.status import (
    action_delivered,
    action_cancel_orders,
    action_update_delivery_time,
)

__all__ = [
    # 解析
    "resolve_order_ids",
    # 处理流程
    "action_fp_verify",
    "action_settlement",
    "action_shipping",
    "action_process_orders",
    # 状态变更
    "action_delivered",
    "action_cancel_orders",
    "action_update_delivery_time",
]
