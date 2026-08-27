# -*- coding: utf-8 -*-
"""
促销活动管理模块
支持：结束活动、查询活动
"""

import time
import json
from typing import Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.mkt_api import MktApiClient
from core.types import ActionResult
from core.exceptions import (
    DataFactoryError,
    AuthError,
    PromotionNotFoundError,
)
from core.constants import is_yami_seller
from modules.promotion.constants import PromotionStatus, PROMO_QUERY_CONFIG
from modules.promotion.helpers import parse_promotion_detail


def _build_error_result(env: str, action: str, error: Exception, elapsed: float) -> ActionResult:
    """
    构建统一的错误返回结果
    
    Args:
        env: 环境
        action: 操作名称
        error: 异常对象
        elapsed: 耗时
    
    Returns:
        ActionResult 错误结果
    """
    result = {
        "success": False,
        "env": env,
        "action": action,
        "data": {},
        "error": str(error),
        "elapsed": elapsed,
    }
    
    # 对自定义异常添加类型信息，便于调试
    if isinstance(error, DataFactoryError):
        result["error_type"] = type(error).__name__
        if error.details:
            result["error_details"] = error.details
    
    return result


def action_finish_promotion(
    client: HttpClient,
    db: DbClient,
    env: str,
    ps_id: int,
) -> ActionResult:
    """
    结束促销活动
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        ps_id: 活动 ID
    
    Returns:
        操作结果
    """
    _start = time.time()
    try:
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        mkt = MktApiClient(client, hub_token)
        resp = mkt.finish_promotion(ps_id)

        if not mkt.is_success(resp):
            raise PromotionNotFoundError(str(ps_id), "ps_id")

        row = db.query_one(
            "SELECT ps_id, ps_sub_title, status FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s LIMIT 1",
            (ps_id,)
        )
        ok = row is not None and row.get("status") == PromotionStatus.ENDED

        return {
            "success": ok,
            "env": env,
            "action": "finish_promotion",
            "data": {
                "ps_id": ps_id,
                "促销标题": row["ps_sub_title"] if row else "",
                "status": row["status"] if row else None,
            },
            "validation": {
                "passed": ok,
                "checks": [{"field": "status", "expected": PromotionStatus.ENDED, "actual": row["status"] if row else None, "ok": ok}],
                "failed_checks": [] if ok else [{"field": "status", "actual": row.get("status") if row else "not found", "ok": False}],
                "suggestion": "" if ok else "活动未结束, 请检查 central-mkt 后台",
            },
            "elapsed": time.time() - _start,
        }
    except (DataFactoryError, ValueError) as e:
        return _build_error_result(env, "finish_promotion", e, time.time() - _start)
    except Exception as e:
        return _build_error_result(env, "finish_promotion", e, time.time() - _start)


def action_find_promotion(
    client: HttpClient,
    db: DbClient,
    env: str,
    promo_type: str,
    seller_id: Optional[int] = None,
    status: int = PromotionStatus.ACTIVE,
    limit: int = 1,
) -> ActionResult:
    """
    查询促销活动
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        promo_type: 活动类型 gift/coupon/discount/seckill/giftcard/member
        seller_id: 商家ID筛选，None=不限，0=自营
        status: 活动状态，默认 PromotionStatus.ACTIVE(30=生效中)，可选 PromotionStatus.PENDING(20=待生效)
        limit: 返回数量，默认1，设为0返回全部
    
    Returns:
        操作结果
    """
    _start = time.time()
    try:
        if promo_type not in PROMO_QUERY_CONFIG:
            raise PromotionNotFoundError(promo_type, "promo_type")
        
        config = PROMO_QUERY_CONFIG[promo_type]
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        mkt = MktApiClient(client, hub_token)
        # 优惠券的"生效中"状态是 50，普通促销是 30
        query_status = PromotionStatus.COUPON_ACTIVE if promo_type == "coupon" and status == PromotionStatus.ACTIVE else status

        # 计算请求的 pageSize
        # limit=0 表示返回全部，请求 200 条
        # limit>0 时，对于需要过滤 discountMode 的类型，请求 50 条以确保过滤后有足够数据
        if limit == 0:
            request_page_size = 200
        elif promo_type in ("discount", "seckill", "giftcard", "member"):
            request_page_size = max(50, limit * 10)  # 请求更多以便过滤
        else:
            request_page_size = limit

        # 构建请求参数
        if promo_type == "coupon":
            body = {
                "create_platform": 1,
                "pageType": "couponList",
                "ps_title": "",
                "keyword": "",
                "status": str(query_status),
                "start_time": "",
                "end_time": "",
                "item_number": "",
                "ps_code": "",
                "coupon_form": "",
                "pageSize": request_page_size,
                "startColumn": 0,
                "order": {"orderColumn": "ps_id", "orderRule": "desc"},
                "draw": 1,
            }
        else:
            body = {
                "status": str(query_status),
                "pageSize": request_page_size,
                "startColumn": 0,
                "is_seller": 1 if is_yami_seller(seller_id) else (2 if seller_id and seller_id > 0 else ""),
                "create_platform": 1,
                "order": {"orderColumn": "ps_id", "orderRule": "desc"},
            }
        
        if promo_type == "gift":
            body["keyword"] = ""
            body["main_keyword"] = ""
            body["gift_keyword"] = ""
            body["start_time"] = ""
            body["end_time"] = ""
            body["draw"] = 1
        
        if promo_type in ("discount", "giftcard", "member"):
            body["type"] = 10
        
        if promo_type == "seckill":
            body["type"] = 11

        if seller_id is not None and seller_id > 0:
            body["seller_id"] = seller_id

        # 调用接口
        resp = mkt.post(config["api"], body)

        if not mkt.is_success(resp):
            raise RuntimeError(f"查询失败: {mkt.get_error(resp)}")

        body_data = resp.get("body", {})
        data_list = body_data.get("data", []) if isinstance(body_data, dict) else []
        
        if not data_list:
            status_name = "生效中" if status == PromotionStatus.ACTIVE else "待生效" if status == PromotionStatus.PENDING else str(status)
            return {
                "success": True,
                "env": env,
                "action": "find_promotion",
                "data": {
                    "found": False,
                    "promo_type": promo_type,
                    "活动类型": config["name"],
                    "查询状态": status_name,
                    "提示": f"未找到{status_name}的{config['name']}",
                    "创建命令": f"python main.py --env {env} --action {config['create_action']}",
                },
                "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - _start,
            }

        # 按 discountMode 过滤
        if promo_type in ("discount", "seckill", "giftcard", "member"):
            target_modes = config.get("discount_modes", [])
            filtered_list = []
            for item in data_list:
                ps_content = item.get("ps_content")
                if isinstance(ps_content, str):
                    try:
                        ps_content = json.loads(ps_content)
                    except Exception:
                        continue
                if ps_content:
                    mode = str(ps_content.get("discountMode", ""))
                    if mode in target_modes:
                        filtered_list.append(item)
            data_list = filtered_list
            
            if not data_list:
                status_name = "生效中" if status == PromotionStatus.ACTIVE else "待生效" if status == PromotionStatus.PENDING else str(status)
                return {
                    "success": True,
                    "env": env,
                    "action": "find_promotion",
                    "data": {
                        "found": False,
                        "promo_type": promo_type,
                        "活动类型": config["name"],
                        "查询状态": status_name,
                        "提示": f"未找到{status_name}的{config['name']}",
                        "创建命令": f"python main.py --env {env} --action {config['create_action']}",
                    },
                    "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                    "elapsed": time.time() - _start,
                }

        # 根据 limit 截取结果
        if limit > 0:
            data_list = data_list[:limit]

        # 如果只返回一条，保持原有格式
        if len(data_list) == 1:
            item = data_list[0]
            result_data = parse_promotion_detail(promo_type, item, config)
            result_data["found"] = True
            result_data["promo_type"] = promo_type
            result_data["活动类型"] = config["name"]
            
            # 查询 item_number
            goods_ids_to_query = []
            if "_goods_ids" in result_data:
                goods_ids_to_query.extend(result_data.pop("_goods_ids"))
            if "_gift_goods_id" in result_data:
                goods_ids_to_query.append(result_data.pop("_gift_goods_id"))
            
            if goods_ids_to_query:
                try:
                    placeholders = ",".join(["%s"] * len(goods_ids_to_query))
                    sql = f"SELECT goods_id, item_number FROM yamibuy_im.im_item WHERE goods_id IN ({placeholders})"
                    rows = db.query_all(sql, tuple(goods_ids_to_query))
                    id_to_item = {str(r["goods_id"]): r["item_number"] for r in rows} if rows else {}
                    
                    if len(goods_ids_to_query) > 1 or (len(goods_ids_to_query) == 1 and promo_type != "gift"):
                        item_numbers = [id_to_item.get(gid, gid) for gid in goods_ids_to_query]
                        result_data["商品item_number"] = item_numbers
                    elif len(goods_ids_to_query) == 1 and promo_type == "gift":
                        gid = goods_ids_to_query[0]
                        result_data["赠品item_number"] = id_to_item.get(gid, gid)
                except Exception:
                    if len(goods_ids_to_query) == 1 and promo_type == "gift":
                        result_data["赠品goods_id"] = goods_ids_to_query[0]
                    else:
                        result_data["商品goods_id"] = goods_ids_to_query

            return {
                "success": True,
                "env": env,
                "action": "find_promotion",
                "data": result_data,
                "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - _start,
            }

        # 返回多条记录
        results = []
        all_goods_ids = []
        for item in data_list:
            result_item = parse_promotion_detail(promo_type, item, config)
            result_item["promo_type"] = promo_type
            result_item["活动类型"] = config["name"]
            
            # 收集 goods_ids
            if "_goods_ids" in result_item:
                all_goods_ids.extend(result_item.pop("_goods_ids"))
            if "_gift_goods_id" in result_item:
                all_goods_ids.append(result_item.pop("_gift_goods_id"))
            
            results.append(result_item)

        # 批量查询 item_number
        id_to_item = {}
        if all_goods_ids:
            try:
                unique_ids = list(set(all_goods_ids))
                placeholders = ",".join(["%s"] * len(unique_ids))
                sql = f"SELECT goods_id, item_number FROM yamibuy_im.im_item WHERE goods_id IN ({placeholders})"
                rows = db.query_all(sql, tuple(unique_ids))
                id_to_item = {str(r["goods_id"]): r["item_number"] for r in rows} if rows else {}
            except Exception:
                pass

        return {
            "success": True,
            "env": env,
            "action": "find_promotion",
            "data": {
                "found": True,
                "promo_type": promo_type,
                "活动类型": config["name"],
                "总数": len(results),
                "活动列表": results,
            },
            "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
            "elapsed": time.time() - _start,
        }
    except (DataFactoryError, ValueError) as e:
        return _build_error_result(env, "find_promotion", e, time.time() - _start)
    except Exception as e:
        return _build_error_result(env, "find_promotion", e, time.time() - _start)
