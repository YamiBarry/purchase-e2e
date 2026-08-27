# -*- coding: utf-8 -*-
"""
用户余额模块
支持：礼卡余额设置/增加、积分设置/增加
"""

import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

from core.http_client import HttpClient
from core.auth import _get_hub_token
from core.db import DbClient
from core.types import ActionResult, Environment
from core.exceptions import UserNotFoundError, GiftcardError, PointsError, AuthError
from validators.user_validator import validate_giftcard, validate_points
from config import VALIDATION_WAIT, MKT_INTERNAL_SECRET


def _to_decimal(value: Union[int, float, str, Decimal, None], default: str = "0") -> Decimal:
    """
    安全地将值转换为 Decimal，避免浮点精度问题
    
    Args:
        value: 要转换的值
        default: 默认值字符串
    
    Returns:
        Decimal 对象
    """
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    # 先转字符串再转 Decimal，避免 float 精度问题
    return Decimal(str(value))


def _round_money(value: Decimal) -> Decimal:
    """
    金额四舍五入到分（2位小数）
    
    Args:
        value: Decimal 金额
    
    Returns:
        四舍五入后的 Decimal
    """
    return value.quantize(Decimal("0.01"), ROUND_HALF_UP)


def action_set_giftcard(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: str,
    amount: float
) -> ActionResult:
    """
    设置用户礼卡余额为指定绝对值（支持增加和减少）
    
    增加: POST /mkt/eGiftCard/internal/send
    减少: 直接修改数据库 use_amount
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        amount: 目标余额（美元）
    
    Returns:
        ActionResult: 包含 email/amount/delta/current_balance
    """
    start = time.time()
    try:
        # 查当前礼卡总余额和 user_id
        user_row = db.query_one(
            "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
            (email,)
        )
        if not user_row:
            raise UserNotFoundError(email)
        user_id = user_row["user_id"]

        # 查询有效礼卡余额（过滤已过期的）
        current_ts = int(time.time())
        balance_row = db.query_one(
            """
            SELECT COALESCE(SUM(card_amount - use_amount), 0) as balance
            FROM yamibuy_master.xysc_egift_card
            WHERE redeem_user = %s AND is_active = 1 AND is_delete = 0
              AND card_amount <> use_amount
              AND (expired_time = 0 OR expired_time > %s)
            """,
            (user_id, current_ts)
        )
        # 使用 Decimal 进行精确计算
        current_balance = _to_decimal(balance_row["balance"] if balance_row else 0)
        target_amount = _to_decimal(amount)
        delta = _round_money(target_amount - current_balance)

        # 转换为 float 用于返回（保持 API 兼容）
        current_balance_float = float(current_balance)
        delta_float = float(delta)

        if delta == 0:
            return {
                "success": True, "env": env, "action": "set_giftcard",
                "data": {"email": email, "amount": amount, "delta": 0},
                "validation": {"passed": True, "checks": [{"field": "giftcard_balance", "expected": amount, "actual": current_balance_float, "ok": True}], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - start,
            }

        if delta > 0:
            # 增加礼卡
            expired_time = int(time.time()) + 365 * 24 * 3600
            sale_type = f"qa_test_{int(time.time())}"
            hub_token = _get_hub_token(client, env)
            if not hub_token:
                raise AuthError("获取 Hub admin token 失败", "hub")
            body = {
                "activity_name": "QA造数据-礼卡充值",
                "activity_detail": f"QA造数据: 给 {email} 充值 ${delta_float} 礼卡",
                "sale_type_desc": sale_type,
                "egiftCardSendDetails": [{"user_email": email, "card_amount": delta_float, "expired_time": str(expired_time)}],
            }
            secret = MKT_INTERNAL_SECRET.get(env, MKT_INTERNAL_SECRET.get("UAT"))
            orig_token = client.token
            client.token = hub_token
            status, resp = client.post("/mkt/eGiftCard/internal/send", body=body, use_central=True, extra_headers={"secretKey": secret})
            client.token = orig_token
            if not client.is_success(status, resp):
                raise GiftcardError("充值", client.get_error(resp), email, delta_float)
        else:
            # 减少礼卡：直接修改数据库 use_amount
            deduct = abs(delta)
            remaining = deduct
            
            # 查询用户所有有效礼卡，按 card_id 排序
            cards = db.query_all(
                """
                SELECT card_id, card_amount, use_amount
                FROM yamibuy_master.xysc_egift_card
                WHERE redeem_user = %s AND is_active = 1 AND is_delete = 0
                  AND card_amount > use_amount
                  AND (expired_time = 0 OR expired_time > %s)
                ORDER BY card_id ASC
                """,
                (user_id, current_ts)
            )
            
            if not cards:
                raise GiftcardError("扣减", "用户没有可扣减的礼卡", email)
            
            # 逐张扣减（使用 Decimal 精确计算）
            for card in cards:
                if remaining <= 0:
                    break
                card_id = card["card_id"]
                card_amount = _to_decimal(card["card_amount"])
                use_amount = _to_decimal(card["use_amount"])
                available = card_amount - use_amount
                
                to_deduct = min(available, remaining)
                new_use_amount = _round_money(use_amount + to_deduct)
                
                db.execute(
                    "UPDATE yamibuy_master.xysc_egift_card SET use_amount = %s WHERE card_id = %s",
                    (float(new_use_amount), card_id)
                )
                remaining = _round_money(remaining - to_deduct)
            
            # 使用 Decimal 比较，容差 0.01
            if remaining > Decimal("0.01"):
                raise GiftcardError("扣减", f"礼卡余额不足，还差 ${float(remaining):.2f}", email)

        time.sleep(VALIDATION_WAIT)
        # 验证：查 DB 确认余额
        current_ts = int(time.time())
        balance_row = db.query_one(
            """
            SELECT COALESCE(SUM(card_amount - use_amount), 0) as balance 
            FROM yamibuy_master.xysc_egift_card 
            WHERE redeem_user = %s AND is_active = 1 AND is_delete = 0 
              AND card_amount <> use_amount
              AND (expired_time = 0 OR expired_time > %s)
            """,
            (user_id, current_ts)
        )
        actual_balance = _round_money(_to_decimal(balance_row["balance"] if balance_row else 0))
        actual_balance_float = float(actual_balance)
        ok = abs(actual_balance - target_amount) < Decimal("0.01")
        validation = {
            "passed": ok,
            "checks": [{"field": "giftcard_balance", "expected": amount, "actual": actual_balance_float, "ok": ok}],
            "failed_checks": [] if ok else [{"field": "giftcard_balance", "expected": amount, "actual": actual_balance_float, "ok": False}],
            "suggestion": "" if ok else "礼卡余额与预期不符，可能有其他礼卡影响",
        }
        return {
            "success": ok,
            "env": env,
            "action": "set_giftcard",
            "data": {"email": email, "amount": amount, "delta": delta_float, "current_balance": current_balance_float},
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except (UserNotFoundError, GiftcardError, AuthError) as e:
        return {
            "success": False, "env": env, "action": "set_giftcard",
            "data": {"email": email}, "error": str(e), "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "set_giftcard",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }


def action_set_points(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: str,
    points: int,
    user_id: Optional[int] = None
) -> ActionResult:
    """
    设置用户积分为指定绝对值
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        points: 目标积分值
        user_id: 用户ID（可选，不传则通过 email 查询）
    
    Returns:
        ActionResult: 包含 email/user_id/points/delta
    """
    start = time.time()
    try:
        # 查当前积分和 user_id
        if not user_id:
            row = db.query_one(
                "SELECT user_id, pay_points FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
                (email,)
            )
            if not row:
                raise UserNotFoundError(email)
            user_id = row["user_id"]
            current_points = int(row.get("pay_points") or 0)
        else:
            row = db.query_one(
                "SELECT pay_points FROM yamibuy_master.xysc_users WHERE user_id = %s LIMIT 1",
                (user_id,)
            )
            current_points = int(row["pay_points"] or 0) if row else 0

        delta = points - current_points
        if delta == 0:
            return {
                "success": True, "env": env, "action": "set_points",
                "data": {"email": email, "user_id": user_id, "points": points, "delta": 0},
                "validation": {"passed": True, "checks": [{"field": "pay_points", "expected": points, "actual": current_points, "ok": True}], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - start,
            }

        body = [{"user_id": user_id, "point": delta, "type": 4, "reason_type": 0,
                 "operation": "add" if delta > 0 else "subtract", "memo": "QA造数据"}]
        status, result = client.put("/ec-customer/account/point", body=body)
        if result.get("messageId") not in ("200", "10000"):
            raise PointsError("设置", result.get('zhError', str(result)[:100]), email, points)

        time.sleep(VALIDATION_WAIT)
        validation = validate_points(db, email, points)
        return {
            "success": validation["passed"],
            "env": env,
            "action": "set_points",
            "data": {"email": email, "user_id": user_id, "points": points, "delta": delta},
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except (UserNotFoundError, PointsError) as e:
        return {
            "success": False, "env": env, "action": "set_points",
            "data": {"email": email}, "error": str(e), "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "set_points",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }


def action_add_giftcard(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: str,
    amount: float
) -> ActionResult:
    """
    给用户增加礼卡（增量，在现有余额基础上加 amount）
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        amount: 增加金额（美元）
    
    Returns:
        ActionResult: 包含 email/added
    """
    start = time.time()
    try:
        expired_time = int(time.time()) + 365 * 24 * 3600
        sale_type = f"qa_test_{int(time.time())}"
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")
        body = {
            "activity_name": "QA造数据-礼卡充值",
            "activity_detail": f"QA造数据: 给 {email} 增加 ${amount} 礼卡",
            "sale_type_desc": sale_type,
            "egiftCardSendDetails": [{"user_email": email, "card_amount": amount, "expired_time": str(expired_time)}],
        }
        secret = MKT_INTERNAL_SECRET.get(env, MKT_INTERNAL_SECRET.get("UAT"))
        orig_token = client.token
        client.token = hub_token
        status, resp = client.post("/mkt/eGiftCard/internal/send", body=body, use_central=True, extra_headers={"secretKey": secret})
        client.token = orig_token
        if not client.is_success(status, resp):
            raise GiftcardError("充值", client.get_error(resp), email, amount)

        time.sleep(VALIDATION_WAIT)
        validation = validate_giftcard(db, email, amount)
        # 查询当前余额（需要先获取 user_id）
        user_row = db.query_one(
            "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
            (email,)
        )
        current_balance = 0.0
        if user_row:
            user_id = user_row["user_id"]
            current_ts = int(time.time())
            row = db.query_one(
                """
                SELECT COALESCE(SUM(card_amount - use_amount), 0) as balance
                FROM yamibuy_master.xysc_egift_card
                WHERE redeem_user = %s AND is_active = 1 AND is_delete = 0
                  AND card_amount > use_amount
                  AND (expired_time = 0 OR expired_time > %s)
                """,
                (user_id, current_ts)
            )
            current_balance = float(row["balance"] or 0) if row else 0
        return {
            "success": validation["passed"],
            "env": env,
            "action": "add_giftcard",
            "data": {"email": email, "增加礼卡": f"${amount}", "当前余额": f"${current_balance:.2f}"},
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except (GiftcardError, AuthError) as e:
        return {"success": False, "env": env, "action": "add_giftcard", 
                "data": {"email": email}, "error": str(e), "elapsed": time.time() - start}
    except Exception as e:
        return {"success": False, "env": env, "action": "add_giftcard", 
                "data": {}, "error": str(e), "elapsed": time.time() - start}


def action_add_points(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: str,
    points: int
) -> ActionResult:
    """
    给用户增加积分（增量，在现有积分基础上加 points）
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        points: 增加积分数
    
    Returns:
        ActionResult: 包含 email/added/current
    """
    start = time.time()
    try:
        row = db.query_one(
            "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
            (email,)
        )
        if not row:
            raise UserNotFoundError(email)
        user_id = row["user_id"]

        body = [{"user_id": user_id, "point": points, "type": 4, "reason_type": 0, "operation": "add", "memo": "QA造数据"}]
        status, result = client.put("/ec-customer/account/point", body=body)
        if result.get("messageId") not in ("200", "10000"):
            raise PointsError("增加", result.get('zhError', str(result)[:100]), email, points)

        time.sleep(VALIDATION_WAIT)
        # 验证：查加完后的实际积分
        row = db.query_one("SELECT pay_points FROM yamibuy_master.xysc_users WHERE user_id = %s LIMIT 1", (user_id,))
        actual = int(row["pay_points"] or 0) if row else 0
        ok = actual >= points
        validation = {
            "passed": ok,
            "checks": [{"field": "pay_points_added", "expected": f"+{points}", "actual": actual, "ok": ok}],
            "failed_checks": [] if ok else [{"field": "pay_points_added", "expected": f"+{points}", "actual": actual, "ok": False}],
            "suggestion": "" if ok else "积分未增加，可能是接口异常",
        }
        return {
            "success": ok,
            "env": env,
            "action": "add_points",
            "data": {"email": email, "增加积分": points, "当前积分": actual},
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except (UserNotFoundError, PointsError) as e:
        return {"success": False, "env": env, "action": "add_points", 
                "data": {"email": email}, "error": str(e), "elapsed": time.time() - start}
    except Exception as e:
        return {"success": False, "env": env, "action": "add_points", 
                "data": {}, "error": str(e), "elapsed": time.time() - start}
