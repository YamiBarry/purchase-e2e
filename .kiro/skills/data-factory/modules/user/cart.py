# -*- coding: utf-8 -*-
"""
购物车模块
支持：加购商品、清空购物车
"""

import time
from typing import List, Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.types import ActionResult, Environment
from core.exceptions import CartError
from core.constants import YAMI_SELLER_ID_US, YAMI_SELLER_ID_CA


def _get_user_zipcode(client: HttpClient) -> tuple:
    """
    获取用户当前的 zipcode 和仓库信息
    
    Args:
        client: HTTP 客户端（已设置用户 token）
    
    Returns:
        (zipcode, warehouse_number, warehouse_name) 元组
        获取失败返回 ("91789", "001", "LA")
    """
    try:
        status, resp = client.get("/ec-customer/zipcode")
        if status == 200 and resp.get("body"):
            body = resp["body"]
            zipcode = body.get("zipcode", "91789")
            wh_number = body.get("customer_wh_number", "001")
            wh_name = "NJ" if wh_number == "002" else "LA"
            return zipcode, wh_number, wh_name
    except Exception:
        pass
    return "91789", "001", "LA"


def _get_warehouse_by_zipcode(client: HttpClient, zipcode: str) -> dict:
    """
    根据 zipcode 获取对应的仓库信息
    
    通过更新用户 zipcode 后再查询来获取仓库信息
    
    Args:
        client: HTTP 客户端
        zipcode: 邮编
    
    Returns:
        仓库信息字典，包含 warehouse_id, warehouse_name, warehouse_number 等
    """
    try:
        # 先更新 zipcode，再查询获取仓库信息
        client.put("/ec-customer/zipcode", body={"zipcode": zipcode, "country": "United States"})
        status, resp = client.get("/ec-customer/zipcode")
        if status == 200 and resp.get("body"):
            body = resp["body"]
            wh_number = body.get("customer_wh_number", "001")
            wh_name = "NJ" if wh_number == "002" else "LA"
            wh_id = 2 if wh_number == "002" else 1
            return {
                "warehouse_id": wh_id,
                "warehouse_name": wh_name,
                "warehouse_number": wh_number,
                "zipcode": zipcode,
            }
    except Exception:
        pass
    # 默认 LA 仓库
    return {"warehouse_id": 1, "warehouse_name": "LA", "warehouse_number": "001", "zipcode": zipcode}


def _find_item_by_type_and_warehouse(db: DbClient, item_type: str, warehouse_number: str, 
                                      zipcode: str, limit: int = 1) -> List[str]:
    """
    根据商品类型和仓库查找有库存的商品
    
    Args:
        db: 数据库客户端
        item_type: 商品类型（如 yami, fby, seller 等）
        warehouse_number: 仓库编号（001=LA, 002=NJ）
        zipcode: 邮编（用于地区限制商品）
        limit: 返回数量
    
    Returns:
        商品编号列表
    """
    from modules.item.find import ITEM_TYPES
    
    if item_type not in ITEM_TYPES:
        raise ValueError(f"不支持的商品类型: {item_type}")
    
    type_config = ITEM_TYPES[item_type]
    params = []
    
    # 基础 SELECT
    select_fields = "i.item_number"
    
    # 基础 FROM 和 JOIN
    from_clause = """
        FROM yamibuy_im.im_item i
        JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
    """
    
    # 基础 WHERE 条件
    where_conditions = [
        "i.status = 'A'",
        "g.is_on_sale = 1",
        "g.is_delete = 0",
        f"i.business_type = {type_config['business_type']}",
        f"i.item_type = {type_config['item_type']}",
    ]
    
    # seller_id 条件
    seller_id_config = type_config.get("seller_id")
    if seller_id_config == 0:
        # 自营：根据仓库号推断站点（101=CA站，其他=US站）
        if warehouse_number == "101":
            where_conditions.append(f"i.seller_id = {YAMI_SELLER_ID_CA}")
        else:
            where_conditions.append(f"i.seller_id = {YAMI_SELLER_ID_US}")
    elif seller_id_config == ">0":
        where_conditions.append(f"i.seller_id > 0 AND i.seller_id != {YAMI_SELLER_ID_CA}")
        where_conditions.append("i.seller_status = 'A'")
    
    # category_id 条件（第三方礼券）
    if type_config.get("category_id"):
        where_conditions.append(f"i.category_id = {type_config['category_id']}")
    
    # share_inventory 条件
    share_config = type_config.get("share")
    if share_config is not None:
        from_clause += """
        JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
        """
        where_conditions.append(f"ie.share_inventory = {share_config}")
        if type_config["item_type"] != 6:
            where_conditions.append("ie.storage_type = 0")
    
    # 地区限制条件
    area_type = type_config.get("area_type")
    if area_type is None:
        # 无地区限制：排除有地区映射的商品
        where_conditions.append("""
            i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
        """)
    elif area_type == "local":
        # 本地化商品
        from_clause += """
        JOIN yamibuy_im.im_item_area_mapping am ON i.item_number = am.item_number
        JOIN yamibuy_master.xysc_shop_district_zipcode sdz ON am.zipcode_limit_id = sdz.rule_id
        """
        where_conditions.append("sdz.zipcode = %s")
        params.append(zipcode)
    elif area_type == "region":
        # 大区商品
        from_clause += """
        JOIN yamibuy_im.im_item_area_mapping am ON i.item_number = am.item_number
        JOIN yamibuy_master.xysc_shop_district_zipcode sdz ON am.zipcode_limit_id = sdz.rule_id
        JOIN yamibuy_master.xysc_shop_district_rule sdr ON am.zipcode_limit_id = sdr.rule_id
        """
        where_conditions.append("sdz.zipcode = %s")
        params.append(zipcode)
        where_conditions.append("sdr.area_type = 3")
    
    # 库存条件：只查指定仓库有库存的商品
    is_third_party = type_config["business_type"] == 3 or (type_config["business_type"] == 6 and seller_id_config == ">0")
    
    if is_third_party:
        # 第三方商品：查总库存
        from_clause += """
        JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
        """
        having_clause = "HAVING SUM(inv.available_qty) >= 1"
    else:
        # 自营/FBY 商品：只查指定仓库
        from_clause += """
        JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
            AND inv.warehouse_number = %s
        """
        params.append(warehouse_number)
        having_clause = "HAVING SUM(inv.available_qty) >= 1"
    
    # 组装 SQL
    sql = f"""
        SELECT {select_fields}
        {from_clause}
        WHERE {" AND ".join(where_conditions)}
        GROUP BY i.item_number
        {having_clause}
        ORDER BY RAND()
        LIMIT {limit}
    """
    
    rows = db.query_all(sql, tuple(params) if params else None)
    return [row["item_number"] for row in rows] if rows else []


def action_add_to_cart(
    client: HttpClient,
    env: Environment,
    email: str,
    item_numbers: Optional[List[str]] = None,
    item_type: Optional[str] = None,
    zipcode: Optional[str] = None,
    qty: int = 1,
    db: Optional[DbClient] = None
) -> ActionResult:
    """
    给用户购物车加商品
    
    支持两种方式：
    1. 指定 item_numbers：直接加购指定商品
    2. 指定 item_type：自动查找该类型在用户仓库有库存的商品并加购
    
    Args:
        client: HTTP 客户端
        env: 环境
        email: 用户邮箱
        item_numbers: 商品编号列表（与 item_type 二选一）
        item_type: 商品类型（与 item_numbers 二选一），如 yami, fby, seller 等
        zipcode: 邮编（可选）。指定时更新用户 zipcode；不指定时使用用户当前 zipcode
        qty: 查找商品数量（item_type 模式），默认 1
        db: 数据库客户端（item_type 模式需要）
    
    Returns:
        ActionResult: 包含 success_items/failed_items/warehouse
    """
    start = time.time()
    try:
        # 校验参数
        if not item_numbers and not item_type:
            raise ValueError("必须提供 item_numbers 或 item_type")
        
        # 处理 zipcode 逻辑
        if zipcode:
            # 用户明确指定了 zipcode，更新用户的 zipcode 并获取仓库信息
            warehouse_info = _get_warehouse_by_zipcode(client, zipcode)
            current_zipcode = zipcode
            warehouse_number = warehouse_info.get("warehouse_number", "001")
            warehouse_name = warehouse_info.get("warehouse_name", "LA")
        else:
            # 用户没指定，获取用户当前的 zipcode 和仓库信息（不修改）
            current_zipcode, warehouse_number, warehouse_name = _get_user_zipcode(client)
        
        # 如果指定了 item_type，自动查找商品
        found_by_type = False
        if item_type and not item_numbers:
            if not db:
                raise ValueError("item_type 模式需要数据库连接")
            item_numbers = _find_item_by_type_and_warehouse(db, item_type, warehouse_number, current_zipcode, limit=qty)
            found_by_type = True
            if not item_numbers:
                return {
                    "success": False,
                    "env": env,
                    "action": "add_to_cart",
                    "data": {
                        "email": email,
                        "zipcode": current_zipcode,
                        "warehouse": warehouse_name,
                        "item_type": item_type,
                        "message": f"未找到类型为 {item_type} 且在 {warehouse_name} 仓库有库存的商品",
                    },
                    "validation": {"passed": False, "checks": [], "failed_checks": [], "suggestion": "尝试其他商品类型或检查库存"},
                    "elapsed": time.time() - start,
                }

        success_items = []
        failed_items = []

        for item_number in item_numbers:
            status, resp = client.post(
                "/ec-so/cart",
                body=[{"item_number": item_number, "qty": 1, "check_status": 1}],
            )
            body = resp.get("body", {})
            failed = body.get("failed_items", []) if isinstance(body, dict) else []
            if status != 200 or failed:
                reason = failed[0].get("reason", client.get_error(resp)) if failed else client.get_error(resp)
                failed_items.append({"item_number": item_number, "reason": reason})
            else:
                success_items.append(item_number)
        
        # 验证：查询购物车确认商品是否真的加入
        time.sleep(0.5)
        cart_status, cart_resp = client.get("/ec-so/cart", extra_headers={"source_flag": "1"})
        cart_items = []
        if cart_status == 200 and cart_resp.get("body"):
            cart_body = cart_resp["body"]
            if isinstance(cart_body, dict):
                for seller in cart_body.get("normal_items", []):
                    for item in seller.get("items", []):
                        cart_items.append(item.get("item_number"))
        
        # 检查 success_items 是否真的在购物车中
        verified_success = []
        for item in success_items:
            if item in cart_items:
                verified_success.append(item)
            else:
                failed_items.append({"item_number": item, "reason": "加购接口返回成功但购物车中未找到"})
        success_items = verified_success

        all_success = len(failed_items) == 0 and len(success_items) > 0
        checks = []
        for item in success_items:
            checks.append({"field": f"cart_{item}", "expected": "added", "actual": "added", "ok": True})
        for item in failed_items:
            checks.append({"field": f"cart_{item['item_number']}", "expected": "added", "actual": item["reason"], "ok": False})

        validation = {
            "passed": all_success,
            "checks": checks,
            "failed_checks": [c for c in checks if not c["ok"]],
            "suggestion": "部分商品加购失败，可能是库存不足、商品下架或地区限制" if failed_items else "",
        }
        
        data = {
            "email": email,
            "zipcode": current_zipcode,
            "warehouse": warehouse_name,
            "success_items": success_items,
            "failed_items": failed_items,
        }
        if found_by_type:
            data["item_type"] = item_type
            data["found_by_type"] = True
        
        return {
            "success": all_success,
            "env": env,
            "action": "add_to_cart",
            "data": data,
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except Exception as e:
        return {"success": False, "env": env, "action": "add_to_cart",
                "data": {}, "error": str(e), "elapsed": time.time() - start}


def action_clear_cart(
    client: HttpClient,
    env: Environment,
    email: str
) -> ActionResult:
    """
    清空用户购物车
    
    Args:
        client: HTTP 客户端
        env: 环境
        email: 用户邮箱
    
    Returns:
        ActionResult: 包含 cleared/cleared_items
    """
    start = time.time()
    try:
        # 查购物车
        status, resp = client.get("/ec-so/cart", extra_headers={"source_flag": "1"})
        if status != 200:
            raise CartError("查询", client.get_error(resp))

        body = resp.get("body", {})
        if not isinstance(body, dict):
            return {
                "success": True, "env": env, "action": "clear_cart",
                "data": {"email": email, "cleared": 0},
                "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - start,
            }

        item_numbers = []
        for seller in body.get("normal_items", []):
            for item in seller.get("items", []):
                num = item.get("item_number")
                if num and num not in item_numbers:
                    item_numbers.append(num)
        for item in body.get("error_items", []):
            num = item.get("item_number")
            if num and num not in item_numbers:
                item_numbers.append(num)

        if not item_numbers:
            return {
                "success": True, "env": env, "action": "clear_cart",
                "data": {"email": email, "cleared": 0, "message": "购物车已经是空的"},
                "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - start,
            }

        # 删除所有商品
        status, resp = client.delete("/ec-so/cart", body=item_numbers,
                                     extra_headers={"source_flag": "1"})

        # 验证购物车是否为空
        time.sleep(1)
        status2, resp2 = client.get("/ec-so/cart", extra_headers={"source_flag": "1"})
        cart_body = resp2.get("body", {}) if status2 == 200 else {}
        remaining = []
        if isinstance(cart_body, dict):
            for seller in cart_body.get("normal_items", []):
                for item in seller.get("items", []):
                    remaining.append(item.get("item_number"))

        ok = len(remaining) == 0
        validation = {
            "passed": ok,
            "checks": [{"field": "cart_empty", "expected": True, "actual": ok, "ok": ok}],
            "failed_checks": [] if ok else [{"field": "cart_empty", "expected": True, "actual": False, "ok": False}],
            "suggestion": "" if ok else "购物车清空失败，请重试",
        }
        return {
            "success": ok, "env": env, "action": "clear_cart",
            "data": {"email": email, "cleared": len(item_numbers), "cleared_items": item_numbers},
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except Exception as e:
        return {"success": False, "env": env, "action": "clear_cart",
                "data": {}, "error": str(e), "elapsed": time.time() - start}
