# -*- coding: utf-8 -*-
"""
订单状态变更模块
支持：送达、取消订单、修改送达时间
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.constants import (
    OrderStatus, ShippingStatus, PayStatus,
    TrackingStatusType, CancelReason, CancelSubReason,
)
from core.types import ActionResult
from core.exceptions import (
    DataFactoryError,
    OrderNotFoundError,
    OrderStatusError,
    AuthError,
)
from core.utils import build_error_result
from modules.order.helpers import get_order_info
from modules.order.resolve import resolve_order_ids


def action_delivered(client: HttpClient, db: DbClient, env: str,
                     order_ids: List[int] = None,
                     order_sns: List[str] = None,
                     user_id: int = None,
                     email: str = None,
                     recent: int = 10) -> ActionResult:
    """
    订单已送达（批量）
    
    直接更新 yamibuy_so.so_tracking_info 表的物流状态为已送达。
    
    支持多种输入方式：
    - order_ids: 指定订单ID列表
    - order_sns: 指定订单编号列表
    - user_id + recent: 用户最近N单
    - email + recent: 用户最近N单
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_ids: 订单ID列表
        order_sns: 订单编号列表
        user_id: 用户ID
        email: 用户邮箱
        recent: 最近N单，默认10
    
    Returns:
        ActionResult 操作结果
    
    Raises:
        OrderNotFoundError: 订单不存在
        OrderStatusError: 订单状态不是已发货
    """
    start = time.time()
    try:
        # 1. 解析订单ID
        target_order_ids = resolve_order_ids(
            db, order_ids, order_sns, user_id, email, recent,
            exclude_shipped=False
        )
        
        if not target_order_ids:
            return {
                "success": True,
                "message": "没有可处理的订单",
            }
        
        # 2. 查询订单信息
        order_info = get_order_info(db, target_order_ids)
        
        missing = [oid for oid in target_order_ids if oid not in order_info]
        if missing:
            raise OrderNotFoundError(str(missing), by="order_id")
        
        # 3. 校验订单状态必须是已发货
        shipped_orders = []
        not_shipped = []
        
        for oid in target_order_ids:
            info = order_info[oid]
            os = info["order_status"]
            ss = info["shipping_status"]
            ps = info["pay_status"]
            
            # 只处理已发货订单（order_status=SHIPPED, shipping_status=SHIPPED, pay_status=PAID）
            if os == OrderStatus.SHIPPED and ss == ShippingStatus.SHIPPED and ps == PayStatus.PAID:
                shipped_orders.append(oid)
            else:
                not_shipped.append({
                    "order_id": oid,
                    "order_sn": info["order_sn"],
                    "order_status": os,
                    "shipping_status": ss,
                    "pay_status": ps,
                })
        
        # 如果有订单状态不符合，直接报错
        if not_shipped:
            raise OrderStatusError(
                str([item['order_sn'] for item in not_shipped]),
                expected="已发货",
                actual="未发货",
                action="标记为送达"
            )
        
        # 4. 构造物流状态数据
        current_time = int(time.time())
        current_datetime = datetime.utcfromtimestamp(current_time).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 物流节点信息（按 7Hours 格式）
        status_list = [
            {
                "datetime": current_datetime,
                "imageArray": [
                    "https://7hoursexpress.s3.us-west-1.amazonaws.com/da55cd5de492d7f67b25f2597785afd8_Order_w1OZn2BnDl.jpg",
                    "https://7hoursexpress.s3.us-west-1.amazonaws.com/b4434b0a60f3f218ed9129b012f9cdb7_Order_w1OZn2BnDl.jpg"
                ],
                "imageUrl": "https://7hoursexpress.s3.us-west-1.amazonaws.com/da55cd5de492d7f67b25f2597785afd8_Order_w1OZn2BnDl.jpg",
                "info": "Delivered",
                "note": "Delivered to recipient",
                "time": current_time,
                "type": TrackingStatusType.DELIVERED,
            },
            {
                "datetime": datetime.utcfromtimestamp(current_time - 3600).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "info": "Out For Delivery",
                "time": current_time - 3600,
                "type": TrackingStatusType.OUT_FOR_DELIVERY,
            },
            {
                "datetime": datetime.utcfromtimestamp(current_time - 7200).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "info": "In Transit",
                "time": current_time - 7200,
                "type": TrackingStatusType.IN_TRANSIT,
            },
            {
                "datetime": datetime.utcfromtimestamp(current_time - 10800).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "info": "Order Processed: Ready for 7 Hours Express",
                "time": current_time - 10800,
                "type": TrackingStatusType.PROCESSED,
            },
        ]
        
        updated = []
        failed = []
        
        for oid in shipped_orders:
            info = order_info[oid]
            try:
                # 从 xysc_order_info.invoice_no 获取物流单号（多个用逗号分隔）
                invoice_row = db.query_one(
                    """
                    SELECT invoice_no
                    FROM yamibuy_master.xysc_order_info
                    WHERE order_id = %s
                    """,
                    (oid,)
                )
                invoice_no = invoice_row["invoice_no"] if invoice_row and invoice_row["invoice_no"] else ""
                
                # 解析物流单号列表（逗号分隔）
                tracking_numbers = [tn.strip() for tn in invoice_no.split(",") if tn.strip()]
                if not tracking_numbers:
                    tracking_numbers = [f"test{oid}"]
                
                # 更新每个物流单号的状态
                updated_trackings = []
                for tracking_number in tracking_numbers:
                    db.execute(
                        """
                        UPDATE yamibuy_so.so_tracking_info
                        SET status = %s,
                            delivery_status = 1,
                            delivery_time = %s,
                            tracking_status = 'Delivered',
                            carrier = '7 Hours Express',
                            carrier_type = 1,
                            edit_dtm = %s
                        WHERE order_id = %s AND tracking_number = %s
                        """,
                        (json.dumps(status_list), current_time, current_time, oid, tracking_number)
                    )
                    updated_trackings.append(tracking_number)
                
                updated.append({
                    "order_id": oid,
                    "order_sn": info["order_sn"],
                    "tracking_numbers": updated_trackings,
                    "status": "success",
                })
                    
            except Exception as e:
                failed.append({
                    "order_id": oid,
                    "order_sn": info["order_sn"],
                    "error": str(e),
                })
        
        # 5. 汇总结果
        return {
            "success": len(failed) == 0,
            "env": env,
            "action": "delivered",
            "message": f"成功更新 {len(updated)} 个订单为已送达",
            "data": {
                "updated": updated if updated else None,
                "failed": failed if failed else None,
            },
            "elapsed": time.time() - start,
        }
        
    except (DataFactoryError, ValueError) as e:
        return build_error_result(env, "delivered", e, time.time() - start)
    except Exception as e:
        return build_error_result(env, "delivered", e, time.time() - start)


def action_cancel_orders(client: HttpClient, db: DbClient, env: str,
                         order_ids: List[int] = None,
                         order_sns: List[str] = None,
                         user_id: int = None,
                         email: str = None,
                         recent: int = 10,
                         reason: int = CancelReason.OTHER,
                         sub_reason: int = CancelSubReason.DEFAULT,
                         memo: str = "其他") -> ActionResult:
    """
    取消订单（批量）
    
    支持多种输入方式：
    - order_ids: 指定订单ID列表
    - order_sns: 指定订单编号列表
    - user_id + recent: 用户最近N单
    - email + recent: 用户最近N单
    
    未发货订单：直接取消
    已发货订单：走 RMA 整单拒收流程
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_ids: 订单ID列表
        order_sns: 订单编号列表
        user_id: 用户ID
        email: 用户邮箱
        recent: 最近N单，默认10
        reason: 取消原因，默认14
        sub_reason: 取消子原因，默认4
        memo: 备注，默认"测试取消"
    
    Returns:
        ActionResult 操作结果
    
    Raises:
        OrderNotFoundError: 订单不存在
        AuthError: 获取 Hub token 失败
    """
    try:
        # 1. 解析订单ID（不排除已发货订单）
        target_order_ids = resolve_order_ids(
            db, order_ids, order_sns, user_id, email, recent,
            exclude_shipped=False
        )
        
        if not target_order_ids:
            return {
                "success": True,
                "message": "没有可取消的订单",
            }
        
        # 2. 查询订单信息获取 order_sn
        order_info = get_order_info(db, target_order_ids)
        
        missing = [oid for oid in target_order_ids if oid not in order_info]
        if missing:
            raise OrderNotFoundError(str(missing), by="order_id")
        
        # 3. 分类订单：可直接取消 / 需要RMA / 已取消跳过
        cancelable = []      # 未发货，可直接取消
        need_rma = []        # 已发货，需要RMA
        skipped = []         # 已取消，跳过
        
        for oid in target_order_ids:
            info = order_info[oid]
            info["order_id"] = oid  # 补充 order_id
            os = info["order_status"]
            # 已取消状态
            if os in (OrderStatus.CANCELLED_USER, OrderStatus.CANCELLED_SYSTEM):
                skipped.append({"order_id": oid, "order_sn": info["order_sn"], "reason": "已取消"})
            # 已发货状态
            elif os == OrderStatus.SHIPPED and info["shipping_status"] == ShippingStatus.SHIPPED:
                need_rma.append(info)
            else:
                cancelable.append(info["order_sn"])
        
        # 如果没有可处理的订单
        if not cancelable and not need_rma:
            return {
                "success": True,
                "message": "没有可取消的订单",
                "skipped": skipped if skipped else None,
            }
        
        # 4. 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", token_type="hub")
        
        orig_token = client.token
        client.token = hub_token
        
        cancelled = []
        rma_created = []
        failed = []
        
        try:
            # 5. 直接取消未发货订单
            if cancelable:
                status, resp = client.post(
                    "/so/order/cancel_batch/",
                    body={
                        "lstOrderSn": cancelable,
                        "reason": reason,
                        "sub_reason": sub_reason,
                        "third_sub_reason": "",
                        "memo": memo,
                    },
                    use_central=True
                )
                if client.is_success(status, resp):
                    body = resp.get("body", {})
                    cancelled = body.get("succeedOrderSn", [])
                    failed = body.get("failedOrderSn", [])
                else:
                    failed = cancelable
            
            # 6. 已发货订单走 RMA 整单拒收
            for info in need_rma:
                order_sn = info["order_sn"]
                try:
                    # POST /rma/order/orderReject/{order_sn} - 使用 central API
                    status, resp = client.post(
                        f"/rma/order/orderReject/{order_sn}",
                        body={
                            "reissue_addr": 0,
                            "order_type": info.get("order_type", 1),
                            "vendor_id": info.get("vendor_id", 0),
                            "tracking_list": [],
                            "user_id": info["user_id"],
                            "rma_type": "1",
                            "reason_code1": 6,
                            "reason_code2": 58,
                            "reason_code": 58,
                        },
                        use_central=True
                    )
                    if client.is_success(status, resp):
                        rma_id = resp.get("body")
                        # 自动退款（注意：退款接口是 GET 方法）
                        if rma_id:
                            refund_status, refund_resp = client.get(
                                f"/rma/order/returnPrice/{rma_id}",
                                use_central=True
                            )
                            if client.is_success(refund_status, refund_resp):
                                rma_created.append({"order_sn": order_sn, "rma_id": rma_id})
                            else:
                                failed.append({"order_sn": order_sn, "reason": f"RMA创建成功但退款失败: {refund_resp}"})
                        else:
                            failed.append({"order_sn": order_sn, "reason": "RMA创建成功但未返回rma_id"})
                    else:
                        failed.append({"order_sn": order_sn, "reason": f"RMA创建失败: {resp}"})
                except Exception as e:
                    failed.append({"order_sn": order_sn, "reason": str(e)})
        finally:
            client.token = orig_token
        
        # 7. 汇总结果
        total_success = len(cancelled) + len(rma_created)
        msg_parts = []
        if cancelled:
            msg_parts.append(f"取消 {len(cancelled)} 个")
        if rma_created:
            msg_parts.append(f"RMA退货 {len(rma_created)} 个")
        
        # 构建 data 字段用于输出
        data = {}
        if cancelled:
            data["直接取消"] = cancelled
        if rma_created:
            data["RMA退货"] = [f"{item['order_sn']} (RMA: {item['rma_id']})" for item in rma_created]
        if failed:
            data["失败"] = failed
        if skipped:
            data["跳过"] = skipped
        
        return {
            "success": total_success > 0 and not failed,
            "message": f"成功处理 {total_success} 个订单" + (f"（{', '.join(msg_parts)}）" if msg_parts else ""),
            "data": data if data else None,
            "cancelled": cancelled if cancelled else None,
            "rma_created": rma_created if rma_created else None,
            "failed": failed if failed else None,
            "skipped": skipped if skipped else None,
        }
        
    except (DataFactoryError, ValueError) as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__ if isinstance(e, DataFactoryError) else "ValueError",
            "error_details": e.details if isinstance(e, DataFactoryError) and e.details else None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def action_update_delivery_time(client: HttpClient, db: DbClient, env: str,
                                 order_id: int = None,
                                 order_sn: str = None,
                                 target_timestamp: int = None) -> ActionResult:
    """
    修改订单送达时间
    
    将已送达订单的送达时间修改为指定时间戳，同时调整其他物流节点时间到送达时间之前。
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        order_id: 订单ID（与 order_sn 二选一）
        order_sn: 订单编号（与 order_id 二选一）
        target_timestamp: 目标送达时间戳（秒）
    
    Returns:
        ActionResult 操作结果
    
    Raises:
        OrderNotFoundError: 订单不存在
        OrderStatusError: 订单不是已送达状态
    """
    start = time.time()
    try:
        # 1. 解析订单ID
        if not order_id and not order_sn:
            raise ValueError("必须提供 order_id 或 order_sn")
        
        target_order_ids = resolve_order_ids(
            db, 
            order_ids=[order_id] if order_id else None, 
            order_sns=[order_sn] if order_sn else None,
            user_id=None, email=None, recent=1,
            exclude_shipped=False
        )
        
        if not target_order_ids:
            raise OrderNotFoundError(str(order_id or order_sn), by="order_id" if order_id else "order_sn")
        
        oid = target_order_ids[0]
        
        # 2. 查询订单信息
        order_info = get_order_info(db, [oid])
        if oid not in order_info:
            raise OrderNotFoundError(str(order_id or order_sn), by="order_id" if order_id else "order_sn")
        
        info = order_info[oid]
        
        # 3. 查询当前物流状态，确认是否已送达
        tracking_row = db.query_one(
            """
            SELECT tracking_number, delivery_status, delivery_time, status
            FROM yamibuy_so.so_tracking_info
            WHERE order_id = %s
            LIMIT 1
            """,
            (oid,)
        )
        
        if not tracking_row:
            raise OrderStatusError(
                info["order_sn"],
                expected="已送达",
                actual="无物流记录",
                action="修改送达时间"
            )
        
        if tracking_row["delivery_status"] != 1:
            raise OrderStatusError(
                info["order_sn"],
                expected="已送达(delivery_status=1)",
                actual=f"delivery_status={tracking_row['delivery_status']}",
                action="修改送达时间"
            )
        
        # 4. 使用目标时间戳
        new_delivery_time = target_timestamp
        new_delivery_datetime = datetime.fromtimestamp(new_delivery_time).strftime("%Y-%m-%d %H:%M:%S")
        
        old_delivery_time = tracking_row["delivery_time"]
        old_delivery_datetime = datetime.fromtimestamp(old_delivery_time).strftime("%Y-%m-%d %H:%M:%S") if old_delivery_time else "无"
        
        # 5. 更新物流状态中的时间
        # 解析现有 status JSON，更新其中的时间
        status_list = []
        if tracking_row["status"]:
            try:
                status_list = json.loads(tracking_row["status"]) if isinstance(tracking_row["status"], str) else tracking_row["status"]
            except Exception:
                status_list = []
        
        # 更新 status 中所有节点的时间
        # 物流节点时间间隔（秒）：每个节点比下一个节点早 1 小时
        # DELIVERED(3) -> OUT_FOR_DELIVERY(2) -> IN_TRANSIT(1) -> PROCESSED(0)
        node_time_offset = {
            TrackingStatusType.DELIVERED: 0,           # 送达时间
            TrackingStatusType.OUT_FOR_DELIVERY: 3600, # 送达前 1 小时
            TrackingStatusType.IN_TRANSIT: 7200,       # 送达前 2 小时
            TrackingStatusType.PROCESSED: 10800,       # 送达前 3 小时
        }
        
        if status_list:
            for item in status_list:
                node_type = item.get("type")
                if node_type in node_time_offset:
                    # 计算该节点的时间（送达时间 - 偏移量）
                    node_time = new_delivery_time - node_time_offset[node_type]
                    item["time"] = node_time
                    item["datetime"] = datetime.utcfromtimestamp(node_time).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 6. 更新数据库
        db.execute(
            """
            UPDATE yamibuy_so.so_tracking_info
            SET delivery_time = %s,
                status = %s,
                edit_dtm = %s
            WHERE order_id = %s
            """,
            (new_delivery_time, json.dumps(status_list) if status_list else None, int(time.time()), oid)
        )
        
        # 7. 返回结果
        return {
            "success": True,
            "env": env,
            "action": "update_delivery_time",
            "message": f"订单 {info['order_sn']} 送达时间已修改",
            "data": {
                "order_id": oid,
                "order_sn": info["order_sn"],
                "tracking_number": tracking_row["tracking_number"],
                "原送达时间": old_delivery_datetime,
                "新送达时间": new_delivery_datetime,
            },
            "elapsed": time.time() - start,
        }
        
    except (DataFactoryError, ValueError) as e:
        return build_error_result(env, "update_delivery_time", e, time.time() - start)
    except Exception as e:
        return build_error_result(env, "update_delivery_time", e, time.time() - start)
