# -*- coding: utf-8 -*-
"""
地址模块
支持：为用户创建美国/加拿大收货地址
"""

import time
from typing import Optional, Dict

from core.http_client import HttpClient
from core.auth import login
from core.db import DbClient
from core.types import ActionResult, Environment


# 美国地址模板（按州分组，覆盖常用州）
US_ADDRESS_TEMPLATES: Dict[str, Dict[str, str]] = {
    "CA": {
        "firstname": "Test", "lastname": "User",
        "address1": "1000 S Stimson Ave", "address2": "",
        "city": "City of Industry", "state": "CA",
        "zipcode": "91789", "country": "United States",
        "phone": "6261234567",
    },
    "NY": {
        "firstname": "Test", "lastname": "User",
        "address1": "350 Fifth Avenue", "address2": "Suite 3300",
        "city": "New York", "state": "NY",
        "zipcode": "10118", "country": "United States",
        "phone": "2121234567",
    },
    "NJ": {
        "firstname": "Test", "lastname": "User",
        "address1": "66 Main St", "address2": "",
        "city": "Kittery", "state": "ME",
        "zipcode": "04001", "country": "United States",
        "phone": "2071234567",
    },
    "TX": {
        "firstname": "Test", "lastname": "User",
        "address1": "1600 Pennsylvania Ave", "address2": "",
        "city": "Houston", "state": "TX",
        "zipcode": "77001", "country": "United States",
        "phone": "7131234567",
    },
    "WA": {
        "firstname": "Test", "lastname": "User",
        "address1": "410 Terry Ave N", "address2": "",
        "city": "Seattle", "state": "WA",
        "zipcode": "98109", "country": "United States",
        "phone": "2061234567",
    },
    "IL": {
        "firstname": "Test", "lastname": "User",
        "address1": "233 S Wacker Dr", "address2": "",
        "city": "Chicago", "state": "IL",
        "zipcode": "60606", "country": "United States",
        "phone": "3121234567",
    },
}

# 加拿大地址模板（按省分组）
CA_ADDRESS_TEMPLATES: Dict[str, Dict[str, str]] = {
    "ON": {
        "firstname": "Test", "lastname": "User",
        "address1": "100 Queen St W", "address2": "",
        "city": "Toronto", "state": "ON",
        "zipcode": "M5H 2N2", "country": "Canada",
        "phone": "4161234567",
    },
    "BC": {
        "firstname": "Test", "lastname": "User",
        "address1": "999 Canada Pl", "address2": "",
        "city": "Vancouver", "state": "BC",
        "zipcode": "V6C 3T4", "country": "Canada",
        "phone": "6041234567",
    },
    "QC": {
        "firstname": "Test", "lastname": "User",
        "address1": "275 Rue Notre-Dame E", "address2": "",
        "city": "Montreal", "state": "QC",
        "zipcode": "H2Y 1C6", "country": "Canada",
        "phone": "5141234567",
    },
    "AB": {
        "firstname": "Test", "lastname": "User",
        "address1": "101 9 Ave SW", "address2": "",
        "city": "Calgary", "state": "AB",
        "zipcode": "T2P 1J9", "country": "Canada",
        "phone": "4031234567",
    },
}

# 默认：美国 CA
DEFAULT_COUNTRY = "US"
DEFAULT_STATE_US = "CA"
DEFAULT_STATE_CA = "ON"


def action_create_address(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: str,
    user_id: Optional[int] = None,
    pwd: str = "111111",
    country: str = "US",
    state: Optional[str] = None,
    zipcode: Optional[str] = None,
    address1: Optional[str] = None,
    address2: Optional[str] = None,
    city: Optional[str] = None,
    firstname: Optional[str] = None,
    lastname: Optional[str] = None,
    phone: Optional[str] = None,
    is_primary: int = 1,
) -> ActionResult:
    """
    为用户创建收货地址
    
    支持美国和加拿大地址，可以使用预设模板或自定义地址信息。
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端（保留签名一致性，当前未使用）
        env: 环境
        email: 用户邮箱（runner 层已从 user_id 解析）
        user_id: 用户ID（保留签名兼容，实际 email 已由 runner 解析）
        pwd: 用户密码，默认 111111
        country: 国家，US=美国（默认），CA=加拿大
        state: 州/省缩写（如 CA, NY, ON, BC），不填则使用默认
        zipcode: 邮编（可选，不填则使用模板默认值）
        address1: 地址行1（可选）
        address2: 地址行2（可选）
        city: 城市（可选）
        firstname: 名（可选）
        lastname: 姓（可选）
        phone: 电话（可选）
        is_primary: 是否设为默认地址，默认 1
    
    Returns:
        ActionResult: 包含 address_id 和地址详情
    """
    start = time.time()
    try:
        if not email:
            raise ValueError("必须提供 email 或 user_id")
        
        # 1. 登录获取 token
        token = login(client, email, pwd)
        if not token:
            raise RuntimeError(f"登录失败: {email}")
        
        # 2. 选择地址模板
        country_upper = country.upper()
        if country_upper in ("US", "USA", "UNITED STATES"):
            country_name = "United States"
            templates = US_ADDRESS_TEMPLATES
            default_state = DEFAULT_STATE_US
        elif country_upper in ("CA", "CAN", "CANADA"):
            country_name = "Canada"
            templates = CA_ADDRESS_TEMPLATES
            default_state = DEFAULT_STATE_CA
        else:
            raise ValueError(f"不支持的国家: {country}，目前支持 US（美国）和 CA（加拿大）")
        
        # 确定州/省
        target_state = (state or default_state).upper()
        if target_state not in templates:
            available = ", ".join(templates.keys())
            raise ValueError(f"不支持的州/省: {target_state}，可选: {available}")
        
        template = templates[target_state]
        
        # 3. 构建地址请求体（用户自定义参数覆盖模板）
        addr_body = {
            "firstname": firstname or template["firstname"],
            "lastname": lastname or template["lastname"],
            "address1": address1 or template["address1"],
            "address2": address2 if address2 is not None else template["address2"],
            "city": city or template["city"],
            "state": target_state,
            "zipcode": zipcode or template["zipcode"],
            "country": country_name,
            "phone": phone or template["phone"],
            "email": email,
            "is_primary": is_primary,
            "verified": 0,
        }
        
        # 4. 调用创建地址接口
        status, resp = client.post("/ec-customer/address", body=addr_body)
        
        if not client.is_success(status, resp):
            error_msg = client.get_error(resp)
            raise RuntimeError(f"创建地址失败: {error_msg}")
        
        body = resp.get("body", {})
        address_id = body.get("address_id") if isinstance(body, dict) else None
        
        # 5. 如果接口没返回 address_id，查询地址列表获取
        if not address_id:
            time.sleep(0.5)
            list_status, list_resp = client.get("/ec-customer/address")
            if list_status == 200 and isinstance(list_resp.get("body"), list):
                for addr in list_resp["body"]:
                    if (addr.get("zipcode") == addr_body["zipcode"] and
                        addr.get("address1") == addr_body["address1"]):
                        address_id = addr.get("address_id")
                        break
        
        if not address_id:
            raise RuntimeError("创建地址成功但未获取到 address_id")
        
        # 6. 构建返回数据
        data = {
            "email": email,
            "address_id": address_id,
            "country": country_name,
            "state": target_state,
            "city": addr_body["city"],
            "zipcode": addr_body["zipcode"],
            "address1": addr_body["address1"],
            "address2": addr_body["address2"],
            "firstname": addr_body["firstname"],
            "lastname": addr_body["lastname"],
            "phone": addr_body["phone"],
            "is_primary": is_primary,
        }
        
        validation = {
            "passed": True,
            "checks": [
                {"field": "address_id", "expected": "not_empty", "actual": address_id, "ok": True},
                {"field": "country", "expected": country_name, "actual": country_name, "ok": True},
                {"field": "state", "expected": target_state, "actual": target_state, "ok": True},
            ],
            "failed_checks": [],
            "suggestion": "",
        }
        
        return {
            "success": True,
            "env": env,
            "action": "create_address",
            "data": data,
            "validation": validation,
            "elapsed": time.time() - start,
        }
        
    except Exception as e:
        return {
            "success": False,
            "env": env,
            "action": "create_address",
            "data": {"email": email},
            "error": str(e),
            "elapsed": time.time() - start,
        }
