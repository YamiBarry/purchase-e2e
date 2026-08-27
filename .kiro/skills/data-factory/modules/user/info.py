# -*- coding: utf-8 -*-
"""
用户信息模块
支持：查询用户信息、优惠券兑换
"""

import time
from typing import Optional, Dict, Any

from core.http_client import HttpClient
from core.auth import login
from core.db import DbClient
from core.types import ActionResult, Environment
from core.exceptions import UserNotFoundError, UserLoginError, CouponError


def action_get_user_id(db: DbClient, email: str) -> int:
    """
    通过邮箱查询 user_id（供其他模块使用）
    
    Args:
        db: 数据库客户端
        email: 用户邮箱
    
    Returns:
        用户ID
    
    Raises:
        UserNotFoundError: 用户不存在
    """
    row = db.query_one(
        "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
        (email,)
    )
    if not row:
        raise UserNotFoundError(email)
    return row["user_id"]


def _get_user_email_by_id(db: DbClient, user_id: int) -> str:
    """
    通过 user_id 查询用户邮箱
    
    Args:
        db: 数据库客户端
        user_id: 用户ID
    
    Returns:
        用户邮箱
    
    Raises:
        UserNotFoundError: 用户不存在
    """
    row = db.query_one(
        "SELECT email FROM yamibuy_master.xysc_users WHERE user_id = %s LIMIT 1",
        (user_id,)
    )
    if not row:
        raise UserNotFoundError(str(user_id), by="user_id")
    return row["email"]


def action_convert_coupon(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    ps_code: str,
    email: Optional[str] = None,
    user_id: Optional[int] = None,
    pwd: str = "111111"
) -> ActionResult:
    """
    为用户兑换优惠券
    
    通过用户邮箱或 user_id 登录获取 token，然后调用兑换接口将优惠券兑换到用户账号。
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        ps_code: 优惠券兑换码
        email: 用户邮箱（与 user_id 二选一）
        user_id: 用户ID（与 email 二选一）
        pwd: 用户密码，默认 111111
    
    Returns:
        ActionResult 格式的操作结果
    """
    start = time.time()
    try:
        # 1. 确定用户邮箱
        if not email and not user_id:
            raise ValueError("必须提供 email 或 user_id")
        
        if not email:
            email = _get_user_email_by_id(db, user_id)
        
        # 2. 登录获取用户 token
        user_token = login(client, email, pwd)
        if not user_token:
            raise UserLoginError(email, "token 为空")
        
        # 3. 调用优惠券兑换接口
        orig_token = client.token
        client.token = user_token
        
        try:
            status, resp = client.post(
                "/ec-mkt/coupon/v1/convert",
                body={"ps_code": ps_code}
            )
        finally:
            client.token = orig_token
        
        if not client.is_success(status, resp):
            error_msg = client.get_error(resp)
            raise CouponError("兑换", error_msg, ps_code)
        
        # 4. 解析兑换结果
        body = resp.get("body", {})
        coupon_info = body if isinstance(body, dict) else {}
        coupon_code = coupon_info.get("coupon_code")
        
        return {
            "success": True,
            "env": env,
            "action": "convert_coupon",
            "data": {
                "ps_code": ps_code,
                "coupon_code": coupon_code,
                "email": email,
            },
            "validation": {
                "passed": True, 
                "checks": [{"field": "coupon_code", "expected": "not_empty", "actual": coupon_code, "ok": bool(coupon_code)}], 
                "failed_checks": [], 
                "suggestion": ""
            },
            "elapsed": time.time() - start,
        }
        
    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": "convert_coupon",
            "data": {"ps_code": ps_code},
            "error": str(e),
            "elapsed": time.time() - start,
        }


def action_get_user_info(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: Optional[str] = None,
    user_id: Optional[int] = None,
    pwd: str = "111111"
) -> ActionResult:
    """
    查询用户信息
    
    通过邮箱或 user_id 查询用户的基本信息，包括：
    - user_id
    - email
    - token（登录成功时才返回）
    - 积分余额 (pay_points)
    - 礼卡余额
    - is_validated（邮箱是否验证）
    - is_phone_validated（手机号是否验证）
    - is_api_validated（邮箱API是否验证）
    - 最近5个订单的 order_sn
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱（与 user_id 二选一）
        user_id: 用户ID（与 email 二选一）
        pwd: 用户密码，默认 111111
    
    Returns:
        用户信息字典
    """
    start = time.time()
    try:
        if not email and not user_id:
            raise ValueError("必须提供 email 或 user_id")
        
        # 1. 查询用户基本信息
        if email:
            user_row = db.query_one(
                """SELECT user_id, email, pay_points, is_validated, is_phone_validated, is_api_validated 
                   FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1""",
                (email,)
            )
        else:
            user_row = db.query_one(
                """SELECT user_id, email, pay_points, is_validated, is_phone_validated, is_api_validated 
                   FROM yamibuy_master.xysc_users WHERE user_id = %s LIMIT 1""",
                (user_id,)
            )
        
        if not user_row:
            raise UserNotFoundError(email if email else str(user_id), by="email" if email else "user_id")
        
        uid = user_row["user_id"]
        user_email = user_row["email"]
        pay_points = int(user_row.get("pay_points") or 0)
        is_validated = int(user_row.get("is_validated") or 0)
        is_phone_validated = int(user_row.get("is_phone_validated") or 0)
        is_api_validated = int(user_row.get("is_api_validated") or 0)
        
        # 2. 尝试登录获取 token，失败则不返回 token
        token = None
        try:
            token = login(client, user_email, pwd)
        except Exception:
            pass
        
        # 3. 查询礼卡余额（过滤已过期的）
        current_ts = int(time.time())
        giftcard_row = db.query_one(
            """
            SELECT COALESCE(SUM(card_amount - use_amount), 0) as balance
            FROM yamibuy_master.xysc_egift_card
            WHERE redeem_user = %s AND is_active = 1 AND is_delete = 0
              AND card_amount > use_amount
              AND (expired_time = 0 OR expired_time > %s)
            """,
            (uid, current_ts)
        )
        giftcard_balance = round(float(giftcard_row["balance"]) if giftcard_row else 0.0, 2)
        
        # 4. 查询最近5个订单（排除拆单子订单）
        order_rows = db.query_all(
            """
            SELECT order_sn, order_id, order_status, pay_status, shipping_status, add_time
            FROM yamibuy_master.xysc_order_info
            WHERE user_id = %s AND is_separate = 0
            ORDER BY order_id DESC
            LIMIT 5
            """,
            (uid,)
        )
        recent_order_sns = [row["order_sn"] for row in order_rows]
        
        # 构建返回数据
        data = {
            "user_id": uid,
            "email": user_email,
            "pay_points": pay_points,
            "giftcard_balance": giftcard_balance,
            "is_validated": is_validated,
            "is_phone_validated": is_phone_validated,
            "is_api_validated": is_api_validated,
            "recent_order_sns": recent_order_sns,
        }
        
        if token:
            data["token"] = token
        
        return {
            "success": True,
            "env": env,
            "action": "get_user_info",
            "data": data,
            "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
            "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "get_user_info",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }
