# -*- coding: utf-8 -*-
"""
用户模块
支持：注册新用户、登录、设置礼卡余额、设置积分、购物车操作、用户信息查询

接口来源：
  注册: POST /ec-customer/users/register
  登录: POST /ec-customer/users/login
  礼卡: POST /central-mkt/eGiftCard/internal/send
  积分: POST /central-customer/points_v2
"""

# 认证相关
from modules.user.auth import action_register, action_register_ca, action_login

# 余额相关
from modules.user.balance import (
    action_set_giftcard,
    action_set_points,
    action_add_giftcard,
    action_add_points,
)

# 购物车相关
from modules.user.cart import action_add_to_cart, action_clear_cart

# 地址相关
from modules.user.address import action_create_address

# VIP 等级相关
from modules.user.vip import action_set_vip_level

# 用户信息相关
from modules.user.info import (
    action_get_user_id,
    action_convert_coupon,
    action_get_user_info,
    _get_user_email_by_id,
)

__all__ = [
    # 认证
    "action_register",
    "action_register_ca",
    "action_login",
    # 余额
    "action_set_giftcard",
    "action_set_points",
    "action_add_giftcard",
    "action_add_points",
    # 购物车
    "action_add_to_cart",
    "action_clear_cart",
    # 地址
    "action_create_address",
    # VIP
    "action_set_vip_level",
    # 用户信息
    "action_get_user_id",
    "action_convert_coupon",
    "action_get_user_info",
    "_get_user_email_by_id",
]
