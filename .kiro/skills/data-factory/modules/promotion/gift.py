# -*- coding: utf-8 -*-
"""
赠品活动模块

支持: 创建赠品活动（买赠/满赠）, 结束赠品活动

gift_type: 0=买赠, 1=满赠
cal_type: 满赠计算方式 0=按金额, 1=按数量
overlap: 0=不可叠加, 1=可叠加
"""

import time
import json
from typing import Any, Dict, Optional, Tuple, List
from dataclasses import dataclass

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.mkt_api import MktApiClient
from core.types import ActionResult
from core.exceptions import AuthError, PromotionCreateError, PromotionNotFoundError, ItemNotFoundError
from core.utils import build_error_result
from core.constants import is_yami_seller, YAMI_SELLER_ID_US, YAMI_SELLER_ID_CA
from config import VALIDATION_WAIT


# ─────────────────────────────────────────────────────────────────────────────
# 数据类定义
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GiftCreationContext:
    """赠品活动创建上下文，封装创建过程中的中间状态"""
    # 输入参数
    seller_id: Optional[int]
    item_id: Optional[str]
    gift_item_id: Optional[str]
    gift_type: int
    cal_type: int
    num: int
    line: float
    overlap: int
    gift_num: int
    la_qty: int
    nj_qty: int
    start_time: Optional[int]
    end_time: Optional[int]
    ps_sub_title: Optional[str]
    
    # 计算结果
    by_item: bool = False
    actual_seller_id: int = 0
    actual_business_type: int = 1
    code_type: str = "1"
    item_list: List[str] = None
    main_item_info: Dict[str, Any] = None
    gift_item_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.item_list is None:
            self.item_list = []


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _get_item_info_for_gift(db: DbClient, item_number: str) -> Dict[str, Any]:
    """
    从数据库查询商品信息用于赠品活动
    
    Args:
        db: 数据库客户端
        item_number: 商品编号
    
    Returns:
        商品信息字典 {item_number, goods_id, seller_id, business_type, goods_name}
    
    Raises:
        ItemNotFoundError: 商品不存在或已下架
    """
    row = db.query_one(
        """SELECT i.goods_id, i.item_number, i.seller_id, i.business_type,
                  COALESCE(g.goods_ename, g.goods_name, '') as goods_name
           FROM yamibuy_im.im_item i
           LEFT JOIN yamibuy_master.xysc_goods g ON i.goods_id = g.goods_id
           WHERE i.item_number = %s AND i.status = 'A' LIMIT 1""",
        (item_number,)
    )
    if not row:
        raise ItemNotFoundError(item_number)
    
    return {
        "item_number": row["item_number"],
        "goods_id": row["goods_id"],
        "seller_id": row["seller_id"] or 0,
        "business_type": row["business_type"] or 1,
        "goods_name": row["goods_name"] or "",
    }


def _get_inventory_available_qty(db: DbClient, item_number: str, warehouse: str) -> int:
    """
    查询商品在指定仓库的可用库存
    
    Args:
        db: 数据库客户端
        item_number: 商品编号
        warehouse: 仓库代码 'LA' 或 'NJ'
    
    Returns:
        可用库存数量，不存在时返回 0
    """
    warehouse_map: Dict[str, str] = {"LA": "001", "NJ": "002"}
    warehouse_number = warehouse_map.get(warehouse, warehouse)
    
    row = db.query_one(
        """SELECT available_qty FROM yamibuy_inventory.inventory_transaction 
           WHERE item_number = %s AND warehouse_number = %s LIMIT 1""",
        (item_number, warehouse_number)
    )
    return row["available_qty"] if row else 0


def _get_seller_info(db: DbClient, seller_id: int) -> Dict[str, Any]:
    """
    查询商家信息，判断是自营还是第三方
    
    Args:
        db: 数据库客户端
        seller_id: 商家 ID
    
    Returns:
        商家信息字典 {seller_id, is_yami, business_type}
    
    Raises:
        ItemNotFoundError: 商家不存在
    """
    if is_yami_seller(seller_id):
        return {"seller_id": seller_id, "is_yami": True, "business_type": 1}
    row = db.query_one(
        "SELECT vendor_id, business_type FROM yamibuy_master.xysc_vendor_info WHERE vendor_id = %s LIMIT 1",
        (seller_id,)
    )
    if not row:
        raise ItemNotFoundError(f"seller_{seller_id}")
    return {
        "seller_id": seller_id,
        "is_yami": row["business_type"] == 1,
        "business_type": row["business_type"],
    }


def _find_item_for_gift(db: DbClient, seller_id: Optional[int] = None) -> str:
    """
    查找一个可售商品用于赠品活动
    
    Args:
        db: 数据库客户端
        seller_id: 商家ID，None 或 0 表示查找自营商品
    
    Returns:
        商品编号 item_number
    
    Raises:
        ItemNotFoundError: 未找到符合条件的商品
    """
    if seller_id is None or seller_id == YAMI_SELLER_ID_US:
        # US 站自营全国可售商品（seller_id=0，仓库 001+002）
        sql = """
            SELECT i.item_number
            FROM yamibuy_inventory.inventory_transaction it1
            INNER JOIN yamibuy_inventory.inventory_transaction it2 
                ON it1.item_number = it2.item_number
            INNER JOIN yamibuy_im.im_item i 
                ON i.item_number = it1.item_number
            WHERE it1.warehouse_number = '001' 
              AND it1.available_qty >= 5
              AND it2.warehouse_number = '002' 
              AND it2.available_qty >= 5
              AND i.business_type = 1 
              AND i.seller_id = 0
              AND i.site_code = 'us'
              AND i.status = 'A'
            LIMIT 1
        """
        row = db.query_one(sql, ())
        if not row:
            raise ItemNotFoundError("自营全国可售商品（两仓库存>=5）")
    else:
        # 指定商家的商品
        biz_sql = """
            SELECT DISTINCT business_type 
            FROM yamibuy_im.im_item 
            WHERE seller_id = %s AND status = 'A' 
            LIMIT 1
        """
        biz_row = db.query_one(biz_sql, (seller_id,))
        if not biz_row:
            raise ItemNotFoundError(f"seller_{seller_id}_items")
        
        business_type = biz_row["business_type"]
        
        if business_type in (3, 6):
            # 第三方直邮(3)或第三方预售(6)
            warehouse_number = f"9000{seller_id}"
            sql = """
                SELECT i.item_number
                FROM yamibuy_inventory.inventory_transaction it
                INNER JOIN yamibuy_im.im_item i 
                    ON i.item_number = it.item_number
                WHERE it.warehouse_number = %s 
                  AND it.available_qty >= 5
                  AND i.seller_id = %s 
                  AND i.status = 'A'
                LIMIT 1
            """
            row = db.query_one(sql, (warehouse_number, seller_id))
        else:
            # FBY(5) 或其他
            sql = """
                SELECT i.item_number
                FROM yamibuy_inventory.inventory_transaction it1
                INNER JOIN yamibuy_inventory.inventory_transaction it2 
                    ON it1.item_number = it2.item_number
                INNER JOIN yamibuy_im.im_item i 
                    ON i.item_number = it1.item_number
                WHERE it1.warehouse_number = '001' 
                  AND it1.available_qty >= 5
                  AND it2.warehouse_number = '002' 
                  AND it2.available_qty >= 5
                  AND i.seller_id = %s 
                  AND i.status = 'A'
                LIMIT 1
            """
            row = db.query_one(sql, (seller_id,))
        
        if not row:
            raise ItemNotFoundError(f"seller_{seller_id}_items（库存>=5）")
    
    return row["item_number"]


# ─────────────────────────────────────────────────────────────────────────────
# 创建赠品活动 - 拆分后的子函数
# ─────────────────────────────────────────────────────────────────────────────

def _determine_creation_mode(ctx: GiftCreationContext, db: DbClient) -> None:
    """
    确定创建模式：按商品还是按商家
    
    根据用户指定的参数组合，确定活动的创建模式，并自动查找缺失的商品。
    
    Args:
        ctx: 创建上下文（会被修改）
        db: 数据库客户端
    
    场景说明：
    1. 什么都没指定 → 自动查找自营全国可售商品作为主品和赠品（单品参与）
    2. 指定商家+赠品 → 该商家全场参与，赠品用指定的
    3. 指定商品+赠品 → 该商品参与，赠品用指定的
    4. 只指定商品 → 该商品参与，赠品也用这个商品
    5. 只指定商家 → 该商家全场参与，自动查找该商家的商品作为赠品
    """
    has_seller = ctx.seller_id is not None
    has_item = ctx.item_id is not None
    has_gift = ctx.gift_item_id is not None
    
    if not has_seller and not has_item and not has_gift:
        # 场景1: 什么都没指定
        auto_item = _find_item_for_gift(db, None)
        ctx.item_id = auto_item
        ctx.gift_item_id = auto_item
        ctx.by_item = True
    elif has_seller and has_gift and not has_item:
        # 场景2: 指定商家+赠品
        ctx.by_item = False
    elif has_item and has_gift:
        # 场景3: 指定商品+赠品
        ctx.by_item = True
    elif has_item and not has_gift:
        # 场景4: 只指定商品
        ctx.gift_item_id = ctx.item_id
        ctx.by_item = True
    elif has_seller and not has_gift and not has_item:
        # 场景5: 只指定商家
        auto_item = _find_item_for_gift(db, ctx.seller_id)
        ctx.gift_item_id = auto_item
        ctx.by_item = False
    else:
        ctx.by_item = has_item


def _resolve_item_info(ctx: GiftCreationContext, db: DbClient) -> None:
    """
    解析商品信息
    
    根据创建模式获取主商品和赠品的详细信息。
    
    Args:
        ctx: 创建上下文（会被修改）
        db: 数据库客户端
    """
    if ctx.by_item:
        # 按商品创建
        ctx.main_item_info = _get_item_info_for_gift(db, ctx.item_id)
        ctx.actual_seller_id = ctx.main_item_info["seller_id"]
        ctx.actual_business_type = ctx.main_item_info["business_type"]
        
        if ctx.gift_item_id and ctx.gift_item_id != ctx.item_id:
            ctx.gift_item_info = _get_item_info_for_gift(db, ctx.gift_item_id)
        else:
            ctx.gift_item_info = ctx.main_item_info
            ctx.gift_item_id = ctx.item_id
        
        ctx.code_type = "4"  # 单品参与
        ctx.item_list = [ctx.item_id]
    else:
        # 按商家创建（全场参与）
        ctx.actual_seller_id = ctx.seller_id
        ctx.gift_item_info = _get_item_info_for_gift(db, ctx.gift_item_id)
        ctx.actual_business_type = ctx.gift_item_info["business_type"]
        ctx.code_type = "1"  # 全场参与
        ctx.item_list = []


def _calculate_time_range(ctx: GiftCreationContext) -> Tuple[int, int]:
    """
    计算活动时间范围
    
    Args:
        ctx: 创建上下文
    
    Returns:
        (start_time, end_time) 时间戳元组
    """
    now = int(time.time())
    
    if ctx.start_time is None:
        _start_time = now - 5 * 60  # 默认：当前时间前5分钟
    else:
        _start_time = ctx.start_time
    
    if ctx.end_time is None:
        if ctx.start_time is None:
            _end_time = now + 24 * 3600  # 默认：当前时间后24小时
        elif _start_time < now:
            _end_time = now + 24 * 3600
        else:
            _end_time = _start_time + 24 * 3600
    else:
        _end_time = ctx.end_time
    
    return _start_time, _end_time


def _calculate_inventory(ctx: GiftCreationContext, db: DbClient) -> Dict[str, int]:
    """
    计算赠品库存
    
    根据赠品的业务类型，计算各仓库的实际可用库存。
    
    Args:
        ctx: 创建上下文
        db: 数据库客户端
    
    Returns:
        库存信息字典 {
            actual_la_qty, actual_nj_qty, actual_all_qty,
            max_la_qty, max_nj_qty, max_all_qty
        }
    """
    gift_item_number = ctx.gift_item_info["item_number"]
    gift_business_type = ctx.gift_item_info["business_type"]
    gift_seller_id = ctx.gift_item_info["seller_id"]
    
    # 用户期望设置的库存数量
    expected_la_qty = ctx.la_qty
    expected_nj_qty = ctx.nj_qty
    expected_total_qty = expected_la_qty + expected_nj_qty
    
    if gift_business_type in (3, 6):
        # 第三方直邮(3)或第三方预售(6)：使用商家仓库
        warehouse_number = f"9000{gift_seller_id}"
        row = db.query_one(
            """SELECT available_qty FROM yamibuy_inventory.inventory_transaction 
               WHERE item_number = %s AND warehouse_number = %s LIMIT 1""",
            (gift_item_number, warehouse_number)
        )
        available_total_qty = row["available_qty"] if row else 0
        
        return {
            "actual_la_qty": 0,
            "actual_nj_qty": 0,
            "actual_all_qty": min(expected_total_qty, available_total_qty) if available_total_qty > 0 else 0,
            "max_la_qty": 0,
            "max_nj_qty": 0,
            "max_all_qty": available_total_qty,
        }
    else:
        # 自营(1)或FBY(5)：使用 LA/NJ 仓库
        max_la_qty = _get_inventory_available_qty(db, gift_item_number, "LA")
        max_nj_qty = _get_inventory_available_qty(db, gift_item_number, "NJ")
        
        return {
            "actual_la_qty": min(expected_la_qty, max_la_qty),
            "actual_nj_qty": min(expected_nj_qty, max_nj_qty),
            "actual_all_qty": 0,
            "max_la_qty": max_la_qty,
            "max_nj_qty": max_nj_qty,
            "max_all_qty": max_la_qty + max_nj_qty,
        }


def _build_ps_content(ctx: GiftCreationContext, inventory: Dict[str, int]) -> Dict[str, Any]:
    """
    构建活动内容 ps_content
    
    Args:
        ctx: 创建上下文
        inventory: 库存信息
    
    Returns:
        ps_content 字典
    """
    ps_content = {
        "gift_type": ctx.gift_type,
        "cal_type": ctx.cal_type,
        "overlap": str(ctx.overlap),
        "seller_id": ctx.actual_seller_id,
        "business_type": ctx.actual_business_type,
        "businessTypeList": [],
        "auto_qty_assign": "0",
        "lstGiftItem": [{
            "gift_item_number": "",
            "origin_item_number": ctx.gift_item_info["item_number"],
            "gift_num": ctx.gift_num,
            "all_qty": inventory["actual_all_qty"],
            "la_qty": inventory["actual_la_qty"],
            "nj_qty": inventory["actual_nj_qty"],
            "max_all_qty": inventory["max_all_qty"],
            "max_la_qty": inventory["max_la_qty"],
            "max_nj_qty": inventory["max_nj_qty"],
            "la_nj_qty_error": False,
            "allqty_error": False,
            "num_qty_error": False,
            "goods_name": ctx.gift_item_info["goods_name"],
        }],
        "codeItemsScope": {
            "code_type": ctx.code_type,
            "goodsAmount": 0,
            "total_sku_num": 0,
            "containRule": {
                "goodsList": [],
                "itemList": ctx.item_list,
                "categoryList": [],
                "brandList": [],
                "excelData": [],
                "excelErrorData": [],
                "excel_url": "",
                "excel_total_row": 0,
                "excel_name": "",
                "excel_valid_row": 0,
            },
            "eliminateRule": {
                "goodsList": [],
                "itemList": [],
                "categoryList": [],
                "brandList": [],
            },
        },
        "set_auto_qty": False,
    }
    
    # 满赠时添加门槛参数
    if ctx.gift_type == 1:
        ps_content["num"] = ctx.num if ctx.cal_type == 1 else None
        ps_content["line"] = ctx.line if ctx.cal_type == 0 else None
    
    return ps_content


def _generate_title(ctx: GiftCreationContext) -> str:
    """
    生成活动名称
    
    Args:
        ctx: 创建上下文
    
    Returns:
        活动名称
    """
    if ctx.ps_sub_title:
        return ctx.ps_sub_title
    
    if ctx.by_item:
        return f"{ctx.item_id}【{ctx.gift_item_info['item_number']}】"
    else:
        return f"test{ctx.seller_id}"


# ─────────────────────────────────────────────────────────────────────────────
# 创建赠品活动 - 主函数
# ─────────────────────────────────────────────────────────────────────────────

def action_create_gift_promotion(
    client: HttpClient,
    db: DbClient,
    env: str,
    seller_id: Optional[int] = None,
    item_id: Optional[str] = None,
    gift_item_id: Optional[str] = None,
    ps_sub_title: Optional[str] = None,
    gift_type: int = 0,
    cal_type: int = 1,
    num: int = 1,
    line: float = 10.0,
    overlap: int = 1,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    gift_num: int = 1,
    la_qty: int = 20,
    nj_qty: int = 20,
) -> ActionResult:
    """
    创建赠品活动
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        seller_id: 商家号（按商家建全场活动时指定）
        item_id: 主商品 item_number（按商品建时指定）
        gift_item_id: 赠品 item_number（不填时使用主商品）
        ps_sub_title: 活动名称（不填时自动生成）
        gift_type: 0=买赠, 1=满赠
        cal_type: 满赠计算方式 0=按金额, 1=按数量
        num: 满赠数量门槛（默认1）
        line: 满赠金额门槛（默认10）
        overlap: 0=不可叠加, 1=可叠加（默认1）
        start_time: 开始时间戳（默认当前-5分钟）
        end_time: 结束时间戳（默认开始+24小时）
        gift_num: 赠品数量（默认1）
        la_qty: LA仓库存（默认20，超过实际库存时使用实际值）
        nj_qty: NJ仓库存（默认20，超过实际库存时使用实际值）
    
    Returns:
        操作结果
    """
    _start = time.time()
    try:
        # 1. 获取 Hub token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")
        
        mkt = MktApiClient(client, hub_token)
        
        # 2. 创建上下文并确定创建模式
        ctx = GiftCreationContext(
            seller_id=seller_id, item_id=item_id, gift_item_id=gift_item_id,
            gift_type=gift_type, cal_type=cal_type, num=num, line=line,
            overlap=overlap, gift_num=gift_num, la_qty=la_qty, nj_qty=nj_qty,
            start_time=start_time, end_time=end_time, ps_sub_title=ps_sub_title,
        )
        _determine_creation_mode(ctx, db)
        
        # 3. 解析商品信息
        _resolve_item_info(ctx, db)
        
        # 4. 生成活动名称
        title = _generate_title(ctx)
        
        # 5. 计算时间范围
        _start_time, _end_time = _calculate_time_range(ctx)
        
        # 6. 计算库存
        inventory = _calculate_inventory(ctx, db)
        
        # 7. 构建 ps_content
        ps_content = _build_ps_content(ctx, inventory)
        
        # 8. 构建请求体
        payload = {
            "ps_sub_title": title,
            "ps_title": "",
            "seller_id": ctx.actual_seller_id,
            "type": 20,
            "start_time": _start_time,
            "end_time": _end_time,
            "ps_version": "1.0",
            "ps_content": json.dumps(ps_content),
            "status": None,
            "in_dtm": None,
            "in_user": "",
            "exGoodsList": [],
            "goodsList": ctx.item_list,
            "defaultScope": ctx.code_type,
            "PSContent": ps_content,
        }
        
        # 9. 创建活动
        resp = mkt.insert_gift_promotion(payload)
        if not mkt.is_success(resp):
            raise PromotionCreateError("赠品活动", mkt.get_error(resp))
        
        ps_id = resp.get("body")
        if not ps_id:
            raise PromotionCreateError("赠品活动", f"未返回 ps_id, resp={resp}")
        
        # 10. 提交活动
        submit_ok, submit_error = _submit_gift_promotion(mkt, ps_id)
        
        # 11. 验证结果
        time.sleep(VALIDATION_WAIT + 3)
        row = db.query_one(
            "SELECT ps_id, ps_sub_title, status, start_time, end_time FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s LIMIT 1",
            (ps_id,)
        )
        
        ok = row is not None and row.get("status") in (20, 30)
        
        # 12. 构建返回结果
        return _build_gift_result(
            ok, env, ps_id, title, ctx, inventory, _start_time, _end_time,
            row, submit_ok, submit_error, time.time() - _start
        )
        
    except Exception as e:
        return build_error_result(env, "create_gift_promotion", e, time.time() - _start)


def _submit_gift_promotion(mkt: MktApiClient, ps_id: int) -> Tuple[bool, str]:
    """
    提交赠品活动
    
    Args:
        mkt: MKT API 客户端
        ps_id: 活动 ID
    
    Returns:
        (submit_ok, submit_error) 提交结果
    """
    submit_ok = False
    submit_error = ""
    
    try:
        submit_resp = mkt.submit_gift_promotion(ps_id, step=1)
        submit_ok = mkt.is_success(submit_resp)
        submit_error = mkt.get_error(submit_resp) if not submit_ok else ""
    except Exception as e:
        submit_error = f"提交请求超时: {str(e)[:50]}"
    
    # 如果有重叠冲突，自动确认提交
    if not submit_ok and "重叠" in submit_error:
        try:
            confirm_resp = mkt.submit_gift_promotion(ps_id, step=2)
            submit_ok = mkt.is_success(confirm_resp)
            submit_error = mkt.get_error(confirm_resp) if not submit_ok else "(已确认提交)"
        except Exception as e:
            submit_error = f"确认提交超时: {str(e)[:50]}"
    
    return submit_ok, submit_error


def _build_gift_result(
    ok: bool, env: str, ps_id: int, title: str,
    ctx: GiftCreationContext, inventory: Dict[str, int],
    start_time: int, end_time: int,
    row: Optional[Dict], submit_ok: bool, submit_error: str,
    elapsed: float
) -> ActionResult:
    """
    构建赠品活动创建结果
    
    Args:
        ok: 是否成功
        env: 环境
        ps_id: 活动 ID
        title: 活动名称
        ctx: 创建上下文
        inventory: 库存信息
        start_time: 开始时间
        end_time: 结束时间
        row: 数据库查询结果
        submit_ok: 提交是否成功
        submit_error: 提交错误信息
        elapsed: 耗时
    
    Returns:
        ActionResult
    """
    result_data = {
        "ps_id": ps_id,
        "活动名称": title,
        "赠品类型": "买赠" if ctx.gift_type == 0 else "满赠",
        "叠加规则": "可叠加" if ctx.overlap == 1 else "不可叠加",
        "seller_id": ctx.actual_seller_id,
        "business_type": ctx.actual_business_type,
        "主商品范围": "全场" if ctx.code_type == "1" else "单品",
        "主商品": ctx.item_list if ctx.item_list else "全场",
        "赠品": ctx.gift_item_info["item_number"],
        "赠品名称": ctx.gift_item_info["goods_name"],
        "赠品数量": ctx.gift_num,
        "LA库存": inventory["actual_la_qty"] if inventory["actual_la_qty"] > 0 else "-",
        "NJ库存": inventory["actual_nj_qty"] if inventory["actual_nj_qty"] > 0 else "-",
        "总库存": inventory["actual_all_qty"] if inventory["actual_all_qty"] > 0 else "-",
        "start_time": start_time,
        "end_time": end_time,
        "status": row["status"] if row else None,
    }
    
    if ctx.gift_type == 1:
        result_data["满赠门槛"] = f"{ctx.num}件" if ctx.cal_type == 1 else f"${ctx.line}"
    
    suggestion = ""
    if not submit_ok and submit_error:
        suggestion = f"提交失败: {submit_error}"
    elif not ok:
        suggestion = "活动状态异常, 请到 central-mkt 后台查看"
    
    return {
        "success": ok,
        "env": env,
        "action": "create_gift_promotion",
        "data": result_data,
        "validation": {
            "passed": ok,
            "checks": [
                {"field": "ps_id", "actual": row["ps_id"] if row else None, "ok": bool(row)},
                {"field": "status", "expected": "20/30", "actual": row["status"] if row else None, "ok": row.get("status") in (20, 30) if row else False},
            ],
            "failed_checks": [] if ok else [{"field": "status", "actual": row.get("status") if row else "not found", "ok": False}] if row else [],
            "suggestion": suggestion,
        },
        "elapsed": elapsed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 结束赠品活动
# ─────────────────────────────────────────────────────────────────────────────

def action_finish_gift_promotion(
    client: HttpClient,
    db: DbClient,
    env: str,
    ps_id: int,
) -> ActionResult:
    """
    结束赠品活动
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        ps_id: 活动 ID
    
    Returns:
        操作结果
    
    活动状态: 10=草稿, 20=待生效, 30=生效中, 40=已结束
    """
    _start = time.time()
    try:
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        mkt = MktApiClient(client, hub_token)

        # 先查询活动信息
        row_before = db.query_one(
            "SELECT ps_id, ps_sub_title, status, type FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s LIMIT 1",
            (ps_id,)
        )
        if not row_before:
            raise PromotionNotFoundError(str(ps_id))
        
        # 检查是否是赠品活动 (type=20)
        if row_before.get("type") != 20:
            raise PromotionNotFoundError(str(ps_id), by=f"type={row_before.get('type')}，赠品活动 type=20")
        
        # 检查活动状态
        status_before = row_before.get("status")
        if status_before == 40:
            return {
                "success": True,
                "env": env,
                "action": "finish_gift_promotion",
                "data": {
                    "ps_id": ps_id,
                    "活动名称": row_before["ps_sub_title"],
                    "status": 40,
                    "说明": "活动已经是结束状态",
                },
                "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
                "elapsed": time.time() - _start,
            }
        
        if status_before == 10:
            raise PromotionNotFoundError(str(ps_id), by="status=10 草稿状态，请先提交活动")

        # 调用结束接口
        resp = mkt.finish_gift_promotion(ps_id)

        if not mkt.is_success(resp):
            raise PromotionCreateError("结束赠品活动", mkt.get_error(resp))

        # 验证
        time.sleep(VALIDATION_WAIT)
        row = db.query_one(
            "SELECT ps_id, ps_sub_title, status FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s LIMIT 1",
            (ps_id,)
        )
        ok = row is not None and row.get("status") == 40

        return {
            "success": ok,
            "env": env,
            "action": "finish_gift_promotion",
            "data": {
                "ps_id": ps_id,
                "活动名称": row["ps_sub_title"] if row else "",
                "status_before": status_before,
                "status": row["status"] if row else None,
            },
            "validation": {
                "passed": ok,
                "checks": [{"field": "status", "expected": 40, "actual": row["status"] if row else None, "ok": ok}],
                "failed_checks": [] if ok else [{"field": "status", "actual": row.get("status") if row else "not found", "ok": False}],
                "suggestion": "" if ok else "活动未结束, 请检查 central-mkt 后台",
            },
            "elapsed": time.time() - _start,
        }
    except Exception as e:
        return build_error_result(env, "finish_gift_promotion", e, time.time() - _start)
