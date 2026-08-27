# -*- coding: utf-8 -*-
"""
订单ID解析模块
支持多种输入方式解析订单ID
"""

from typing import List

from core.db import DbClient
from core.exceptions import OrderNotFoundError
from modules.order.helpers import (
    get_order_ids_by_sns,
    get_user_id_by_email,
    get_user_recent_orders,
)


def resolve_order_ids(db: DbClient, 
                      order_ids: List[int] = None,
                      order_sns: List[str] = None,
                      user_id: int = None,
                      email: str = None,
                      recent: int = 10,
                      exclude_shipped: bool = False) -> List[int]:
    """
    解析订单ID，支持多种输入方式
    
    优先级：order_ids > order_sns > user_id > email
    
    Args:
        db: 数据库客户端
        order_ids: 订单ID列表
        order_sns: 订单编号列表
        user_id: 用户ID（配合 recent 使用）
        email: 用户邮箱（配合 recent 使用）
        recent: 最近N个订单，默认10
        exclude_shipped: 是否排除已发货订单（仅对 user_id/email 模式生效），默认False
    
    Returns:
        订单ID列表
    
    Raises:
        OrderNotFoundError: 订单不存在
        UserNotFoundError: 用户不存在
        ValueError: 未提供任何订单标识
    """
    # 用户指定具体订单时，不过滤
    if order_ids:
        return order_ids
    
    if order_sns:
        ids = get_order_ids_by_sns(db, order_sns)
        if not ids:
            raise OrderNotFoundError(str(order_sns), by="order_sns")
        return ids
    
    # 查"近N单"时，支持过滤已发货订单
    if user_id:
        ids = get_user_recent_orders(db, user_id, recent, exclude_shipped=exclude_shipped)
        if not ids:
            raise OrderNotFoundError(str(user_id), by="user_id")
        return ids
    
    if email:
        uid = get_user_id_by_email(db, email)
        ids = get_user_recent_orders(db, uid, recent, exclude_shipped=exclude_shipped)
        if not ids:
            raise OrderNotFoundError(email, by="email")
        return ids
    
    raise ValueError("请提供 order_ids / order_sns / user_id / email")
