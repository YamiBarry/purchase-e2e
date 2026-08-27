# -*- coding: utf-8 -*-
"""
用户 VIP 等级模块
支持：设置用户 VIP 等级（Ruby/Silver/Gold）

通过调用 central-customer 服务的 upgrade 接口实现等级变更，
接口会自动更新数据库、刷新缓存、发送 MQ 消息。

等级映射：
  - 1 = Ruby（门槛 $0）
  - 2 = Silver（门槛 $150）
  - 3 = Gold（门槛 $350）

接口（central base）：
  升级: POST /customer/vip/{customer_id}/upgrade
  重置: PUT /customer/vip/reset
  查询: GET /customer/vip/{customer_id}/vip_info
"""

import time
from typing import Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.types import ActionResult, Environment
from core.exceptions import UserNotFoundError

# VIP 等级常量
VIP_LEVELS = {
    "ruby": {"level_id": 1, "name": "Ruby", "threshold": 0.00},
    "silver": {"level_id": 2, "name": "Silver", "threshold": 150.00},
    "gold": {"level_id": 3, "name": "Gold", "threshold": 350.00},
}

# 验证等待时间（秒）
VALIDATION_WAIT = 1.0


def _resolve_level(level_str: str) -> dict:
    """
    解析等级字符串为等级信息

    Args:
        level_str: 等级名称（不区分大小写），支持 ruby/silver/gold

    Returns:
        等级信息字典 {"level_id": int, "name": str, "threshold": float}

    Raises:
        ValueError: 无效的等级名称
    """
    key = level_str.strip().lower()
    if key not in VIP_LEVELS:
        valid = ", ".join(VIP_LEVELS.keys())
        raise ValueError(f"无效的 VIP 等级: '{level_str}'，可选: {valid}")
    return VIP_LEVELS[key]


def _get_user_order_id(db: DbClient, user_id: int) -> Optional[str]:
    """
    查询用户的一个有效订单 order_id（upgrade 接口需要）

    Args:
        db: 数据库客户端
        user_id: 用户ID

    Returns:
        订单ID字符串，无订单则返回 None
    """
    row = db.query_one(
        "SELECT order_id FROM yamibuy_master.xysc_order_info WHERE user_id = %s ORDER BY order_id DESC LIMIT 1",
        (user_id,)
    )
    return str(row["order_id"]) if row else None


def _get_current_vip_info(db: DbClient, user_id: int) -> dict:
    """
    查询用户当前 VIP 信息

    Args:
        db: 数据库客户端
        user_id: 用户ID

    Returns:
        {"level_id": int, "consumed_amount": float} 或空字典
    """
    row = db.query_one(
        "SELECT level_id, consumed_amount FROM yamibuy_crm.crm_customer_vip_info WHERE customer_id = %s",
        (user_id,)
    )
    if row:
        return {
            "level_id": int(row["level_id"]),
            "consumed_amount": float(row["consumed_amount"]),
        }
    return {}


def _auto_place_order(client: HttpClient, db: DbClient, env: str, email: str, pwd: str = "111111") -> Optional[str]:
    """
    自动为用户下一个订单（用于 upgrade 接口需要 order_id 的场景）

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        pwd: 用户密码

    Returns:
        订单 order_id 字符串，失败返回 None
    """
    from core.auth import login
    from modules.order_place import action_place_order

    # 先登录
    login(client, email, pwd)

    # 下一个默认订单（case=1，全国可售自营）
    results = action_place_order(client, db, env, email, case_id=1, count=1)

    if results and results[0].get("success"):
        # 下单成功后，从数据库查最新的 order_id
        user_row = db.query_one(
            "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
            (email,)
        )
        if user_row:
            return _get_user_order_id(db, user_row["user_id"])

    return None


def _call_upgrade(client: HttpClient, user_id: int, order_id: str, amount: float) -> dict:
    """
    调用 central-customer 的 upgrade 接口

    POST /customer/vip/{customer_id}/upgrade (central)
    Body: {"order_id": "xxx", "amount": 200.00}

    Args:
        client: HTTP 客户端
        user_id: 用户ID
        order_id: 有效订单ID
        amount: 增加的金额

    Returns:
        接口响应字典
    """
    path = f"/customer/vip/{user_id}/upgrade"
    body = {"order_id": order_id, "amount": amount}
    status, resp = client.post(path, body=body, use_central=True)
    return resp


def _call_reset(client: HttpClient, user_id: int) -> dict:
    """
    调用 central-customer 的 reset 接口（重新计算等级并刷新缓存）

    PUT /customer/vip/reset (central)
    Body: [customer_id]

    Args:
        client: HTTP 客户端
        user_id: 用户ID

    Returns:
        接口响应字典
    """
    path = "/customer/vip/reset"
    status, resp = client.put(path, body=[user_id], use_central=True)
    return resp


def _call_vip_info(client: HttpClient, user_id: int) -> dict:
    """
    调用 central-customer 的 vip_info 接口查询用户等级

    GET /customer/vip/{customer_id}/vip_info (central)

    Args:
        client: HTTP 客户端
        user_id: 用户ID

    Returns:
        接口响应字典
    """
    path = f"/customer/vip/{user_id}/vip_info"
    status, resp = client.get(path, use_central=True)
    return resp


def action_set_vip_level(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: str,
    level: str,
    user_id: Optional[int] = None,
    pwd: str = "111111",
) -> ActionResult:
    """
    设置用户 VIP 等级

    策略：
    - 升级：调用 upgrade 接口传入足够金额（需要用户有订单）
    - 降级：直接修改 DB（reset 会从 SO 重算覆盖）
    - 如果用户无订单且需要升级，先下一个订单再升级

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        email: 用户邮箱
        level: 目标等级（ruby/silver/gold）
        user_id: 用户ID（可选，不传则通过 email 查询）
        pwd: 用户密码，默认 111111

    Returns:
        ActionResult 格式的操作结果
    """
    start = time.time()
    try:
        # 1. 解析目标等级
        level_info = _resolve_level(level)
        target_level_id = level_info["level_id"]
        target_name = level_info["name"]
        target_threshold = level_info["threshold"]

        # 2. 查询用户 ID
        if not user_id:
            row = db.query_one(
                "SELECT user_id FROM yamibuy_master.xysc_users WHERE email = %s LIMIT 1",
                (email,)
            )
            if not row:
                raise UserNotFoundError(email)
            user_id = row["user_id"]

        # 3. 查询当前 VIP 信息
        current_info = _get_current_vip_info(db, user_id)
        current_level_id = current_info.get("level_id", 1)
        current_amount = current_info.get("consumed_amount", 0.0)

        # 4. 判断升级还是降级
        if target_level_id > current_level_id:
            # 升级：调用 upgrade 接口
            order_id = _get_user_order_id(db, user_id)
            if not order_id:
                # 用户没有订单，自动下一个
                order_id = _auto_place_order(client, db, env, email, pwd)
                if not order_id:
                    raise ValueError(
                        f"用户 {email} 没有订单，且自动下单失败。"
                        f"请手动用 --action place_order 给用户下一个订单后重试。"
                    )

            # 计算需要增加的金额：目标阈值 - 当前已消费 + 缓冲值
            needed_amount = target_threshold - current_amount + 50.0
            if needed_amount <= 0:
                # 已经够了但等级没升，可能是缓存问题，传一个小金额触发升级逻辑
                needed_amount = 1.0

            resp = _call_upgrade(client, user_id, order_id, needed_amount)
            msg_id = resp.get("messageId", "")
            if msg_id not in ("200", "10000", "SUCCESS"):
                error_msg = resp.get("zhError") or resp.get("message") or str(resp)[:200]
                raise RuntimeError(f"upgrade 接口失败: {error_msg}")

        elif target_level_id < current_level_id:
            # 降级：直接修改 DB（不调 reset，因为 reset 会从 SO 重算覆盖我们的值）
            target_amount = target_threshold + 10.0  # 略高于目标等级阈值

            db.execute(
                "UPDATE yamibuy_crm.crm_customer_vip_info SET level_id = %s, consumed_amount = %s, edit_dtm = %s WHERE customer_id = %s",
                (target_level_id, target_amount, int(time.time()), user_id)
            )

        else:
            # 等级相同，无需操作
            return {
                "success": True,
                "env": env,
                "action": "set_vip_level",
                "data": {
                    "email": email,
                    "user_id": user_id,
                    "level": target_name,
                    "level_id": target_level_id,
                    "message": "用户已是该等级，无需变更",
                },
                "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - start,
            }

        # 5. 验证结果
        time.sleep(VALIDATION_WAIT)
        validation = _validate_vip_level(client, db, user_id, target_level_id)

        return {
            "success": validation["passed"],
            "env": env,
            "action": "set_vip_level",
            "data": {
                "email": email,
                "user_id": user_id,
                "level": target_name,
                "level_id": target_level_id,
                "previous_level_id": current_level_id,
            },
            "validation": validation,
            "elapsed": time.time() - start,
        }

    except (UserNotFoundError, ValueError) as e:
        return {
            "success": False,
            "env": env,
            "action": "set_vip_level",
            "data": {"email": email, "level": level},
            "error": str(e),
            "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": "set_vip_level",
            "data": {"email": email, "level": level},
            "error": str(e),
            "elapsed": time.time() - start,
        }


def _validate_vip_level(client: HttpClient, db: DbClient, user_id: int, expected_level_id: int) -> dict:
    """
    验证 VIP 等级是否设置成功（通过接口查询）

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        user_id: 用户ID
        expected_level_id: 期望的等级ID

    Returns:
        验证结果字典
    """
    from validators.base import make_check, build_validation

    # 通过接口查询（读缓存）
    resp = _call_vip_info(client, user_id)
    body = resp.get("body", {})
    actual_level = body.get("level_id") if body else None

    # 同时查数据库确认
    vip_row = db.query_one(
        "SELECT level_id FROM yamibuy_crm.crm_customer_vip_info WHERE customer_id = %s",
        (user_id,)
    )
    db_level = int(vip_row["level_id"]) if vip_row else None

    checks = [
        make_check("api_vip_level_id", expected_level_id, actual_level),
        make_check("db_vip_level_id", expected_level_id, db_level),
    ]

    suggestion = ""
    if actual_level != expected_level_id and db_level == expected_level_id:
        suggestion = "数据库已更新但接口缓存未刷新，Redis 缓存会在过期后自动刷新（通常几分钟内）"
    elif actual_level != expected_level_id:
        suggestion = "降级依赖用户实际消费金额，如果半年内消费超过目标等级阈值则无法降级。可尝试用新注册用户测试低等级场景"

    return build_validation(checks, suggestion)
