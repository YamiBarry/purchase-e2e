# -*- coding: utf-8 -*-
"""
订单相关 Action Handlers
"""

import sys
from handlers.base import (
    parse_order_ids, parse_order_sns, 
    require_order_identifier, login_user
)
from output import print_results


def handle_place_order(client, db, env, args, email):
    """下单"""
    from modules.order_place import action_place_order
    login_user(client, email, args.pwd)
    
    wh_number = "001"
    zipcode_override = None
    if args.wh:
        parts = str(args.wh).split(":")
        wh_number = "001" if parts[0] == "1" else "002"
        if len(parts) > 1:
            zipcode_override = parts[1]
    
    results = action_place_order(
        client, db, env,
        email=email,
        case_id=int(args.case) if args.case and str(args.case).isdigit() else (args.case or 1),
        wh_number=wh_number,
        zipcode_override=zipcode_override,
        use_giftcard=args.use_giftcard,
        use_points=args.use_points,
        coupon_code=args.coupon_code,
        item_numbers=args.item_numbers or ([args.item_number] if args.item_number else None),
        qty=args.qty if hasattr(args, "qty") and args.qty else 1,
        count=args.count or 1,
    )
    print_results(results)
    return None  # 已打印，返回 None 跳过外层打印


def handle_fp_verify(client, db, env, args, email):
    """FP 审核"""
    from modules.order_process import action_fp_verify, resolve_order_ids
    order_ids, order_sns = require_order_identifier(args)
    is_recent_mode = not order_ids and not order_sns
    target_orders = resolve_order_ids(
        db, order_ids, order_sns,
        user_id=args.user_id,
        email=args.email,
        recent=args.recent or 10,
        exclude_shipped=is_recent_mode,
    )
    return action_fp_verify(client, db, env, target_orders)


def handle_settlement(client, db, env, args, email):
    """结算"""
    from modules.order_process import action_settlement, resolve_order_ids
    order_ids, order_sns = require_order_identifier(args)
    is_recent_mode = not order_ids and not order_sns
    target_orders = resolve_order_ids(
        db, order_ids, order_sns,
        user_id=args.user_id,
        email=args.email,
        recent=args.recent or 10,
        exclude_shipped=is_recent_mode,
    )
    return action_settlement(client, db, env, target_orders)


def handle_shipping(client, db, env, args, email):
    """发货（完整流程：FP审核 → 结算 → 发货）"""
    from modules.order_process import action_process_orders, resolve_order_ids
    order_ids, order_sns = require_order_identifier(args)
    is_recent_mode = not order_ids and not order_sns
    target_orders = resolve_order_ids(
        db, order_ids, order_sns,
        user_id=args.user_id,
        email=args.email,
        recent=args.recent or 10,
        exclude_shipped=is_recent_mode,
    )
    return action_process_orders(
        client, db, env,
        order_ids=target_orders,
        tracking_number=args.tracking_number,
        shipping_carrier=args.shipping_carrier or "7 Hours Express",
    )


def handle_process_orders(client, db, env, args, email):
    """处理订单（可选跳过步骤）"""
    from modules.order_process import action_process_orders
    order_ids = parse_order_ids(args)
    order_sns = parse_order_sns(args)
    return action_process_orders(
        client, db, env,
        order_ids=order_ids,
        order_sns=order_sns,
        user_id=args.user_id,
        email=email if args.email else None,
        recent=args.recent or 10,
        tracking_number=args.tracking_number,
        shipping_carrier=args.shipping_carrier or "7 Hours Express",
        skip_fp=args.skip_fp,
        skip_settlement=args.skip_settlement,
        skip_shipping=args.skip_shipping,
    )


def handle_cancel_orders(client, db, env, args, email):
    """取消订单"""
    from modules.order_process import action_cancel_orders
    order_ids, order_sns = require_order_identifier(args)
    return action_cancel_orders(
        client, db, env,
        order_ids=order_ids,
        order_sns=order_sns,
        user_id=args.user_id,
        email=args.email,
        recent=args.recent or 10,
    )


def handle_delivered(client, db, env, args, email):
    """标记送达"""
    from modules.order_process import action_delivered
    order_ids, order_sns = require_order_identifier(args)
    return action_delivered(
        client, db, env,
        order_ids=order_ids,
        order_sns=order_sns,
        user_id=args.user_id,
        email=args.email,
        recent=args.recent or 10,
    )


def handle_update_delivery_time(client, db, env, args, email):
    """修改送达时间"""
    from modules.order.status import action_update_delivery_time
    
    order_id = args.order_id
    order_sn = args.order_sn
    
    if not order_id and not order_sn:
        print("❌ 请提供 --order-id 或 --order-sn")
        sys.exit(1)
    
    # 计算目标时间
    # 优先级：指定时间戳 > 偏移量组合
    target_timestamp = None
    if args.delivery_timestamp:
        target_timestamp = args.delivery_timestamp
    else:
        # 计算偏移量（可组合使用）
        total_offset_seconds = 0
        has_offset = False
        
        if args.days_offset is not None:
            total_offset_seconds += args.days_offset * 24 * 3600
            has_offset = True
        if args.hours_offset is not None:
            total_offset_seconds += args.hours_offset * 3600
            has_offset = True
        if args.minutes_offset is not None:
            total_offset_seconds += args.minutes_offset * 60
            has_offset = True
        
        # 如果没有任何偏移参数，默认 +1 天
        if not has_offset:
            total_offset_seconds = 24 * 3600
        
        import time
        target_timestamp = int(time.time()) + total_offset_seconds
    
    return action_update_delivery_time(
        client, db, env,
        order_id=order_id,
        order_sn=order_sn,
        target_timestamp=target_timestamp,
    )


# Handler 注册表
ORDER_HANDLERS = {
    "place_order": handle_place_order,
    "fp_verify": handle_fp_verify,
    "settlement": handle_settlement,
    "shipping": handle_shipping,
    "process_orders": handle_process_orders,
    "cancel_orders": handle_cancel_orders,
    "delivered": handle_delivered,
    "update_delivery_time": handle_update_delivery_time,
}
