# -*- coding: utf-8 -*-
"""
商品上下架模块
支持：单个/批量商品上下架
"""

import time
from typing import List

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.types import ActionResult
from core.exceptions import AuthError, ApiRequestError
from validators.item_validator import validate_batch_status
from config import VALIDATION_WAIT
from modules.item.find import ItemStatus


# 默认平台渠道配置
DEFAULT_PLAT_CHANNEL_LIST = [
    {"platform_code": "B2C", "channel_code": "Computer"}
]


def action_set_status(client: HttpClient, db: DbClient, env: str, item_number: str, status: str) -> ActionResult:
    """
    单个商品上下架（兼容旧接口）
    status: 'on' 上架 / 'off' 下架
    """
    return action_batch_set_status(client, db, env, [item_number], status)


def action_batch_set_status(client: HttpClient, db: DbClient, env: str, item_numbers: List[str], status: str) -> ActionResult:
    """
    批量上下架商品

    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        item_numbers: 商品编号列表
        status: 'on' 上架 / 'off' 下架

    Returns:
        操作结果
    """
    start = time.time()
    try:
        # 参数校验
        if status not in ("on", "off"):
            raise ValueError(f"status 只能是 'on' 或 'off'，当前值: {status}")

        if not item_numbers:
            raise ValueError("item_numbers 不能为空")

        # 转换状态值
        api_status = ItemStatus.ACTIVE if status == "on" else ItemStatus.DEACTIVE
        status_desc = "上架" if status == "on" else "下架"

        # 获取 Hub admin token
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败，请检查 HUB_ADMIN_ACCOUNT 配置", "hub")

        # 保存原 token，使用 hub token 调用接口
        orig_token = client.token
        client.token = hub_token

        # 构建处方药信息（默认都不是处方药）
        prescription_drugs_info = [
            {"item_number": item_no, "prescription_drugs_flag": 0}
            for item_no in item_numbers
        ]

        # 构建请求体
        body = {
            "status": api_status,
            "itemList": item_numbers,
            "platChannelList": DEFAULT_PLAT_CHANNEL_LIST,
            "prescriptionDrugsInfo": prescription_drugs_info,
        }

        try:
            # 调用接口
            resp_status, resp = client.post(
                "/im/item/batchUpdateStatusV2",
                body=body,
                use_central=True
            )
        finally:
            # 恢复原 token
            client.token = orig_token

        if not client.is_success(resp_status, resp):
            raise ApiRequestError("/im/item/batchUpdateStatusV2", resp_status, client.get_error(resp))

        # 等待数据同步
        time.sleep(VALIDATION_WAIT)

        # 验证结果
        validation = validate_batch_status(db, item_numbers, status)

        return {
            "success": validation["passed"],
            "env": env,
            "action": f"batch_set_status ({status_desc})",
            "data": {
                "item_numbers": item_numbers,
                "status": status,
                "api_status": api_status,
                "count": len(item_numbers),
            },
            "validation": validation,
            "elapsed": time.time() - start,
        }

    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": f"batch_set_status",
            "data": {"item_numbers": item_numbers, "status": status},
            "error": str(e),
            "elapsed": time.time() - start,
        }
