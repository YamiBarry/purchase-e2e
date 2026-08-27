#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
造数据工具 - 统一入口

用法：
    # 单个操作
    python main.py --env UAT --action register
    python main.py --env UAT --action set_giftcard --email xxx@yami.com --amount 100
    python main.py --env UAT --action set_points   --email xxx@yami.com --points 500
    python main.py --env UAT --action set_stock    --item-number YAM-123 --stock 100
    python main.py --env UAT --action set_price    --item-number YAM-123 --price 19.9
    python main.py --env UAT --action set_status   --item-number YAM-123 --status on
    python main.py --env UAT --action create_promotion    --item-number YAM-123 --price 9.9
    python main.py --env UAT --action create_seckill      --item-number YAM-123 --price 5.9 --stock 100
    python main.py --env UAT --action create_member_price --item-number YAM-123 --price 8.8
    python main.py --env UAT --action create_giftcard_price --item-number YAM-123 --price 7.7
    python main.py --env UAT --action create_gift_bundle  --item-number YAM-123 --gift-item YAM-456
    python main.py --env UAT --action create_coupon       --discount 5 --min-order 30
    python main.py --env UAT --action place_order --email xxx --item-number YAM-123

    # 配方模式（组合场景）
    python main.py --env UAT --recipe new_user
    python main.py --env UAT --recipe user_with_balance   --giftcard 100 --points 500
    python main.py --env UAT --recipe seckill_item        --item-number YAM-123 --price 5.9 --stock 100
    python main.py --env UAT --recipe new_user_order      --item-number YAM-123 --use-giftcard --giftcard 50
    python main.py --env UAT --recipe existing_user_order --email xxx --item-number YAM-123 --use-coupon CP_xxx
"""

import sys
import os

# 把 skill 根目录加入 path，确保 import 正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg
from cli import parse_args
from runner import run_action, run_recipe


def main():
    """主入口"""
    # 初始化日志配置
    cfg.init_logging()
    
    # 解析命令行参数
    args = parse_args()

    # 根据模式执行
    if args.action:
        run_action(args)
    elif args.recipe:
        run_recipe(args)
    else:
        from cli import create_parser
        create_parser().print_help()


if __name__ == "__main__":
    main()
