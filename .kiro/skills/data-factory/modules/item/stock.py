# -*- coding: utf-8 -*-
"""
商品库存模块
支持：修改单个/批量商品库存
"""

import time
from typing import Dict, List, Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.types import ActionResult
from core.exceptions import ItemNotFoundError, ItemStockError, AuthError
from core.constants import is_third_party_seller
from validators.item_validator import validate_batch_stock_multi_warehouse
from config import VALIDATION_WAIT


def action_set_stock(client: HttpClient, db: DbClient, env: str, item_number: str, stock: int, warehouse: str = "001") -> ActionResult:
    """
    修改单个商品库存（设置到指定值）

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        item_number: 商品编号
        stock: 目标库存值
        warehouse: 仓库编号，默认 001（仅 US 站自营/FBY 商品生效；CA 站自营商品自动使用 101 仓；第三方商品自动使用 9000{seller_id}）

    Returns:
        操作结果
    """
    return action_batch_set_stock(client, db, env, [item_number], stock, warehouse)


def _get_item_warehouse_info(db: DbClient, item_numbers: List[str]) -> Dict[str, Dict]:
    """
    查询商品的仓库信息，自动判断第三方商品的仓库

    商品类型判断规则：
    - 自营（US站）：business_type=1, seller_id=0, site_code=us → 仓库 001/002，用 inventoryPMAdjust
    - 自营（CA站）：business_type=1, seller_id=5000, site_code=ca → 仓库 101，用 inventoryPMAdjust
    - 自营预售：business_type=6, seller_id=0(US)/5000(CA) → 仓库 001/002（US）或 101（CA），用 inventoryPMAdjust
    - FBY：business_type=5, seller_id>0（非自营） → 仓库 001/002，用 inventoryPMAdjust
    - 第三方直邮：business_type=3, seller_id 非自营 → 仓库 9000{seller_id}，用 updateInventoryInfo
    - 第三方预售：business_type=6, seller_id 非自营 → 仓库 9000{seller_id}，用 updateInventoryInfo

    Args:
        db: 数据库客户端
        item_numbers: 商品编号列表

    Returns:
        {item_number: {"seller_id": x, "business_type": y, "site_code": z, "auto_warehouse": "xxx" or None}}
    """
    placeholders = ",".join(["%s"] * len(item_numbers))
    rows = db.query_all(
        f"""
        SELECT item_number, seller_id, business_type, site_code
        FROM yamibuy_im.im_item
        WHERE item_number IN ({placeholders})
        """,
        tuple(item_numbers)
    )

    result = {}
    for row in rows:
        item_no = row["item_number"]
        seller_id = int(row["seller_id"]) if row["seller_id"] else 0
        business_type = int(row["business_type"]) if row["business_type"] else 1
        site_code = (row.get("site_code") or "us").lower()

        # 第三方商品：business_type 为 3 或 6，且 seller_id 不是自营（US=0，CA=5000）
        if is_third_party_seller(seller_id, business_type):
            warehouse = f"9000{seller_id}"
        else:
            warehouse = None  # 自营/FBY 不在这里指定，由 site_code 决定

        result[item_no] = {
            "seller_id": seller_id,
            "business_type": business_type,
            "site_code": site_code,
            "auto_warehouse": warehouse,
        }

    return result


def action_batch_set_stock(client: HttpClient, db: DbClient, env: str, item_numbers: List[str], stock: int, warehouse: str = "001") -> ActionResult:
    """
    批量修改商品库存（设置到指定值）

    自动判断商品类型：
    - 第三方（business_type=3 或 6，且 seller_id>0）：使用 updateInventoryInfo 接口直接设置，自动使用 9000{seller_id} 仓库
    - 自营/FBY/自营预售：使用 inventoryPMAdjust 接口增量调整，使用 warehouse 参数指定的仓库

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        item_numbers: 商品编号列表
        stock: 目标库存值（所有商品设置为相同值）
        warehouse: 仓库编号，默认 001（仅对自营/FBY/自营预售商品生效）

    Returns:
        操作结果
    """
    start = time.time()
    try:
        if not item_numbers:
            raise ValueError("item_numbers 不能为空")

        # 1. 查询商品类型，确定每个商品的仓库和调用方式
        item_info = _get_item_warehouse_info(db, item_numbers)

        # 检查是否所有商品都存在
        missing_items = [item for item in item_numbers if item not in item_info]
        if missing_items:
            raise ItemNotFoundError(', '.join(missing_items))

        # 分组：自营/FBY 和 第三方直邮
        yami_items = []
        seller_items = []
        item_warehouse_map = {}

        for item_no in item_numbers:
            info = item_info[item_no]
            if info["auto_warehouse"]:
                # 第三方商品：使用自动确定的仓库（9000{seller_id}）
                seller_items.append(item_no)
                item_warehouse_map[item_no] = info["auto_warehouse"]
            else:
                # 自营/FBY 商品：根据 site_code 决定仓库
                # CA 站自营只有 101 仓；US 站用用户传入的 warehouse 参数（默认 001）
                yami_items.append(item_no)
                if info.get("site_code") == "ca":
                    item_warehouse_map[item_no] = "101"
                else:
                    item_warehouse_map[item_no] = warehouse

        # 2. 批量查询当前库存
        conditions = []
        params = []
        for item_no, wh in item_warehouse_map.items():
            conditions.append("(item_number = %s AND warehouse_number = %s)")
            params.extend([item_no, wh])

        rows = db.query_all(
            f"""
            SELECT rec_id, item_number, warehouse_number, available_qty, allocated_qty
            FROM yamibuy_inventory.inventory_transaction
            WHERE {" OR ".join(conditions)}
            """,
            tuple(params)
        )

        # 构建当前库存映射
        current_map = {
            row["item_number"]: {
                "rec_id": int(row["rec_id"]),
                "warehouse": row["warehouse_number"],
                "available_qty": int(row["available_qty"]),
                "allocated_qty": int(row["allocated_qty"]),
            }
            for row in rows
        }

        # 检查是否所有商品都有库存记录
        missing = []
        for item_no in item_numbers:
            if item_no not in current_map:
                wh = item_warehouse_map[item_no]
                missing.append(f"{item_no}(仓库:{wh})")
        if missing:
            raise ItemStockError(', '.join(missing), "没有库存记录")

        # 3. 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        details = []

        # 4. 处理自营/FBY 商品（使用 inventoryPMAdjust）
        yami_adjust_list = []
        need_expand_allocated = []

        for item_no in yami_items:
            current = current_map[item_no]
            current_qty = current["available_qty"]
            allocated_qty = current["allocated_qty"]
            rec_id = current["rec_id"]
            item_wh = item_warehouse_map[item_no]
            change_qty = stock - current_qty

            if change_qty == 0:
                details.append({
                    "item_number": item_no,
                    "warehouse": item_wh,
                    "type": "yami",
                    "current_stock": current_qty,
                    "change_qty": 0,
                    "status": "skip",
                    "message": "已是目标值",
                })
                continue

            # 校验变更范围
            if change_qty > allocated_qty:
                expand_qty = change_qty - allocated_qty
                need_expand_allocated.append({
                    "item_number": item_no,
                    "warehouse": item_wh,
                    "rec_id": rec_id,
                    "expand_qty": expand_qty,
                    "change_qty": change_qty,
                    "current_qty": current_qty,
                    "allocated_qty": allocated_qty,
                })
                continue

            if change_qty < -current_qty:
                details.append({
                    "item_number": item_no,
                    "warehouse": item_wh,
                    "type": "yami",
                    "current_stock": current_qty,
                    "change_qty": change_qty,
                    "status": "error",
                    "message": f"变更值小于 -available_qty ({-current_qty})",
                })
                continue

            yami_adjust_list.append({
                "warehouse_number": item_wh,
                "item_number": item_no,
                "change_qty": change_qty,
                "in_user": "data-factory",
            })
            details.append({
                "item_number": item_no,
                "warehouse": item_wh,
                "type": "yami",
                "current_stock": current_qty,
                "change_qty": change_qty,
                "status": "pending",
            })

        # 5. 处理第三方直邮商品（使用 updateInventoryInfo）
        seller_update_list = []
        for item_no in seller_items:
            current = current_map[item_no]
            current_qty = current["available_qty"]
            item_wh = item_warehouse_map[item_no]
            change_qty = stock - current_qty

            if change_qty == 0:
                details.append({
                    "item_number": item_no,
                    "warehouse": item_wh,
                    "type": "seller",
                    "current_stock": current_qty,
                    "change_qty": 0,
                    "status": "skip",
                    "message": "已是目标值",
                })
                continue

            seller_update_list.append({
                "warehouse_number": item_wh,
                "item_number": item_no,
                "quantity": stock,
            })
            details.append({
                "item_number": item_no,
                "warehouse": item_wh,
                "type": "seller",
                "current_stock": current_qty,
                "target_stock": stock,
                "status": "pending",
            })

        # 6. 调用接口
        orig_token = client.token
        client.token = hub_token

        try:
            # 6.1 先处理需要扩展 allocated_qty 的商品
            if need_expand_allocated:
                expand_list = []
                for item in need_expand_allocated:
                    expand_list.append({
                        "rec_id": item["rec_id"],
                        "warehouse_number": item["warehouse"],
                        "item_number": item["item_number"],
                        "quantity": item["expand_qty"],
                        "edit_user": "data-factory",
                    })

                expand_body = {
                    "updateListMap": {
                        "allocated_qty": expand_list
                    },
                    "logList": []
                }

                resp_status, resp = client.post(
                    "/inventoryTransaction/items",
                    body=expand_body,
                    use_central=True,
                    service="inventory"
                )

                if not client.is_success(resp_status, resp):
                    for item in need_expand_allocated:
                        details.append({
                            "item_number": item["item_number"],
                            "warehouse": item["warehouse"],
                            "type": "yami",
                            "current_stock": item["current_qty"],
                            "change_qty": item["change_qty"],
                            "status": "error",
                            "message": f"扩展 allocated_qty 失败: {client.get_error(resp)}",
                        })
                else:
                    for item in need_expand_allocated:
                        yami_adjust_list.append({
                            "warehouse_number": item["warehouse"],
                            "item_number": item["item_number"],
                            "change_qty": item["change_qty"],
                            "in_user": "data-factory",
                        })
                        details.append({
                            "item_number": item["item_number"],
                            "warehouse": item["warehouse"],
                            "type": "yami",
                            "current_stock": item["current_qty"],
                            "change_qty": item["change_qty"],
                            "allocated_expanded": item["expand_qty"],
                            "status": "pending",
                        })

            # 6.2 调用自营商品接口
            if yami_adjust_list:
                resp_status, resp = client.post(
                    "/service/inventoryPMAdjust",
                    body=yami_adjust_list,
                    use_central=True,
                    service="inventory"
                )
                if not client.is_success(resp_status, resp):
                    raise ItemStockError("批量", f"自营商品库存调整失败: {client.get_error(resp)}")

                adjusted_items = {item["item_number"] for item in yami_adjust_list}
                for d in details:
                    if d["item_number"] in adjusted_items and d["status"] == "pending":
                        d["status"] = "success"

            # 6.3 调用第三方直邮商品接口
            if seller_update_list:
                body = {
                    "type": "seller",
                    "action": "Update",
                    "user": "data-factory",
                    "iteminfos": seller_update_list,
                }
                resp_status, resp = client.post(
                    "/service/updateInventoryInfo",
                    body=body,
                    use_central=True,
                    service="inventory"
                )
                if not client.is_success(resp_status, resp):
                    raise ItemStockError("批量", f"第三方商品库存更新失败: {client.get_error(resp)}")

                updated_items = {item["item_number"] for item in seller_update_list}
                for d in details:
                    if d["item_number"] in updated_items and d["status"] == "pending":
                        d["status"] = "success"
        finally:
            client.token = orig_token

        # 7. 等待数据同步
        time.sleep(VALIDATION_WAIT)

        # 8. 验证结果
        validation = validate_batch_stock_multi_warehouse(db, item_warehouse_map, stock)

        adjusted_count = len([d for d in details if d["status"] == "success"])

        return {
            "success": validation["passed"],
            "env": env,
            "action": "batch_set_stock",
            "data": {
                "item_numbers": item_numbers,
                "default_warehouse": warehouse,
                "target_stock": stock,
                "adjusted_count": adjusted_count,
                "yami_count": len(yami_items),
                "seller_count": len(seller_items),
                "details": details,
            },
            "validation": validation,
            "elapsed": time.time() - start,
        }

    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": "batch_set_stock",
            "data": {"item_numbers": item_numbers, "warehouse": warehouse, "stock": stock},
            "error": str(e),
            "elapsed": time.time() - start,
        }
