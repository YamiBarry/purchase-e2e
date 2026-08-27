# -*- coding: utf-8 -*-
"""
商品价格模块
支持：修改全国价格、区域价格
"""

import time
from typing import Dict, List, Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.types import ActionResult, ValidationResult
from core.exceptions import ItemNotFoundError, AuthError, ApiRequestError
from validators.item_validator import validate_price
from config import VALIDATION_WAIT


def _get_seller_id(db: DbClient, item_number: str) -> Optional[int]:
    """
    从数据库查询商品的 seller_id

    Args:
        db: 数据库客户端
        item_number: 商品编号

    Returns:
        seller_id，不存在则返回 None
    """
    item = db.query_one(
        """
        SELECT seller_id
        FROM yamibuy_im.im_item
        WHERE item_number = %s
        """,
        (item_number,)
    )
    if not item:
        return None
    return int(item["seller_id"]) if item["seller_id"] else 0


def _get_item_full_info_from_api(client: HttpClient, item_number: str, seller_id: int = 0) -> Dict:
    """
    通过 API 查询商品完整信息（包含 stash）

    stash 是后端通过 MD5 计算商品完整信息生成的，用于防止脏数据。
    必须通过 API 获取，不能从数据库直接查询。

    Args:
        client: HTTP 客户端（需要已设置 hub token）
        item_number: 商品编号
        seller_id: 商家ID，默认 0（自营）

    Returns:
        API 返回的商品完整信息，包含 stash 字段
    """
    hub_headers = {"Yami-Origin": "central-web"}

    body = {
        "item_number": item_number,
        "seller_id": seller_id
    }

    status, resp = client.post(
        "/im/item/queryByItemNumber",
        body=body,
        use_central=True,
        extra_headers=hub_headers
    )

    if not client.is_success(status, resp):
        raise ApiRequestError("/im/item/queryByItemNumber", status, client.get_error(resp))

    resp_body = resp.get("body")
    if not resp_body:
        raise ItemNotFoundError(item_number)

    return resp_body


def _check_area_prices(db: DbClient, item_number: str) -> List[Dict]:
    """
    检查商品是否有区域价格记录

    Returns:
        区域价格列表，每项包含 rule_id, unit_price, market_price
    """
    rows = db.query_all(
        """
        SELECT rule_id, unit_price, market_price
        FROM yamibuy_im.im_item_area_price_setting
        WHERE item_number = %s
        ORDER BY rule_id
        """,
        (item_number,)
    )
    return rows or []


def action_set_price(client: HttpClient, db: DbClient, env: str, item_number: str, price: float,
                     rule_id: Optional[int] = None, market_price: Optional[float] = None) -> ActionResult:
    """
    修改商品价格

    智能检测区域价：
    - 用户未指定 rule_id 时，自动检测商品是否有区域价
    - 如果有区域价，返回提示信息，列出所有区域及当前价格
    - 如果没有区域价，直接修改全国价
    - 用户指定 rule_id > 0 时，修改指定区域价格
    - 用户指定 rule_id = 0 时，强制修改全国价格

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        item_number: 商品编号
        price: 目标售价（unit_price）
        rule_id: 指定区域 rule_id（可选，None=自动检测，0=强制全国价，>0=指定区域）
        market_price: 市场价（可选，不填则保持原值）

    Returns:
        操作结果
    """
    start = time.time()

    try:
        # 1. 从数据库查询 seller_id
        seller_id = _get_seller_id(db, item_number)
        if seller_id is None:
            raise ItemNotFoundError(item_number)

        # 2. 用户未指定 rule_id 时，自动检测区域价
        if rule_id is None:
            area_prices = _check_area_prices(db, item_number)
            if area_prices:
                area_info = []
                for ap in area_prices:
                    area_info.append(f"rule_id={ap['rule_id']}: 售价={ap['unit_price']}, 市场价={ap['market_price']}")

                return {
                    "success": False,
                    "env": env,
                    "action": "set_price",
                    "data": {"item_number": item_number, "price": price},
                    "error": f"该商品有 {len(area_prices)} 个区域价，请指定 --rule-id 参数",
                    "hint": "区域价格列表:\n  " + "\n  ".join(area_info) + "\n使用 --rule-id 0 可强制修改全国价（不影响区域价）",
                    "elapsed": time.time() - start,
                }

        target_rule_id = rule_id if rule_id is not None else 0

        # 3. 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        orig_token = client.token
        client.token = hub_token
        hub_headers = {"Yami-Origin": "central-web"}

        try:
            if target_rule_id > 0:
                return _update_area_price(client, db, env, item_number, price, target_rule_id, market_price, hub_headers, start)
            else:
                return _update_national_price(client, db, env, item_number, price, seller_id, market_price, hub_headers, start)

        finally:
            client.token = orig_token

    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": "set_price",
            "data": {"item_number": item_number, "price": price, "rule_id": rule_id},
            "error": str(e),
            "elapsed": time.time() - start,
        }


def _update_area_price(client: HttpClient, db: DbClient, env: str, item_number: str, price: float,
                       rule_id: int, market_price: Optional[float], hub_headers: Dict, start: float) -> ActionResult:
    """
    更新区域价格（使用 updateAreaPrices 接口）

    Args:
        client: HTTP 客户端（已设置 hub token）
        db: 数据库客户端
        env: 环境
        item_number: 商品编号
        price: 目标售价
        rule_id: 区域 rule_id
        market_price: 市场价（可选）
        hub_headers: Hub 请求头
        start: 开始时间

    Returns:
        操作结果
    """
    # 1. 查询当前区域价格
    current_area_price = db.query_one(
        """
        SELECT rule_id, unit_price, market_price, limit_quantity
        FROM yamibuy_im.im_item_area_price_setting
        WHERE item_number = %s AND rule_id = %s
        """,
        (item_number, rule_id)
    )

    if not current_area_price:
        raise ItemNotFoundError(f"{item_number} 区域 {rule_id}")

    old_unit_price = float(current_area_price["unit_price"]) if current_area_price["unit_price"] else 0
    old_market_price = float(current_area_price["market_price"]) if current_area_price["market_price"] else 0

    # 2. 构建请求体
    body = {
        "item_number": item_number,
        "rule_id": rule_id,
        "unit_price": price,
        "market_price": market_price if market_price is not None else old_market_price,
        "limit_quantity": int(current_area_price["limit_quantity"]) if current_area_price["limit_quantity"] else 0,
        "source": 5,
        "is_promotion": "N",
        "isLimit": "N"
    }

    # 3. 调用 updateAreaPrices 接口
    status, resp = client.post(
        "/im/item/updateAreaPrices",
        body=body,
        use_central=True,
        extra_headers=hub_headers
    )

    if not client.is_success(status, resp):
        raise ApiRequestError("/im/item/updateAreaPrices", status, client.get_error(resp))

    # 4. 等待数据同步
    time.sleep(VALIDATION_WAIT)

    # 5. 验证结果
    validation = _validate_area_price(db, item_number, rule_id, price)

    return {
        "success": validation["passed"],
        "env": env,
        "action": "set_price (area)",
        "data": {
            "item_number": item_number,
            "rule_id": rule_id,
            "old_unit_price": old_unit_price,
            "new_unit_price": price,
            "old_market_price": old_market_price,
            "new_market_price": market_price if market_price is not None else old_market_price,
        },
        "validation": validation,
        "elapsed": time.time() - start,
    }


def _validate_area_price(db: DbClient, item_number: str, rule_id: int, expected_price: float) -> ValidationResult:
    """
    验证区域价格是否更新成功
    """
    current = db.query_one(
        """
        SELECT unit_price
        FROM yamibuy_im.im_item_area_price_setting
        WHERE item_number = %s AND rule_id = %s
        """,
        (item_number, rule_id)
    )

    actual = float(current["unit_price"]) if current and current["unit_price"] else None
    ok = actual is not None and abs(actual - expected_price) < 0.01

    checks = [{
        "field": f"area_{rule_id}.unit_price",
        "expected": expected_price,
        "actual": actual,
        "ok": ok,
    }]

    return {
        "passed": ok,
        "checks": checks,
        "failed_checks": [] if ok else checks,
        "suggestion": "" if ok else f"区域 {rule_id} 价格未生效，可能需要等待数据同步",
    }


def _update_national_price(client: HttpClient, db: DbClient, env: str, item_number: str, price: float,
                           seller_id: int, market_price: Optional[float], hub_headers: Dict, start: float) -> ActionResult:
    """
    更新全国价格（使用 updateItemPrices 接口）

    重要：必须传递完整的商品信息，只修改价格相关字段，其他字段保持原样。
    后端会校验 stash（MD5 签名），如果数据不完整会返回系统异常。

    Args:
        client: HTTP 客户端（已设置 hub token）
        db: 数据库客户端
        env: 环境
        item_number: 商品编号
        price: 目标售价
        seller_id: 商家ID
        market_price: 市场价（可选）
        hub_headers: Hub 请求头
        start: 开始时间

    Returns:
        操作结果
    """
    # 1. 通过 API 获取商品完整信息（包含 stash）
    item_data = _get_item_full_info_from_api(client, item_number, seller_id)

    stash = item_data.get("stash")
    if not stash:
        raise ApiRequestError("/im/item/queryByItemNumber", 200, "API 返回的商品信息缺少 stash 字段")

    old_unit_price = 0
    item_price_list = item_data.get("itemPriceList", [])
    if item_price_list:
        old_unit_price = float(item_price_list[0].get("unit_price", 0))

    old_market_price = float(item_data.get("market_price", 0))

    # 2. 调用 price/check 接口
    check_body = [{
        "item_number": item_number,
        "clone_type": 0,
        "adjust_price": price,
        "rule_id": 0
    }]

    check_status, check_resp = client.post(
        "/im/item/price/check",
        body=check_body,
        use_central=True,
        extra_headers=hub_headers
    )

    if not client.is_success(check_status, check_resp):
        raise ApiRequestError("/im/item/price/check", check_status, client.get_error(check_resp))

    # 3. 基于 API 返回的完整数据构建请求体
    update_body = dict(item_data)

    if market_price is not None:
        update_body["market_price"] = market_price

    updated_price_list = []
    for p in item_price_list:
        updated_p = dict(p)
        updated_p["unit_price"] = price
        updated_p["source"] = 5
        updated_p["isLimit"] = "N"
        updated_price_list.append(updated_p)
    update_body["itemPriceList"] = updated_price_list

    # 4. 调用 updateItemPrices 接口
    update_status, update_resp = client.post(
        "/im/item/updateItemPrices?source=5",
        body=update_body,
        use_central=True,
        extra_headers=hub_headers
    )

    if not client.is_success(update_status, update_resp):
        error_detail = client.get_error(update_resp)
        resp_str = str(update_resp)[:500] if update_resp else "empty"
        raise ApiRequestError("/im/item/updateItemPrices", update_status, f"{error_detail} | 响应: {resp_str}")

    # 5. 等待数据同步
    time.sleep(VALIDATION_WAIT)

    # 6. 验证结果
    validation = validate_price(db, item_number, price)

    return {
        "success": validation["passed"],
        "env": env,
        "action": "set_price",
        "data": {
            "item_number": item_number,
            "old_unit_price": old_unit_price,
            "new_unit_price": price,
            "old_market_price": old_market_price,
            "new_market_price": market_price if market_price is not None else old_market_price,
            "rule_id": 0,
            "stash": stash[:16] + "..." if stash else None,
        },
        "validation": validation,
        "elapsed": time.time() - start,
    }
