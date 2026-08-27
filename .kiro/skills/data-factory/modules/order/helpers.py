# -*- coding: utf-8 -*-
"""
订单处理辅助函数
"""

import random
import string
from datetime import datetime
from typing import Dict, List, Union

from core.db import DbClient
from core.exceptions import UserNotFoundError


# 发货单号计数器（按日期重置）
_tracking_counter = {"date": None, "count": 0}


def generate_tracking_number(custom: str = None) -> str:
    """
    生成发货单号
    
    格式：TEST{YYYYMMDD}{4位随机字母数字}，如 TEST20260418A1B2
    
    Args:
        custom: 自定义单号，不为空则直接返回（保持原样）
    
    Returns:
        发货单号
    """
    if custom:
        return custom
    
    today = datetime.now().strftime("%Y%m%d")
    # 4位随机：2个字母 + 2个数字，打乱顺序
    chars = random.choices(string.ascii_uppercase, k=2) + random.choices(string.digits, k=2)
    random.shuffle(chars)
    return f"TEST{today}{''.join(chars)}"


def get_order_info(db: DbClient, order_ids: List[int]) -> Dict[int, Dict[str, Union[str, int]]]:
    """
    查询订单信息
    
    Args:
        db: 数据库客户端
        order_ids: 订单ID列表
    
    Returns:
        {order_id: {"order_sn": x, "purchase_id": y, "user_id": z, "order_status": w, "abnormal": v, ...}}
    """
    placeholders = ",".join(["%s"] * len(order_ids))
    rows = db.query_all(
        f"""
        SELECT order_id, order_sn, purchase_id, user_id, order_status, shipping_status, 
               pay_status, abnormal, order_type, vendor_id
        FROM yamibuy_master.xysc_order_info
        WHERE order_id IN ({placeholders})
        """,
        tuple(order_ids)
    )
    
    return {
        int(row["order_id"]): {
            "order_sn": row["order_sn"],
            "purchase_id": row["purchase_id"],
            "user_id": int(row["user_id"]) if row["user_id"] else 0,
            "order_status": int(row["order_status"]) if row["order_status"] else 0,
            "shipping_status": int(row["shipping_status"]) if row["shipping_status"] else 0,
            "pay_status": int(row["pay_status"]) if row["pay_status"] else 0,
            "abnormal": int(row["abnormal"]) if row["abnormal"] else 0,
            "order_type": int(row["order_type"]) if row["order_type"] else 1,
            "vendor_id": int(row["vendor_id"]) if row["vendor_id"] else 0,
        }
        for row in rows
    }


def get_order_ids_by_sns(db: DbClient, order_sns: List[str]) -> List[int]:
    """
    通过 order_sn 查询 order_id
    
    Args:
        db: 数据库客户端
        order_sns: 订单编号列表
    
    Returns:
        订单ID列表
    """
    placeholders = ",".join(["%s"] * len(order_sns))
    rows = db.query_all(
        f"""
        SELECT order_id
        FROM yamibuy_master.xysc_order_info
        WHERE order_sn IN ({placeholders})
        """,
        tuple(order_sns)
    )
    return [int(row["order_id"]) for row in rows]


def get_user_id_by_email(db: DbClient, email: str) -> int:
    """
    通过邮箱查询 user_id
    
    Args:
        db: 数据库客户端
        email: 用户邮箱
    
    Returns:
        用户ID
    
    Raises:
        UserNotFoundError: 用户不存在
    """
    row = db.query_one(
        """
        SELECT user_id
        FROM yamibuy_master.xysc_users
        WHERE email = %s
        """,
        (email,)
    )
    if not row:
        raise UserNotFoundError(email, by="email")
    return int(row["user_id"])


def get_user_recent_orders(db: DbClient, user_id: int, limit: int = 10, 
                           exclude_shipped: bool = False) -> List[int]:
    """
    查询用户最近的订单（排除拆单子订单）
    
    Args:
        db: 数据库客户端
        user_id: 用户ID
        limit: 返回数量，默认10
        exclude_shipped: 是否排除已发货订单，默认False
    
    Returns:
        订单ID列表
    """
    from core.constants import OrderStatus, ShippingStatus, PayStatus
    
    if exclude_shipped:
        # 排除已发货订单（order_status=SHIPPED, shipping_status=SHIPPED, pay_status=PAID）
        rows = db.query_all(
            f"""
            SELECT order_id
            FROM yamibuy_master.xysc_order_info
            WHERE user_id = %s 
              AND is_separate = 0
              AND NOT (order_status = {OrderStatus.SHIPPED} AND shipping_status = {ShippingStatus.SHIPPED} AND pay_status = {PayStatus.PAID})
            ORDER BY order_id DESC
            LIMIT %s
            """,
            (user_id, limit)
        )
    else:
        rows = db.query_all(
            """
            SELECT order_id
            FROM yamibuy_master.xysc_order_info
            WHERE user_id = %s
              AND is_separate = 0
            ORDER BY order_id DESC
            LIMIT %s
            """,
            (user_id, limit)
        )
    return [int(row["order_id"]) for row in rows]
