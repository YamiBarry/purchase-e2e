# -*- coding: utf-8 -*-
"""
动态查询各商品类型的 item_number

使用方式：
    python fetch_items.py          # 查询并更新 test_cases.py
    python fetch_items.py --dry    # 只查询，不写入文件
"""

import sys
import re
import os

# ==================== 数据库连接配置 ====================
DB_CONFIG = {
    "host": "eks-uat-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
    "port": 3306,
    "user": "yami",
    "password": "cyKP13KoxK3dtg==",
    "database": "yamibuy_master",
    "connect_timeout": 10,
}

DB_CONFIGS = {
    "UAT": DB_CONFIG,
    "GQC": {
        "host": "eks-gqc-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306, "user": "yami", "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master", "connect_timeout": 10,
    },
    "DEV": {
        "host": "eks-dev-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306, "user": "yami", "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master", "connect_timeout": 10,
    },
}
try:
    from config import ENV as _ENV
    DB_CONFIG = DB_CONFIGS.get(_ENV, DB_CONFIG)
except Exception:
    pass

# ==================== 各用例查询 SQL ====================
QUERIES = {
    "1a": {
        "name": "全国可售共享库存商品（购物车仓下单）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img,
                SUM(CASE WHEN inv.warehouse_number = '{warehouse}' THEN inv.available_qty ELSE 0 END) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number IN ('{wh_main}', '{wh_alt}')
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 1
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING SUM(CASE WHEN inv.warehouse_number = '{wh_main}' THEN inv.available_qty ELSE 0 END) > 5
               AND SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    "1c": {
        "name": "全国可售共享库存商品（购物车仓无货）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img,
                SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number IN ('{wh_main}', '{wh_alt}')
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 1
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING SUM(CASE WHEN inv.warehouse_number = '{wh_main}' THEN inv.available_qty ELSE 0 END) <= 0
               AND SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    1: {
        "name": "全国可售自营商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number = '{warehouse}'
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 0
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    2: {
        "name": "自营本地化商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number = '{warehouse}'
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            JOIN yamibuy_im.im_item_area_price_setting aps ON i.item_number = aps.item_number
            JOIN yamibuy_im.im_item_area_mapping am ON i.item_number = am.item_number
            JOIN yamibuy_master.xysc_shop_district_zipcode sdz ON am.zipcode_limit_id = sdz.rule_id AND sdz.zipcode = '{zipcode}'
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 0
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (
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
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    3: {
        "name": "自营大区商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number = '{warehouse}'
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 0
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number IN (
                  SELECT am.item_number
                  FROM yamibuy_im.im_item_area_mapping am
                  GROUP BY am.item_number
                  HAVING GROUP_CONCAT(DISTINCT am.zipcode_limit_id ORDER BY am.zipcode_limit_id) = (
                      SELECT GROUP_CONCAT(rule_id ORDER BY rule_id)
                      FROM yamibuy_master.xysc_shop_district_rule
                      WHERE status = 1 AND area_type = 3
                  )
              )
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    4: {
        "name": "自营大区共享库存商品（购物车仓下单）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img,
                SUM(CASE WHEN inv.warehouse_number = '{warehouse}' THEN inv.available_qty ELSE 0 END) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number IN ('{wh_main}', '{wh_alt}')
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 1
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number IN (
                  SELECT am.item_number
                  FROM yamibuy_im.im_item_area_mapping am
                  GROUP BY am.item_number
                  HAVING GROUP_CONCAT(DISTINCT am.zipcode_limit_id ORDER BY am.zipcode_limit_id) = (
                      SELECT GROUP_CONCAT(rule_id ORDER BY rule_id)
                      FROM yamibuy_master.xysc_shop_district_rule
                      WHERE status = 1 AND area_type = 3
                  )
              )
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING SUM(CASE WHEN inv.warehouse_number = '{wh_main}' THEN inv.available_qty ELSE 0 END) > 5
               AND SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    "4c": {
        "name": "自营大区共享库存商品（购物车仓无货）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img,
                SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number IN ('{wh_main}', '{wh_alt}')
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 1
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number IN (
                  SELECT am.item_number
                  FROM yamibuy_im.im_item_area_mapping am
                  GROUP BY am.item_number
                  HAVING GROUP_CONCAT(DISTINCT am.zipcode_limit_id ORDER BY am.zipcode_limit_id) = (
                      SELECT GROUP_CONCAT(rule_id ORDER BY rule_id)
                      FROM yamibuy_master.xysc_shop_district_rule
                      WHERE status = 1 AND area_type = 3
                  )
              )
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING SUM(CASE WHEN inv.warehouse_number = '{wh_main}' THEN inv.available_qty ELSE 0 END) <= 0
               AND SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    5: {
        "name": "自营预售全国可售商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number = '{warehouse}'
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 6 AND i.item_type = 6 AND i.status = 'A'
              AND ie.share_inventory = 0
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 0
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    "6a": {
        "name": "FBY全国可售共享库存商品（购物车仓下单）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img,
                SUM(CASE WHEN inv.warehouse_number = '{warehouse}' THEN inv.available_qty ELSE 0 END) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number IN ('{wh_main}', '{wh_alt}')
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 5 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 1
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING SUM(CASE WHEN inv.warehouse_number = '{wh_main}' THEN inv.available_qty ELSE 0 END) > 5
               AND SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    "6c": {
        "name": "FBY全国可售共享库存商品（购物车仓无货）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img,
                SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number IN ('{wh_main}', '{wh_alt}')
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 5 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 1
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING SUM(CASE WHEN inv.warehouse_number = '{wh_main}' THEN inv.available_qty ELSE 0 END) <= 0
               AND SUM(CASE WHEN inv.warehouse_number = '{wh_alt}' THEN inv.available_qty ELSE 0 END) > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    6: {
        "name": "FBY全国可售商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number = '{warehouse}'
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 5 AND i.item_type = 1 AND i.status = 'A'
              AND ie.share_inventory = 0
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 5
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
    7: {
        "name": "第三方直邮商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
            WHERE i.business_type = 3 AND i.item_type = 1 AND i.status = 'A'
              AND i.seller_id != 17
              AND i.seller_status = 'A'
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 5
            ORDER BY g.add_time DESC
            LIMIT 1
        """,
    },
    8: {
        "name": "第三方预售商品",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
            WHERE i.business_type = 6 AND i.item_type = 6 AND i.status = 'A'
              AND i.seller_id != 17 AND i.seller_id > 0
              AND i.seller_status = 'A'
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 0
            ORDER BY g.add_time DESC
            LIMIT 1
        """,
    },
    10: {
        "name": "第三方礼券商品（本地服务）",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number
            WHERE i.business_type = 3 AND i.item_type = 1 AND i.status = 'A'
              AND i.category_id = 1406
              AND i.seller_id != 17
              AND i.seller_status = 'A'
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 5
            ORDER BY g.add_time DESC
            LIMIT 1
        """,
    },
    9: {
        "name": "自营虚拟礼卡",
        "warehouse": "001",
        "sql": """
            SELECT i.item_number, g.goods_name, g.goods_img, SUM(inv.available_qty) as total_qty
            FROM yamibuy_im.im_item i
            JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
            JOIN yamibuy_inventory.inventory_transaction inv ON i.item_number = inv.item_number AND inv.warehouse_number = '{warehouse}'
            JOIN yamibuy_im.im_item_extend ie ON i.item_number = ie.item_number
            WHERE i.business_type = 1 AND i.item_type = 7 AND i.status = 'A'
              AND ie.share_inventory = 0
              AND ie.storage_type = 0
              AND g.is_on_sale = 1 AND g.is_delete = 0
              AND i.item_number NOT IN (SELECT am.item_number FROM yamibuy_im.im_item_area_mapping am)
            GROUP BY i.item_number, g.goods_name, g.goods_img
            HAVING total_qty > 0
            ORDER BY total_qty DESC
            LIMIT 1
        """,
    },
}


def query_db(sql):
    """执行 SQL 查询，返回第一行结果"""
    try:
        import mysql.connector
    except ImportError:
        print("  [ERROR] 需要安装依赖: pip install mysql-connector-python")
        return None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(sql.strip())
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception as e:
        print(f"  [ERROR] 数据库查询失败: {e}")
        return None


def fetch_all():
    """查询所有用例的 item_number，返回结果字典"""
    results = {}
    for case_id, info in QUERIES.items():
        name = info["name"]
        wh = info.get("warehouse", "001")
        wh_zip = "91789" if wh == "001" else "04001"
        wh_alt = "002" if wh == "001" else "001"
        row = query_db(info["sql"].format(warehouse=wh, zipcode=wh_zip, wh_main=wh, wh_alt=wh_alt))
        if row:
            item_number = str(row[0])
            goods_name = str(row[1])
            goods_img = str(row[2]) if len(row) > 2 and row[2] else ""
            total_qty = row[3] if len(row) > 3 else "N/A"
            results[case_id] = {
                "item_number": item_number,
                "goods_name": goods_name,
                "goods_img": goods_img,
                "total_qty": total_qty,
                "source": "db",
            }
            print(f"  OK [{case_id}] {name}: {item_number}  ({goods_name[:30]})  qty={total_qty}")
        else:
            results[case_id] = {
                "item_number": "",
                "goods_name": "",
                "goods_img": "",
                "total_qty": 0,
                "source": "no_data",
            }
            print(f"  !! [{case_id}] {name}: 查无商品数据")
    return results


def update_test_cases(results):
    """将查询结果写入 test_cases.py 的 item_number 字段"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.py")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    current_id = None
    for line in lines:
        id_match = re.search(r'"id":\s*(\w+)', line)
        if id_match:
            val = id_match.group(1)
            current_id = int(val) if val.isdigit() else val

        if current_id in results and '"item_number"' in line:
            info = results[current_id]
            item_number = info["item_number"]
            goods_name = info["goods_name"]
            total_qty = info["total_qty"]
            tag = "DB" if info["source"] == "db" else "no_data"
            new_line = re.sub(
                r'("item_number":\s*")[^"]+(",\s*).*',
                rf'\g<1>{item_number}\g<2># {tag}: {goods_name}, qty={total_qty}',
                line
            )
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"\n  test_cases.py 已更新: {path}")


if __name__ == "__main__":
    dry_run = "--dry" in sys.argv

    try:
        from config import ENV as _DISPLAY_ENV
    except Exception:
        _DISPLAY_ENV = "DB"

    print("=" * 55)
    print(f"  亚米冒烟下单 - 动态查询商品 item_number（{_DISPLAY_ENV}）")
    print("=" * 55)

    results = fetch_all()

    if not dry_run:
        update_test_cases(results)
    else:
        print("\n  [dry-run] 不写入文件")

    print("\n  汇总：")
    for case_id in sorted(results.keys(), key=lambda x: str(x)):
        info = results[case_id]
        tag = "DB" if info["source"] == "db" else "no_data"
        print(f"    [{case_id}] {info['item_number']}  [{tag}]  {info['goods_name']}")
