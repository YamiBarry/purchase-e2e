# -*- coding: utf-8 -*-
"""
促销活动数据验证
验证各类活动是否正确创建，统一通过 ps_id 查询
"""

from core.db import DbClient
from validators.base import make_check, build_validation


def validate_promotion_exists(db: DbClient, ps_id: int) -> dict:
    """验证活动是否存在且状态正常（MKT 系统）"""
    row = db.query_one(
        """
        SELECT ps_id, ps_sub_title, status, start_time, end_time
        FROM yamibuy_mkt.mkt_promotion_schedule
        WHERE ps_id = %s
        LIMIT 1
        """,
        (ps_id,)
    )
    if not row:
        return build_validation([
            {"field": "ps_id", "expected": ps_id, "actual": None, "ok": False}
        ])
    # MKT 系统状态: 10=草稿, 20=待生效, 30=生效中, 40=已结束
    checks = [
        make_check("ps_id", ps_id, row["ps_id"]),
        make_check("status", "20/30", row.get("status") if row.get("status") in (20, 30) else row.get("status")),
    ]
    checks[-1]["ok"] = row.get("status") in (20, 30)
    return build_validation(checks)


def validate_promotion_item(db: DbClient, ps_id: int, item_number: str, expected_price: float = None) -> dict:
    """验证活动商品是否关联正确，可选验证活动价格"""
    row = db.query_one(
        """
        SELECT pi.item_number, pi.promotion_price, pi.status
        FROM yamibuy_master.xysc_promotion_item pi
        WHERE pi.ps_id = %s AND pi.item_number = %s
        LIMIT 1
        """,
        (ps_id, item_number)
    )
    if not row:
        return build_validation([
            {"field": "promotion_item", "expected": f"ps_id={ps_id},item={item_number}", "actual": None, "ok": False}
        ])
    checks = [
        make_check("item_number", item_number, row["item_number"]),
    ]
    if expected_price is not None:
        checks.append(make_check("promotion_price", expected_price, float(row["promotion_price"])))
    return build_validation(checks)


def validate_coupon(db: DbClient, ps_id: int, expected_code: str = None) -> dict:
    """验证优惠券活动是否创建，可选验证兑换码"""
    row = db.query_one(
        """
        SELECT ps_id, coupon_code, status, discount_amount, min_order_amount
        FROM yamibuy_master.xysc_promotion_coupon
        WHERE ps_id = %s
        ORDER BY create_time DESC
        LIMIT 1
        """,
        (ps_id,)
    )
    if not row:
        return build_validation([
            {"field": "coupon", "expected": f"ps_id={ps_id}", "actual": None, "ok": False}
        ])
    checks = [
        make_check("ps_id", ps_id, row["ps_id"]),
        make_check("status", 1, row.get("status")),
    ]
    if expected_code:
        checks.append(make_check("coupon_code", expected_code, row.get("coupon_code")))
    return build_validation(checks)


def validate_seckill(db: DbClient, ps_id: int, item_number: str, expected_price: float = None, expected_stock: int = None) -> dict:
    """验证秒杀活动"""
    row = db.query_one(
        """
        SELECT fi.item_number, fi.flash_price, fi.flash_stock, fi.status
        FROM yamibuy_master.xysc_flash_sale_item fi
        WHERE fi.ps_id = %s AND fi.item_number = %s
        LIMIT 1
        """,
        (ps_id, item_number)
    )
    if not row:
        return build_validation([
            {"field": "seckill_item", "expected": f"ps_id={ps_id},item={item_number}", "actual": None, "ok": False}
        ])
    checks = [make_check("item_number", item_number, row["item_number"])]
    if expected_price is not None:
        checks.append(make_check("flash_price", expected_price, float(row["flash_price"])))
    if expected_stock is not None:
        checks.append(make_check("flash_stock", expected_stock, int(row["flash_stock"])))
    return build_validation(checks)
