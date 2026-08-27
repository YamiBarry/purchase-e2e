# -*- coding: utf-8 -*-
"""
优惠券模块
支持: 创建优惠券(折扣券/满减券/现金券/运费券)

coupon_type: discount / reduce / cash / shipping
coupon_form: platform / promo  [运费券自动为3]
send_type:   redeem / receive
scope:       all / category / brand / item(支持多个item_number)
relative:    相对使用时间(分钟)
shipping_group_type: 1=亚米物流 3=商家直邮 4=中国集运 6=预售
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from core.http_client import HttpClient
from core.db import DbClient
from core.auth import _get_hub_token
from core.mkt_api import MktApiClient
from core.types import ActionResult
from core.exceptions import AuthError, PromotionCreateError
from core.utils import wait_for_db_condition
from core.constants import is_yami_seller
from config import VALIDATION_WAIT
from modules.promotion.constants import (
    PromotionStatus,
    CouponType,
    CouponForm,
    CouponSendType,
    CouponScheduleType,
    CouponTheme,
    COUPON_TYPE_MAP,
    COUPON_FORM_MAP,
    COUPON_SEND_TYPE_MAP,
)

_COUPON_CODE_PREFIX = "test"

# group_type -> business_types 映射(字符串数组, 与前端一致)
_GROUP_TYPE_BUSINESS = {
    1: ["1", "2", "5"],
    3: ["3"],
    4: ["4"],
    6: ["6"],
}


def _next_coupon_code(db: DbClient, prefix: Optional[str] = None) -> str:
    """生成当天下一个可用的兑换码"""
    date_str = datetime.now().strftime("%m%d")
    base = prefix or f"{_COUPON_CODE_PREFIX}{date_str}"
    row = db.query_one(
        "SELECT ps_code FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_code LIKE %s ORDER BY ps_id DESC LIMIT 1",
        (f"{base}%",)
    )
    if row:
        try:
            suffix = row["ps_code"][len(base):]
            if suffix.isdigit():
                seq = int(suffix)
                return f"{base}{seq + 1:02d}"
        except Exception:
            pass
    return f"{base}01"


def _get_default_shipping(db: DbClient, seller_id: int) -> Dict[str, any]:
    """查商家默认配送方式, 返回 {shipping_id, shipping_name, shipping_fee}"""
    row = db.query_one(
        "SELECT shipping_id, shipping_name, shipping_fee FROM yamibuy_master.xysc_shipping WHERE vendor_id = %s AND enabled = 1 AND is_primary = 1 LIMIT 1",
        (seller_id,)
    )
    if not row:
        row = db.query_one(
            "SELECT shipping_id, shipping_name, shipping_fee FROM yamibuy_master.xysc_shipping WHERE vendor_id = %s AND enabled = 1 ORDER BY shipping_id LIMIT 1",
            (seller_id,)
        )
    if row:
        return {"shipping_id": row["shipping_id"], "shipping_name": row["shipping_name"], "shipping_fee": float(row["shipping_fee"])}
    return {"shipping_id": 1, "shipping_name": "Standard Shipping", "shipping_fee": 0.0}


def action_create_coupon(
    client: HttpClient,
    db: DbClient,
    env: str,
    coupon_code: Optional[str] = None,
    coupon_type: str = "discount",
    coupon_form: str = "platform",
    send_type: str = "redeem",
    discount: float = 10,
    buy_amount: Optional[float] = None,
    reduce_amount: Optional[float] = None,
    cash_amount: Optional[float] = None,
    coupon_amount: int = 1000,
    hours: int = 24,
    relative: Optional[int] = None,
    seller_id: int = 0,
    scope: str = "all",
    scope_ids: Optional[List] = None,
    limit_user: str = "all",
    send_channel: int = 0,
    shipping_group_type: int = 1,
    shipping_id: Optional[int] = None,
) -> ActionResult:
    """
    创建优惠券: insert -> submitCoupon -> confirmEffective, 返回 ps_id + coupon_code
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境
        coupon_code: 兑换码（可选，不填自动生成）
        coupon_type: 券类型 discount/reduce/cash/shipping
        coupon_form: 券形式 platform/promo
        send_type: 发放方式 redeem/receive
        discount: 折扣百分比（折扣券用）
        buy_amount: 满金额门槛（满减券用）
        reduce_amount: 减金额（满减券用）
        cash_amount: 现金面额（现金券用）
        coupon_amount: 发券数量
        hours: 有效期小时数
        relative: 相对使用时间（分钟）
        seller_id: 商家ID
        scope: 作用范围 all/category/brand/item
        scope_ids: 范围ID列表
        limit_user: 领取用户 all/new
        send_channel: 发放渠道
        shipping_group_type: 运费券业务类型
        shipping_id: 配送方式ID
    
    Returns:
        操作结果
    """
    start = time.time()
    try:
        ps_code = coupon_code or _next_coupon_code(db)
        hub_token = _get_hub_token(client, env)
        if not hub_token:
            raise AuthError("获取 Hub admin token 失败", "hub")

        is_shipping = coupon_type == "shipping"
        now = int(time.time())
        end = now + hours * 3600

        # 运费券: 自动查默认配送方式, reduce_amount = shipping_fee
        shipping_name = None
        if is_shipping and shipping_id is None:
            info = _get_default_shipping(db, seller_id)
            shipping_id = info["shipping_id"]
            shipping_name = info["shipping_name"]
            if reduce_amount is None:
                reduce_amount = info["shipping_fee"]

        # 使用常量替代魔法数字
        coupon_type_val = COUPON_TYPE_MAP.get(coupon_type, CouponType.DISCOUNT)
        coupon_form_val = CouponForm.SHIPPING if is_shipping else COUPON_FORM_MAP.get(coupon_form, CouponForm.PLATFORM)
        send_type_val = CouponSendType.REDEEM if is_shipping else COUPON_SEND_TYPE_MAP.get(send_type, CouponSendType.REDEEM)
        limit_user_val = {"all": 0, "new": 1}.get(limit_user, 0)
        is_relate = relative is not None
        relative_use_time = (relative * 60) if is_relate else 0

        group_type_val = str(shipping_group_type) if is_shipping else None
        business_types = _GROUP_TYPE_BUSINESS.get(shipping_group_type, ["1", "2", "5"]) if is_shipping else None

        code_type = "" if is_shipping else {"all": 1, "category": 2, "brand": 3, "item": 4}.get(scope, 1)
        item_list = scope_ids if scope == "item" else []
        category_list = scope_ids if scope == "category" else []
        brand_list = scope_ids if scope == "brand" else []

        is_yami_logistics = is_shipping and shipping_group_type == 1
        body_seller_id = None if is_yami_logistics else seller_id

        if is_yami_seller(seller_id):
            seller_name = "亚米自营"
            seller_ename = "Yamibuy"
        else:
            seller_row = db.query_one(
                "SELECT vendor_name, vendor_ename FROM yamibuy_master.xysc_vendor_info WHERE vendor_id = %s LIMIT 1",
                (seller_id,)
            )
            seller_name = seller_row["vendor_name"] if seller_row else str(seller_id)
            seller_ename = seller_row["vendor_ename"] if seller_row else str(seller_id)

        body_sellers = [] if is_yami_logistics else [{"seller_id": seller_id, "seller_name": seller_name, "seller_ename": seller_ename}]
        content_seller_id = None if is_yami_logistics else seller_id
        content_seller_name = None if is_yami_logistics else seller_name
        content_seller_ename = None if is_yami_logistics else seller_ename

        body = {
            "coupon_form": str(coupon_form_val),
            "send_type": send_type_val,
            "ps_sub_title": ps_code,
            "ps_title": "renee",
            "ps_text_cn": "", "ps_text_en": "",
            "short_promo_text_cn": "", "short_promo_text_en": "",
            "short_desc_translate": False, "long_desc_translate": False,
            "link_cn": "", "link_en": "",
            "start_time": now, "end_time": end,
            "type": CouponScheduleType.COUPON,
            "status": PromotionStatus.DRAFT,
            "notice_type": None,
            "seller_id": body_seller_id,
            "conflict_status": 0,
            "group_type": group_type_val,
            "multi_seller": False,
            "lstSellers": body_sellers,
            "is_relate": is_relate, "pdpCopy": False,
            "ps_content": {
                "limit_exchange_type": 0,
                "ps_code": ps_code, "ps_code_num": "",
                "coupon_amount_type": 1, "coupon_amount": coupon_amount,
                "per_code_amount": "", "limit_get_type": "0",
                "limit_get_amount": "", "limit_daily_amount": "",
                "ps_code_create_mode": 1, "ps_code_postfix": "",
                "limit_new_cusotmer": limit_user_val, "upload_user_ids": None,
                "seller_type": "", "include_gift": False,
                "origin_item_number": "", "gift_item_number": "",
                "la_qty": 0, "nj_qty": 0, "la_day_limit": 0, "nj_day_limit": 0,
                "group_type": group_type_val,
                "coupon_shipping_type": 1,
                "shipping_id": shipping_id,
                "shipping_name": shipping_name or "",
                "business_types": business_types,
                "is_relate": is_relate, "relative_use_time": relative_use_time,
                "psCodePrefix": {"groupPlayerTeams": [], "lstGroupPlayer": []},
                "codeItemsScope": {
                    "code_type": code_type,
                    "containRule": {
                        "categoryList": [{"category_id": c} for c in category_list] if scope == "category" else [],
                        "brandList": brand_list,
                        "itemList": item_list,
                        "excel_url": None, "excel_name": None, "excelData": [],
                        "excel_total_row": "", "excel_valid_row": 0, "excel_abnormal_reason": []
                    },
                    "eliminateRule": {"itemList": []},
                    "total_sku_num": 0
                },
                "couponContent": {
                    "seller_id": content_seller_id,
                    "seller_name": content_seller_name,
                    "seller_ename": content_seller_ename,
                    "coupon_form": str(coupon_form_val),
                    "platform": 0,
                    "coupon_type": coupon_type_val,
                    "max_discount": 0,
                    "percent": discount if coupon_type == "discount" else "",
                    "buy_amount": buy_amount if buy_amount is not None else "",
                    "reduce_amount": reduce_amount if reduce_amount is not None else "",
                    "cash_amount": cash_amount or "",
                    "use_start_time": None if is_relate else now,
                    "use_end_time": None if is_relate else end,
                    "coupon_desc_cn": "", "coupon_desc_en": "",
                    "group_type": group_type_val,
                    "coupon_shipping_type": 1,
                    "shipping_id": shipping_id,
                    "shipping_name": shipping_name or "",
                    "business_types": business_types
                }
            },
            "send_channel": send_channel,
            "theme": CouponTheme.DEFAULT,
            "ps_version": "0.0.1"
        }

        # 使用 MktApiClient 统一处理 API 调用
        mkt = MktApiClient(client, hub_token)

        resp = mkt.insert_coupon(body)
        if not mkt.is_success(resp):
            raise PromotionCreateError("优惠券", mkt.get_error(resp))
        ps_id = resp.get("body")

        resp2 = mkt.submit_coupon(ps_id)
        if not mkt.is_success(resp2):
            raise PromotionCreateError("优惠券", f"提交失败: {mkt.get_error(resp2)}")

        resp3 = mkt.confirm_coupon(ps_id)
        if not mkt.is_success(resp3):
            raise PromotionCreateError("优惠券", f"确认生效失败: {mkt.get_error(resp3)}")

        time.sleep(VALIDATION_WAIT)

        # 使用轮询等待优惠券生效
        row = wait_for_db_condition(
            db,
            "SELECT ps_id, ps_code, status FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s AND status IN (30, 50) LIMIT 1",
            (ps_id,),
            timeout=VALIDATION_WAIT + 5,
            interval=0.5
        )
        # 如果轮询超时，再查一次获取当前状态
        if not row:
            row = db.query_one(
                "SELECT ps_id, ps_code, status FROM yamibuy_mkt.mkt_promotion_schedule WHERE ps_id = %s LIMIT 1",
                (ps_id,)
            )
        ok = row is not None and row.get("status") in (30, 50)
        validation = {
            "passed": ok,
            "checks": [
                {"field": "ps_id", "expected": ps_id, "actual": row["ps_id"] if row else None, "ok": ok},
                {"field": "ps_code", "expected": ps_code, "actual": row["ps_code"] if row else None, "ok": ok},
                {"field": "status", "expected": "30/50", "actual": row["status"] if row else None, "ok": ok},
            ],
            "failed_checks": [] if ok else [{"field": "coupon", "expected": "active", "actual": "not found", "ok": False}],
            "suggestion": "" if ok else "优惠券未生效, 请检查 mkt-service 是否正常",
        }

        # 构建类型描述，让输出更清晰
        type_desc_map = {
            "discount": f"折扣券（{discount}% off）",
            "reduce": f"满减券（满${buy_amount}减${reduce_amount}）" if buy_amount and reduce_amount else "满减券",
            "cash": f"现金券（${cash_amount}）" if cash_amount else "现金券",
            "shipping": f"运费券（减${reduce_amount}）" if reduce_amount else "运费券",
        }
        
        data = {
            "ps_id": ps_id,
            "兑换码": ps_code,
            "类型": type_desc_map.get(coupon_type, coupon_type),
            "send_type": "redeem" if send_type_val == 2 else send_type,
            "coupon_amount": coupon_amount,
            "scope": scope,
        }
        if not is_shipping:
            data["coupon_form"] = coupon_form
        else:
            data["shipping_id"] = shipping_id
            data["shipping_name"] = shipping_name

        return {
            "success": ok, "env": env, "action": "create_coupon",
            "data": data,
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "create_coupon",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }
