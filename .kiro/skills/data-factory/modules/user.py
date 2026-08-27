# -*- coding: utf-8 -*-
"""
用户模块（兼容性入口）

此文件保留用于向后兼容，实际实现已拆分到 modules/user/ 子模块：
  - auth.py: 注册、登录
  - balance.py: 礼卡、积分操作
  - cart.py: 购物车操作
  - info.py: 用户信息查询、优惠券兑换
"""

# 从子模块重导出所有函数
from modules.user import (
    # 认证
    action_register,
    action_login,
    # 余额
    action_set_giftcard,
    action_set_points,
    action_add_giftcard,
    action_add_points,
    # 购物车
    action_add_to_cart,
    action_clear_cart,
    # 地址
    action_create_address,
    # 用户信息
    action_get_user_id,
    action_convert_coupon,
    action_get_user_info,
    _get_user_email_by_id,
)

__all__ = [
    "action_register",
    "action_login",
    "action_set_giftcard",
    "action_set_points",
    "action_add_giftcard",
    "action_add_points",
    "action_add_to_cart",
    "action_clear_cart",
    "action_create_address",
    "action_get_user_id",
    "action_convert_coupon",
    "action_get_user_info",
    "_get_user_email_by_id",
]
