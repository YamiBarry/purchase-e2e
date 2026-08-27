# -*- coding: utf-8 -*-
"""
Handler 基础工具函数
"""

import sys


def require_param(value, param_name: str):
    """检查必填参数，缺失则退出"""
    if value is None:
        print(f"❌ 请提供 {param_name}")
        sys.exit(1)
    return value


def require_items(args) -> list:
    """获取商品列表参数，支持单个或多个"""
    items = args.item_numbers or ([args.item_number] if args.item_number else None)
    if not items:
        print("❌ 请提供 --item-number 或 --item-numbers")
        sys.exit(1)
    return items


def parse_order_ids(args) -> list:
    """解析订单ID参数，支持单个或多个"""
    if args.order_ids:
        return [int(oid) for oid in args.order_ids]
    elif args.order_id:
        return [int(args.order_id)]
    return None


def parse_order_sns(args) -> list:
    """解析订单编号参数，支持单个或多个"""
    if args.order_sns:
        return args.order_sns
    elif args.order_sn:
        return [args.order_sn]
    return None


def require_order_identifier(args):
    """检查订单标识参数"""
    order_ids = parse_order_ids(args)
    order_sns = parse_order_sns(args)
    if not order_ids and not order_sns and not args.user_id and not args.email:
        print("❌ 请提供 --order-id / --order-ids / --order-sn / --order-sns / --user-id / --email")
        sys.exit(1)
    return order_ids, order_sns


def login_user(client, email: str, pwd: str):
    """登录用户"""
    from core.auth import login
    try:
        login(client, email, pwd or "111111")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        sys.exit(1)
