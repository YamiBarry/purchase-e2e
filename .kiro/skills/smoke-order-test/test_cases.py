# -*- coding: utf-8 -*-
"""
冒烟下单测试用例配置

商品类型说明（来自 im_item 表字段）：
  business_type=1, item_type=1, share=0, 无地区限制  → 全国可售自营
  business_type=1, item_type=1, share=0, 有地区限制  → 自营本地化
  business_type=1, item_type=1, share=0, 大区限制    → 自营大区
  business_type=1, item_type=1, share=1              → 共享库存自营
  business_type=6, item_type=6                       → 自营预售
  business_type=5, item_type=1                       → FBY 商品
  business_type=3, item_type=1                       → 第三方商品
  business_type=1, item_type=7                       → 礼品卡

注意：item_number 和 goods_img 均由 _refresh_item_numbers() 在运行时从数据库动态查询填充，
      此处保持空字符串，不要手动填写。
"""

TEST_CASES = [
    {
        "id": "1a",
        "name": "全国可售共享库存商品（购物车仓下单）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": "1b",
        "name": "全国可售共享库存商品（对仓下单）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "address_id_override": "OTHER_WH",  # 运行时由 run() 替换为对仓动态 address_id
        "enabled": True,
    },
    {
        "id": "1c",
        "name": "全国可售共享库存商品（购物车仓无货）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 1,
        "name": "全国可售自营商品",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 2,
        "name": "自营本地化商品",
        "business_type": 2,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": "2b",
        "name": "自营本地化商品（对仓无法下单）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "address_id_override": "OTHER_WH",  # 运行时由 run() 替换为对仓动态 address_id
        "expect_fail": True,
        "expect_error": "当前地址无法配送",
        "enabled": True,
    },
    {
        "id": 3,
        "name": "自营大区商品",
        "business_type": 4,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": "3b",
        "name": "自营大区商品（对仓下单）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "address_id_override": "OTHER_WH",  # 运行时由 run() 替换为对仓动态 address_id
        "enabled": True,
    },
    {
        "id": 4,
        "name": "自营大区共享库存商品（购物车仓下单）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": "4b",
        "name": "自营大区共享库存商品（对仓下单）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "address_id_override": "OTHER_WH",  # 运行时由 run() 替换为对仓动态 address_id
        "enabled": True,
    },
    {
        "id": "4c",
        "name": "自营大区共享库存商品（购物车仓无货）",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 5,
        "name": "自营预售全国可售商品",
        "business_type": 1,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": "6a",
        "name": "FBY全国可售共享库存商品（购物车仓下单）",
        "business_type": 5,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": "6b",
        "name": "FBY全国可售共享库存商品（对仓下单）",
        "business_type": 5,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "address_id_override": "OTHER_WH",  # 运行时由 run() 替换为对仓动态 address_id
        "enabled": True,
    },
    {
        "id": "6c",
        "name": "FBY全国可售共享库存商品（购物车仓无货）",
        "business_type": 5,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 6,
        "name": "FBY全国可售商品",
        "business_type": 6,
        "item_type": 6,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 7,
        "name": "第三方直邮商品",
        "business_type": 3,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 8,
        "name": "第三方预售商品",
        "business_type": 3,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 10,
        "name": "第三方礼券商品",
        "business_type": 3,
        "item_type": 1,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
    {
        "id": 9,
        "name": "自营虚拟礼卡",
        "business_type": 1,
        "item_type": 7,
        "item_number": "",
        "goods_img": "",
        "qty": 1,
        "enabled": True,
    },
]
