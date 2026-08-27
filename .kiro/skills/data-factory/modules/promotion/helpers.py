# -*- coding: utf-8 -*-
"""
促销活动辅助函数
"""

import json
from datetime import datetime
from typing import Dict, List, Any

from core.mkt_api import MktApiClient
from modules.promotion.constants import PromotionStatus


def get_goods_info_for_mkt(mkt: MktApiClient, item_numbers: List[str]) -> List[Dict[str, Any]]:
    """
    调 /mkt/im/item/queryItemInfoForMkt 批量查商品信息
    
    Args:
        mkt: MktApiClient 实例
        item_numbers: 商品编号列表
    
    Returns:
        商品信息列表，每项包含 goods_id, item_number, unit_price, goods_name, shop_area
    
    Raises:
        RuntimeError: 查询失败或商品不存在
    """
    resp = mkt.query_item_for_mkt(item_numbers)
    if not mkt.is_success(resp):
        raise RuntimeError(f"查询商品信息失败: {mkt.get_error(resp)}")
    
    body = resp.get("body") or []
    result = []
    found = {item["item_number"]: item for item in body}
    
    for item_num in item_numbers:
        if item_num not in found:
            raise RuntimeError(f"商品 {item_num} 不存在或不可用于促销")
        item = found[item_num]
        result.append({
            "goods_id": str(item["goods_id"]),
            "item_number": item["item_number"],
            "unit_price": float(item["unit_price"]),
            "goods_name": item.get("goods_ename") or item.get("goods_name", ""),
            "shop_area": item.get("shop_area") or [],
        })
    return result


def parse_promotion_detail(promo_type: str, item: Dict, config: Dict) -> Dict[str, Any]:
    """
    解析不同类型活动的详情
    
    Args:
        promo_type: 活动类型
        item: 活动数据
        config: 活动配置
    
    Returns:
        解析后的活动详情字典
    """
    # 通用字段
    result = {
        "ps_id": item.get("ps_id"),
        "活动名称": item.get("ps_sub_title") or item.get("ps_title", ""),
        "status": item.get("status"),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
    }
    
    # 时间格式化
    if result["start_time"]:
        try:
            result["开始时间"] = datetime.fromtimestamp(result["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    if result["end_time"]:
        try:
            result["结束时间"] = datetime.fromtimestamp(result["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    # 状态映射 - 优惠券状态不同：50=生效中
    if promo_type == "coupon":
        status_map = {
            PromotionStatus.DRAFT: "草稿",
            PromotionStatus.PENDING: "待生效",
            PromotionStatus.ACTIVE: "待确认",
            PromotionStatus.ENDED: "已结束",
            PromotionStatus.COUPON_ACTIVE: "生效中",
            60: "已失效"
        }
    else:
        status_map = {
            PromotionStatus.DRAFT: "草稿",
            PromotionStatus.PENDING: "待生效",
            PromotionStatus.ACTIVE: "生效中",
            PromotionStatus.ENDED: "已结束",
            PromotionStatus.INVALID: "已失效"
        }
    result["状态"] = status_map.get(item.get("status"), str(item.get("status")))

    # 赠品活动特有字段
    if promo_type == "gift":
        result["seller_id"] = item.get("seller_id")
        gift_type = item.get("gift_type", 0)
        result["赠品类型"] = "买赠" if gift_type == 0 else "满赠"
        ps_content = item.get("ps_content")
        if isinstance(ps_content, str):
            try:
                ps_content = json.loads(ps_content)
            except Exception:
                ps_content = {}
        if ps_content:
            scope_type = ps_content.get("scope_type")
            result["主商品范围"] = "全场" if scope_type == 1 else "单品"
            
            # 单品时返回主商品 item_number
            if scope_type != 1:
                contain_rule = ps_content.get("containRule", {})
                item_list = contain_rule.get("itemList", [])
                if item_list:
                    result["主商品item_number"] = item_list if len(item_list) > 1 else item_list[0]
            
            # 满赠时返回门槛条件
            if gift_type == 1:
                cal_type = ps_content.get("cal_type", 1)  # 0=按金额, 1=按数量
                if cal_type == 1:
                    num = ps_content.get("num", 1)
                    result["满赠门槛"] = f"满{num}件"
                else:
                    line = ps_content.get("line", 0)
                    result["满赠门槛"] = f"满${line}"
            
            gift_list = ps_content.get("giftList", []) or ps_content.get("lstGiftItem", [])
            if gift_list:
                gift = gift_list[0]
                gift_item_number = gift.get("item_number") or gift.get("gift_item_number")
                gift_goods_id = gift.get("goods_id") or gift.get("gift_goods_id")
                if gift_item_number:
                    result["赠品item_number"] = gift_item_number
                elif gift_goods_id:
                    result["_gift_goods_id"] = str(gift_goods_id)
                result["赠品名称"] = gift.get("goods_ename") or gift.get("goods_name", "")
                result["赠品数量"] = gift.get("gift_num", 1)

    # 优惠券特有字段
    elif promo_type == "coupon":
        ps_content = item.get("ps_content")
        if isinstance(ps_content, str):
            try:
                ps_content = json.loads(ps_content)
            except Exception:
                ps_content = {}
        ps_code = item.get("ps_code") or (ps_content.get("ps_code") if ps_content else None)
        result["兑换码"] = ps_code
        if ps_content:
            # 适用范围
            code_items_scope = ps_content.get("codeItemsScope", {})
            code_type = code_items_scope.get("code_type")
            scope_map = {1: "全场", 2: "品类", 3: "品牌", 4: "单品", "1": "全场", "2": "品类", "3": "品牌", "4": "单品"}
            result["适用范围"] = scope_map.get(code_type, "全场" if not code_type else str(code_type))
            
            coupon_content = ps_content.get("couponContent", {})
            coupon_type = coupon_content.get("coupon_type")
            if coupon_type == 1:
                result["券类型"] = "折扣券"
                result["折扣"] = f"{coupon_content.get('percent', '')}% OFF"
            elif coupon_type == 2:
                result["券类型"] = "满减券"
                result["满"] = coupon_content.get("buy_amount")
                result["减"] = coupon_content.get("reduce_amount")
            elif coupon_type == 3:
                result["券类型"] = "现金券"
                result["面额"] = coupon_content.get("cash_amount")
            result["发放数量"] = ps_content.get("coupon_amount")

    # 直降/礼卡专享价/会员价
    elif promo_type in ("discount", "giftcard", "member"):
        ps_content = item.get("ps_content")
        if isinstance(ps_content, str):
            try:
                ps_content = json.loads(ps_content)
            except Exception:
                ps_content = {}
        if ps_content:
            discount_mode = ps_content.get("discountMode")
            mode_map = {
                "1": "百分比折扣", "2": "统一减价", "3": "统一价", "4": "定制价格",
                "7": "礼卡专享价", "8": "会员价-百分比", "9": "会员价-减价", "10": "会员价-定制"
            }
            result["折扣模式"] = mode_map.get(str(discount_mode), str(discount_mode))
            contain_rule = ps_content.get("containRule", {})
            customize_list = contain_rule.get("customizeList", []) or contain_rule.get("customizeListLocal", [])
            if customize_list:
                result["参与商品数"] = len(customize_list)
                goods_ids = [str(g.get("goods_id")) for g in customize_list[:3] if g.get("goods_id")]
                if goods_ids:
                    result["_goods_ids"] = goods_ids

    # 秒杀特有字段
    elif promo_type == "seckill":
        result["预热时间(分钟)"] = item.get("pre_heat_time")
        ps_content = item.get("ps_content")
        if isinstance(ps_content, str):
            try:
                ps_content = json.loads(ps_content)
            except Exception:
                ps_content = {}
        if ps_content:
            customize_list = ps_content.get("containRule", {}).get("customizeList", [])
            if customize_list:
                result["参与商品数"] = len(customize_list)
                goods_ids = [str(g.get("goods_id")) for g in customize_list[:3] if g.get("goods_id")]
                if goods_ids:
                    result["_goods_ids"] = goods_ids
                first = customize_list[0] if customize_list else {}
                result["LA库存"] = first.get("sales_qty")
                result["NJ库存"] = first.get("sales_qty_nj")

    return result
