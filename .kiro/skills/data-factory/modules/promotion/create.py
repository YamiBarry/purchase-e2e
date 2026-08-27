# -*- coding: utf-8 -*-
"""
创建促销活动模块
"""

import time
import json
from datetime import datetime
from typing import List, Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.mkt_api import MktApiClient
from core.types import ActionResult
from core.exceptions import (
    DataFactoryError,
    AuthError,
    PromotionCreateError,
    PromotionNotFoundError,
)
from config import VALIDATION_WAIT
from modules.promotion.constants import (
    PromotionStatus,
    PROMO_TYPE_MODE,
    PROMO_TYPE_NAME,
    CUSTOMIZE_MODES,
    CONFLICT_MSG_IDS,
)
from modules.promotion.helpers import get_goods_info_for_mkt


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


def action_create_promotion(
    client: HttpClient,
    db: DbClient,
    env: str,
    promo_type: str = "discount",
    item_numbers: Optional[List[str]] = None,
    discount_value: Optional[float] = None,
    price_ratio: float = 0.8,
    promote_prices: Optional[List[float]] = None,
    sale_goods_way: int = 1,
    ps_title: str = "renee",
    ps_sub_title: Optional[str] = None,
    hours: int = 24,
    preheat_minutes: int = 10,
    flash_qty: int = 10,
    flash_qty_la: Optional[int] = None,
    flash_qty_nj: Optional[int] = None,
    exclude_rules: Optional[List[int]] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
) -> ActionResult:
    """
    创建促销活动(直降/秒杀/礼卡专享价/会员价)
    insert -> submit, 返回 ps_id + ps_sub_title

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        promo_type: 促销类型 discount/seckill/giftcard/member 等
        item_numbers: 商品编号列表, 定制价格模式必须提供
        discount_value: 折扣值（百分比模式用）
        price_ratio: 定制价格模式下促销价 = unit_price * price_ratio, 默认 0.8
        promote_prices: 指定每个商品的促销价(按 item_numbers 顺序), 优先级高于 price_ratio
        sale_goods_way: 1=自营(默认), 2=第三方
        ps_title: 活动标题
        ps_sub_title: 活动副标题
        hours: 活动时长（小时）
        preheat_minutes: 秒杀预热时间(分钟), 默认10
        flash_qty: 秒杀库存
        flash_qty_la: LA仓秒杀库存
        flash_qty_nj: NJ仓秒杀库存
        exclude_rules: 排除的区域规则ID列表
        start_time: 开始时间戳
        end_time: 结束时间戳
    
    Returns:
        操作结果
    """
    _start = time.time()
    try:
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        mkt = MktApiClient(client, hub_token)
        now = int(time.time())
        is_flash = promo_type in ("seckill", "seckill_preheat")
        default_start = now + 720 if is_flash else now - 120
        _start_time = start_time if start_time is not None else default_start
        
        # 结束时间逻辑
        if end_time is not None:
            _end_time = end_time
        elif start_time is not None and start_time > now:
            _end_time = start_time + hours * 3600
        else:
            _end_time = now + hours * 3600

        # 促销标题
        if ps_sub_title:
            sub_title = ps_sub_title
        elif item_numbers:
            sub_title = ",".join(item_numbers)
        else:
            sub_title = f"{PROMO_TYPE_NAME.get(promo_type, '促销')}{datetime.now().strftime('%m%d')}"

        discount_mode = PROMO_TYPE_MODE.get(promo_type)
        if not discount_mode:
            raise PromotionCreateError(promo_type, f"不支持的促销类型，可选: {list(PROMO_TYPE_MODE.keys())}")

        is_customize = promo_type in CUSTOMIZE_MODES

        customize_list = []
        customize_list_local = []
        goods_list = []
        items_info = []
        
        if is_customize:
            if not item_numbers:
                raise PromotionCreateError(promo_type, "定制价格模式必须提供 --item-numbers 商品编号")
            items_info = get_goods_info_for_mkt(mkt, item_numbers)
            
            for idx, info in enumerate(items_info):
                shop_area = info.get("shop_area") or []
                fixed_price = float(promote_prices[idx]) if promote_prices and idx < len(promote_prices) else None
                
                if shop_area:
                    # 本地化商品
                    price_rules = []
                    for area in shop_area:
                        area_unit_price = float(area.get("unit_price", 0))
                        rule_id = area["rule_id"]
                        excluded = exclude_rules and rule_id in exclude_rules
                        
                        if excluded:
                            price_rules.append({
                                "rule_id": rule_id,
                                "rule_name": area.get("rule_name", ""),
                                "market_price": int(area.get("market_price", 0)),
                                "unit_price": int(area.get("unit_price", 0)),
                                "promote_price": None,
                                "join_sale": False,
                                "limit_quantity": 0,
                                "status": 2,
                            })
                        else:
                            if fixed_price is not None:
                                area_promote_price = round(fixed_price, 2)
                            else:
                                area_promote_price = round(area_unit_price * price_ratio, 2)
                            area_promote_price = max(area_promote_price, 0.01)
                            price_rules.append({
                                "rule_id": rule_id,
                                "rule_name": area.get("rule_name", ""),
                                "market_price": int(area.get("market_price", 0)),
                                "unit_price": int(area.get("unit_price", 0)),
                                "promote_price": area_promote_price,
                                "join_sale": True,
                                "limit_quantity": 0,
                                "status": 1,
                            })
                    
                    local_entry = {
                        "goods_id": info["goods_id"],
                        "sales_qty": (flash_qty_la if flash_qty_la is not None else flash_qty) if is_flash else 0,
                        "sales_qty_nj": (flash_qty_nj if flash_qty_nj is not None else flash_qty) if is_flash else 0,
                        "priceRules": price_rules,
                    }
                    customize_list_local.append(local_entry)
                else:
                    # 全国商品
                    if fixed_price is not None:
                        promote_price = round(fixed_price, 2)
                    else:
                        promote_price = round(info["unit_price"] * price_ratio, 2)
                    promote_price = max(promote_price, 0.01)
                    
                    item_entry = {
                        "goods_id": info["goods_id"],
                        "promote_price": str(promote_price),
                        "sales_qty": (flash_qty_la if flash_qty_la is not None else flash_qty) if is_flash else 0,
                        "sales_qty_nj": (flash_qty_nj if flash_qty_nj is not None else flash_qty) if is_flash else 0,
                    }
                    customize_list.append(item_entry)
                goods_list.append(info["goods_id"])
        else:
            if item_numbers:
                items_info = get_goods_info_for_mkt(mkt, item_numbers)
                for info in items_info:
                    goods_list.append(info["goods_id"])

        # 秒杀预设文案
        _flash_promo_desc = [
            {"status": 1, "desc_cn": "秒杀即将开始，准时参与别错过！", "desc_en": "Hot sale coming soon. Don't miss!", "desc_ko": "플래시 세일이 곧 시작됩니다.", "desc_ja": "フラッシュ セールがまもなく始まります。", "desc_zht": "秒殺即將開始，準時參與別錯過！"},
            {"status": 2, "desc_cn": "秒杀进行中，数量有限，先到先得！", "desc_en": "Hot selling now. Get it quickly!", "desc_ko": "플래시 세일 진행 중이며, 수량 한정, 선착순입니다!", "desc_ja": "フラッシュセール実施中、数量限定、早い者勝ちです！", "desc_zht": "秒殺進行中，數量有限，先到先得！"},
            {"status": 3, "desc_cn": "秒杀已抢光，您可尝试刷新再次获得秒杀资格。", "desc_en": "Selling stock is exhausted.", "desc_ko": "플래시 세일이 매진되었습니다.", "desc_ja": "フラッシュ セールは売り切れました。", "desc_zht": "秒殺已搶光，您可嘗試刷新再次獲得秒殺資格。"},
        ]

        ps_content = {
            "containRule": {
                "goodsList": [],
                "goodsListLocal": [],
                "itemList": [],
                "categoryList": [],
                "brandList": [],
                "mixList": [],
                "customizeList": customize_list,
                "customizeListLocal": customize_list_local,
            },
            "eliminateRule": {
                "goodsList": [],
                "itemList": [],
                "categoryList": [],
                "brandList": [],
            },
            "discountMode": discount_mode,
            "priority": 0,
            "limit_quantity": None,
            "saleGoodsWay": str(sale_goods_way) if not is_flash else sale_goods_way,
            "lstPromoDesc": _flash_promo_desc if is_flash else [],
            "batchSetPrice": False,
            "member_level": ["Gold", "Silver"],
        }

        promo_type_val = 11 if is_flash else 10

        body = {
            "ps_title": ps_title,
            "ps_group": "",
            "ps_sub_title": sub_title,
            "pre_heat_time": preheat_minutes,
            "ps_description": "",
            "start_time": _start_time,
            "end_time": _end_time,
            "type": promo_type_val,
            "status": "",
            "ps_content": ps_content,
            "ps_style": "",
            "selectedGroup": "",
            "ps_text_cn": "",
            "ps_text_en": "",
            "long_desc_translate": False,
            "link_cn": "",
            "link_en": "",
            "ps_version": "1.0",
        }

        # 1. 创建
        resp = mkt.insert_promotion(body)
        if not mkt.is_success(resp):
            raise PromotionCreateError(promo_type, mkt.get_error(resp))
        ps_id = resp.get("body")

        time.sleep(1)

        submit_msg = ""

        # 2. 提交活动
        if is_flash:
            resp2 = mkt.submit_seckill(ps_id)
        else:
            resp2 = mkt.submit_promotion(ps_id)
        
        if resp2.get("messageId") in CONFLICT_MSG_IDS:
            # 冲突错误
            conflict_items = resp2.get("body") or []
            conflict_ps_ids = list({str(item.get("ps_id")) for item in conflict_items if item.get("ps_id")})
            conflict_types = set()
            for item in conflict_items:
                dt = item.get("discount_type")
                if dt == 1:
                    conflict_types.add("直降")
                elif dt == 2:
                    conflict_types.add("秒杀")
                elif dt == 3:
                    conflict_types.add("礼卡专享价")
                elif dt == 4:
                    conflict_types.add("会员价")
                elif item.get("type") == 13:
                    conflict_types.add("秒杀")
            type_str = "/".join(conflict_types) if conflict_types else "促销"
            if conflict_ps_ids:
                submit_msg = f"商品已在{type_str}活动 {', '.join(conflict_ps_ids)} 中存在冲突，请换其他商品创建活动"
            else:
                submit_msg = f"商品与已有{type_str}活动冲突，请换其他商品创建活动"
        elif not mkt.is_success(resp2):
            # 其他错误
            error_details = []
            body_resp = resp2.get("body")
            if isinstance(body_resp, dict):
                for goods_id, detail_str in body_resp.items():
                    try:
                        detail = json.loads(detail_str) if isinstance(detail_str, str) else detail_str
                        item_num = detail.get("item_number") or goods_id
                        err_msg = detail.get("zhError") or detail.get("enError") or ""
                        if err_msg:
                            error_details.append(f"{item_num}: {err_msg}")
                    except (json.JSONDecodeError, TypeError):
                        pass
            elif isinstance(body_resp, list):
                for item in body_resp:
                    item_num = item.get("item_number") or item.get("goods_id") or ""
                    err_msg = item.get("zhError") or item.get("error_msg") or item.get("errorMsg") or ""
                    if item_num and err_msg:
                        error_details.append(f"{item_num}: {err_msg}")
                    elif err_msg:
                        error_details.append(err_msg)
            if error_details:
                submit_msg = f"{'; '.join(error_details)}，请换其他商品创建活动"
            else:
                submit_msg = f"{mkt.get_error(resp2)}，请换其他商品创建活动"

        time.sleep(VALIDATION_WAIT + 2)

        row = db.query_one(
            "SELECT ps_id, ps_sub_title, status, conflict_status FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s LIMIT 1",
            (ps_id,)
        )
        
        ok = row is not None and row.get("status") in (PromotionStatus.PENDING, PromotionStatus.ACTIVE) and row.get("conflict_status") == 0

        # 检查残留冲突
        if row and row.get("conflict_status") == 1 and not submit_msg:
            qr = mkt.query_promotion_goods(ps_id)
            conflict_ps_ids = set()
            if mkt.is_success(qr):
                for g in (qr.get("body", {}).get("data", []) if isinstance(qr.get("body"), dict) else []):
                    for gi in (g.get("goodsInfos") or []):
                        for c in (gi.get("conflictGoodsSimpleList") or []):
                            cid = c.get("conflict_ps_id")
                            if cid and cid != ps_id:
                                conflict_ps_ids.add(str(cid))
            if conflict_ps_ids:
                submit_msg = f"商品与活动 {', '.join(conflict_ps_ids)} 存在冲突，请换其他商品创建活动"
            else:
                submit_msg = "商品与已有活动存在冲突，请换其他商品创建活动"
            ok = False

        # 构建商品价格摘要
        items_summary = []
        for idx, info in enumerate(items_info if is_customize else []):
            shop_area = info.get("shop_area") or []
            fixed_price = float(promote_prices[idx]) if promote_prices and idx < len(promote_prices) else None
            if shop_area:
                if fixed_price is not None:
                    area_prices = [f"{a['rule_name']}={fixed_price}" for a in shop_area]
                    ratio_str = "指定价格"
                else:
                    area_prices = [f"{a['rule_name']}={round(float(a['unit_price'])*price_ratio,2)}" for a in shop_area]
                    ratio_str = f"{price_ratio*100:.0f}%"
                items_summary.append({
                    "item_number": info["item_number"],
                    "goods_id": info["goods_id"],
                    "类型": "本地化",
                    "区域促销价": area_prices,
                    "ratio": ratio_str,
                })
            else:
                cl = next((c for c in customize_list if c["goods_id"] == info["goods_id"]), {})
                items_summary.append({
                    "item_number": info["item_number"],
                    "goods_id": info["goods_id"],
                    "unit_price": info["unit_price"],
                    "promote_price": cl.get("promote_price", ""),
                    "ratio": "指定价格" if fixed_price is not None else f"{price_ratio*100:.0f}%",
                })

        result_data = {
            "ps_id": ps_id,
            "促销标题": sub_title,
            "促销类型": PROMO_TYPE_NAME.get(promo_type, promo_type),
            "discountMode": discount_mode,
            "sale_goods_way": "自营" if sale_goods_way == 1 else "第三方",
            "item_numbers": item_numbers or [],
            "items_promote_price": items_summary,
            "start_time": _start_time,
            "end_time": _end_time,
        }

        suggestion = (
            f"提交失败: {submit_msg}" if not ok and submit_msg else
            ("活动状态异常, 请到 central-mkt 后台查看" if not ok else "")
        )

        return {
            "success": ok,
            "env": env,
            "action": "create_promotion",
            "data": result_data,
            "validation": {
                "passed": ok,
                "checks": [
                    {"field": "ps_id", "actual": row["ps_id"] if row else None, "ok": bool(row)},
                    {"field": "status", "expected": f"{PromotionStatus.PENDING}/{PromotionStatus.ACTIVE}", "actual": row["status"] if row else None, "ok": row.get("status") in (PromotionStatus.PENDING, PromotionStatus.ACTIVE) if row else False},
                ],
                "failed_checks": [] if ok else [{"field": "status", "actual": row.get("status") if row else "not found", "ok": False}] if row else [],
                "suggestion": suggestion,
            },
            "elapsed": time.time() - _start,
        }
    except (DataFactoryError, ValueError) as e:
        return _build_error_result(env, "create_promotion", e, time.time() - _start)
    except Exception as e:
        return _build_error_result(env, "create_promotion", e, time.time() - _start)
