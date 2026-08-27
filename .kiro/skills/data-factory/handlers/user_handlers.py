# -*- coding: utf-8 -*-
"""
用户相关 Action Handlers
"""

from handlers.base import require_param, require_items, login_user


def handle_register(client, db, env, args, email):
    """注册新用户"""
    from modules.user import action_register
    # 只接受 autous/autoca 开头的自定义邮箱，其他格式（如旧的 aitest）视为无效，让工具自动生成
    reg_email = args.email
    if reg_email and not reg_email.startswith(("autous", "autoca")):
        reg_email = None
    return action_register(client, db, env, reg_email, args.pwd or "111111")


def handle_register_ca(client, db, env, args, email):
    """注册 CA 站新用户（含手机验证）"""
    from modules.user import action_register_ca
    # 只接受 autoca 开头的自定义邮箱，其他格式视为无效，让工具自动生成
    reg_email = args.email
    if reg_email and not reg_email.startswith("autoca"):
        reg_email = None
    return action_register_ca(
        client, db, env,
        email=reg_email,
        pwd=args.pwd or "111111",
        phone=getattr(args, 'phone', None),
    )


def handle_login(client, db, env, args, email):
    """用户登录"""
    from modules.user import action_login
    return action_login(client, env, email, args.pwd or "111111")


def handle_get_token(client, db, env, args, email):
    """获取用户 token"""
    from modules.user import action_login
    return action_login(client, env, email, args.pwd or "111111")


def handle_set_giftcard(client, db, env, args, email):
    """设置礼卡余额"""
    from modules.user import action_set_giftcard
    return action_set_giftcard(client, db, env, email, args.amount)


def handle_add_giftcard(client, db, env, args, email):
    """增加礼卡余额"""
    from modules.user import action_add_giftcard
    return action_add_giftcard(client, db, env, email, args.amount)


def handle_set_points(client, db, env, args, email):
    """设置积分"""
    from modules.user import action_set_points
    return action_set_points(client, db, env, email, int(args.points))


def handle_add_points(client, db, env, args, email):
    """增加积分"""
    from modules.user import action_add_points
    return action_add_points(client, db, env, email, int(args.points))


def handle_convert_coupon(client, db, env, args, email):
    """兑换优惠券"""
    from modules.user import action_convert_coupon
    require_param(args.ps_code, "--ps-code 优惠券兑换码")
    return action_convert_coupon(client, db, env, args.ps_code, email, args.user_id, args.pwd or "111111")


def handle_get_user_info(client, db, env, args, email):
    """获取用户信息"""
    from modules.user import action_get_user_info
    return action_get_user_info(client, db, env, email, args.user_id, args.pwd or "111111")


def handle_add_to_cart(client, db, env, args, email):
    """加入购物车"""
    from modules.user import action_add_to_cart
    login_user(client, email, args.pwd)
    
    # 支持两种模式：
    # 1. 指定 item_numbers：直接加购
    # 2. 指定 item_type：自动查找该类型在用户仓库有库存的商品
    item_numbers = None
    item_type = None
    
    if args.item_numbers or args.item_number:
        # 模式1：指定商品编号
        item_numbers = args.item_numbers or ([args.item_number] if args.item_number else None)
    elif args.item_type:
        # 模式2：指定商品类型，自动查找
        item_type = args.item_type
    else:
        raise ValueError("必须提供 --item-numbers 或 --item-type 参数")
    
    # qty 参数：item_type 模式下查找的商品数量，默认 1
    qty = int(args.qty) if hasattr(args, 'qty') and args.qty else 1
    
    return action_add_to_cart(
        client, env, email,
        item_numbers=item_numbers,
        item_type=item_type,
        zipcode=args.zipcode,
        qty=qty,
        db=db
    )


def handle_clear_cart(client, db, env, args, email):
    """清空购物车"""
    from modules.user import action_clear_cart
    login_user(client, email, args.pwd)
    return action_clear_cart(client, env, email)


def handle_create_address(client, db, env, args, email):
    """创建收货地址"""
    from modules.user import action_create_address
    return action_create_address(
        client, db, env, email,
        user_id=args.user_id,
        pwd=args.pwd or "111111",
        country=getattr(args, 'addr_country', None) or "US",
        state=getattr(args, 'addr_state', None),
        zipcode=getattr(args, 'addr_zipcode', None),
        address1=getattr(args, 'addr_address1', None),
        address2=getattr(args, 'addr_address2', None),
        city=getattr(args, 'addr_city', None),
        firstname=getattr(args, 'addr_firstname', None),
        lastname=getattr(args, 'addr_lastname', None),
        phone=getattr(args, 'addr_phone', None),
        is_primary=getattr(args, 'addr_is_primary', 1) or 1,
    )


def handle_set_vip_level(client, db, env, args, email):
    """设置用户 VIP 等级"""
    from modules.user import action_set_vip_level
    from handlers.base import require_param
    require_param(args.level, "--level VIP等级(ruby/silver/gold)")
    return action_set_vip_level(client, db, env, email, args.level, args.user_id, args.pwd or "111111")


# Handler 注册表
USER_HANDLERS = {
    "register": handle_register,
    "register_ca": handle_register_ca,
    "login": handle_login,
    "get_token": handle_get_token,
    "set_giftcard": handle_set_giftcard,
    "add_giftcard": handle_add_giftcard,
    "set_points": handle_set_points,
    "add_points": handle_add_points,
    "convert_coupon": handle_convert_coupon,
    "get_user_info": handle_get_user_info,
    "add_to_cart": handle_add_to_cart,
    "clear_cart": handle_clear_cart,
    "create_address": handle_create_address,
    "set_vip_level": handle_set_vip_level,
}
