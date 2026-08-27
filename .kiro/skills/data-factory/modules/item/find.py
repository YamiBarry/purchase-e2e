# -*- coding: utf-8 -*-
"""
商品查找模块
支持：按类型查找商品、库存条件筛选
"""

import time
from typing import Dict, List, Optional, Tuple, Any

from core.constants import is_third_party_seller, YAMI_SELLER_ID_US, YAMI_SELLER_ID_CA, YAMI_SELLER_IDS
from core.db import DbClient
from core.types import ActionResult


class ItemStatus:
    """商品状态枚举"""
    ACTIVE = "A"      # 上架
    DEACTIVE = "D"    # 下架


class StockCondition:
    """库存条件"""
    BOTH_HAVE = "both"      # 两仓都有货（默认）
    WH1_ONLY = "wh1_only"   # 仅1仓有货，2仓无货
    WH2_ONLY = "wh2_only"   # 仅2仓有货，1仓无货
    BOTH_NONE = "none"      # 两仓都无货


# 商品类型配置
ITEM_TYPES = {
    "yami": {
        "name": "自营全国商品",
        "desc": "business_type=1, share=0, 无地区限制",
        "business_type": 1,
        "share": 0,
        "area_type": None,
        "seller_id": 0,
        "item_type": 1,
    },
    "yami_share": {
        "name": "自营全国共享库存商品",
        "desc": "business_type=1, share=1, 无地区限制",
        "business_type": 1,
        "share": 1,
        "area_type": None,
        "seller_id": 0,
        "item_type": 1,
    },
    "yami_region": {
        "name": "自营大区商品",
        "desc": "business_type=1, share=0, 有大区限制",
        "business_type": 1,
        "share": 0,
        "area_type": "region",
        "seller_id": 0,
        "item_type": 1,
    },
    "yami_region_share": {
        "name": "自营大区共享库存商品",
        "desc": "business_type=1, share=1, 有大区限制",
        "business_type": 1,
        "share": 1,
        "area_type": "region",
        "seller_id": 0,
        "item_type": 1,
    },
    "yami_local": {
        "name": "自营本地化商品",
        "desc": "business_type=1, share=0, 有本地化限制",
        "business_type": 1,
        "share": 0,
        "area_type": "local",
        "seller_id": 0,
        "item_type": 1,
    },
    "yami_presale": {
        "name": "自营预售商品",
        "desc": "business_type=6, seller_id=0",
        "business_type": 6,
        "share": None,
        "area_type": None,
        "seller_id": 0,
        "item_type": 6,
    },
    "fby": {
        "name": "FBY全国商品",
        "desc": "business_type=5, share=0",
        "business_type": 5,
        "share": 0,
        "area_type": None,
        "seller_id": ">0",
        "item_type": 1,
    },
    "fby_share": {
        "name": "FBY全国共享库存商品",
        "desc": "business_type=5, share=1",
        "business_type": 5,
        "share": 1,
        "area_type": None,
        "seller_id": ">0",
        "item_type": 1,
    },
    "seller": {
        "name": "第三方直邮商品",
        "desc": "business_type=3, seller_id>0",
        "business_type": 3,
        "share": None,
        "area_type": None,
        "seller_id": ">0",
        "item_type": 1,
    },
    "seller_presale": {
        "name": "第三方预售商品",
        "desc": "business_type=6, seller_id>0",
        "business_type": 6,
        "share": None,
        "area_type": None,
        "seller_id": ">0",
        "item_type": 6,
    },
    "seller_coupon": {
        "name": "第三方礼券商品",
        "desc": "business_type=3, category_id=1406",
        "business_type": 3,
        "share": None,
        "area_type": None,
        "seller_id": ">0",
        "item_type": 1,
        "category_id": 1406,
    },
    "egift": {
        "name": "自营虚拟礼卡商品",
        "desc": "business_type=1, item_type=7",
        "business_type": 1,
        "share": 0,
        "area_type": None,
        "seller_id": 0,
        "item_type": 7,
    },
    "crv": {
        "name": "CRV商品",
        "desc": "自营全国商品，带CRV押金（加州等州）",
        "business_type": 1,
        "share": None,  # 不限制共享库存，CRV商品可能是共享或非共享
        "area_type": None,
        "seller_id": 0,
        "item_type": 1,
        "has_crv": True,
    },
    "import_fee": {
        "name": "进口费用商品",
        "desc": "第三方直邮/预售商品，带进口费用",
        "business_type": [3, 6],  # 第三方直邮 + 预售
        "share": None,
        "area_type": None,
        "seller_id": ">0",
        "item_type": [1, 6],  # 普通 + 预售
        "has_import_fee": True,
    },
}


def action_find_item(db: DbClient, env: str, item_type: str,
                     stock_condition: str = "both",
                     seller_id: Optional[int] = None,
                     zipcode: Optional[str] = None,
                     state: Optional[str] = None,
                     site: Optional[str] = None,
                     min_stock: int = 5,
                     limit: int = 1) -> ActionResult:
    """
    查找指定类型的商品

    查询策略：先查库存>=min_stock的商品，如果没有结果，降级查库存>0的商品

    Args:
        db: 数据库客户端
        env: 环境
        item_type: 商品类型（见 ITEM_TYPES）
        stock_condition: 库存条件
            - both: 两仓都有货（默认）
            - wh1_only: 仅1仓有货，2仓无货
            - wh2_only: 仅2仓有货，1仓无货
            - none: 两仓都无货
        seller_id: 指定商家ID（FBY/第三方可选）
        zipcode: 邮编（本地化/大区商品需要）
        state: 州缩写（CRV商品可选，如 CA/CT/HI/IA/ME/MA/NY/OR/VT）
        site: 站点代码，us=美国站，ca=加拿大站，不传则不过滤（默认查所有站点）
        min_stock: 最小库存要求，默认5
        limit: 返回数量，默认1

    Returns:
        查找结果
    """
    start = time.time()

    try:
        # 1. 校验商品类型
        if item_type not in ITEM_TYPES:
            available_types = ", ".join(ITEM_TYPES.keys())
            raise ValueError(f"不支持的商品类型: {item_type}，可选: {available_types}")

        type_config = ITEM_TYPES[item_type]
        type_name = type_config["name"]

        # 2. 校验库存条件
        valid_conditions = [StockCondition.BOTH_HAVE, StockCondition.WH1_ONLY,
                           StockCondition.WH2_ONLY, StockCondition.BOTH_NONE]
        if stock_condition not in valid_conditions:
            raise ValueError(f"不支持的库存条件: {stock_condition}，可选: {', '.join(valid_conditions)}")

        # 3. 本地化/大区商品需要 zipcode
        if type_config.get("area_type") in ("local", "region") and not zipcode:
            zipcode = "91789"  # 默认 LA 地区

        # 4. 先查库存 >= min_stock 的商品
        actual_min_stock = min_stock
        sql, params = _build_find_item_sql(type_config, stock_condition, seller_id, zipcode, state, site, actual_min_stock, limit)
        rows = db.query_all(sql, params)

        # 5. 如果没有结果且 min_stock > 1，降级查库存 > 0 的商品
        fallback_used = False
        if not rows and actual_min_stock > 1 and stock_condition != StockCondition.BOTH_NONE:
            actual_min_stock = 1
            sql, params = _build_find_item_sql(type_config, stock_condition, seller_id, zipcode, state, site, actual_min_stock, limit)
            rows = db.query_all(sql, params)
            fallback_used = True

        if not rows:
            return {
                "success": True,
                "env": env,
                "action": "find_item",
                "data": {
                    "type": item_type,
                    "type_name": type_name,
                    "stock_condition": stock_condition,
                    "items": [],
                    "count": 0,
                    "message": "未找到符合条件的商品",
                },
                "elapsed": time.time() - start,
            }

        # 6. 格式化结果
        items = []
        for row in rows:
            item = {
                "item_number": row["item_number"],
                "goods_name": row.get("goods_name", ""),
                "goods_img": row.get("goods_img", ""),
                "unit_price": float(row.get("unit_price", 0)) if row.get("unit_price") else 0,
                "seller_id": int(row.get("seller_id", 0)) if row.get("seller_id") else 0,
                "business_type": int(row.get("business_type", 1)) if row.get("business_type") else 1,
            }
            # 添加库存信息
            if "wh1_qty" in row:
                item["wh1_qty"] = int(row["wh1_qty"]) if row["wh1_qty"] else 0
            if "wh2_qty" in row:
                item["wh2_qty"] = int(row["wh2_qty"]) if row["wh2_qty"] else 0
            if "total_qty" in row:
                item["total_qty"] = int(row["total_qty"]) if row["total_qty"] else 0
            # 添加 CRV 信息
            if "state" in row:
                item["state"] = row["state"]
            if "crv" in row:
                item["crv"] = float(row["crv"]) if row["crv"] else 0
            # 添加进口费用信息
            if "import_fee" in row:
                item["import_fee"] = float(row["import_fee"]) if row["import_fee"] else 0
            items.append(item)

        result_data = {
            "type": item_type,
            "type_name": type_name,
            "stock_condition": stock_condition,
            "seller_id": seller_id,
            "zipcode": zipcode,
            "min_stock": min_stock,
            "actual_min_stock": actual_min_stock,
            "items": items,
            "count": len(items),
        }
        if fallback_used:
            result_data["fallback"] = f"库存>={min_stock}无结果，降级为库存>=1"

        return {
            "success": True,
            "env": env,
            "action": "find_item",
            "data": result_data,
            "elapsed": time.time() - start,
        }

    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": "find_item",
            "data": {"type": item_type},
            "error": str(e),
            "elapsed": time.time() - start,
        }


def _build_find_item_sql(type_config: Dict[str, Any], stock_condition: str,
                         seller_id: Optional[int], zipcode: Optional[str],
                         state: Optional[str],
                         site: Optional[str],
                         min_stock: int, limit: int) -> Tuple[str, Optional[tuple]]:
    """
    构建查找商品的 SQL

    Args:
        type_config: 商品类型配置
        stock_condition: 库存条件
        seller_id: 商家ID
        zipcode: 邮编
        state: 州缩写（CRV商品用）
        site: 站点代码，us=美国站，ca=加拿大站，None=不过滤
        min_stock: 最小库存
        limit: 返回数量

    Returns:
        (sql, params)
    """
    params = []

    # 基础 SELECT
    select_fields = """
        i.item_number,
        g.goods_name,
        g.goods_img,
        g.shop_price as unit_price,
        i.seller_id,
        i.business_type
    """

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
    ]

    # site_code 条件（us=美国站，ca=加拿大站）
    if site:
        where_conditions.append("i.site_code = %s")
        params.append(site.lower())

    # business_type 条件（支持单值或列表）
    business_type = type_config['business_type']
    if isinstance(business_type, list):
        where_conditions.append(f"i.business_type IN ({', '.join(map(str, business_type))})")
    else:
        where_conditions.append(f"i.business_type = {business_type}")

    # item_type 条件（支持单值或列表）
    item_type = type_config['item_type']
    if isinstance(item_type, list):
        where_conditions.append(f"i.item_type IN ({', '.join(map(str, item_type))})")
    else:
        where_conditions.append(f"i.item_type = {item_type}")

    # seller_id 条件
    seller_id_config = type_config.get("seller_id")
    if seller_id_config == 0:
        # 自营：根据 site_code 选择对应 seller_id
        # US 站 seller_id=0，CA 站 seller_id=5000
        if site and site.lower() == "ca":
            where_conditions.append(f"i.seller_id = {YAMI_SELLER_ID_CA}")
        else:
            # US 站或不指定站点：查 seller_id=0（US自营）
            # 若不指定 site，也兼容查 US 自营
            where_conditions.append(f"i.seller_id = {YAMI_SELLER_ID_US}")
    elif seller_id_config == ">0":
        if seller_id:
            where_conditions.append("i.seller_id = %s")
            params.append(seller_id)
        else:
            # 第三方/FBY：seller_id > 0，但排除 CA 站自营 (5000)
            where_conditions.append(f"i.seller_id > 0 AND i.seller_id != {YAMI_SELLER_ID_CA}")
        # 第三方商品需要 seller_status = 'A'
        where_conditions.append("i.seller_status = 'A'")

    # category_id 条件（第三方礼券）
    if type_config.get("category_id"):
        where_conditions.append(f"i.category_id = {type_config['category_id']}")

    # CRV 商品条件
    group_by_extra = ""
    if type_config.get("has_crv"):
        from_clause += """
        JOIN yamibuy_im.im_item_crv crv ON i.item_number = crv.item_number AND crv.status = 1
        """
        select_fields += ", crv.state, crv.crv"
        group_by_extra = ", crv.state, crv.crv"
        # 可选：指定州
        if state:
            where_conditions.append("crv.state = %s")
            params.append(state.upper())

    # 进口费用商品条件
    if type_config.get("has_import_fee"):
        from_clause += """
        JOIN yamibuy_master.xysc_vendor_ext ve ON i.seller_id = ve.vendor_id AND ve.import_fee > 0
        """
        select_fields += ", ve.import_fee"
        group_by_extra += ", ve.import_fee"

    # share_inventory 条件
    share_config = type_config.get("share")
    if share_config is not None:
        from_clause += """
        JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
        """
        where_conditions.append(f"ie.share_inventory = {share_config}")
        # 非预售商品需要 storage_type = 0
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
        # 排除大区商品
        where_conditions.append("""
            i.item_number NOT IN (
                SELECT am2.item_number
                FROM yamibuy_im.im_item_area_mapping am2
                WHERE am2.zipcode_limit_id IN (
                    SELECT rule_id FROM yamibuy_master.xysc_shop_district_rule
                    WHERE status = 1 AND area_type = 3
                )
                GROUP BY am2.item_number
                HAVING COUNT(DISTINCT am2.zipcode_limit_id) = (
                    SELECT COUNT(*) FROM yamibuy_master.xysc_shop_district_rule
                    WHERE status = 1 AND area_type = 3
                )
            )
        """)
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

    # 库存条件
    business_type = type_config["business_type"]
    # 判断是否为第三方商品（business_type=3 或 business_type=6 且 seller_id>0）
    if isinstance(business_type, list):
        # 列表形式：检查是否包含第三方类型
        is_third_party = (3 in business_type or 6 in business_type) and seller_id_config == ">0"
    else:
        is_third_party = business_type == 3 or (business_type == 6 and seller_id_config == ">0")

    if is_third_party:
        # 第三方商品：只查总库存
        from_clause += """
        JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
        """
        select_fields += ", SUM(inv.available_qty) as total_qty"

        if stock_condition == StockCondition.BOTH_NONE:
            having_clause = "HAVING total_qty = 0"
        else:
            having_clause = f"HAVING total_qty >= {min_stock}"
    else:
        # 自营/FBY 商品：根据 site_code 判断仓库
        # US 站（site_code=us 或不指定）：查 001 和 002 仓库
        # CA 站（site_code=ca）：只查 101 仓库
        if site and site.lower() == "ca":
            # CA 站：只有 101 仓
            from_clause += """
        JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
            AND inv.warehouse_number = '101'
        """
            select_fields += """,
            SUM(CASE WHEN inv.warehouse_number = '101' THEN inv.available_qty ELSE 0 END) as wh1_qty,
            0 as wh2_qty
        """
            if stock_condition == StockCondition.BOTH_NONE:
                having_clause = "HAVING wh1_qty = 0"
            elif stock_condition in (StockCondition.BOTH_HAVE, StockCondition.WH1_ONLY):
                having_clause = f"HAVING wh1_qty >= {min_stock}"
            elif stock_condition == StockCondition.WH2_ONLY:
                # CA 站没有 wh2，wh2_only 条件永远不满足，返回空
                having_clause = "HAVING 1 = 0"
            else:
                having_clause = f"HAVING wh1_qty >= {min_stock}"
        else:
            # US 站（默认）：查 001 和 002 仓库
            from_clause += """
        JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
            AND inv.warehouse_number IN ('001', '002')
        """
            select_fields += """,
            SUM(CASE WHEN inv.warehouse_number = '001' THEN inv.available_qty ELSE 0 END) as wh1_qty,
            SUM(CASE WHEN inv.warehouse_number = '002' THEN inv.available_qty ELSE 0 END) as wh2_qty
        """

            # 根据库存条件构建 HAVING
            if stock_condition == StockCondition.BOTH_HAVE:
                having_clause = f"HAVING wh1_qty >= {min_stock} AND wh2_qty >= {min_stock}"
            elif stock_condition == StockCondition.WH1_ONLY:
                having_clause = f"HAVING wh1_qty >= {min_stock} AND wh2_qty = 0"
            elif stock_condition == StockCondition.WH2_ONLY:
                having_clause = f"HAVING wh1_qty = 0 AND wh2_qty >= {min_stock}"
            elif stock_condition == StockCondition.BOTH_NONE:
                having_clause = "HAVING wh1_qty = 0 AND wh2_qty = 0"
            else:
                having_clause = f"HAVING wh1_qty >= {min_stock} OR wh2_qty >= {min_stock}"

    # 组装 SQL
    sql = f"""
        SELECT {select_fields}
        {from_clause}
        WHERE {" AND ".join(where_conditions)}
        GROUP BY i.item_number, g.goods_name, g.goods_img, g.shop_price, i.seller_id, i.business_type{group_by_extra}
        {having_clause}
        ORDER BY RAND()
        LIMIT {limit}
    """

    return sql, tuple(params) if params else None
