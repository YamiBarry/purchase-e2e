# -*- coding: utf-8 -*-
"""
订单处理流程模块
支持：FP审核 → 结算 → 发货
"""

import time
from typing import List

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.constants import AbnormalStatus, OrderType
from core.types import ActionResult
from core.exceptions import (
    DataFactoryError,
    OrderNotFoundError,
    AuthError,
    OrderStatusError,
)
from modules.order.helpers import generate_tracking_number, get_order_info
from modules.order.resolve import resolve_order_ids


def _build_error_result(env: str, action: str, data: dict, error: Exception, elapsed: float) -> ActionResult:
    """
    构建统一的错误返回结果
    
    Args:
        env: 环境
        action: 操作名称
        data: 相关数据
        error: 异常对象
        elapsed: 耗时
    
    Returns:
        ActionResult 错误结果
    """
    result = {
        "success": False,
        "env": env,
        "action": action,
        "data": data,
        "error": str(error),
        "elapsed": elapsed,
    }
    
    # 对自定义异常添加类型信息，便于调试
    if isinstance(error, DataFactoryError):
        result["error_type"] = type(error).__name__
        if error.details:
            result["error_details"] = error.details
    
    return result


def action_fp_verify(client: HttpClient, db: DbClient, env: str, order_ids: List[int]) -> ActionResult:
    """
    FP审核（批量）
    
    abnormal=FP_APPROVED(4) 的订单自动跳过（已通过FP审核）
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_ids: 订单ID列表
    
    Returns:
        ActionResult 操作结果
    
    Raises:
        ValueError: order_ids 为空
        OrderNotFoundError: 订单不存在
        AuthError: 获取 Hub token 失败
    """
    start = time.time()
    try:
        if not order_ids:
            raise ValueError("order_ids 不能为空")
        
        # 1. 查询订单信息获取 purchase_id 和 abnormal
        order_info = get_order_info(db, order_ids)
        
        missing = [oid for oid in order_ids if oid not in order_info]
        if missing:
            raise OrderNotFoundError(str(missing), by="order_id")
        
        # 2. 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", token_type="hub")
        
        orig_token = client.token
        client.token = hub_token
        
        details = []
        skipped_count = 0
        try:
            for order_id in order_ids:
                info = order_info[order_id]
                purchase_id = info["purchase_id"]
                abnormal = info.get("abnormal", 0)
                
                # abnormal=FP_APPROVED 跳过FP审核（已通过）
                if abnormal == AbnormalStatus.FP_APPROVED:
                    details.append({
                        "order_id": order_id,
                        "purchase_id": purchase_id,
                        "status": "skipped",
                        "reason": f"abnormal={AbnormalStatus.FP_APPROVED}，已通过FP审核",
                    })
                    skipped_count += 1
                    continue
                
                # 调用 FP 审核接口: POST /fp/validation/{purchase_id}/approve
                resp_status, resp = client.post(
                    f"/fp/validation/{purchase_id}/approve",
                    body="aitest",
                    use_central=True
                )
                
                if client.is_success(resp_status, resp):
                    details.append({
                        "order_id": order_id,
                        "purchase_id": purchase_id,
                        "status": "success",
                    })
                else:
                    details.append({
                        "order_id": order_id,
                        "purchase_id": purchase_id,
                        "status": "failed",
                        "error": client.get_error(resp),
                    })
        finally:
            client.token = orig_token
        
        success_count = len([d for d in details if d["status"] in ("success", "skipped")])
        
        return {
            "success": success_count == len(order_ids),
            "env": env,
            "action": "fp_verify",
            "data": {
                "order_ids": order_ids,
                "success_count": success_count,
                "skipped_count": skipped_count,
                "total_count": len(order_ids),
                "details": details,
            },
            "elapsed": time.time() - start,
        }
        
    except (DataFactoryError, ValueError) as e:
        # 自定义异常和参数错误，提供详细信息
        return _build_error_result(env, "fp_verify", {"order_ids": order_ids}, e, time.time() - start)
    except Exception as e:
        # 未预期的异常，记录完整错误
        return _build_error_result(env, "fp_verify", {"order_ids": order_ids}, e, time.time() - start)


def action_settlement(client: HttpClient, db: DbClient, env: str, order_ids: List[int]) -> ActionResult:
    """
    订单结算（批量）
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_ids: 订单ID列表
    
    Returns:
        ActionResult 操作结果
    
    Raises:
        ValueError: order_ids 为空
        AuthError: 获取 Hub token 失败
    """
    start = time.time()
    try:
        if not order_ids:
            raise ValueError("order_ids 不能为空")
        
        # 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", token_type="hub")
        
        orig_token = client.token
        client.token = hub_token
        
        details = []
        try:
            for order_id in order_ids:
                # 调用结算接口
                resp_status, resp = client.post(
                    f"/so/order/settlement/{order_id}",
                    body={},
                    use_central=True
                )
                
                if client.is_success(resp_status, resp):
                    details.append({
                        "order_id": order_id,
                        "status": "success",
                    })
                else:
                    details.append({
                        "order_id": order_id,
                        "status": "failed",
                        "error": client.get_error(resp),
                    })
        finally:
            client.token = orig_token
        
        success_count = len([d for d in details if d["status"] == "success"])
        
        return {
            "success": success_count == len(order_ids),
            "env": env,
            "action": "settlement",
            "data": {
                "order_ids": order_ids,
                "success_count": success_count,
                "total_count": len(order_ids),
                "details": details,
            },
            "elapsed": time.time() - start,
        }
        
    except (DataFactoryError, ValueError) as e:
        return _build_error_result(env, "settlement", {"order_ids": order_ids}, e, time.time() - start)
    except Exception as e:
        return _build_error_result(env, "settlement", {"order_ids": order_ids}, e, time.time() - start)


def action_shipping(client: HttpClient, db: DbClient, env: str, order_ids: List[int],
                    tracking_number: str = None, shipping_carrier: str = "7 Hours Express") -> ActionResult:
    """
    订单发货（批量）
    
    注意：虚拟礼卡订单（order_type=7）会调用 mkt 服务的专用接口发货，
    该接口会自动处理礼卡初始化、发送邮件或直接兑换等逻辑。
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_ids: 订单ID列表
        tracking_number: 自定义发货单号（不填则自动生成），多个用逗号分隔
            注意：虚拟礼卡订单不需要物流单号，此参数会被忽略
        shipping_carrier: 物流公司，默认 "7 Hours Express"
            注意：虚拟礼卡订单不需要物流公司，此参数会被忽略
    
    Returns:
        ActionResult 操作结果
    
    Raises:
        ValueError: order_ids 为空
        OrderNotFoundError: 订单不存在
        AuthError: 获取 Hub token 失败
    """
    start = time.time()
    try:
        if not order_ids:
            raise ValueError("order_ids 不能为空")
        
        # 解析物流单号列表（逗号分隔），保持用户输入原样
        custom_tracking_numbers = []
        if tracking_number:
            custom_tracking_numbers = [tn.strip() for tn in tracking_number.split(",") if tn.strip()]
        
        # 1. 查询订单信息获取 user_id 和 order_type
        order_info = get_order_info(db, order_ids)
        
        missing = [oid for oid in order_ids if oid not in order_info]
        if missing:
            raise OrderNotFoundError(str(missing), by="order_id")
        
        # 2. 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", token_type="hub")
        
        orig_token = client.token
        client.token = hub_token
        
        details = []
        try:
            for idx, order_id in enumerate(order_ids):
                info = order_info[order_id]
                user_id = info["user_id"]
                order_type = info.get("order_type", 1)
                purchase_id = info.get("purchase_id")
                
                # 虚拟礼卡订单（order_type=7）调用 mkt 专用接口
                if order_type == OrderType.EGIFT:
                    # 调用 mkt 虚拟礼卡发货接口
                    # 该接口会自动处理：结算、发货状态更新、礼卡初始化、发送邮件/直接兑换
                    body = {"order_id": order_id}
                    if purchase_id:
                        body["purchase_id"] = int(purchase_id) if isinstance(purchase_id, str) else purchase_id
                    
                    resp_status, resp = client.post(
                        "/mkt/eGiftCard/order/shipping",
                        body=body,
                        use_central=True
                    )
                    
                    if client.is_success(resp_status, resp):
                        details.append({
                            "order_id": order_id,
                            "order_type": "egift",
                            "status": "success",
                            "note": "虚拟礼卡订单，已通过 mkt 服务发货",
                        })
                    else:
                        details.append({
                            "order_id": order_id,
                            "order_type": "egift",
                            "status": "failed",
                            "error": client.get_error(resp),
                        })
                else:
                    # 普通订单：调用 so 发货接口
                    # 获取物流单号：优先使用用户指定的，否则自动生成
                    if custom_tracking_numbers:
                        # 如果用户指定了多个，按顺序分配；不够则循环使用最后一个
                        track_no = custom_tracking_numbers[min(idx, len(custom_tracking_numbers) - 1)]
                    else:
                        track_no = generate_tracking_number()
                    
                    shipping_time = int(time.time())
                    
                    # 调用发货接口
                    body = {
                        "order_id": order_id,
                        "shipping_time": shipping_time,
                        "tracking_number": track_no,
                        "shipping_carrier": shipping_carrier,
                    }
                    
                    resp_status, resp = client.post(
                        f"/so/deliver/shipping?in_user={user_id}",
                        body=body,
                        use_central=True
                    )
                    
                    if client.is_success(resp_status, resp):
                        details.append({
                            "order_id": order_id,
                            "tracking_number": track_no,
                            "shipping_carrier": shipping_carrier,
                            "status": "success",
                        })
                    else:
                        details.append({
                            "order_id": order_id,
                            "tracking_number": track_no,
                            "status": "failed",
                            "error": client.get_error(resp),
                        })
        finally:
            client.token = orig_token
        
        success_count = len([d for d in details if d["status"] == "success"])
        
        return {
            "success": success_count == len(order_ids),
            "env": env,
            "action": "shipping",
            "data": {
                "order_ids": order_ids,
                "success_count": success_count,
                "total_count": len(order_ids),
                "details": details,
            },
            "elapsed": time.time() - start,
        }
        
    except (DataFactoryError, ValueError) as e:
        return _build_error_result(env, "shipping", {"order_ids": order_ids}, e, time.time() - start)
    except Exception as e:
        return _build_error_result(env, "shipping", {"order_ids": order_ids}, e, time.time() - start)


def action_process_orders(client: HttpClient, db: DbClient, env: str, 
                          order_ids: List[int] = None,
                          order_sns: List[str] = None,
                          user_id: int = None,
                          email: str = None,
                          recent: int = 10,
                          tracking_number: str = None,
                          shipping_carrier: str = "7 Hours Express",
                          skip_fp: bool = False,
                          skip_settlement: bool = False,
                          skip_shipping: bool = False) -> ActionResult:
    """
    订单处理流水线：FP审核 → 结算 → 发货
    
    支持多种订单标识方式（优先级：order_ids > order_sns > user_id > email）
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_ids: 订单ID列表
        order_sns: 订单编号列表
        user_id: 用户ID（配合 recent 使用）
        email: 用户邮箱（配合 recent 使用）
        recent: 最近N个订单，默认10
        tracking_number: 自定义发货单号
        shipping_carrier: 物流公司
        skip_fp: 跳过FP审核
        skip_settlement: 跳过结算
        skip_shipping: 跳过发货
    
    Returns:
        ActionResult 操作结果
    """
    start = time.time()
    results = []
    
    try:
        # 1. 解析订单ID
        target_orders = resolve_order_ids(db, order_ids, order_sns, user_id, email, recent)
        
        # 2. FP审核
        if not skip_fp:
            fp_result = action_fp_verify(client, db, env, target_orders)
            results.append(fp_result)
        
        # 3. 结算
        if not skip_settlement:
            settlement_result = action_settlement(client, db, env, target_orders)
            results.append(settlement_result)
        
        # 4. 发货
        if not skip_shipping:
            shipping_result = action_shipping(client, db, env, target_orders, 
                                              tracking_number, shipping_carrier)
            results.append(shipping_result)
        
        # 5. 汇总结果
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "env": env,
            "action": "process_orders",
            "data": {
                "order_ids": target_orders,
                "steps": [r["action"] for r in results],
                "results": results,
            },
            "elapsed": time.time() - start,
        }
        
    except (DataFactoryError, ValueError) as e:
        return _build_error_result(
            env, "process_orders",
            {"order_ids": order_ids, "order_sns": order_sns, "user_id": user_id, "email": email},
            e, time.time() - start
        )
    except Exception as e:
        return _build_error_result(
            env, "process_orders",
            {"order_ids": order_ids, "order_sns": order_sns, "user_id": user_id, "email": email},
            e, time.time() - start
        )
