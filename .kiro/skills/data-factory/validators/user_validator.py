# -*- coding: utf-8 -*-
"""
用户数据验证
验证注册、礼卡余额、积分、优惠券是否正确写入
"""

from core.db import DbClient
from validators.base import make_check, build_validation


def validate_register(db: DbClient, email: str) -> dict:
    """验证用户注册成功且邮箱已验证（is_validated=1）"""
    row = db.query_one(
        "SELECT user_id, is_validated FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
        (email,)
    )
    if not row:
        return build_validation([
            {"field": "user_exists", "expected": True, "actual": False, "ok": False}
        ], "数据未写入，可能是 UAT/GQC customer-service 未正常处理，可稍后重试")
    checks = [
        make_check("user_exists", True, True),
        make_check("is_validated", 1, int(row["is_validated"])),
    ]
    return build_validation(checks, "数据未写入，可能是 UAT/GQC customer-service 未正常处理，可稍后重试")


def validate_giftcard(db: DbClient, email: str, expected_amount: float) -> dict:
    """验证礼卡是否充值成功，查 xysc_egift_card 表"""
    row = db.query_one(
        """
        SELECT ec.card_id, ec.card_amount, ec.use_amount, ec.is_redeem, ec.is_active
        FROM yamibuy_master.xysc_egift_card ec
        JOIN yamibuy_master.xysc_users u ON ec.redeem_user = u.user_id
        WHERE u.email = %s
          AND ec.card_amount = %s
          AND ec.is_redeem = 1
          AND ec.is_active = 1
          AND ec.is_delete = 0
        ORDER BY ec.card_id DESC
        LIMIT 1
        """,
        (email, expected_amount)
    )
    if not row:
        return build_validation([
            {"field": "giftcard", "expected": f"amount={expected_amount}", "actual": None, "ok": False}
        ], "礼卡未到账，可能是 central-mkt-service 未正常处理，可稍后重试")
    checks = [
        make_check("card_amount", float(expected_amount), float(row["card_amount"])),
        make_check("is_redeem", 1, int(row["is_redeem"])),
        make_check("is_active", 1, int(row["is_active"])),
    ]
    return build_validation(checks, "礼卡未到账，可能是 central-mkt-service 未正常处理，可稍后重试")


def validate_points(db: DbClient, email: str, expected_points: int) -> dict:
    """验证积分"""
    row = db.query_one(
        "SELECT pay_points FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
        (email,)
    )
    actual = int(row["pay_points"]) if row else None
    checks = [make_check("pay_points", expected_points, actual)]
    return build_validation(checks, "数据未写入，可能是 UAT/GQC customer-service 未正常处理，可稍后重试")


def validate_user_coupon(db: DbClient, email: str, ps_id: int) -> dict:
    """验证用户账户是否有指定活动的优惠券"""
    row = db.query_one(
        """
        SELECT uc.coupon_id, uc.status
        FROM yamibuy_master.xysc_user_coupon uc
        JOIN yamibuy_master.xysc_users u ON uc.user_id = u.user_id
        WHERE u.email = %s AND uc.ps_id = %s
        ORDER BY uc.create_time DESC
        LIMIT 1
        """,
        (email, ps_id)
    )
    if not row:
        return build_validation([
            {"field": "coupon_in_account", "expected": f"ps_id={ps_id}", "actual": None, "ok": False}
        ], "数据未写入，可能是 UAT/GQC customer-service 未正常处理，可稍后重试")
    checks = [
        make_check("coupon_in_account", f"ps_id={ps_id}", f"coupon_id={row['coupon_id']}"),
        make_check("coupon_status", "unused", row.get("status")),
    ]
    return build_validation(checks, "数据未写入，可能是 UAT/GQC customer-service 未正常处理，可稍后重试")
