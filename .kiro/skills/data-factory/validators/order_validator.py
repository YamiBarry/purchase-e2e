# -*- coding: utf-8 -*-
"""
订单数据验证
验证订单状态、支付状态是否正确
"""

from core.db import DbClient
from validators.base import make_check, build_validation


def validate_order(db: DbClient, purchase_id: int) -> dict:
    """验证订单基本状态"""
    row = db.query_one(
        """
        SELECT oi.purchase_id, oi.order_status, oi.pay_status,
               oi.warehouse_number, oi.cart_warehouse_number
        FROM yamibuy_master.xysc_order_info oi
        WHERE oi.purchase_id = %s
        LIMIT 1
        """,
        (purchase_id,)
    )
    if not row:
        return build_validation([
            {"field": "order", "expected": f"purchase_id={purchase_id}", "actual": None, "ok": False}
        ], "订单数据异常，可能是 so-service 或 payment-service 未正常处理，可稍后重试")
    checks = [
        make_check("purchase_id", purchase_id, row["purchase_id"]),
        # order_status=1 待支付，pay_status=1 已支付
        {"field": "order_status", "expected": "exists", "actual": row["order_status"], "ok": True},
    ]
    return build_validation(checks)


def validate_paid_order(db: DbClient, purchase_id: int) -> dict:
    """验证订单已支付，查 purchase_id 下所有 is_separate=0 的订单"""
    rows = db.query_all(
        """
        SELECT order_sn, pay_status, order_status
        FROM yamibuy_master.xysc_order_info
        WHERE purchase_id = %s AND is_separate = 0
        """,
        (purchase_id,)
    )
    if not rows:
        return build_validation([
            {"field": "order", "expected": f"purchase_id={purchase_id}", "actual": None, "ok": False}
        ], "订单数据异常，可能是 so-service 或 payment-service 未正常处理，可稍后重试")
    # 所有子单都要 pay_status=2
    checks = []
    for row in rows:
        ok = int(row.get("pay_status", 0)) == 2
        checks.append({
            "field": f"pay_status({row['order_sn']})",
            "expected": 2,
            "actual": row.get("pay_status"),
            "ok": ok,
        })
    return build_validation(checks, "订单数据异常，可能是 so-service 或 payment-service 未正常处理，可稍后重试")
