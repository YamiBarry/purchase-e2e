# -*- coding: utf-8 -*-
"""
促销相关 Action Handlers
"""

import sys
from handlers.base import require_param


# action 名称 -> promo_type 映射
_ACTION_TO_PROMO_TYPE = {
    "create_promotion": "discount",
    "create_seckill": "seckill",
    "create_member_price": "member_price",
    "create_giftcard_price": "giftcard",
}


# ==================== 公共参数解析工具 ====================

def _parse_float(value, default=None):
    """安全解析浮点数"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_int(value, default=None):
    """安全解析整数"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _get_item_numbers(args):
    """从 args 中提取商品编号列表"""
    if args.item_numbers:
        return args.item_numbers
    if args.item_number:
        return [args.item_number]
    return None


# ==================== Handlers ====================


# ==================== Handlers ====================

def handle_create_promotion(client, db, env, args, email):
    """创建促销活动（通用）"""
    from modules.promotion import action_create_promotion
    promo_type = args.promo_type or _ACTION_TO_PROMO_TYPE.get(args.action, "discount")
    return action_create_promotion(
        client, db, env,
        promo_type=promo_type,
        item_numbers=_get_item_numbers(args),
        discount_value=_parse_float(args.discount_value),
        price_ratio=_parse_float(args.price_ratio, 0.8),
        promote_prices=args.promote_prices,
        sale_goods_way=_parse_int(args.sale_goods_way, 1),
        ps_title=args.ps_title or "renee",
        ps_sub_title=args.ps_sub_title,
        hours=args.hours or 24,
        preheat_minutes=args.preheat_minutes or 10,
        flash_qty=args.flash_qty or 10,
        flash_qty_la=args.flash_qty_la,
        flash_qty_nj=args.flash_qty_nj,
        exclude_rules=args.exclude_rules or [],
        start_time=args.start_time,
        end_time=args.end_time,
    )


def handle_finish_promotion(client, db, env, args, email):
    """结束促销活动"""
    from modules.promotion import action_finish_promotion
    require_param(args.ps_id, "--ps-id")
    return action_finish_promotion(client, db, env, int(args.ps_id))


def handle_create_gift_promotion(client, db, env, args, email):
    """创建赠品活动"""
    from modules.promotion import action_create_gift_promotion
    return action_create_gift_promotion(
        client, db, env,
        seller_id=args.seller_id,
        item_id=args.item_number,
        gift_item_id=args.gift_item,
        ps_sub_title=args.ps_sub_title,
        gift_type=_parse_int(args.gift_type, 0),
        cal_type=_parse_int(args.cal_type, 1),
        num=_parse_int(args.gift_threshold_num, 1),
        line=_parse_float(args.gift_threshold_line, 10.0),
        overlap=_parse_int(args.gift_overlap, 1),
        start_time=args.start_time,
        end_time=args.end_time,
        gift_num=_parse_int(args.gift_num, 1),
        la_qty=_parse_int(args.gift_la_qty, 20),
        nj_qty=_parse_int(args.gift_nj_qty, 20),
    )


def handle_finish_gift_promotion(client, db, env, args, email):
    """结束赠品活动"""
    from modules.promotion import action_finish_gift_promotion
    require_param(args.ps_id, "--ps-id")
    return action_finish_gift_promotion(client, db, env, int(args.ps_id))


def handle_find_promotion(client, db, env, args, email):
    """查找促销活动"""
    from modules.promotion import action_find_promotion
    require_param(args.promo_type, "--promo-type，可选: gift/coupon/discount/seckill/giftcard/member")
    return action_find_promotion(
        client, db, env,
        promo_type=args.promo_type,
        seller_id=args.seller_id,
        status=args.promo_status or 30,
        limit=args.promo_limit if hasattr(args, 'promo_limit') else 1,
    )


def handle_create_coupon(client, db, env, args, email):
    """创建优惠券"""
    from modules.promotion import action_create_coupon
    return action_create_coupon(
        client, db, env,
        coupon_code=args.coupon_code,
        coupon_type=args.coupon_type,
        coupon_form=args.coupon_form_type,
        send_type=args.send_type,
        discount=_parse_float(args.discount, 10),
        buy_amount=_parse_float(args.buy_amount),
        reduce_amount=_parse_float(args.reduce_amount),
        cash_amount=_parse_float(args.cash_amount),
        coupon_amount=args.coupon_amount or 1000,
        hours=args.hours or 24,
        relative=args.relative,
        seller_id=args.seller_id or 0,
        scope=args.scope or "all",
        scope_ids=args.scope_ids or [],
        limit_user=args.limit_user or "all",
        send_channel=args.send_channel or 0,
        shipping_group_type=args.shipping_group_type or 1,
        shipping_id=args.shipping_id,
    )


# Handler 注册表
PROMOTION_HANDLERS = {
    "create_promotion": handle_create_promotion,
    "create_seckill": handle_create_promotion,
    "create_member_price": handle_create_promotion,
    "create_giftcard_price": handle_create_promotion,
    "finish_promotion": handle_finish_promotion,
    "create_gift_promotion": handle_create_gift_promotion,
    "finish_gift_promotion": handle_finish_gift_promotion,
    "find_promotion": handle_find_promotion,
    "create_coupon": handle_create_coupon,
}
