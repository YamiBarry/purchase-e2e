# -*- coding: utf-8 -*-
"""
商品数据验证
验证库存、价格、上下架状态是否正确写入
"""

from core.db import DbClient
from validators.base import make_check, build_validation


def validate_stock(db: DbClient, item_number: str, expected_stock: int, warehouse: str = "001") -> dict:
    """验证库存"""
    row = db.query_one(
        """
        SELECT available_qty
        FROM yamibuy_inventory.inventory_transaction
        WHERE item_number = %s AND warehouse_number = %s
        LIMIT 1
        """,
        (item_number, warehouse)
    )
    actual = int(row["available_qty"]) if row else None
    checks = [make_check("available_qty", expected_stock, actual)]
    return build_validation(checks, "数据未生效，可能是 im-service 或 inventory-service 未正常处理，可稍后重试")


def validate_price(db: DbClient, item_number: str, expected_price: float) -> dict:
    """验证商品价格（检查 im_item_price_setting.unit_price）"""
    row = db.query_one(
        """
        SELECT unit_price
        FROM yamibuy_im.im_item_price_setting
        WHERE item_number = %s
        LIMIT 1
        """,
        (item_number,)
    )
    actual = float(row["unit_price"]) if row and row["unit_price"] else None
    checks = [make_check("unit_price", expected_price, actual)]
    return build_validation(checks, "数据未生效，可能是 im-service 或 inventory-service 未正常处理，可稍后重试")


def validate_status(db: DbClient, item_number: str, expected_status: str) -> dict:
    """
    验证上下架状态
    
    Args:
        db: 数据库客户端
        item_number: 商品编号
        expected_status: 'on' 或 'off'
    
    Returns:
        验证结果，同时检查 im_item.status 和 xysc_goods.is_on_sale
    """
    row = db.query_one(
        """
        SELECT i.status, g.is_on_sale
        FROM yamibuy_im.im_item i
        JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
        WHERE i.item_number = %s
        LIMIT 1
        """,
        (item_number,)
    )
    
    # status: 'A'=上架 'D'=下架
    # is_on_sale: 1=上架 0=下架
    expected_status_val = "A" if expected_status == "on" else "D"
    expected_is_on_sale = 1 if expected_status == "on" else 0
    
    actual_status = row["status"] if row else None
    actual_is_on_sale = int(row["is_on_sale"]) if row else None
    
    checks = [
        make_check("im_item.status", expected_status_val, actual_status),
        make_check("xysc_goods.is_on_sale", expected_is_on_sale, actual_is_on_sale),
    ]
    return build_validation(checks, "数据未生效，可能是 im-service 或 inventory-service 未正常处理，可稍后重试")


def validate_batch_status(db: DbClient, item_numbers: list, expected_status: str) -> dict:
    """
    批量验证上下架状态，同时检查 im_item.status 和 xysc_goods.is_on_sale
    
    Args:
        db: 数据库客户端
        item_numbers: 商品编号列表
        expected_status: 'on' 或 'off'
    
    Returns:
        验证结果
    """
    if not item_numbers:
        return {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""}
    
    # 使用参数化查询构建 IN 子句
    rows = db.query_in(
        """
        SELECT i.item_number, i.status, g.is_on_sale
        FROM yamibuy_im.im_item i
        JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
        WHERE i.item_number IN ({placeholders})
        """,
        item_numbers
    )
    
    # 构建结果映射
    result_map = {row["item_number"]: {"status": row["status"], "is_on_sale": int(row["is_on_sale"])} for row in rows}
    
    # status: 'A'=上架 'D'=下架
    # is_on_sale: 1=上架 0=下架
    expected_status_val = "A" if expected_status == "on" else "D"
    expected_is_on_sale = 1 if expected_status == "on" else 0
    status_desc = "上架" if expected_status == "on" else "下架"
    
    checks = []
    for item_no in item_numbers:
        item_data = result_map.get(item_no, {})
        actual_status = item_data.get("status")
        actual_is_on_sale = item_data.get("is_on_sale")
        
        # 检查 im_item.status
        status_check = {
            "field": f"{item_no}.status",
            "expected": expected_status_val,
            "actual": actual_status,
            "ok": actual_status == expected_status_val,
        }
        checks.append(status_check)
        
        # 检查 xysc_goods.is_on_sale
        is_on_sale_check = {
            "field": f"{item_no}.is_on_sale",
            "expected": expected_is_on_sale,
            "actual": actual_is_on_sale,
            "ok": actual_is_on_sale == expected_is_on_sale,
        }
        checks.append(is_on_sale_check)
    
    failed = [c for c in checks if not c["ok"]]
    suggestion = ""
    if failed:
        # 提取失败的商品编号（去重）
        failed_items = list(set(c["field"].split(".")[0] for c in failed))
        suggestion = f"以下商品{status_desc}未生效: {', '.join(failed_items)}，可能需要等待数据同步或检查商品状态"
    
    return {
        "passed": len(failed) == 0,
        "checks": checks,
        "failed_checks": failed,
        "suggestion": suggestion,
    }


def validate_batch_stock(db: DbClient, item_numbers: list, expected_stock: int, warehouse: str = "001") -> dict:
    """
    批量验证库存
    
    Args:
        db: 数据库客户端
        item_numbers: 商品编号列表
        expected_stock: 期望的库存值
        warehouse: 仓库编号
    
    Returns:
        验证结果
    """
    if not item_numbers:
        return {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""}
    
    # 使用参数化查询构建 IN 子句
    rows = db.query_in(
        """
        SELECT item_number, available_qty
        FROM yamibuy_inventory.inventory_transaction
        WHERE item_number IN ({placeholders}) AND warehouse_number = %s
        """,
        item_numbers,
        extra_params=(warehouse,)
    )
    
    # 构建结果映射
    result_map = {row["item_number"]: int(row["available_qty"]) for row in rows}
    
    checks = []
    for item_no in item_numbers:
        actual = result_map.get(item_no)
        check = {
            "field": f"{item_no}.available_qty",
            "expected": expected_stock,
            "actual": actual,
            "ok": actual == expected_stock,
        }
        checks.append(check)
    
    failed = [c for c in checks if not c["ok"]]
    suggestion = ""
    if failed:
        failed_items = [c["field"].split(".")[0] for c in failed]
        suggestion = f"以下商品库存未生效: {', '.join(failed_items)}，可能需要等待数据同步"
    
    return {
        "passed": len(failed) == 0,
        "checks": checks,
        "failed_checks": failed,
        "suggestion": suggestion,
    }


def validate_batch_stock_multi_warehouse(db: DbClient, item_warehouse_map: dict, expected_stock: int) -> dict:
    """
    批量验证库存（支持不同仓库）
    
    Args:
        db: 数据库客户端
        item_warehouse_map: {item_number: warehouse_number} 映射
        expected_stock: 期望的库存值
    
    Returns:
        验证结果
    """
    if not item_warehouse_map:
        return {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""}
    
    # 使用参数化查询构建 OR 条件
    rows = db.query_or_conditions(
        """
        SELECT item_number, warehouse_number, available_qty
        FROM yamibuy_inventory.inventory_transaction
        WHERE {conditions}
        """,
        condition_template="(item_number = %s AND warehouse_number = %s)",
        params_list=[(item_no, wh) for item_no, wh in item_warehouse_map.items()]
    )
    
    # 构建结果映射
    result_map = {row["item_number"]: int(row["available_qty"]) for row in rows}
    
    checks = []
    for item_no, wh in item_warehouse_map.items():
        actual = result_map.get(item_no)
        check = {
            "field": f"{item_no}.available_qty({wh})",
            "expected": expected_stock,
            "actual": actual,
            "ok": actual == expected_stock,
        }
        checks.append(check)
    
    failed = [c for c in checks if not c["ok"]]
    suggestion = ""
    if failed:
        failed_items = [c["field"].split(".")[0] for c in failed]
        suggestion = f"以下商品库存未生效: {', '.join(failed_items)}，可能需要等待数据同步"
    
    return {
        "passed": len(failed) == 0,
        "checks": checks,
        "failed_checks": failed,
        "suggestion": suggestion,
    }
