# -*- coding: utf-8 -*-
"""
促销活动模块（兼容性重导出）

此文件保留用于向后兼容，实际实现已拆分到 modules/promotion/ 子模块：
  - modules/promotion/constants.py  - 常量定义
  - modules/promotion/helpers.py    - 辅助函数
  - modules/promotion/create.py     - 创建促销活动
  - modules/promotion/manage.py     - 管理促销活动（结束、查询）

新代码请直接从 modules.promotion 导入。
"""

# 从子模块重导出所有公开内容
from modules.promotion.constants import (
    PromotionStatus,
    PROMO_TYPE_MODE as _PROMO_TYPE_MODE,
    PROMO_TYPE_NAME as _PROMO_TYPE_NAME,
    CUSTOMIZE_MODES as _CUSTOMIZE_MODES,
    CONFLICT_MSG_IDS as _CONFLICT_MSG_IDS,
    PROMO_QUERY_CONFIG as _PROMO_QUERY_CONFIG,
)

from modules.promotion.helpers import (
    get_goods_info_for_mkt as _get_goods_info_for_mkt,
    parse_promotion_detail as _parse_promotion_detail,
)

from modules.promotion.create import action_create_promotion

from modules.promotion.manage import (
    action_finish_promotion,
    action_find_promotion,
)

__all__ = [
    # 常量
    "PromotionStatus",
    "_PROMO_TYPE_MODE",
    "_PROMO_TYPE_NAME",
    "_CUSTOMIZE_MODES",
    "_CONFLICT_MSG_IDS",
    "_PROMO_QUERY_CONFIG",
    # 辅助函数
    "_get_goods_info_for_mkt",
    "_parse_promotion_detail",
    # 创建
    "action_create_promotion",
    # 管理
    "action_finish_promotion",
    "action_find_promotion",
]
