# -*- coding: utf-8 -*-
"""
商品相关 Action Handlers
"""

import sys
from handlers.base import require_param, require_items


def handle_set_stock(client, db, env, args, email):
    """设置库存"""
    from modules.item import action_batch_set_stock
    items = require_items(args)
    require_param(args.stock, "--stock 参数")
    warehouse = "001"  # 默认 LA 仓
    if args.wh:
        parts = str(args.wh).split(":")
        warehouse = "001" if parts[0] == "1" else "002"
    return action_batch_set_stock(client, db, env, items, int(args.stock), warehouse)


def handle_set_price(client, db, env, args, email):
    """设置价格"""
    from modules.item import action_set_price
    require_param(args.item_number, "--item-number")
    require_param(args.price, "--price 参数")
    return action_set_price(
        client, db, env, args.item_number, float(args.price),
        rule_id=args.rule_id,
        market_price=float(args.market_price) if args.market_price is not None else None,
    )


def handle_set_status(client, db, env, args, email):
    """设置上下架状态"""
    from modules.item import action_batch_set_status
    items = require_items(args)
    return action_batch_set_status(client, db, env, items, args.status)


def handle_find_item(client, db, env, args, email):
    """查找商品"""
    from modules.item import action_find_item
    require_param(args.item_type, "--type 参数指定商品类型")
    return action_find_item(
        db, env,
        item_type=args.item_type,
        stock_condition=args.stock_condition or "both",
        seller_id=args.seller_id,
        zipcode=args.zipcode,
        state=getattr(args, 'state', None),
        site=getattr(args, 'site', None),
        min_stock=args.min_stock or 5,
        limit=args.limit or 1,
    )


# Handler 注册表
ITEM_HANDLERS = {
    "set_stock": handle_set_stock,
    "set_price": handle_set_price,
    "set_status": handle_set_status,
    "find_item": handle_find_item,
}
