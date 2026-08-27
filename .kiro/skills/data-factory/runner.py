# -*- coding: utf-8 -*-
"""
Action 执行器模块
使用 handler 字典映射模式
"""

import sys
import config as cfg
from core.http_client import HttpClient
from core.db import DbClient
from core.exceptions import UserNotFoundError, ConfigError
from output import print_results
from handlers import ACTION_HANDLERS, NO_EMAIL_ACTIONS, LOGIN_REQUIRED_ACTIONS


def _build_client(env: str, token: str = None) -> HttpClient:
    """构建 HTTP 客户端"""
    ec = cfg.ENV_CONFIG[env]["ec_base"]
    central = cfg.ENV_CONFIG[env]["central_base"]
    return HttpClient(ec, central, token=token)


def _build_db(env: str) -> DbClient:
    """构建数据库客户端"""
    return DbClient(env)


def _print_dry_run_info(action: str, args, env: str) -> None:
    """
    打印 dry-run 预览信息。
    
    Args:
        action: 操作名称
        args: 命令行参数
        env: 环境名称
    """
    print(f"\n{'─'*50}")
    print(f"  🔍 DRY-RUN 预览模式（不会实际执行）")
    print(f"{'─'*50}")
    print(f"  环境: {env}")
    print(f"  操作: {action}")
    
    # 显示关键参数
    key_params = []
    if args.email:
        key_params.append(f"邮箱: {args.email}")
    if args.user_id:
        key_params.append(f"用户ID: {args.user_id}")
    if args.item_number:
        key_params.append(f"商品: {args.item_number}")
    if args.item_numbers:
        key_params.append(f"商品列表: {', '.join(args.item_numbers)}")
    if args.amount:
        key_params.append(f"金额: {args.amount}")
    if args.points:
        key_params.append(f"积分: {args.points}")
    if args.stock:
        key_params.append(f"库存: {args.stock}")
    if args.order_id:
        key_params.append(f"订单ID: {args.order_id}")
    if args.order_sn:
        key_params.append(f"订单号: {args.order_sn}")
    if args.recent:
        key_params.append(f"最近N个: {args.recent}")
    
    if key_params:
        print(f"  参数:")
        for p in key_params:
            print(f"    - {p}")
    
    print(f"\n  💡 移除 --dry-run 参数以实际执行")
    print(f"{'─'*50}\n")


def _resolve_email(args, db) -> str:
    """
    从 --email 或 --user-id 解析出邮箱，优先 email。
    
    Args:
        args: 命令行参数对象
        db: 数据库客户端
    
    Returns:
        用户邮箱字符串
    
    Raises:
        UserNotFoundError: 当 user_id 不存在时
        ConfigError: 当既没有 email 也没有 user_id 时
    """
    if args.email:
        return args.email
    if args.user_id:
        row = db.query_one(
            "SELECT email FROM yamibuy_master.xysc_users WHERE user_id = %s LIMIT 1",
            (args.user_id,)
        )
        if not row:
            raise UserNotFoundError(f"user_id {args.user_id} 不存在")
        return row["email"]
    raise ConfigError("请提供 --email 或 --user-id")


def run_action(args):
    """
    单个操作模式
    使用 handler 字典映射，替代 if-elif 链
    支持 --dry-run 预览模式
    """
    env = args.env.upper()
    if env not in cfg.ENV_CONFIG:
        print(f"❌ 不支持的环境: {env}，可选: UAT / GQC / DEV")
        sys.exit(1)

    action = args.action
    if action not in ACTION_HANDLERS:
        print(f"❌ 未知 action: {action}")
        sys.exit(1)

    # dry-run 模式：只显示将要执行的操作
    if getattr(args, 'dry_run', False):
        _print_dry_run_info(action, args, env)
        return

    client = _build_client(env)
    db = _build_db(env)

    # 解析 email（部分 action 不需要）
    if action not in NO_EMAIL_ACTIONS:
        try:
            resolved_email = _resolve_email(args, db)
        except UserNotFoundError as e:
            print(f"❌ {e}")
            return
        except ConfigError as e:
            print(f"❌ {e}")
            return
    else:
        resolved_email = args.email

    # 需要登录的 action，先登录
    if action in LOGIN_REQUIRED_ACTIONS:
        from core.auth import login
        try:
            login(client, resolved_email, args.pwd or "111111")
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            sys.exit(1)

    # 调用对应的 handler
    handler = ACTION_HANDLERS[action]
    result = handler(client, db, env, args, resolved_email)

    # 打印结果（handler 返回 None 表示已自行打印）
    if result is not None:
        print_results([result])


def run_recipe(args):
    """配方模式"""
    env = args.env.upper()
    if env not in cfg.ENV_CONFIG:
        print(f"❌ 不支持的环境: {env}")
        sys.exit(1)

    client = _build_client(env)
    db = _build_db(env)
    results = []

    if args.recipe == "new_user":
        from recipes.user_recipes import recipe_new_user
        results = recipe_new_user(client, db, env, args.email, args.pwd or "Test@123456")

    elif args.recipe == "user_with_balance":
        from recipes.user_recipes import recipe_user_with_balance
        results = recipe_user_with_balance(
            client, db, env, args.email, args.pwd or "Test@123456",
            giftcard=float(args.giftcard or 0), points=int(args.points or 0),
        )

    elif args.recipe == "seckill_item":
        from recipes.item_recipes import recipe_seckill_item
        results = recipe_seckill_item(client, db, env, args.item_number, float(args.price), int(args.stock))

    elif args.recipe == "promotion_item":
        from recipes.item_recipes import recipe_promotion_item
        results = recipe_promotion_item(client, db, env, args.item_number, float(args.price), int(args.stock or 100))

    elif args.recipe == "new_user_order":
        from recipes.order_recipes import recipe_new_user_place_order
        results = recipe_new_user_place_order(
            client, db, env,
            item_number=args.item_number, qty=int(args.qty or 1),
            email=args.email, pwd=args.pwd or "Test@123456",
            use_giftcard=args.use_giftcard, giftcard_amount=float(args.giftcard or 0),
            use_points=args.use_points, points=int(args.points or 0),
            coupon_code=args.coupon_code,
        )

    elif args.recipe == "existing_user_order":
        from recipes.order_recipes import recipe_existing_user_place_order
        results = recipe_existing_user_place_order(
            client, db, env,
            email=args.email, pwd=args.pwd,
            item_number=args.item_number, qty=int(args.qty or 1),
            use_giftcard=args.use_giftcard,
            use_points=args.use_points,
            coupon_code=args.coupon_code,
        )

    elif args.recipe == "coupon_in_account":
        from recipes.promotion_recipes import recipe_coupon_in_account
        results = recipe_coupon_in_account(
            client, db, env,
            email=args.email, pwd=args.pwd,
            discount=float(args.discount), min_order=float(args.min_order),
        )
    else:
        print(f"❌ 未知 recipe: {args.recipe}")
        sys.exit(1)

    print_results(results)
